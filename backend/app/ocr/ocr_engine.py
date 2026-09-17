import os
import sys

def _configure_tesseract():
    try:
        import pytesseract
        # Auto-detect Tesseract binary on Windows
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                pytesseract.pytesseract.tesseract_cmd = c
                print(f"[OCR] Located Tesseract binary at: {c}")
                break
    except Exception:
        pass

_configure_tesseract()


class OCREngine:
    def __init__(self):
        self._paddle = None
        self._paddle_failed = False

    def extract_text(self, prepared_image, language: str = "eng+tam"):
        tesseract_text = self._run_tesseract(prepared_image, language)
        if tesseract_text.strip():
            return {"engine": "tesseract", "text": tesseract_text, "language": language}

        paddle_text = self._run_paddle(prepared_image)
        if paddle_text.strip():
            return {"engine": "paddleocr", "text": paddle_text, "language": language}

        return {"engine": "none", "text": "", "language": language}

    def _run_tesseract(self, prepared_image, language: str):
        try:
            import pytesseract

            config = "--psm 6"
            return pytesseract.image_to_string(prepared_image, lang=language, config=config)
        except Exception:
            if language != "eng":
                try:
                    import pytesseract

                    return pytesseract.image_to_string(prepared_image, lang="eng", config="--psm 6")
                except Exception:
                    return ""
            return ""

    def _run_paddle(self, prepared_image):
        if self._paddle_failed:
            return ""

        try:
            if self._paddle is None:
                from paddleocr import PaddleOCR
                self._paddle = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)

            result = self._paddle.ocr(prepared_image, cls=False)
            lines = []
            for page in result or []:
                for item in page or []:
                    if len(item) >= 2:
                        lines.append(item[1][0])
            return "\n".join(lines)
        except Exception as exc:
            self._paddle_failed = True
            print(f"[OCR] PaddleOCR fallback notice: {exc}")
            return ""
