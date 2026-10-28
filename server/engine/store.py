from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UPLOADS = ROOT / "uploads"
EXPORTS = ROOT / "exports"
INBOX = ROOT / "inbox"
TZ = ZoneInfo("Asia/Shanghai")

_LOCK = threading.RLock()

DEFAULTS: dict[str, Any] = {
    "project": {
        "version": 1,
        "course": "我的课程",
        "exam_date": "",
        "days": 3,
        "hours_per_day": 5,
        "mode": "sprint",
        "created_at": "",
        "updated_at": "",
        "status": "empty",
        "docs": [],
        "analysis": None,
        "job": None,
    },
    "corpus": {"docs": []},
    "settings": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": "",
        "temperature": 0.25,
    },
    "progress": {
        "cards": {},
        "questions": {},
        "mock": {"attempts": []},
        "plan": {},
        "sessions": [],
    },
}


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def today_str() -> str:
    return datetime.now(TZ).date().isoformat()


def ensure_dirs() -> None:
    for p in (DATA, UPLOADS, EXPORTS, INBOX):
        p.mkdir(parents=True, exist_ok=True)


def _path(name: str) -> Path:
    if name not in DEFAULTS:
        raise KeyError(name)
    return DATA / f"{name}.json"


def read(name: str) -> dict[str, Any]:
    ensure_dirs()
    with _LOCK:
        p = _path(name)
        if not p.exists():
            return json.loads(json.dumps(DEFAULTS[name]))
        try:
            with p.open("r", encoding="utf-8") as f:
                value = json.load(f)
        except (OSError, json.JSONDecodeError):
            value = json.loads(json.dumps(DEFAULTS[name]))
        base = json.loads(json.dumps(DEFAULTS[name]))
        if isinstance(base, dict) and isinstance(value, dict):
            base.update(value)
            value = base
        return value


def write(name: str, value: dict[str, Any]) -> None:
    ensure_dirs()
    with _LOCK:
        p = _path(name)
        fd, tmp = tempfile.mkstemp(prefix=f".{name}-", suffix=".tmp", dir=str(DATA))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def reset_all(keep_settings: bool = True) -> None:
    settings = read("settings") if keep_settings else json.loads(json.dumps(DEFAULTS["settings"]))
    for name in DEFAULTS:
        write(name, json.loads(json.dumps(DEFAULTS[name])))
    if keep_settings:
        write("settings", settings)


def project_with_runtime() -> dict[str, Any]:
    p = read("project")
    if not p.get("exam_date"):
        from datetime import timedelta

        p["exam_date"] = (datetime.now(TZ).date() + timedelta(days=3)).isoformat()
    return p
