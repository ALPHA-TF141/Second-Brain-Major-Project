from hashlib import sha1

import pyperclip


class ClipboardTracker:
    def __init__(self):
        self.last_hash = ""

    def read_change(self):
        try:
            text = pyperclip.paste()
        except pyperclip.PyperclipException:
            return None

        if not text or not isinstance(text, str):
            return None

        text = text.strip()
        if not text:
            return None

        text_hash = sha1(text.encode("utf-8", errors="ignore")).hexdigest()
        if text_hash == self.last_hash:
            return None

        self.last_hash = text_hash
        preview = text[:500]
        return {"text_preview": preview, "text_hash": text_hash}
