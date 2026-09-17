import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

from app.agents.card_schema import JSONMemoryCard


class GitVaultAgent:
    """Agent that manages the persistent GitHub Memory Vault:
    - Writes structured JSON cards to disk.
    - Aggregates the dynamic live Knowledge Graph JSON.
    - Commits and pushes cards to the user's GitHub repository.
    - Prunes ephemeral screenshots so local disk usage stays minimal.
    """

    def __init__(self, vault_root: str = "memory_vault"):
        self.vault_root = Path(vault_root)
        self.cards_dir = self.vault_root / "cards"
        self.cards_dir.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.vault_root / "knowledge_graph.json"
        self._pending_push = False
        self._sync_task = None
        self._init_graph_file()

    def _init_graph_file(self):
        if not self.graph_file.exists():
            initial_graph = {
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "nodes": [
                    {"id": "JARVIS_CORE", "label": "Jarvis Core", "domain": "Core", "priority": "high", "val": 20}
                ],
                "edges": []
            }
            self.graph_file.write_text(json.dumps(initial_graph, indent=2), encoding="utf-8")

    def store_card(self, card: JSONMemoryCard) -> str:
        """Saves a JSON card organized by date: memory_vault/cards/YYYY-MM-DD/<id>.json"""
        date_folder = self.cards_dir / datetime.utcnow().strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        card_path = date_folder / f"{card.id}.json"
        card_path.write_text(card.model_dump_json(indent=2), encoding="utf-8")

        # Update Knowledge Graph
        self._update_knowledge_graph(card)
        self._pending_push = True

        return str(card_path)

    def prune_screenshot(self, screenshot_file_path: str):
        """Deletes raw screenshot file from disk after text & card extraction.
        Keeps user's laptop storage completely free!"""
        try:
            if screenshot_file_path and os.path.exists(screenshot_file_path):
                os.remove(screenshot_file_path)
                print(f"[VaultAgent] Ephemeral screenshot purged: {screenshot_file_path}")
        except Exception as exc:
            print(f"[VaultAgent] Notice: could not remove {screenshot_file_path}: {exc}")

    def _update_knowledge_graph(self, card: JSONMemoryCard):
        try:
            data = json.loads(self.graph_file.read_text(encoding="utf-8"))
        except Exception:
            data = {"updated_at": datetime.utcnow().isoformat(), "nodes": [], "edges": []}

        nodes = {n["id"]: n for n in data.get("nodes", [])}
        edges = data.get("edges", [])

        # Add domain hub node if not present
        domain_id = f"DOMAIN_{card.domain.upper()}"
        if domain_id not in nodes:
            nodes[domain_id] = {
                "id": domain_id,
                "label": card.domain,
                "domain": card.domain,
                "priority": "high",
                "val": 15
            }
            edges.append({"source": "JARVIS_CORE", "target": domain_id, "label": "tracks"})

        # Add Card node
        card_label = card.topic if card.topic else card.window_title[:24]
        nodes[card.id] = {
            "id": card.id,
            "label": card_label,
            "domain": card.domain,
            "priority": card.priority,
            "summary": card.summary,
            "val": 10 if card.priority == "high" else 6
        }
        edges.append({"source": domain_id, "target": card.id, "label": "contains"})

        # Add Entity nodes and link them
        for ent in card.entities[:4]:
            ent_id = f"ENT_{ent.lower()}"
            if ent_id not in nodes:
                nodes[ent_id] = {
                    "id": ent_id,
                    "label": ent,
                    "domain": card.domain,
                    "priority": card.priority,
                    "val": 8
                }
            edges.append({"source": card.id, "target": ent_id, "label": "mentions"})

        data["updated_at"] = datetime.utcnow().isoformat() + "Z"
        data["nodes"] = list(nodes.values())[-350:]  # Keep top 350 most relevant active nodes
        data["edges"] = edges[-500:]

        self.graph_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    async def sync_to_github(self) -> bool:
        """Pushes pending memory cards and updated graph to GitHub."""
        if not self._pending_push:
            return True

        return await asyncio.to_thread(self._git_commit_push)

    def _git_commit_push(self) -> bool:
        try:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            # 1. Stage memory vault files
            subprocess.run(["git", "add", "memory_vault/"], check=True, capture_output=True, text=True)
            # 2. Check if there are changes to commit
            status = subprocess.run(["git", "status", "--porcelain", "memory_vault/"], capture_output=True, text=True)
            if not status.stdout.strip():
                self._pending_push = False
                return True

            # 3. Commit
            commit_msg = f"chore(vault): auto-sync memory cards and knowledge graph [{timestamp}]"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)

            # 4. Push to origin main
            push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
            if push_res.returncode == 0:
                print(f"[VaultAgent] Successfully pushed memory cards to GitHub: {timestamp}")
                self._pending_push = False
                return True
            else:
                print(f"[VaultAgent] Git push warning: {push_res.stderr}")
                return False
        except Exception as exc:
            print(f"[VaultAgent] Sync to GitHub exception: {exc}")
            return False


vault_agent = GitVaultAgent()
