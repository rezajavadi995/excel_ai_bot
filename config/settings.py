from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path.home() / ".config" / "excel_ai_bot"
SECRETS_FILE = APP_DIR / "secrets.json"


@dataclass
class Settings:
    bot_token: str
    admin_id: int


def _from_env() -> Settings | None:
    token = os.getenv("BOT_TOKEN")
    admin = os.getenv("ADMIN_ID")
    if token and admin and admin.isdigit():
        return Settings(bot_token=token, admin_id=int(admin))
    return None


def _from_file() -> Settings | None:
    if not SECRETS_FILE.exists():
        return None
    data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    token = str(data.get("BOT_TOKEN", "")).strip()
    admin = data.get("ADMIN_ID")
    if token and isinstance(admin, int):
        return Settings(bot_token=token, admin_id=admin)
    return None


def get_settings() -> Settings:
    env = _from_env()
    if env:
        return env
    file_settings = _from_file()
    if file_settings:
        return file_settings
    raise RuntimeError(
        "تنظیمات ربات پیدا نشد. ابتدا install.sh را اجرا کنید تا BOT_TOKEN و ADMIN_ID ثبت شوند."
    )
