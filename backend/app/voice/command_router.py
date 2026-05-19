class VoiceCommandRouter:
    def detect_intent(self, text: str):
        lowered = text.lower()
        if "start memory capture" in lowered or "start recording" in lowered:
            return "start_capture"
        if "stop recording" in lowered or "stop capture" in lowered:
            return "stop_capture"
        if "timeline" in lowered:
            return "open_timeline"
        if "open ai chat" in lowered or "chat" in lowered:
            return "open_chat"
        if "search" in lowered:
            return "semantic_search"
        return "ask_memory"


voice_command_router = VoiceCommandRouter()
