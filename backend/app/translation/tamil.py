def contains_tamil(text: str):
    return any("\u0b80" <= char <= "\u0bff" for char in text)


class TamilLanguageHelper:
    def detect_language(self, text: str):
        if contains_tamil(text):
            ascii_letters = sum(char.isascii() and char.isalpha() for char in text)
            return "mixed" if ascii_letters else "ta"
        return "en"

    def response_instruction(self, preference: str, detected: str):
        if preference == "ta" or detected == "ta":
            return "Reply in natural Tamil. If technical terms are clearer in English, keep them in English."
        if preference == "mixed" or detected == "mixed":
            return "Reply in natural Tamil-English mixed style when useful."
        return "Reply in clear English."


tamil_helper = TamilLanguageHelper()
