import base64
from datetime import datetime
from pathlib import Path

from app.models.voice import ConversationAudio, LanguagePreference, Transcript, VoiceCommand, VoiceSession
from app.rag.pipeline import rag_pipeline
from app.translation.tamil import tamil_helper
from app.tts.coqui_tts import coqui_tts
from app.voice.command_router import voice_command_router
from app.wakeword.wakeword_detector import wakeword_detector


class VoiceOrchestrator:
    def __init__(self, storage_dir: str = "data/voice/input"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def get_preferences(self, db, user_id: int):
        prefs = db.query(LanguagePreference).filter(LanguagePreference.user_id == user_id).first()
        if not prefs:
            prefs = LanguagePreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs

    def start_session(self, db, user_id: int, payload: dict):
        prefs = self.get_preferences(db, user_id)
        session = VoiceSession(
            user_id=user_id,
            mode=payload.get("mode", "continuous"),
            language=payload.get("language", prefs.preferred_language),
            conversation_id=payload.get("conversation_id"),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def store_audio_chunk(self, db, session_id: int, audio_base64: str):
        raw = base64.b64decode(audio_base64)
        file_path = self.storage_dir / f"voice_{session_id}_{datetime.utcnow().strftime('%H%M%S_%f')}.webm"
        file_path.write_bytes(raw)
        audio = ConversationAudio(voice_session_id=session_id, file_path=str(file_path), direction="input")
        db.add(audio)
        db.commit()
        return audio

    async def handle_text(self, db, user_id: int, session: VoiceSession, text: str, force: bool = False):
        prefs = self.get_preferences(db, user_id)
        wake_words = [word.strip() for word in prefs.wake_words.split(",")]
        detected_language = tamil_helper.detect_language(text)

        should_answer = force or session.mode in {"continuous", "push_to_talk"}
        if session.mode == "wake_word":
            should_answer = wakeword_detector.is_wake_phrase(text, wake_words)
            text = wakeword_detector.strip_wake_phrase(text, wake_words)

        transcript = Transcript(
            voice_session_id=session.id,
            speaker="user",
            text=text,
            language=detected_language,
            confidence=0.95 if force else 0.75,
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        intent = voice_command_router.detect_intent(text)
        command = VoiceCommand(voice_session_id=session.id, command_text=text, intent=intent)
        db.add(command)
        db.commit()

        if not should_answer or not text:
            return {"transcript": transcript, "intent": intent, "answer": "", "references": [], "audio": ""}

        question = self._augment_question(text, prefs.reply_language, detected_language, intent)
        answer = ""
        references = []
        async for event in rag_pipeline.answer_stream(db, user_id, question, session.conversation_id, self._mode_for_intent(intent)):
            if event["type"] == "conversation":
                session.conversation_id = event["conversation_id"]
            elif event["type"] == "references":
                references = event["items"]
            elif event["type"] == "token":
                answer += event["token"]

        assistant_transcript = Transcript(
            voice_session_id=session.id,
            speaker="assistant",
            text=answer,
            language=prefs.reply_language if prefs.reply_language != "auto" else detected_language,
            confidence=1.0,
        )
        db.add(assistant_transcript)
        command.result = answer[:1000]
        db.commit()

        audio_result = coqui_tts.synthesize(answer, prefs.voice_model)
        if audio_result["file_path"]:
            db.add(ConversationAudio(voice_session_id=session.id, transcript_id=assistant_transcript.id, file_path=audio_result["file_path"], direction="output"))
            db.commit()

        return {"transcript": transcript, "intent": intent, "answer": answer, "references": references, "audio": audio_result["file_path"]}

    def _augment_question(self, text: str, reply_language: str, detected_language: str, intent: str):
        instruction = tamil_helper.response_instruction(reply_language, detected_language)
        if intent != "ask_memory":
            return f"{text}\n\nVoice command intent: {intent}. {instruction}"
        return f"{text}\n\n{instruction}"

    def _mode_for_intent(self, intent: str):
        if intent in {"open_timeline", "semantic_search"}:
            return "timeline"
        if intent == "start_capture":
            return "summary"
        return "teaching"


voice_orchestrator = VoiceOrchestrator()
