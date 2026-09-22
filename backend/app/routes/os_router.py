import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.routes.os_store import os_store

router = APIRouter(prefix="/api/os", tags=["os"])


class TaskPayload(BaseModel):
    title: str
    project: Optional[str] = "General"
    priority: Optional[str] = "medium"
    due_date: Optional[str] = None
    status: Optional[str] = "pending"


class ReminderPayload(BaseModel):
    text: str
    remind_at: str
    recurring: Optional[str] = "None"


class CalendarPayload(BaseModel):
    title: str
    start_time: str
    end_time: str
    location: Optional[str] = "Virtual"
    project_id: Optional[str] = "General"
    ai_insight: Optional[str] = ""


class AutomationPayload(BaseModel):
    name: str
    trigger: str
    schedule: Optional[str] = "Custom"
    tools: List[str]
    ai_analysis: str
    action: str


# ============ 1. DAILY INTELLIGENCE & HOME SUMMARY ============

@router.get("/intelligence")
def get_daily_intelligence():
    """Returns the comprehensive home intelligence summary:
    - 'While you were away' metrics
    - 'What needs your attention?' priority items
    """
    tasks = os_store.get_tasks()
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    tasks_due_today = [t for t in tasks if t.get("due_date") == today_str and t.get("status") != "completed"]
    reminders = os_store.get_reminders()
    active_reminders = [r for r in reminders if r.get("status") == "active"]
    automations = os_store.get_automations()
    active_automations = [a for a in automations if a.get("status") == "active"]
    events = os_store.get_calendar_events()

    attention_items = []
    # Real priority attention items based on actual store
    if tasks_due_today:
        attention_items.append({
            "id": "att_1",
            "type": "deadline",
            "title": "Immediate Priority Due Today",
            "description": f"'{tasks_due_today[0]['title']}' is due for completion today.",
            "action_label": "View Tasks",
            "target": "/tasks",
        })

    if events:
        attention_items.append({
            "id": "att_2",
            "type": "calendar",
            "title": f"Upcoming Session: {events[0]['title']}",
            "description": f"Scheduled at {events[0]['start_time']}. AI Insight: {events[0].get('ai_insight', 'Review materials.')}",
            "action_label": "View Schedule",
            "target": "/calendar",
        })

    if active_reminders:
        attention_items.append({
            "id": "att_3",
            "type": "reminder",
            "title": f"Active Reminder: {active_reminders[0]['text']}",
            "description": f"Set for {active_reminders[0].get('remind_at')}.",
            "action_label": "View Reminders",
            "target": "/reminders",
        })

    return {
        "greeting": "Good day, Immanuel",
        "timestamp": datetime.utcnow().isoformat(),
        "while_you_were_away": {
            "emails_unread": 0,
            "notifications_count": len(attention_items) + 2,
            "calendar_events_today": len(events),
            "tasks_due_today": len(tasks_due_today),
            "reminders_active": len(active_reminders),
            "automated_actions_completed": len(active_automations),
        },
        "attention_items": attention_items,
    }


# ============ 2. TASKS WORKSPACE ============

@router.get("/tasks")
def list_tasks():
    return os_store.get_tasks()


@router.post("/tasks")
def create_task(payload: TaskPayload):
    return os_store.add_task(payload.model_dump())


@router.put("/tasks/{task_id}")
def update_task(task_id: str, updates: dict):
    updated = os_store.update_task(task_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    os_store.delete_task(task_id)
    return {"status": "deleted"}


# ============ 3. REMINDERS ============

@router.get("/reminders")
def list_reminders():
    return os_store.get_reminders()


@router.post("/reminders")
def create_reminder(payload: ReminderPayload):
    return os_store.add_reminder(payload.model_dump())


@router.put("/reminders/{rem_id}/toggle")
def toggle_reminder(rem_id: str):
    res = os_store.toggle_reminder(rem_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return res


# ============ 4. CALENDAR ============

@router.get("/calendar")
def list_calendar_events():
    return os_store.get_calendar_events()


@router.post("/calendar")
def create_calendar_event(payload: CalendarPayload):
    return os_store.add_calendar_event(payload.model_dump())


# ============ 5. PROJECTS ============

@router.get("/projects")
def list_projects():
    return os_store.get_projects()


@router.get("/projects/{project_id}")
def get_project_detail(project_id: str):
    proj = os_store.get_project_detail(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


# ============ 6. AUTOMATIONS ============

@router.get("/automations")
def list_automations():
    return os_store.get_automations()


@router.post("/automations")
def create_automation(payload: AutomationPayload):
    return os_store.add_automation(payload.model_dump())


@router.post("/automations/{auto_id}/toggle")
def toggle_automation(auto_id: str):
    res = os_store.toggle_automation(auto_id)
    if not res:
        raise HTTPException(status_code=404, detail="Automation not found")
    return res


@router.post("/automations/{auto_id}/run")
def run_automation(auto_id: str):
    res = os_store.run_automation_now(auto_id)
    if not res:
        raise HTTPException(status_code=404, detail="Automation not found")
    return res


# ============ 7. AGENT ACTIVITY AUDIT ============

@router.get("/activity")
def list_agent_activity():
    return os_store.get_activities()


# ============ 8. INTEGRATIONS ============

@router.get("/notifications")
def list_notifications(limit: int = 50):
    """Real notifications produced by agents (mail ingestion, insights)."""
    return os_store.get_notifications(limit=limit)


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str):
    item = os_store.mark_notification_read(notification_id)
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item


@router.delete("/notifications")
def clear_notifications(only_read: bool = True):
    return {"removed": os_store.clear_notifications(only_read=only_read)}


@router.get("/integrations")
def list_integrations():
    return os_store.get_integrations()


@router.post("/integrations/{service_key}")
def update_integration(service_key: str, payload: dict):
    return os_store.update_integration(service_key, payload)


# ============ 9. UNIVERSAL CROSS-MODULE SEARCH ============

@router.get("/search")
def universal_search(q: str = ""):
    """Searches across Tasks, Projects, Master Wiki, Knowledge Cards, and Graph."""
    query = q.strip().lower()
    if not query:
        return {"results": []}

    results = []

    # 1. Search Tasks
    for t in os_store.get_tasks():
        if query in t.get("title", "").lower() or query in t.get("project", "").lower():
            results.append({
                "type": "task",
                "title": t.get("title"),
                "subtitle": f"Task · {t.get('project')} · Due: {t.get('due_date')}",
                "target": "/tasks",
            })

    # 2. Search Projects
    for p in os_store.get_projects():
        if query in p.get("name", "").lower() or query in p.get("description", "").lower():
            results.append({
                "type": "project",
                "title": p.get("name"),
                "subtitle": f"Project · {p.get('status')} · {p.get('description')[:60]}...",
                "target": f"/projects",
            })

    # 3. Search Master Wiki
    wiki_dir = Path("memory_vault/wiki")
    if wiki_dir.exists():
        for f in wiki_dir.rglob("*.md"):
            if f.name == "INDEX.md":
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            if query in f.name.lower() or query in text.lower():
                results.append({
                    "type": "wiki",
                    "title": f.stem.replace("_", " ").title(),
                    "subtitle": f"Master Wiki Article · Domain: {f.parent.name.title()}",
                    "target": "/knowledge",
                })

    # 4. Search Knowledge Cards
    cards_dir = Path("memory_vault/cards")
    if cards_dir.exists():
        for cf in sorted(cards_dir.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
            try:
                card = json.loads(cf.read_text(encoding="utf-8"))
                if query in card.get("topic", "").lower() or query in card.get("summary", "").lower():
                    results.append({
                        "type": "card",
                        "title": card.get("topic") or card.get("window_title"),
                        "subtitle": f"Knowledge Card · {card.get('domain')} · {card.get('summary')[:50]}...",
                        "target": "/knowledge",
                    })
            except Exception:
                pass

    return {"query": q, "count": len(results), "results": results[:25]}
