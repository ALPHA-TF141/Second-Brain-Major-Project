from collections import Counter


class SessionSummarizer:
    def summarize(self, session, memories, app_names: list[str], topics: list[str]):
        duration = self._duration_minutes(session)
        dominant_apps = ", ".join(app_names[:3]) if app_names else "unknown apps"
        topic_text = ", ".join(topics[:3]) if topics else "captured screen activity"

        if memories:
            category = Counter(memory.category for memory in memories).most_common(1)[0][0]
        else:
            category = session.session_type or "activity"

        title = topics[0] if topics else f"{category.title()} Session"
        summary = f"User spent about {duration} minutes in a {category} session using {dominant_apps}, focused on {topic_text}."
        return {"title": title, "summary": summary, "session_type": category}

    def _duration_minutes(self, session):
        if not session.started_at:
            return 0
        end = session.ended_at or session.started_at
        return max(1, int((end - session.started_at).total_seconds() // 60))
