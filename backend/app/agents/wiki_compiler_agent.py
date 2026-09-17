import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from app.agents.card_schema import JSONMemoryCard


class WikiCompilerAgent:
    """Inspired by Andrej Karpathy's Self-Improving Second Brain:
    Instead of just keeping raw, disjointed logs, this agent autonomously
    'compiles' raw memory cards into living, interconnected Master Wiki Articles
    under `memory_vault/wiki/`.

    It groups cards by Topic, synthesizes key takeaways, tracks knowledge gaps,
    and maintains a browsable, cross-linked digital encyclopedia with zero manual editing.
    """

    def __init__(self, vault_root: str = "memory_vault"):
        self.project_root = Path(__file__).resolve().parents[3]
        self.vault_root = self.project_root / vault_root
        self.wiki_dir = self.vault_root / "wiki"
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.wiki_dir / "INDEX.md"
        self._init_index()

    def _init_index(self):
        if not self.index_file.exists():
            content = """# JARVIS Self-Improving Knowledge Wiki
*Autonomous digital encyclopedia continuously synthesized by your AI Agent Swarm.*

## Master Topic Compilations
*(Automatically updated as you browse, code, and learn)*

---
"""
            self.index_file.write_text(content, encoding="utf-8")

    def compile_card_into_wiki(self, card: JSONMemoryCard) -> str:
        """Incrementally synthesizes a JSON Memory Card into a rich, permanent Markdown Wiki Page."""
        try:
            # 1. Determine target domain folder & topic filename
            domain_slug = card.domain.lower()
            domain_dir = self.wiki_dir / domain_slug
            domain_dir.mkdir(parents=True, exist_ok=True)

            topic_slug = "".join(c if c.isalnum() else "_" for c in (card.topic or "general")).strip("_").lower()
            topic_file = domain_dir / f"{topic_slug}.md"

            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

            # 2. If article already exists, update & append new knowledge
            if topic_file.exists():
                existing = topic_file.read_text(encoding="utf-8")
                addition = f"""
### Synthesized Entry: {card.window_title[:60] or 'Session Capture'} ({now_str})
- **Source Application:** `{card.app_source}`
- **Priority Rating:** `{card.priority.upper()}`
- **Context Summary:** {card.summary}

#### Key Takeaways & Evidence:
"""
                for ptr in card.key_pointers:
                    addition += f"- {ptr}\n"

                if card.entities:
                    addition += f"\n**Identified Concepts & Entities:** {', '.join(f'`{e}`' for e in card.entities)}\n"

                if card.hero_image:
                    addition += f"\n![Hero Visual Evidence](../../{card.hero_image})\n"

                addition += "\n---\n"
                new_content = existing + addition
                topic_file.write_text(new_content, encoding="utf-8")
            else:
                # 3. Create brand-new Master Topic Article
                new_content = f"""# Master Synthesis: {card.topic or card.domain}
*Domain: {card.domain} | First Synthesized: {now_str}*

## Executive Overview
{card.summary}

## Core Entities & Concepts
{', '.join(f'`{e}`' for e in card.entities) if card.entities else 'Continuous exploration'}

## Knowledge Timeline & Captured Insights

### Entry: {card.window_title[:60] or 'Session Capture'} ({now_str})
- **Application:** `{card.app_source}`
- **Quality Score:** `{card.quality_score}`

#### Key Pointers:
"""
                for ptr in card.key_pointers:
                    new_content += f"- {ptr}\n"

                if card.hero_image:
                    new_content += f"\n![Hero Visual Evidence](../../{card.hero_image})\n"

                new_content += "\n---\n"
                topic_file.write_text(new_content, encoding="utf-8")

            # 4. Refresh Master Index
            self._update_index(card.domain, card.topic, f"{domain_slug}/{topic_slug}.md")
            print(f"[WikiCompiler] Compiled knowledge into master wiki: {topic_file.name}")
            return str(topic_file)
        except Exception as exc:
            print(f"[WikiCompiler] Notice: could not compile wiki: {exc}")
            return ""

    def _update_index(self, domain: str, topic: str, rel_path: str):
        try:
            current_index = self.index_file.read_text(encoding="utf-8")
            entry_line = f"- [{domain}: {topic}]({rel_path})"
            if entry_line not in current_index:
                updated = current_index + f"\n{entry_line} — *Updated {datetime.utcnow().strftime('%Y-%m-%d')}*"
                self.index_file.write_text(updated, encoding="utf-8")
        except Exception:
            pass

    def list_wiki_articles(self) -> List[Dict]:
        """Returns all compiled wiki articles for the frontend."""
        articles = []
        if not self.wiki_dir.exists():
            return []

        for md_file in sorted(self.wiki_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            if md_file.name == "INDEX.md":
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                lines = content.split("\n")
                title = lines[0].replace("#", "").strip() if lines else md_file.stem
                articles.append({
                    "filename": md_file.name,
                    "title": title,
                    "domain": md_file.parent.name.title(),
                    "updated_at": datetime.fromtimestamp(md_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "preview": "\n".join(lines[1:6]).strip(),
                    "path": str(md_file.relative_to(self.vault_root)).replace("\\", "/")
                })
            except Exception:
                pass
        return articles


wiki_compiler = WikiCompilerAgent()
