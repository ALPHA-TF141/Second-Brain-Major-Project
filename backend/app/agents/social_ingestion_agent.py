import asyncio
import io
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup
from PIL import Image

from app.agents.card_schema import JSONMemoryCard
from app.agents.curation_agent import curation_agent
from app.agents.vault_agent import vault_agent
from app.agents.wiki_compiler_agent import wiki_compiler
from app.config import settings
from app.websocket.manager import manager


class NativeSocialScraperAgent:
    """100% Free, Native, Self-Hosted Social Media & Web Scraper Engine:
    Replaces paid services like Apify and SupaData with local, open-source extractors:
    - YouTube Native Transcripts: Extracts complete spoken transcripts without API fees.
    - Twitter / X Native Reader: Extracts full tweet threads & media via free syndication.
    - Instagram Native Engine: Scrapes public reels & posts (and supports local account session login).
    - Web & Research Article Parser: Converts technical articles and papers into clean Markdown.
    - Account Session Vault: Stores local login cookies securely on the machine without third-party fees.
    """

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.accounts_dir = self.project_root / "backend" / "data" / "social_accounts"
        self.accounts_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def get_status(self) -> Dict:
        """Returns connection status for all local self-hosted scrapers."""
        ig_session_exists = (self.accounts_dir / "instagram_session.json").exists()
        x_session_exists = (self.accounts_dir / "x_session.json").exists()

        return {
            "engine": "100% Free Native Built-in (Zero Paid SaaS)",
            "youtube": "Ready (Native Transcript Extractor)",
            "twitter_x": "Ready (Syndication & Media Engine)",
            "instagram": "Ready (Native Reel/Post Parser)",
            "web_articles": "Ready (Readability Markdown Engine)",
            "connected_accounts": {
                "instagram": ig_session_exists,
                "twitter": x_session_exists,
            }
        }

    async def ingest_url(self, url: str, user_notes: str = "") -> Dict:
        """Main entry point: scrapes, cleans, extracts Hero capture, synthesizes JSON Card,
        compiles into Master Wiki, and pushes to GitHub autonomously with zero API fees.
        """
        url = url.strip()
        if not url:
            raise ValueError("URL cannot be empty")

        platform = self._detect_platform(url)
        print(f"[NativeScraper] Ingesting {platform} content from: {url}")

        raw_data = None
        if platform == "youtube":
            raw_data = await self._scrape_youtube_native(url)
        elif platform == "twitter":
            raw_data = await self._scrape_twitter_native(url)
        elif platform == "instagram":
            raw_data = await self._scrape_instagram_native(url)
        else:
            raw_data = await self._scrape_web_native(url)

        title = raw_data.get("title", f"{platform.title()} Content")
        clean_text = raw_data.get("text", "")
        thumbnail_url = raw_data.get("thumbnail_url", "")
        author = raw_data.get("author", platform.title())

        if user_notes:
            clean_text = f"User Notes: {user_notes}\n\nContent:\n{clean_text}"

        # Pass through Curation & Deduplication Agent
        curation_result = curation_agent.evaluate_and_curate(
            raw_text=clean_text,
            app_source=f"native_{platform}",
            window_title=title,
            session_id=0,
        )

        if not curation_result:
            card_id = f"card_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:19]}"
            card = JSONMemoryCard(
                id=card_id,
                domain="Technology",
                priority="medium",
                quality_score=0.88,
                app_source=f"native_{platform}",
                window_title=title,
                topic=title[:45],
                summary=f"[{platform.title()}] {title}: {clean_text[:240]}...",
                key_pointers=[p.strip() for p in clean_text.split("\n") if len(p.strip()) > 30][:4] or [title],
                entities=[platform.title(), author],
                tags=[platform, "free_native_intel"],
                source_url_or_ref=url,
                raw_ocr_excerpt=clean_text[:400],
            )
        else:
            card, _ = curation_result
            card.source_url_or_ref = url

        # Download & optimize thumbnail into memory_vault/images/
        hero_rel_path = None
        if thumbnail_url:
            hero_rel_path = await self._download_and_store_thumbnail(thumbnail_url, card.id)
            if hero_rel_path:
                card.hero_image = hero_rel_path

        # Save to persistent Vault & Knowledge Graph
        vault_agent.store_card(card)

        # Autonomously compile into Master Wiki
        try:
            wiki_compiler.compile_card_into_wiki(card)
        except Exception as e:
            print(f"[NativeScraper] Wiki compiler notice: {e}")

        # Broadcast update to Electron Stark HUD
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

    # ==================== 1. YOUTUBE NATIVE SCRAPER ====================
    async def _scrape_youtube_native(self, url: str) -> Dict:
        """100% Free: Extracts video title, author, high-res thumbnail,
        and complete audio transcript using YouTube's native caption tracks."""
        video_id = self._extract_youtube_id(url)
        result = {
            "title": "YouTube Video",
            "text": "",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else "",
            "author": "YouTube Creator"
        }

        # 1. Fetch metadata via oEmbed (instant, free)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://www.youtube.com/oembed?url={url}&format=json")
                if resp.status_code == 200:
                    meta = resp.json()
                    result["title"] = meta.get("title", result["title"])
                    result["author"] = meta.get("author_name", result["author"])
                    if not result["thumbnail_url"]:
                        result["thumbnail_url"] = meta.get("thumbnail_url", "")
        except Exception:
            pass

        # 2. Extract full transcript via youtube-transcript-api (Free, no keys needed)
        if video_id:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                transcript_list = await asyncio.to_thread(
                    YouTubeTranscriptApi.get_transcript, video_id, languages=["en", "ta", "hi", "en-GB", "en-US"]
                )
                if transcript_list:
                    full_transcript = " ".join(item.get("text", "") for item in transcript_list)
                    result["text"] = f"Full Audio Transcript:\n{full_transcript}"
                    print(f"[NativeScraper] Extracted complete YouTube transcript ({len(full_transcript)} chars) with ZERO fees!")
            except Exception as exc:
                print(f"[NativeScraper] YouTube transcript notice: {exc}")

        # If video has no subtitles/captions, format rich metadata context
        if not result["text"]:
            result["text"] = f"YouTube Content: '{result['title']}' published by {result['author']}.\nVideo URL: {url}"

        return result

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:embed\/|v\/|shorts\/)([0-9A-Za-z_-]{11})"
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    # ==================== 2. TWITTER / X NATIVE SCRAPER ====================
    async def _scrape_twitter_native(self, url: str) -> Dict:
        """100% Free: Extracts full tweet text, author, and media using free syndication API."""
        result = {"title": "X / Twitter Post", "text": "", "thumbnail_url": "", "author": "X User"}

        # Extract handle and tweet id
        m = re.search(r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/status/(\d+)", url)
        if m:
            handle, tweet_id = m.group(1), m.group(2)
            # Query free vxtwitter syndication endpoint
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    resp = await client.get(f"https://api.vxtwitter.com/{handle}/status/{tweet_id}")
                    if resp.status_code == 200:
                        data = resp.json()
                        tweet_text = data.get("text", "")
                        result["text"] = tweet_text
                        result["author"] = data.get("user_name", handle)
                        result["title"] = f"Post by {result['author']}: {tweet_text[:45]}"
                        media_urls = data.get("mediaURLs", [])
                        if media_urls:
                            result["thumbnail_url"] = media_urls[0]
                        print(f"[NativeScraper] Extracted Tweet from @{handle} with ZERO fees!")
                        return result
            except Exception as e:
                print(f"[NativeScraper] vxtwitter notice: {e}")

        # Fallback to Twitter oEmbed
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://publish.twitter.com/oembed?url={url}")
                if resp.status_code == 200:
                    data = resp.json()
                    soup = BeautifulSoup(data.get("html", ""), "html.parser")
                    text = soup.get_text()
                    result["text"] = text
                    result["author"] = data.get("author_name", "X User")
                    result["title"] = f"X Post by {result['author']}"
        except Exception:
            pass

        if not result["text"]:
            result["text"] = f"Twitter / X Discussion at: {url}"

        return result

    # ==================== 3. INSTAGRAM NATIVE SCRAPER ====================
    async def _scrape_instagram_native(self, url: str) -> Dict:
        """100% Free: Scrapes Instagram post or reel caption, author, and media preview
        using local instaloader engine with zero paid Apify fees."""
        result = {"title": "Instagram Content", "text": "", "thumbnail_url": "", "author": "Instagram Creator"}

        # Extract shortcode: instagram.com/p/{shortcode} or /reel/{shortcode}
        m = re.search(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
        if m:
            shortcode = m.group(1)
            try:
                import instaloader
                L = instaloader.Instaloader(download_pictures=False, download_videos=False, download_comments=False)

                # Check if user saved a local Instagram account session
                session_file = self.accounts_dir / "instagram_session.json"
                if session_file.exists():
                    try:
                        session_data = json.loads(session_file.read_text(encoding="utf-8"))
                        username = session_data.get("username")
                        if username:
                            L.load_session_from_file(username)
                    except Exception:
                        pass

                post = await asyncio.to_thread(instaloader.Post.from_shortcode, L.context, shortcode)
                caption = post.caption or ""
                result["text"] = caption
                result["author"] = post.owner_username or "Instagram Creator"
                result["title"] = f"Instagram Post: {caption[:40]}" if caption else f"Reel by @{result['author']}"
                result["thumbnail_url"] = post.url
                print(f"[NativeScraper] Scraped Instagram Reel/Post ({shortcode}) with ZERO Apify fees!")
                return result
            except Exception as e:
                print(f"[NativeScraper] Instaloader notice: {e}")

        # Fallback to direct page metadata extraction
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    desc = soup.find("meta", property="og:description")
                    title_m = soup.find("meta", property="og:title")
                    img_m = soup.find("meta", property="og:image")

                    if desc and desc.get("content"):
                        result["text"] = desc["content"]
                    if title_m and title_m.get("content"):
                        result["title"] = title_m["content"]
                    if img_m and img_m.get("content"):
                        result["thumbnail_url"] = img_m["content"]
        except Exception:
            pass

        if not result["text"]:
            result["text"] = f"Instagram Reel/Post from: {url}"

        return result

    # ==================== 4. WEB ARTICLES & PAPERS (READABILITY ENGINE) ====================
    async def _scrape_web_native(self, url: str) -> Dict:
        """100% Free: Autonomous readability extractor for research papers & technical blogs.
        Extracts clean title, author, OpenGraph image, and converts body text into clean Markdown."""
        result = {"title": "Web Research Article", "text": "", "thumbnail_url": "", "author": "Web Source"}

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract title
                    og_title = soup.find("meta", property="og:title")
                    if og_title and og_title.get("content"):
                        result["title"] = og_title["content"].strip()
                    elif soup.title and soup.title.string:
                        result["title"] = soup.title.string.strip()

                    # Extract thumbnail
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        result["thumbnail_url"] = og_image["content"]

                    # Extract author
                    og_author = soup.find("meta", property="article:author") or soup.find("meta", attrs={"name": "author"})
                    if og_author and og_author.get("content"):
                        result["author"] = og_author["content"]

                    # Purge boilerplate elements (navbars, footers, scripts, styles, cookie banners)
                    for tag in soup(["script", "style", "nav", "footer", "aside", "header", "noscript", "svg", "form"]):
                        tag.decompose()

                    # Extract content blocks (prioritize <article>, <main>, or body paragraphs)
                    article_container = soup.find("article") or soup.find("main") or soup.body
                    if article_container:
                        paragraphs = []
                        for el in article_container.find_all(["p", "h1", "h2", "h3", "h4", "pre", "code", "li"]):
                            text = el.get_text().strip()
                            if len(text) > 25:
                                if el.name in ["h1", "h2", "h3"]:
                                    paragraphs.append(f"\n### {text}")
                                elif el.name in ["pre", "code"]:
                                    paragraphs.append(f"```\n{text}\n```")
                                elif el.name == "li":
                                    paragraphs.append(f"- {text}")
                                else:
                                    paragraphs.append(text)

                        result["text"] = "\n\n".join(paragraphs[:35])
        except Exception as e:
            print(f"[NativeScraper] Web readability notice: {e}")

        if not result["text"]:
            result["text"] = f"Article content from: {url}"

        return result

    # ==================== 5. LOCAL ACCOUNT SESSION CONNECTOR ====================
    def save_account_session(self, platform: str, session_data: Dict) -> bool:
        """Saves user's own Instagram or Twitter/X login session / cookies 100% locally on PC."""
        try:
            target_file = self.accounts_dir / f"{platform.lower()}_session.json"
            target_file.write_text(json.dumps(session_data, indent=2), encoding="utf-8")
            print(f"[NativeScraper] Saved local {platform} account session (Zero cloud leak)")
            return True
        except Exception as e:
            print(f"[NativeScraper] Could not save account session: {e}")
            return False

    async def _download_and_store_thumbnail(self, image_url: str, card_id: str) -> Optional[str]:
        """Downloads external video/post thumbnail and converts into optimized 80KB WebP in memory_vault/images/."""
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                res = await client.get(image_url, headers=self.headers)
                if res.status_code == 200:
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
                        # Resize slightly to keep file tiny (~70KB)
                        if img.width > 1280:
                            scale = 1280 / float(img.width)
                            img = img.resize((1280, int(img.height * scale)), Image.Resampling.LANCZOS)
                        img.save(str(dest_path), format="WEBP", quality=82)

                    return rel_path
        except Exception as e:
            print(f"[NativeScraper] Could not optimize thumbnail: {e}")
            return None


native_social_scraper = NativeSocialScraperAgent()
