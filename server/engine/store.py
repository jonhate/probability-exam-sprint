from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UPLOADS = ROOT / "uploads"
EXPORTS = ROOT / "exports"
INBOX = ROOT / "inbox"
COURSES = DATA / "courses"
ACTIVE = DATA / "active_course.json"
COURSES_META = DATA / "courses.json"
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

COURSE_FILES = {"project", "corpus", "progress"}


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def today_str() -> str:
    return datetime.now(TZ).date().isoformat()


def _read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return json.loads(json.dumps(default))
    try:
        with path.open("r", encoding="utf-8") as f:
            value = json.load(f)
    except (OSError, json.JSONDecodeError):
        value = json.loads(json.dumps(default))
    if isinstance(default, dict) and isinstance(value, dict):
        merged = json.loads(json.dumps(default))
        merged.update(value)
        return merged
    return value


def _write_json_file(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _read_meta() -> dict[str, Any]:
    meta = _read_json_file(COURSES_META, {"courses": []})
    if not isinstance(meta.get("courses"), list):
        meta["courses"] = []
    return meta


def _course_slug(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_\-\u4e00-\u9fff]+", "-", name).strip("-")[:36]
    return base or "course"


def _new_course_dir(course_id: str, name: str) -> Path:
    d = COURSES / course_id
    d.mkdir(parents=True, exist_ok=True)
    project = json.loads(json.dumps(DEFAULTS["project"]))
    project["course"] = name
    project["exam_date"] = (datetime.now(TZ).date() + timedelta(days=3)).isoformat()
    project["created_at"] = now_iso()
    project["updated_at"] = now_iso()
    project["status"] = "empty"
    _write_json_file(d / "project.json", project)
    _write_json_file(d / "corpus.json", json.loads(json.dumps(DEFAULTS["corpus"])))
    _write_json_file(d / "progress.json", json.loads(json.dumps(DEFAULTS["progress"])))
    return d


def _ensure_active() -> str:
    """Create/migrate the active course and return its id.

    The first run migrates the old single-project files (data/project.json,
    data/corpus.json, data/progress.json) into a course folder. This preserves
    the probability pack while enabling additional courses.
    """
    COURSES.mkdir(parents=True, exist_ok=True)
    if ACTIVE.exists():
        try:
            active = json.loads(ACTIVE.read_text(encoding="utf-8"))
            cid = str(active.get("id") or "")
            if cid and (COURSES / cid).exists():
                return cid
        except Exception:
            pass

    meta = _read_meta()
    legacy_project = DATA / "project.json"

    if legacy_project.exists():
        cid = "probability-midterm"
        d = COURSES / cid
        d.mkdir(parents=True, exist_ok=True)
        for name in ("project", "corpus", "progress"):
            src = DATA / f"{name}.json"
            if src.exists():
                value = _read_json_file(src, DEFAULTS[name])
                _write_json_file(d / f"{name}.json", value)
        course_name = _read_json_file(d / "project.json", DEFAULTS["project"]).get("course") or "概率统计"
        if not any(x.get("id") == cid for x in meta["courses"]):
            meta["courses"].append({"id": cid, "name": course_name, "created_at": now_iso()})
        _write_json_file(COURSES_META, meta)
        _write_json_file(ACTIVE, {"id": cid})
        return cid

    # Fresh installation: create an empty first course.
    cid = "course-1"
    _new_course_dir(cid, "我的课程")
    meta["courses"].append({"id": cid, "name": "我的课程", "created_at": now_iso()})
    _write_json_file(COURSES_META, meta)
    _write_json_file(ACTIVE, {"id": cid})
    return cid


def ensure_dirs() -> None:
    for p in (DATA, UPLOADS, EXPORTS, INBOX, COURSES):
        p.mkdir(parents=True, exist_ok=True)
    _ensure_active()


def _path(name: str) -> Path:
    if name not in DEFAULTS:
        raise KeyError(name)
    if name in COURSE_FILES:
        return COURSES / _ensure_active() / f"{name}.json"
    return DATA / f"{name}.json"


def active_course_id() -> str:
    ensure_dirs()
    return _ensure_active()


def list_courses() -> list[dict[str, Any]]:
    ensure_dirs()
    meta = _read_meta()
    active = active_course_id()
    out = []
    for c in meta.get("courses", []):
        cid = str(c.get("id") or "")
        if not cid:
            continue
        d = COURSES / cid
        if not d.exists():
            continue
        proj = _read_json_file(d / "project.json", DEFAULTS["project"])
        out.append(
            {
                "id": cid,
                "name": proj.get("course") or c.get("name") or cid,
                "status": proj.get("status", "empty"),
                "docs": len(proj.get("docs", [])),
                "has_analysis": bool(proj.get("analysis")),
                "created_at": c.get("created_at", ""),
                "active": cid == active,
            }
        )
    return out


def create_course(name: str) -> dict[str, Any]:
    ensure_dirs()
    name = (name or "新课程").strip()[:60] or "新课程"
    meta = _read_meta()
    base = _course_slug(name)
    cid = base
    i = 2
    while (COURSES / cid).exists():
        cid = f"{base}-{i}"
        i += 1
    _new_course_dir(cid, name)
    meta["courses"].append({"id": cid, "name": name, "created_at": now_iso()})
    _write_json_file(COURSES_META, meta)
    _write_json_file(ACTIVE, {"id": cid})
    return {"id": cid, "name": name}


def switch_course(cid: str) -> dict[str, Any]:
    ensure_dirs()
    cid = str(cid or "")
    if not cid or not (COURSES / cid).exists():
        raise ValueError("课程不存在")
    meta = _read_meta()
    if not any(c.get("id") == cid for c in meta.get("courses", [])):
        raise ValueError("课程不在课程列表中")
    _write_json_file(ACTIVE, {"id": cid})
    proj = _read_json_file(COURSES / cid / "project.json", DEFAULTS["project"])
    return {"id": cid, "name": proj.get("course", cid)}


def read(name: str) -> dict[str, Any]:
    ensure_dirs()
    with _LOCK:
        p = _path(name)
        return _read_json_file(p, DEFAULTS[name])


def write(name: str, value: dict[str, Any]) -> None:
    ensure_dirs()
    with _LOCK:
        p = _path(name)
        _write_json_file(p, value)


def reset_all(keep_settings: bool = True) -> None:
    settings = read("settings") if keep_settings else json.loads(json.dumps(DEFAULTS["settings"]))
    for name in DEFAULTS:
        write(name, json.loads(json.dumps(DEFAULTS[name])))
    if keep_settings:
        write("settings", settings)


def project_with_runtime() -> dict[str, Any]:
    p = read("project")
    if not p.get("exam_date"):
        p["exam_date"] = (datetime.now(TZ).date() + timedelta(days=3)).isoformat()
    return p
