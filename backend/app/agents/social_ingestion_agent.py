import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

from app.agents.card_schema import JSONMemoryCard
from app.agents.curation_agent import curation_agent
from app.agents.vault_agent import vault_agent
from app.agents.wiki_compiler_agent import wiki_compiler
from app.config import settings
from app.websocket.manager import manager


class SocialIngestionAgent:
    """Autonomous Social Media & Web Ingestion Agent:
    Connects to Apify & SupaData APIs to scrape, transcribe, and ingest:
    - YouTube videos & shorts (full audio transcripts, key takeaways)
    - Twitter / X threads & posts
    - Instagram posts & reels
    - LinkedIn articles & posts
    - Web research papers & technical blogs

    Transforms scraped intelligence into structured JSON Memory Cards,
    downloads the richest Hero image into memory_vault/images/, compiles into
    the Master Wiki, and commits to GitHub autonomously.
    """

    def __init__(self):
        self.supadata_base_url = "https://api.supadata.ai/v1"
        self.apify_base_url = "https://api.apify.com/v2"

    def get_configured_services(self) -> Dict[str, bool]:
        """Returns connection status for scrapers."""
        return {
            "supadata": bool(settings.supadata_api_key),
            "apify": bool(settings.apify_api_token),
            "universal_scraper": True,
        }

    async def ingest_url(self, url: str, user_notes: str = "") -> Dict:
        """Universal entry point to ingest any social media or web URL."""
        url = url.strip()
        if not url:
            raise ValueError("URL cannot be empty")

        platform = self._detect_platform(url)
        print(f"[SocialAgent] Ingesting {platform} content from: {url}")

        raw_data = None
        # 1. Route to specialized service
        if platform == "youtube":
            raw_data = await self._ingest_youtube(url)
        elif platform == "twitter":
            raw_data = await self._ingest_twitter(url)
        elif platform == "instagram":
            raw_data = await self._ingest_instagram(url)
        else:
            raw_data = await self._ingest_web_article(url)

        if not raw_data or not raw_data.get("text"):
            # Universal fallback scraper
            raw_data = await self._universal_web_scrape(url)

        # 2. Extract structured content
        title = raw_data.get("title", f"{platform.title()} Content")
        clean_text = raw_data.get("text", "")
        thumbnail_url = raw_data.get("thumbnail_url", "")
        author = raw_data.get("author", platform.title())

        if user_notes:
            clean_text = f"User Notes: {user_notes}\n\nContent:\n{clean_text}"

        # 3. Pass through Curation Agent (evaluates information density & priority)
        curation_result = curation_agent.evaluate_and_curate(
            raw_text=clean_text,
            app_source=f"{platform}_scraper",
            window_title=title,
            session_id=0,
        )

        if not curation_result:
            # If curation filtered it as low-entropy, build a baseline card for explicit user ingest
            card_id = f"card_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:19]}"
            card = JSONMemoryCard(
                id=card_id,
                domain="Technology",
                priority="medium",
                quality_score=0.85,
                app_source=f"{platform}_scraper",
                window_title=title,
                topic=title[:45],
                summary=f"[{platform.title()}] {title}: {clean_text[:240]}...",
                key_pointers=[p.strip() for p in clean_text.split("\n") if len(p.strip()) > 30][:4] or [title],
                entities=[platform.title(), author],
                tags=[platform, "social_intel"],
                source_url_or_ref=url,
                raw_ocr_excerpt=clean_text[:400],
            )
        else:
            card, _ = curation_result
            card.source_url_or_ref = url

        # 4. Save Hero Thumbnail Evidence into memory_vault/images/ if available
        hero_rel_path = None
        if thumbnail_url:
            hero_rel_path = await self._download_and_store_thumbnail(thumbnail_url, card.id)
            if hero_rel_path:
                card.hero_image = hero_rel_path

        # 5. Save JSON Card & update Knowledge Graph
        vault_agent.store_card(card)

        # 6. Incrementally compile into Master Wiki
        try:
            wiki_compiler.compile_card_into_wiki(card)
        except Exception as e:
            print(f"[SocialAgent] Wiki compiler notice: {e}")

        # 7. Broadcast live update to Electron Stark HUD
        await manager.broadcast({
            "type": "social_ingested",
            "data": {
                "id": card.id,
                "title": card.topic or card.window_title,
                "platform": platform,
                "domain": card.domain,
                "hero_image": card.hero_image,
                "url": url,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

        print(f"[SocialAgent] Successfully synthesized {platform} intel: {card.id}")
        return {
            "status": "success",
            "card_id": card.id,
            "platform": platform,
            "title": card.topic or card.window_title,
            "domain": card.domain,
            "summary": card.summary,
            "key_pointers": card.key_pointers,
            "hero_image": card.hero_image,
            "url": url,
        }

    def _detect_platform(self, url: str) -> str:
        low = url.lower()
        if "youtube.com" in low or "youtu.be" in low:
            return "youtube"
        if "twitter.com" in low or "x.com" in low:
            return "twitter"
        if "instagram.com" in low:
            return "instagram"
        if "linkedin.com" in low:
            return "linkedin"
        if "reddit.com" in low:
            return "reddit"
        return "web_article"

    async def _ingest_youtube(self, url: str) -> Dict:
        """Extracts YouTube video title, full audio transcript, and thumbnail via SupaData or oEmbed."""
        result = {"title": "YouTube Video", "text": "", "thumbnail_url": "", "author": "YouTube"}

        # 1. Fetch metadata via YouTube oEmbed (Free & instant)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                oembed = await client.get(f"https://www.youtube.com/oembed?url={url}&format=json")
                if oembed.status_code == 200:
                    meta = oembed.json()
                    result["title"] = meta.get("title", result["title"])
                    result["thumbnail_url"] = meta.get("thumbnail_url", "")
                    result["author"] = meta.get("author_name", "YouTube Creator")
        except Exception:
            pass

        # 2. Extract full transcript via SupaData if configured
        if settings.supadata_api_key:
            try:
                headers = {"x-api-key": settings.supadata_api_key}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(
                        f"{self.supadata_base_url}/youtube/transcript",
                        params={"url": url, "text": "true"},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        result["text"] = data.get("content", "") or data.get("text", "")
                        print(f"[SocialAgent] Fetched YouTube transcript via SupaData ({len(result['text'])} chars)")
            except Exception as e:
                print(f"[SocialAgent] SupaData transcript notice: {e}")

        # If transcript not retrieved, use title and author context
        if not result["text"]:
            result["text"] = f"YouTube Video: {result['title']} by {result['author']}. Watch URL: {url}"

        return result

    async def _ingest_twitter(self, url: str) -> Dict:
        """Extracts Tweet or thread text via SupaData or Apify."""
        result = {"title": "X / Twitter Post", "text": "", "thumbnail_url": "", "author": "Twitter User"}

        if settings.supadata_api_key:
            try:
                headers = {"x-api-key": settings.supadata_api_key}
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.get(
                        f"{self.supadata_base_url}/twitter/tweet",
                        params={"url": url},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        result["text"] = data.get("text", "")
                        result["author"] = data.get("author", {}).get("name", "X User")
                        result["title"] = f"Post by {result['author']}: {result['text'][:50]}"
            except Exception as e:
                print(f"[SocialAgent] SupaData Twitter notice: {e}")

        if not result["text"]:
            result["text"] = f"Twitter / X Content at: {url}"

        return result

    async def _ingest_instagram(self, url: str) -> Dict:
        """Ingests Instagram post or reel via Apify or metadata extraction."""
        result = {"title": "Instagram Post", "text": "", "thumbnail_url": "", "author": "Instagram Creator"}

        if settings.apify_api_token:
            try:
                # Trigger Apify Instagram Scraper actor
                actor_id = "apify~instagram-scraper"
                headers = {"Authorization": f"Bearer {settings.apify_api_token}", "Content-Type": "application/json"}
                async with httpx.AsyncClient(timeout=60.0) as client:
                    run_resp = await client.post(
                        f"{self.apify_base_url}/acts/{actor_id}/run-sync-get-dataset-items",
                        headers=headers,
                        json={"directUrls": [url], "resultsType": "posts", "resultsLimit": 1},
                    )
                    if run_resp.status_code in (200, 201):
                        items = run_resp.json()
                        if items and len(items) > 0:
                            item = items[0]
                            caption = item.get("caption", "")
                            result["text"] = caption
                            result["author"] = item.get("ownerUsername", "Instagram")
                            result["title"] = f"Instagram Post: {caption[:40]}" if caption else "Instagram Reel"
                            result["thumbnail_url"] = item.get("displayUrl", "") or item.get("thumbnailUrl", "")
            except Exception as e:
                print(f"[SocialAgent] Apify Instagram notice: {e}")

        if not result["text"]:
            result["text"] = f"Instagram Content from URL: {url}"

        return result

    async def _ingest_web_article(self, url: str) -> Dict:
        """Extracts clean article markdown and metadata via SupaData or Universal Scraper."""
        result = {"title": "Web Research Article", "text": "", "thumbnail_url": "", "author": "Web"}

        if settings.supadata_api_key:
            try:
                headers = {"x-api-key": settings.supadata_api_key}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(
                        f"{self.supadata_base_url}/web/scrape",
                        params={"url": url},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        result["text"] = data.get("content", "") or data.get("markdown", "")
                        result["title"] = data.get("title", result["title"])
            except Exception as e:
                print(f"[SocialAgent] SupaData Web notice: {e}")

        return result

    async def _universal_web_scrape(self, url: str) -> Dict:
        """Lightweight built-in scraper using httpx for public articles & blogs."""
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                if resp.status_code == 200:
                    html = resp.text
                    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                    title = title_m.group(1).strip() if title_m else "Web Document"

                    # Strip tags and script blocks
                    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = " ".join(text.split())

                    return {"title": title, "text": text[:3500], "thumbnail_url": "", "author": "Web Source"}
        except Exception as e:
            print(f"[SocialAgent] Universal scrape notice: {e}")

        return {"title": "Captured Web Intel", "text": f"Scraped from {url}", "thumbnail_url": "", "author": "Web"}

    async def _download_and_store_thumbnail(self, image_url: str, card_id: str) -> Optional[str]:
        """Downloads external video/post thumbnail and optimizes into memory_vault/images/ as Hero Capture."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(image_url)
                if res.status_code == 200:
                    from PIL import Image
                    import io

                    img_bytes = res.content
                    date_str = datetime.utcnow().strftime("%Y-%m-%d")
                    dest_dir = vault_agent.images_dir / date_str
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    dest_filename = f"hero_{card_id}.webp"
                    dest_path = dest_dir / dest_filename
                    rel_path = f"memory_vault/images/{date_str}/{dest_filename}"

                    with Image.open(io.BytesIO(img_bytes)) as img:
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.save(str(dest_path), format="WEBP", quality=82)

                    return rel_path
        except Exception as e:
            print(f"[SocialAgent] Could not download thumbnail: {e}")
            return None


social_agent = SocialIngestionAgent()
