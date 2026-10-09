"""
Contribution 3 (Neural Extension) - Lightweight ONNX Natural Language Inference
===========================================================================
Replaces or augments heuristic string/regex contradiction detection with a
quantized Cross-Encoder NLI model running on pure CPU via ONNX Runtime.

Model: DistilBERT-base-uncased-MNLI INT8 (~64 MB, ~15ms inference on CPU).
Classes:
  0: ENTAILMENT
  1: NEUTRAL
  2: CONTRADICTION

Provides continuous calibrated contradiction probabilities:
  severity s = P(Contradiction)
which directly powers the rank damping multiplier:
  multiplier = 1.0 - (0.7 * s)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_REPO = "onnx-community/distilbert-base-uncased-mnli-ONNX"
DEFAULT_MODEL_FILE = "onnx/model_int8.onnx"


class NeuralNLIClassifier:
    """
    Lightweight, thread-safe NLI classifier backed by ONNX Runtime.
    Lazy-loads weights on first call. Gracefully degrades to None if unavailable.
    """

    def __init__(self, repo_id: str = DEFAULT_REPO, model_file: str = DEFAULT_MODEL_FILE):
        self.repo_id = repo_id
        self.model_file = model_file
        self._session = None
        self._tokenizer = None
        self._initialized = False
        self._available = False
        self._init_error: Optional[str] = None

    def _initialize(self) -> bool:
        if self._initialized:
            return self._available

        self._initialized = True
        try:
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
            import onnxruntime as ort

            model_path = hf_hub_download(self.repo_id, self.model_file)
            tok_path = hf_hub_download(self.repo_id, "tokenizer.json")

            self._tokenizer = Tokenizer.from_file(tok_path)

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = min(4, max(1, os.cpu_count() or 1))
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self._session = ort.InferenceSession(
                model_path,
                sess_options=opts,
                providers=["CPUExecutionProvider"],
            )
            self._available = True
            logger.info("NeuralNLIClassifier successfully initialized (ONNX CPU).")
        except Exception as e:
            self._available = False
            self._init_error = str(e)
            logger.warning("NeuralNLIClassifier failed to initialize: %s. Falling back to rule-based.", e)

        return self._available

    def is_available(self) -> bool:
        return self._initialize()

    def predict_pair(self, premise: str, hypothesis: str) -> Optional[Dict[str, float]]:
        """
        Compute NLI softmax probabilities for (premise, hypothesis).

        Returns:
          {
            "entailment": float,
            "neutral": float,
            "contradiction": float
          } or None if model unavailable.
        """
        if not self._initialize():
            return None

        premise = (premise or "").strip()
        hypothesis = (hypothesis or "").strip()
        if not premise or not hypothesis:
            return None

        try:
            encoding = self._tokenizer.encode(premise, hypothesis)
            input_ids = np.array([encoding.ids], dtype=np.int64)
            attention_mask = np.array([encoding.attention_mask], dtype=np.int64)

            outputs = self._session.run(
                None,
                {"input_ids": input_ids, "attention_mask": attention_mask},
            )
            logits = outputs[0][0]
            # Softmax
            exp = np.exp(logits - np.max(logits))
            probs = exp / np.sum(exp)

            # Class mapping: 0 -> Entailment, 1 -> Neutral, 2 -> Contradiction
            return {
                "entailment": float(probs[0]),
                "neutral": float(probs[1]),
                "contradiction": float(probs[2]),
            }
        except Exception as e:
            logger.warning("NLI inference error: %s", e)
            return None

    def classify_conflict(
        self,
        text_a: str,
        text_b: str,
        threshold: float = 0.50,
    ) -> Tuple[bool, float, str]:
        """
        Check bidirectional contradiction between text_a and text_b.

        Returns:
          (is_conflict, severity, dominant_label)
        """
        probs_ab = self.predict_pair(text_a, text_b)
        probs_ba = self.predict_pair(text_b, text_a)

        if not probs_ab and not probs_ba:
            return False, 0.0, "unknown"

        p_contra_ab = probs_ab["contradiction"] if probs_ab else 0.0
        p_contra_ba = probs_ba["contradiction"] if probs_ba else 0.0
        max_contra = max(p_contra_ab, p_contra_ba)

        is_conflict = max_contra >= threshold
        dominant = "contradiction" if is_conflict else "consistent"
        return is_conflict, round(float(max_contra), 4), dominant


neural_nli = NeuralNLIClassifier()
