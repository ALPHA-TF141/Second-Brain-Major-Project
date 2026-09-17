import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.agents.card_schema import JSONMemoryCard


class GitVaultAgent:
    """Agent that manages the persistent GitHub Memory Vault:
    - Writes structured JSON cards to disk.
    - Stores the single highest-content "Hero" image per session/topic window.
    - Aggregates the dynamic live Knowledge Graph JSON.
    - Commits and pushes cards and hero images directly to GitHub.
    - Prunes all redundant ephemeral screenshots.
    """

    def __init__(self):
        # Always resolve to the true git repository root regardless of where python was spawned from
        self.project_root = Path(__file__).resolve().parents[3]
        self.vault_root = self.project_root / "memory_vault"
        self.cards_dir = self.vault_root / "cards"
        self.images_dir = self.vault_root / "images"
        self.cards_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.vault_root / "knowledge_graph.json"
        self._pending_push = False
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

        # 100% Autonomous Auto-Push: silently sync to GitHub in background
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.sync_to_github())
        except Exception:
            pass

        return str(card_path)

    def optimize_and_store_hero_image(self, source_image_path: str, card_id: str) -> Optional[str]:
        """Compresses a representative screen capture into a lightweight,
        high-clarity WebP/JPEG image (~70-120KB) for permanent GitHub vault storage.
        """
        try:
            from PIL import Image

            if not source_image_path or not os.path.exists(source_image_path):
                return None

            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            dest_dir = self.images_dir / date_str
            dest_dir.mkdir(parents=True, exist_ok=True)

            dest_filename = f"hero_{card_id}.webp"
            dest_path = dest_dir / dest_filename
            rel_path = f"memory_vault/images/{date_str}/{dest_filename}"

            with Image.open(source_image_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Scale down slightly if ultra-wide/4K to preserve clarity with minimal size
                max_width = 1600
                if img.width > max_width:
                    scale = max_width / float(img.width)
                    new_height = int(img.height * scale)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                try:
                    img.save(str(dest_path), format="WEBP", quality=82, method=4)
                except Exception:
                    dest_filename = f"hero_{card_id}.jpg"
                    dest_path = dest_dir / dest_filename
                    rel_path = f"memory_vault/images/{date_str}/{dest_filename}"
                    img.save(str(dest_path), format="JPEG", quality=80, optimize=True)

            file_size_kb = os.path.getsize(dest_path) // 1024
            print(f"[VaultAgent] Saved optimized Hero screenshot ({file_size_kb} KB): {rel_path}")
            self._pending_push = True
            return rel_path
        except Exception as exc:
            print(f"[VaultAgent] Notice: could not optimize hero image: {exc}")
            return None

    def prune_screenshot(self, screenshot_file_path: str):
        """Deletes raw uncompressed screenshot file from disk to eliminate local storage waste."""
        try:
            if screenshot_file_path and os.path.exists(screenshot_file_path):
                os.remove(screenshot_file_path)
                print(f"[VaultAgent] Ephemeral screenshot purged from laptop: {screenshot_file_path}")
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

        # Add Card node with hero image reference
        card_label = card.topic if card.topic else card.window_title[:24]
        nodes[card.id] = {
            "id": card.id,
            "label": card_label,
            "domain": card.domain,
            "priority": card.priority,
            "summary": card.summary,
            "hero_image": card.hero_image,
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
        """Pushes pending memory cards, hero images, and updated graph to GitHub."""
        return await asyncio.to_thread(self._git_commit_push)

    def _git_commit_push(self) -> bool:
        try:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            cwd = str(self.project_root)

            # 1. Stage memory vault files (cards, images, and graph)
            subprocess.run(["git", "add", "memory_vault/"], cwd=cwd, check=True, capture_output=True, text=True)

            # 2. Check if there are changes to commit
            status = subprocess.run(["git", "status", "--porcelain", "memory_vault/"], cwd=cwd, capture_output=True, text=True)
            if not status.stdout.strip():
                self._pending_push = False
                return True

            # 3. Commit with explicit identity to avoid author unknown errors on Windows
            commit_msg = f"chore(vault): auto-sync knowledge cards, hero images & graph [{timestamp}]"
            commit_cmd = [
                "git",
                "-c", "user.name=ALPHA-TF141",
                "-c", "user.email=lmariaimmanuel@gmail.com",
                "commit",
                "-m", commit_msg
            ]
            subprocess.run(commit_cmd, cwd=cwd, check=True, capture_output=True, text=True)

            # 4. Push to origin main
            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=cwd, capture_output=True, text=True)
            if push_res.returncode == 0:
                print(f"[VaultAgent] Successfully pushed memory cards & hero images to GitHub: {timestamp}")
                self._pending_push = False
                return True
            else:
                print(f"[VaultAgent] Git push warning: {push_res.stderr}")
                return False
        except Exception as exc:
            print(f"[VaultAgent] Sync to GitHub exception: {exc}")
            return False


vault_agent = GitVaultAgent()
