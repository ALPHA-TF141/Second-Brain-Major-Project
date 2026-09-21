import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class OSDataStore:
    def __init__(self, data_path: str = "data/os_store.json"):
        self.data_file = Path(data_path)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_data()

    def _init_data(self):
        if not self.data_file.exists():
            default_data = {
                "tasks": [
                    {
                        "id": "task_1",
                        "title": "Review IEEE Paper Proposal Draft with Faculty",
                        "project": "Second Brain Research",
                        "priority": "high",
                        "due_date": datetime.utcnow().strftime("%Y-%m-%d"),
                        "status": "pending",
                        "ai_suggested": False,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                    {
                        "id": "task_2",
                        "title": "Evaluate Air Pollution ML Model (Random Forest on AQI Dataset)",
                        "project": "Air Pollution Project",
                        "priority": "high",
                        "due_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                        "status": "pending",
                        "ai_suggested": True,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                    {
                        "id": "task_3",
                        "title": "Verify Sub-Second YouTube Transcript Extraction Pipeline",
                        "project": "Jarvis Core",
                        "priority": "medium",
                        "due_date": datetime.utcnow().strftime("%Y-%m-%d"),
                        "status": "completed",
                        "ai_suggested": False,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                    {
                        "id": "task_4",
                        "title": "Test Local Qwen 2.5 Inference Latency on RTX 3050 GPU",
                        "project": "Jarvis Core",
                        "priority": "medium",
                        "due_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
                        "status": "pending",
                        "ai_suggested": False,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                ],
                "reminders": [
                    {
                        "id": "rem_1",
                        "text": "Submit project documentation to department head",
                        "remind_at": datetime.utcnow().strftime("%Y-%m-%d 17:00"),
                        "recurring": "None",
                        "status": "active",
                    },
                    {
                        "id": "rem_2",
                        "text": "Synchronize memory vault with GitHub repository",
                        "remind_at": datetime.utcnow().strftime("%Y-%m-%d 20:00"),
                        "recurring": "Daily",
                        "status": "active",
                    },
                ],
                "calendar_events": [
                    {
                        "id": "evt_1",
                        "title": "AI Project Progress Review Meeting",
                        "start_time": (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:00"),
                        "end_time": (datetime.utcnow() + timedelta(hours=4)).strftime("%Y-%m-%d %H:00"),
                        "location": "Seminar Hall / Online",
                        "project_id": "Second Brain Research",
                        "ai_insight": "Review presentation slides and live 3D graph demo beforehand.",
                    },
                    {
                        "id": "evt_2",
                        "title": "Air Pollution Dataset Validation Workshop",
                        "start_time": (datetime.utcnow() + timedelta(days=1, hours=2)).strftime("%Y-%m-%d 10:00"),
                        "end_time": (datetime.utcnow() + timedelta(days=1, hours=3)).strftime("%Y-%m-%d 11:30"),
                        "location": "Systems Lab",
                        "project_id": "Air Pollution Project",
                        "ai_insight": "Prepare AQI data correlation graphs.",
                    },
                ],
                "projects": [
                    {
                        "id": "proj_1",
                        "name": "Second Brain AI Operating System",
                        "description": "Autonomous multimodal personal knowledge synthesizer with on-device graph RAG.",
                        "status": "active",
                        "deadline": "2026-10-15",
                        "tags": ["AI", "Architecture", "Python", "React", "Ollama"],
                        "task_count": 4,
                        "notes_count": 12,
                        "files_count": 8,
                    },
                    {
                        "id": "proj_2",
                        "name": "Air Pollution Analysis & AQI Forecasting",
                        "description": "Machine learning system predicting regional air quality indices using Random Forest & XGBoost.",
                        "status": "active",
                        "deadline": "2026-11-01",
                        "tags": ["Machine Learning", "Python", "Data Science", "Research"],
                        "task_count": 3,
                        "notes_count": 7,
                        "files_count": 5,
                    },
                    {
                        "id": "proj_3",
                        "name": "Autonomous Cognitive Agent Swarm",
                        "description": "Multi-agent framework orchestrating sensory capture, wiki distillation, and git sync.",
                        "status": "active",
                        "deadline": "2026-09-30",
                        "tags": ["Multi-Agent", "LLM", "Automation"],
                        "task_count": 2,
                        "notes_count": 5,
                        "files_count": 4,
                    },
                ],
                "automations": [
                    {
                        "id": "auto_1",
                        "name": "Daily Morning Intelligence Briefing",
                        "trigger": "Every day at 8:00 AM",
                        "schedule": "0 8 * * *",
                        "tools": ["Gmail", "Calendar", "Tasks", "Memory Vault"],
                        "ai_analysis": "Identify urgent deadlines, unread priority emails, and synthesize 3-bullet trajectory.",
                        "action": "Generate Jarvis Voice Briefing and HUD Summary",
                        "status": "active",
                        "last_run": datetime.utcnow().strftime("%Y-%m-%d 08:00 UTC"),
                    },
                    {
                        "id": "auto_2",
                        "name": "Autonomous Screen Knowledge Distillation",
                        "trigger": "Continuous desktop activity capture",
                        "schedule": "Real-time (5s poll)",
                        "tools": ["Screen OCR", "Curation Agent", "Wiki Compiler"],
                        "ai_analysis": "Filter redundant frames, elect Hero capture, prune 3MB bitmaps, and compile wiki.",
                        "action": "Sync memory cards to GitHub Vault",
                        "status": "active",
                        "last_run": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    },
                    {
                        "id": "auto_3",
                        "name": "Academic Paper & ArXiv Ingestion",
                        "trigger": "When PDF or Research URL is browsed",
                        "schedule": "Event-driven",
                        "tools": ["Web Scraper", "Semantic Chunker", "Knowledge Graph"],
                        "ai_analysis": "Extract abstract, methodology, and citations; link with active projects.",
                        "action": "Create Master Topic Wiki Page",
                        "status": "active",
                        "last_run": (datetime.utcnow() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M UTC"),
                    },
                ],
                "agent_activity": [
                    {
                        "id": "act_1",
                        "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                        "type": "briefing",
                        "title": "Synthesized Daily Executive Briefing",
                        "status": "success",
                        "details": "Compiled 3 active project priorities and verified hardware readiness on RTX 3050.",
                    },
                    {
                        "id": "act_2",
                        "timestamp": (datetime.utcnow() - timedelta(minutes=6)).strftime("%H:%M:%S"),
                        "type": "vault_sync",
                        "title": "Autonomous Git Memory Vault Pushed",
                        "status": "success",
                        "details": "Committed knowledge cards, hero captures, and graph updates to GitHub repository.",
                    },
                    {
                        "id": "act_3",
                        "timestamp": (datetime.utcnow() - timedelta(minutes=14)).strftime("%H:%M:%S"),
                        "type": "curation",
                        "title": "Hero Frame Elected & Ephemeral Bitmaps Pruned",
                        "status": "success",
                        "details": "Evaluated Information Density S(Ft) = 84.5. Preserved 80KB WebP anchor and purged raw image.",
                    },
                    {
                        "id": "act_4",
                        "timestamp": (datetime.utcnow() - timedelta(minutes=28)).strftime("%H:%M:%S"),
                        "type": "ingestion",
                        "title": "Native YouTube Transcript Ingested",
                        "status": "success",
                        "details": "Extracted 983 characters of spoken audio transcript in 0.98s with zero paid API fees.",
                    },
                ],
                "integrations": {
                    "gmail": {
                        "connected": False,
                        "email": "",
                        "service_name": "Google Workspace / Gmail",
                        "description": "Inbox search, task extraction, meeting identification, and automated draft synthesis.",
                        "permissions": ["Read Inbox", "Draft Replies", "Detect Deadlines"],
                    },
                    "calendar": {
                        "connected": False,
                        "email": "",
                        "service_name": "Google Calendar",
                        "description": "Event synchronization, schedule conflict detection, and AI timeline intelligence.",
                        "permissions": ["Read Events", "Schedule Reminders"],
                    },
                    "github": {
                        "connected": True,
                        "account": "ALPHA-TF141",
                        "repo": "ALPHA-TF141/Second-Brain-Major-Project",
                        "service_name": "GitHub Memory Layer",
                        "description": "24/7 autonomous version-controlled backup of all knowledge cards and master wiki articles.",
                        "permissions": ["SSH Deploy Key (Write Access)"],
                    },
                    "ollama": {
                        "connected": True,
                        "model": "qwen2.5:3b",
                        "endpoint": "http://localhost:11434",
                        "service_name": "Local LLM Acceleration",
                        "description": "100% private on-device reasoning accelerated by NVIDIA GeForce RTX 3050 Laptop GPU.",
                        "permissions": ["Direct Native Streaming"],
                    },
                    "scraper": {
                        "connected": True,
                        "service_name": "Native Social Media & Web Engine",
                        "description": "Self-hosted zero-fee scraping for YouTube audio transcripts, Tweets, and research articles.",
                        "permissions": ["Sub-Second Extraction"],
                    },
                },
                "gmail_messages": [],
            }
            self.data_file.write_text(json.dumps(default_data, indent=2), encoding="utf-8")

    def _read(self) -> Dict[str, Any]:
        try:
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception:
            self._init_data()
            return json.loads(self.data_file.read_text(encoding="utf-8"))

    def _write(self, data: Dict[str, Any]):
        self.data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Tasks
    def get_tasks(self) -> List[Dict]:
        return self._read().get("tasks", [])

    def add_task(self, task: Dict) -> Dict:
        data = self._read()
        task["id"] = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        task["created_at"] = datetime.utcnow().isoformat()
        if "status" not in task:
            task["status"] = "pending"
        data.setdefault("tasks", []).insert(0, task)
        self._write(data)
        self.add_activity("task", f"Created task: {task['title']}", "success", f"Project: {task.get('project', 'General')}")
        return task

    def update_task(self, task_id: str, updates: Dict) -> Optional[Dict]:
        data = self._read()
        tasks = data.get("tasks", [])
        for t in tasks:
            if t["id"] == task_id:
                t.update(updates)
                self._write(data)
                return t
        return None

    def delete_task(self, task_id: str) -> bool:
        data = self._read()
        tasks = data.get("tasks", [])
        data["tasks"] = [t for t in tasks if t["id"] != task_id]
        self._write(data)
        return True

    # Reminders
    def get_reminders(self) -> List[Dict]:
        return self._read().get("reminders", [])

    def add_reminder(self, reminder: Dict) -> Dict:
        data = self._read()
        reminder["id"] = f"rem_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        reminder["status"] = "active"
        data.setdefault("reminders", []).insert(0, reminder)
        self._write(data)
        self.add_activity("reminder", f"Set reminder: {reminder['text']}", "success", f"Trigger: {reminder.get('remind_at')}")
        return reminder

    def toggle_reminder(self, rem_id: str) -> Optional[Dict]:
        data = self._read()
        for r in data.get("reminders", []):
            if r["id"] == rem_id:
                r["status"] = "completed" if r["status"] == "active" else "active"
                self._write(data)
                return r
        return None

    # Calendar
    def get_calendar_events(self) -> List[Dict]:
        return self._read().get("calendar_events", [])

    def add_calendar_event(self, event: Dict) -> Dict:
        data = self._read()
        event["id"] = f"evt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        data.setdefault("calendar_events", []).append(event)
        self._write(data)
        self.add_activity("calendar", f"Scheduled: {event['title']}", "success", f"Time: {event.get('start_time')}")
        return event

    # Projects
    def get_projects(self) -> List[Dict]:
        return self._read().get("projects", [])

    def get_project_detail(self, proj_id: str) -> Optional[Dict]:
        data = self._read()
        for p in data.get("projects", []):
            if p["id"] == proj_id:
                # Attach tasks
                tasks = [t for t in data.get("tasks", []) if t.get("project") == p["name"]]
                events = [e for e in data.get("calendar_events", []) if e.get("project_id") == p["name"] or e.get("project_id") == p["id"]]
                return {**p, "tasks": tasks, "events": events}
        return None

    # Automations
    def get_automations(self) -> List[Dict]:
        return self._read().get("automations", [])

    def add_automation(self, automation: Dict) -> Dict:
        data = self._read()
        automation["id"] = f"auto_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        automation["status"] = "active"
        automation["last_run"] = "Never"
        data.setdefault("automations", []).insert(0, automation)
        self._write(data)
        self.add_activity("automation", f"Installed workflow: {automation['name']}", "success", automation.get("trigger", ""))
        return automation

    def toggle_automation(self, auto_id: str) -> Optional[Dict]:
        data = self._read()
        for a in data.get("automations", []):
            if a["id"] == auto_id:
                a["status"] = "paused" if a["status"] == "active" else "active"
                self._write(data)
                return a
        return None

    def run_automation_now(self, auto_id: str) -> Optional[Dict]:
        data = self._read()
        for a in data.get("automations", []):
            if a["id"] == auto_id:
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                a["last_run"] = now_str
                self._write(data)
                self.add_activity("automation_run", f"Executed workflow: {a['name']}", "success", f"Triggered on-demand at {now_str}")
                return a
        return None

    # Activity Log
    def get_activities(self) -> List[Dict]:
        return self._read().get("agent_activity", [])

    def add_activity(self, act_type: str, title: str, status: str, details: str):
        data = self._read()
        item = {
            "id": f"act_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:19]}",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "type": act_type,
            "title": title,
            "status": status,
            "details": details,
        }
        data.setdefault("agent_activity", []).insert(0, item)
        data["agent_activity"] = data["agent_activity"][:60]
        self._write(data)

    # Integrations
    def get_integrations(self) -> Dict:
        return self._read().get("integrations", {})

    def update_integration(self, service_key: str, updates: Dict) -> Dict:
        data = self._read()
        integs = data.setdefault("integrations", {})
        if service_key in integs:
            integs[service_key].update(updates)
            self._write(data)
            status_text = "connected" if updates.get("connected") else "configured"
            self.add_activity("integration", f"Updated {service_key.title()} status: {status_text}", "success", f"Account: {updates.get('email', '')}")
            return integs[service_key]
        return {}


os_store = OSDataStore()
