class OCREngine:
    def extract_text(self, prepared_image, language: str = "eng+tam"):
        tesseract_text = self._run_tesseract(prepared_image, language)
        if tesseract_text.strip():
            return {"engine": "tesseract", "text": tesseract_text, "language": language}

        paddle_text = self._run_paddle(prepared_image)
        return {"engine": "paddleocr", "text": paddle_text, "language": language}

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
        try:
            from paddleocr import PaddleOCR

            ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            result = ocr.ocr(prepared_image, cls=True)
            lines = []
            for page in result or []:
                for item in page or []:
                    if len(item) >= 2:
                        lines.append(item[1][0])
            return "\n".join(lines)
        except Exception:
            return ""
