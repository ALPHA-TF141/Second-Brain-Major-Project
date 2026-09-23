from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Second Brain Backend"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/second_brain.db"
    jwt_secret_key: str = "change-this-dev-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    cors_origins: str = "*"
    demo_username: str = "Immanuel"
    demo_password: str = "secondbrain"
    openai_api_key: str = ""
    openai_model: str = "qwen2.5:3b"
    openai_base_url: str = "http://localhost:11434/v1"
    rag_context_limit: int = 8
    apify_api_token: str = ""
    supadata_api_key: str = ""

    # --- Google Workspace integration (Gmail + Calendar) ---------------------
    # Create these once at https://console.cloud.google.com and paste them here
    # or into backend/.env. See GOOGLE_SETUP.md for the exact walkthrough.
    # The app works fine with these empty - the UI shows "Not Connected".
    google_client_id: str = ""
    google_client_secret: str = ""
    # MUST match the redirect URI registered in Google Cloud exactly.
    google_redirect_uri: str = "http://127.0.0.1:8000/api/google/callback"
    # Directory holding OAuth tokens. Lives under backend/data/ which is
    # git-ignored, so credentials are never committed or synced to the vault.
    #
    # EMPTY means "work it out": backend/data/integrations, anchored to this
    # file's location. Set it only to move credentials somewhere else.
    #
    # It used to default to the relative "./data/integrations", which is resolved
    # against the process working directory. Launch the backend from anywhere but
    # backend/ - an IDE run configuration, a shell one level up, a different
    # shortcut - and the app would read an empty directory and report every
    # account as disconnected, while the real tokens sat in the other folder.
    google_token_dir: str = ""

    # --- Automatic mail ingestion into the memory vault ---------------------
    mail_sync_enabled: bool = True
    mail_sync_interval_minutes: int = 10
    # Which IMAP folders to read. INBOX by default - add "sent" to also learn
    # from what you write.
    mail_sync_folders: str = "inbox"
    # New messages processed per folder per run, so a huge mailbox cannot stall
    # the app on first sync.
    mail_sync_limit: int = 25
    # On the very first Google sync, how far back to look.
    mail_sync_backfill_days: int = 7
    # Skip newsletters/promotions (detected via List-Unsubscribe / Precedence).
    mail_sync_skip_bulk: bool = True
    # Also write each email into the GitHub-backed memory vault + wiki + graph.
    mail_store_in_vault: bool = True

    # --- Hands-free: local wake word ("Hey Jarvis") -------------------------
    # 100% offline via openWakeWord. Optional: without the packages the app
    # still runs and Alt+J works, the status endpoint just explains why.
    wake_word_enabled: bool = True
    wake_word_model: str = "hey_jarvis"
    wake_word_threshold: float = 0.5
    wake_word_debounce_seconds: float = 2.5

    # --- Proactive voice: Jarvis speaks first -------------------------------
    voice_announce_enabled: bool = True
    # Only say things at or above this level: low | normal | high | critical
    voice_announce_min_priority: str = "high"
    # "23:00-07:00" silences announcements; critical bypasses it.
    voice_quiet_hours: str = "23:00-07:00"
    voice_announce_cooldown_seconds: int = 90
    voice_announce_dedupe_minutes: int = 30

    @property
    def google_configured(self) -> bool:
        return bool(self.google_client_id.strip() and self.google_client_secret.strip())

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


def credentials_dir() -> str:
    """
    Absolute path of the credential directory.

    Anchored to this file, so it does not depend on the working directory, and
    honours GOOGLE_TOKEN_DIR when it is set. Every credential store resolves
    through here, which is what makes "connect once" actually mean once.
    """
    import os
    from pathlib import Path

    configured = (os.getenv("GOOGLE_TOKEN_DIR") or "").strip() or \
        (getattr(settings, "google_token_dir", "") or "").strip()
    if configured:
        return str(Path(configured).expanduser().resolve())
    return str((Path(__file__).resolve().parent.parent / "data" / "integrations"))
