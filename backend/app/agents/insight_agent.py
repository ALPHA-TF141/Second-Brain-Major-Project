import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.agents.card_schema import JSONMemoryCard
from app.config import settings
from app.database.session import SessionLocal
from app.llm.llm_client import llm_client
from app.models.capture import ActivityLog, AppUsage
from app.websocket.manager import manager


class InsightCollisionAgent:
    """The Proactive Intelligence Core of Jarvis:
    1. Detects 'Insight Collisions': Analyzes active window & screen captures against
       past memory cards to spot hidden connections, answers to past bugs, and complementary research.
    2. Proactively broadcasts HUD alerts to Electron via WebSockets without the user asking.
    3. Synthesizes the 'Daily Executive Briefing': Formulates an Iron Man style morning
       audio-briefing summarizing yesterday's breakthroughs, active topics, and open gaps.
    """

    def __init__(self, history_capacity: int = 50):
        self.recent_insights: List[Dict] = []
        self._last_collision_time = datetime.min
        self.cached_briefing: Optional[Dict] = None

    async def evaluate_collision(self, current_card: JSONMemoryCard, recent_cards: List[JSONMemoryCard]) -> Optional[Dict]:
        """Compares current screen/web activity against recent sessions to spot proactive connections."""
        now = datetime.utcnow()
        # Rate limit proactive interruptions to at most once every 3 minutes
        if (now - self._last_collision_time) < timedelta(minutes=3):
            return None

        if not recent_cards:
            return None

        # Filter candidate targets from different apps or older sessions
        candidates = [c for c in recent_cards if c.id != current_card.id and c.app_source != current_card.app_source]
        if not candidates:
            return None

        # Find overlapping entities or complementary domains
        curr_entities = set(e.lower() for e in current_card.entities)
        for prev in candidates[:10]:
            prev_entities = set(e.lower() for e in prev.entities)
            overlap = curr_entities.intersection(prev_entities)

            # Direct conceptual collision
            if overlap or (current_card.domain == prev.domain and current_card.priority == "high" and prev.priority == "high"):
                connection_topic = list(overlap)[0].title() if overlap else current_card.topic
                insight = {
                    "id": f"insight_{now.strftime('%Y%m%d_%H%M%S')}",
                    "timestamp": now.isoformat() + "Z",
                    "title": f"Cognitive Collision: {connection_topic}",
                    "connection": f"Your active session in {current_card.app_source} directly relates to earlier research in {prev.app_source} regarding '{prev.topic}'.",
                    "source_app": current_card.app_source,
                    "target_app": prev.app_source,
                    "action_suggestion": f"Review key pointers from {prev.topic} to accelerate current work.",
                    "related_card_id": prev.id,
                    "current_card_id": current_card.id,
                }

                self.recent_insights.append(insight)
                self.recent_insights = self.recent_insights[-30:]
                self._last_collision_time = now

                # Proactively broadcast to Electron Stark HUD
                await manager.broadcast({
                    "type": "proactive_insight",
                    "data": insight,
                    "timestamp": now.isoformat()
                })
                print(f"[InsightAgent] ⚡ Proactive Collision Detected: {insight['title']}")
                return insight

        return None

    async def generate_daily_briefing(self, db_session) -> Dict:
        """Synthesizes an executive Iron Man style morning audio-briefing based on recent memory cards & activity."""
        now = datetime.utcnow()
        now_date_str = now.strftime("%A, %B %d")

        # 1. Fetch recent activity from the last 24-48 hours
        activities = (
            db_session.query(ActivityLog)
            .order_by(ActivityLog.created_at.desc())
            .limit(40)
            .all()
        )
        apps = (
            db_session.query(AppUsage.app_name)
            .order_by(AppUsage.started_at.desc())
            .limit(25)
            .all()
        )

        top_apps = list(set([a[0] for a in apps if a[0]]))[:4]
        recent_topics = [a.title for a in activities if a.activity_type == "window"][:6]

        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You are JARVIS, Tony Stark's personal AI operating system. "
                    "Synthesize a concise, witty, highly professional 45-second morning intelligence briefing. "
                    "Tone: calm, subtle British wit, exceptionally sharp, confident. "
                    "Format: exactly 3-4 natural spoken sentences. "
                    "Address the user as 'Sir'. State what they focused on recently, their active domains, "
                    "and one proactive priority for today. Do NOT use bullet points or markdown asterisks."
                ),
            },
            {
                "role": "user",
                "content": f"Current Date: {now_date_str}. Recent active tools: {', '.join(top_apps)}. Recent topics: {', '.join(recent_topics)}.",
            },
        ]

        spoken_script = ""
        try:
            async for token in llm_client.stream(prompt_messages, []):
                spoken_script += token
        except Exception:
            spoken_script = (
                f"Good morning, Sir. Today is {now_date_str}. Your recent telemetry shows intensive focus across "
                f"{', '.join(top_apps) if top_apps else 'your core engineering modules'}. "
                "I have compiled your memory cards and synchronized the knowledge graph. All systems are operating at peak efficiency."
            )

        spoken_script = spoken_script.strip()

        briefing = {
            "date": now_date_str,
            "spoken_script": spoken_script,
            "primary_focus": top_apps[0] if top_apps else "Engineering & Research",
            "active_domains": ["Technology", "Science", "Geopolitics"],
            "generated_at": now.isoformat() + "Z",
            "key_priorities": [
                f"Continue deep synthesis on {recent_topics[0] if recent_topics else 'core architecture'}",
                "Review proactive insights from recent knowledge captures",
                "Maintain autonomous GitHub memory vault synchronization",
            ],
        }

        self.cached_briefing = briefing
        return briefing


insight_agent = InsightCollisionAgent()
