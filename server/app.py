from __future__ import annotations

import argparse
import base64
import hmac
import json
import mimetypes
import hashlib
import ipaddress
import tempfile
from functools import wraps
import os
import re
import sys
import threading
import time
import traceback
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR / "vendor"))

from engine import exports, store  # noqa: E402
from engine.llm import LLMClient, LLMError  # noqa: E402
from engine.parsers import SUPPORTED, parse_file  # noqa: E402
from engine.pipeline import AnalysisError, Pipeline  # noqa: E402
from engine.prompts import ask_prompt  # noqa: E402
from engine.textutil import classify_filename, doc_id_for, keyword_overlap, safe_filename, sha256_file  # noqa: E402

MAX_UPLOAD = 80 * 1024 * 1024
MAX_TOTAL_UPLOAD = 400 * 1024 * 1024
# Set this on a public server. When empty, the local app stays password-free.
ACCESS_TOKEN = os.environ.get("EXAMSPRINT_ACCESS_TOKEN", "").strip()

_JOB_LOCK = store._LOCK
_JOB_THREAD: threading.Thread | None = None
_JOB_STATE: dict[str, Any] = {}
_SERVER_STARTED = time.time()



def analysis_revision(project):
    raw = json.dumps(project.get("analysis"), ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def request_scope(fn):
    @wraps(fn)
    def wrapped(self):
        path = urllib.parse.urlparse(self.path).path
        # Authentication and origin checks precede any state access.
        if not self._check_auth():
            return
        if not ACCESS_TOKEN:
            hostname = urllib.parse.urlsplit("//" + self.headers.get("Host", "")).hostname
            if hostname not in {"localhost", "127.0.0.1", "::1"}:
                return self._error(403, "本地服务仅接受本机地址访问")
        if fn.__name__ == "do_POST" and not self._same_origin():
            return self._error(403, "拒绝跨站请求")
        if fn.__name__ == "do_GET" and path == "/api/health":
            return fn(self)
        def run():
            cid = store.active_course_id()
            expected = urllib.parse.unquote(self.headers.get("X-Course-ID", ""))
            if fn.__name__ == "do_POST" and expected and expected != cid:
                return self._error(409, "课程已在其他窗口切换，请刷新后重试")
            with store.course_scope(cid):
                if path == "/api/progress":
                    rev = self.headers.get("X-Analysis-Revision", "")
                    if rev and rev != analysis_revision(store.read("project")):
                        return self._error(409, "冲刺包已更新，请刷新后再记录进度")
                blocked = {"/api/upload", "/api/import-inbox", "/api/project", "/api/reset", "/api/doc-kind", "/api/delete-doc"}
                if fn.__name__ == "do_POST" and path in blocked and _JOB_THREAD and _JOB_THREAD.is_alive():
                    return self._error(409, "生成中，请完成后再修改资料、设置或重置")
                return fn(self)
        try:
            if path in {"/api/ask", "/api/settings/test"}:
                return run()
            with store._LOCK:
                return run()
        except ValueError as exc:
            return self._error(400, str(exc))
    return wrapped

def _now() -> str:
    return datetime.now(store.TZ).isoformat(timespec="seconds")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_course(value: Any) -> str:
    s = str(value or "").strip()
    return s[:80] or "我的课程"


def _validate_date(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return (datetime.now(store.TZ).date() + timedelta(days=3)).isoformat()
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("考试日期格式应为 YYYY-MM-DD") from exc
    return s


def _public_settings() -> dict[str, Any]:
    s = store.read("settings")
    key = str(s.get("api_key") or "")
    return {
        "base_url": s.get("base_url", "https://api.deepseek.com/v1"),
        "model": s.get("model", "deepseek-chat"),
        "has_key": bool(key),
        "key_hint": "已配置" if key else "",
        "temperature": s.get("temperature", 0.25),
    }


def _build_insights(project: dict[str, Any], progress: dict[str, Any]) -> dict[str, Any]:
    a = project.get("analysis") or {}
    cards = a.get("cards", [])
    questions = a.get("questions", [])
    cp = progress.get("cards", {})
    qp = progress.get("questions", {})
    now = datetime.now(store.TZ)
    due = 0
    mastery_values: list[float] = []
    seen = 0
    for c in cards:
        st = cp.get(c.get("id"), {})
        m = _safe_float(st.get("mastery"), 0)
        if st.get("seen"):
            seen += 1
        mastery_values.append(m if st.get("seen") else 0)
        due_at = st.get("due")
        if not st.get("seen"):
            due += 1
        else:
            try:
                if datetime.fromisoformat(due_at) <= now:
                    due += 1
            except Exception:
                due += 1
    card_mastery = sum(mastery_values) / max(1, len(mastery_values))
    card_coverage = seen / max(1, len(cards)) * 100
    attempts = 0
    correct = 0
    for q in questions:
        st = qp.get(q.get("id"), {})
        for x in st.get("attempts", [])[-1:]:
            attempts += 1
            if x.get("correct"):
                correct += 1
    practice_acc = correct / max(1, attempts) * 100
    mock_attempts = progress.get("mock", {}).get("attempts", [])
    last_mock = _safe_float(mock_attempts[-1].get("percent")) if mock_attempts else 0
    best_mock = max((_safe_float(x.get("percent")) for x in mock_attempts), default=0)
    readiness = (
        0.30 * card_coverage
        + 0.30 * card_mastery
        + 0.20 * practice_acc
        + 0.20 * (last_mock * 0.6 + best_mock * 0.4)
    )
    readiness = max(0, min(100, round(readiness)))

    topic_rows = []
    for t in a.get("topics", []):
        tc = [cp.get(c["id"], {}) for c in cards if c.get("topic_id") == t.get("id")]
        tm = sum(_safe_float(x.get("mastery")) for x in tc) / max(1, len(tc))
        tq = [qp.get(q["id"], {}) for q in questions if q.get("topic_id") == t.get("id")]
        ta = [att for st in tq for att in st.get("attempts", [])[-1:]]
        tacc = sum(1 for x in ta if x.get("correct")) / max(1, len(ta)) * 100
        topic_rows.append(
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "priority": t.get("priority"),
                "mastery": round(0.65 * tm + 0.35 * tacc),
                "cards_seen": sum(1 for x in tc if x.get("seen")),
                "cards_total": len(tc),
                "answers": len(ta),
            }
        )
    plan_total = sum(len(d.get("blocks", [])) for d in a.get("plan", []))
    plan_done = sum(1 for v in progress.get("plan", {}).values() if v)
    days_left = None
    exam_date = project.get("exam_date") or a.get("exam_date")
    if exam_date:
        try:
            days_left = (datetime.strptime(exam_date, "%Y-%m-%d").date() - datetime.now(store.TZ).date()).days
        except Exception:
            pass
    next_action = "上传资料并生成冲刺包"
    if a:
        if not attempts and not mock_attempts:
            next_action = "先做 10 道练习，完成起点诊断"
        elif due:
            next_action = f"先复习 {due} 张到期/未看卡片"
        elif topic_rows:
            weakest = min(topic_rows, key=lambda x: x["mastery"])
            next_action = f"补最弱考点：{weakest['name']}"
        else:
            next_action = "做一套限时仿真卷"
    return {
        "readiness": readiness,
        "card_total": len(cards),
        "card_seen": seen,
        "card_mastery": round(card_mastery),
        "due_cards": due,
        "questions_total": len(questions),
        "attempts": attempts,
        "accuracy": round(practice_acc),
        "mock_count": len(mock_attempts),
        "last_mock": round(last_mock),
        "best_mock": round(best_mock),
        "plan_total": plan_total,
        "plan_done": plan_done,
        "topics": topic_rows,
        "days_left": days_left,
        "next_action": next_action,
        "server_uptime": int(time.time() - _SERVER_STARTED),
    }


def _state_payload() -> dict[str, Any]:
    project = store.project_with_runtime()
    progress = store.read("progress")
    # Do not send full corpus pages to the browser.
    project["docs"] = [
        {k: v for k, v in d.items() if k not in ("pages", "text")}
        for d in project.get("docs", [])
    ]
    return {
        "project": project,
        "settings": _public_settings(),
        "progress": progress,
        "courses": store.list_courses(),
        "active_course_id": store.active_course_id(),
        "analysis_revision": analysis_revision(project),
        "insights": _build_insights(project, progress),
        "server": {"time": _now(), "version": "1.0.0", "active_job": bool(_JOB_THREAD and _JOB_THREAD.is_alive())},
    }


def _merge_corpus_docs(project: dict[str, Any]) -> list[dict[str, Any]]:
    corpus = store.read("corpus")
    by_id = {d.get("doc_id"): d for d in corpus.get("docs", []) if d.get("doc_id")}
    out = []
    for meta in project.get("docs", []):
        doc = by_id.get(meta.get("doc_id"))
        if doc:
            # Project metadata is authoritative for role/name.
            doc = dict(doc)
            doc.update({"name": meta.get("name", doc.get("name")), "kind": meta.get("kind", doc.get("kind"))})
            out.append(doc)
    return out


def _ingest_path(path: Path, kind_hint: str | None = None, source: str = "", original_name: str = "") -> dict[str, Any]:
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"{path.name}: 不支持 {ext}")
    size = path.stat().st_size
    if size > MAX_UPLOAD:
        raise ValueError(f"{path.name}: 单文件超过 80 MB")
    filename = safe_filename(original_name or path.name)
    file_hash = sha256_file(path)
    doc_id = "d_" + file_hash[:12]
    project = store.read("project")
    existing = next((d for d in project.get("docs", []) if d.get("doc_id") == doc_id), None)
    if existing:
        return {"ok": True, "duplicate": True, "doc": {k: v for k, v in existing.items() if k != "pages"}}
    if sum(int(d.get("size", 0) or 0) for d in project.get("docs", [])) + size > MAX_TOTAL_UPLOAD:
        raise ValueError("资料总量超过 400 MB，请删掉不需要的文件")
    kind = kind_hint if kind_hint in ("slides", "homework", "exam", "other") else classify_filename(filename)
    upload_path = store.UPLOADS / f"{doc_id}{ext}"
    if not upload_path.exists():
        tmp = upload_path.with_suffix(upload_path.suffix + ".part")
        tmp.write_bytes(path.read_bytes())
        os.replace(tmp, upload_path)
    parsed = parse_file(upload_path, filename, kind, doc_id)
    meta = {
        "doc_id": doc_id,
        "name": filename,
        "kind": kind,
        "ext": ext,
        "size": size,
        "page_count": parsed.get("page_count", 0),
        "chars": parsed.get("chars", 0),
        "warnings": parsed.get("warnings", []),
        "uploaded_at": _now(),
        "source_path": source,
    }
    project = store.read("project")
    project.setdefault("docs", []).append(meta)
    if project.get("analysis"):
        project["stale"] = True
    project["status"] = "ready"
    project["updated_at"] = _now()
    store.write("project", project)
    corpus = store.read("corpus")
    docs = [d for d in corpus.get("docs", []) if d.get("doc_id") != doc_id]
    docs.append(parsed)
    corpus["docs"] = docs
    store.write("corpus", corpus)
    return {"ok": True, "duplicate": False, "doc": meta}


def _scan_inboxes() -> dict[str, Any]:
    roots = [store.INBOX, store.ROOT.parent / "course_input"]
    added, skipped, errors = [], [], []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in SUPPORTED:
                continue
            resolved = str(p.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            parent = str(p.parent).lower()
            hint = None
            if "真题" in parent or "exam" in parent or "试卷" in parent:
                hint = "exam"
            elif "作业" in parent or "homework" in parent or "习题" in parent:
                hint = "homework"
            elif "课件" in parent or "讲义" in parent or "slides" in parent:
                hint = "slides"
            try:
                result = _ingest_path(p, hint, source=str(p))
                (skipped if result.get("duplicate") else added).append(result["doc"])
            except Exception as exc:
                errors.append({"file": str(p), "error": str(exc)})
    return {"ok": True, "added": added, "skipped": skipped, "errors": errors, "roots": [str(r) for r in roots]}


def _search_corpus(query: str, docs: list[dict[str, Any]], k: int = 6) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    qlow = query.lower().strip()
    for doc in docs:
        for page in doc.get("pages", []):
            text = page.get("text", "")
            if len(text) < 10:
                continue
            overlap = keyword_overlap(query, text)
            exact = 3.0 if qlow and qlow in text.lower() else 0
            title_hit = 1.0 if qlow and qlow in (page.get("title", "") + doc.get("name", "")).lower() else 0
            if overlap <= 0 and not exact:
                continue
            kind_boost = {"exam": 1.15, "homework": 1.1, "slides": 1.0}.get(doc.get("kind"), 0.95)
            scored.append(
                (
                    kind_boost * (overlap * 3 + exact + title_hit),
                    {
                        "doc_id": doc.get("doc_id"),
                        "name": doc.get("name"),
                        "kind": doc.get("kind"),
                        "locator": page.get("locator"),
                        "title": page.get("title"),
                        "text": text,
                    },
                )
            )
    scored.sort(key=lambda x: -x[0])
    out = []
    used = set()
    for _, c in scored:
        key = (c["doc_id"], c["locator"])
        if key in used:
            continue
        used.add(key)
        out.append(c)
        if len(out) >= k:
            break
    return out


def _api_analyze(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    global _JOB_THREAD, _JOB_STATE
    with _JOB_LOCK:
        if _JOB_THREAD and _JOB_THREAD.is_alive():
            return 409, {"ok": False, "error": "已有分析任务在运行，请等它结束。"}
        course_id = store.active_course_id()
        project = store.read("project")
        docs = _merge_corpus_docs(project)
        if not docs:
            return 400, {"ok": False, "error": "还没有可分析的资料。"}
        force_offline = bool(body.get("force_offline"))
        allow_fallback = body.get("allow_fallback", True) is not False
        settings = store.read("settings")
        project["job"] = {
            "status": "running",
            "stage": "queued",
            "progress": 0,
            "message": "已进入队列…",
            "started_at": _now(),
            "finished_at": "",
            "error": "",
        }
        project["status"] = "analyzing"
        project["updated_at"] = _now()
        store.write("project", project)
        _JOB_STATE = project["job"]

        def emit(stage: str, pct: int, message: str) -> None:
            global _JOB_STATE
            with _JOB_LOCK:
                _JOB_STATE = {
                    **_JOB_STATE,
                    "status": "running",
                    "stage": stage,
                    "progress": max(0, min(100, int(pct))),
                    "message": message,
                    "updated_at": _now(),
                }
                p = store.read("project")
                p["job"] = _JOB_STATE
                store.write("project", p)

        def worker() -> None:
            global _JOB_STATE
            try:
                emit("parse", 2, "装载资料与配置…")
                pipeline = Pipeline(
                    project=project,
                    docs=docs,
                    settings=settings,
                    emit=emit,
                    allow_fallback=allow_fallback,
                    force_offline=force_offline,
                )
                analysis = pipeline.run()
                with store._LOCK:
                    p = store.read("project")
                    # Archive before replacing the pack; sequential IDs cannot identify content.
                    previous = store.read("progress")
                    archive = store.COURSES / course_id / "history"
                    archive.mkdir(parents=True, exist_ok=True)
                    store._write_json_file(archive / f"{time.time_ns()}.json", {"analysis": p.get("analysis"), "progress": previous})
                    store.write("progress", json.loads(json.dumps(store.DEFAULTS["progress"])))
                    analysis.setdefault("generation", {}).setdefault("warnings", []).append("重新生成已归档旧冲刺包和进度；本版进度从零开始，避免题目编号错配。")
                    p["analysis"] = analysis
                    p["status"] = "ready"
                    p["stale"] = False
                    p["updated_at"] = _now()
                    _JOB_STATE = {
                        **_JOB_STATE,
                        "status": "done",
                        "stage": "done",
                        "progress": 100,
                        "message": "冲刺包已生成",
                        "finished_at": _now(),
                    }
                    p["job"] = _JOB_STATE
                    store.write("project", p)
            except Exception as exc:
                log = store.DATA / "analysis_error.log"
                try:
                    log.write_text(
                        f"[{_now()}]\n{traceback.format_exc()}\n",
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                p = store.read("project")
                p["status"] = "error"
                p["updated_at"] = _now()
                _JOB_STATE = {
                    **_JOB_STATE,
                    "status": "error",
                    "stage": "error",
                    "message": "生成失败",
                    "error": str(exc),
                    "finished_at": _now(),
                }
                p["job"] = _JOB_STATE
                store.write("project", p)

        def pinned_worker():
            with store.course_scope(course_id):
                worker()

        _JOB_THREAD = threading.Thread(target=pinned_worker, name="examsprint-analysis", daemon=True)
        _JOB_THREAD.start()
        return 202, {"ok": True, "job": _JOB_STATE}


def _update_progress(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    p = store.read("progress")
    kind = str(body.get("type") or "")
    now = datetime.now(store.TZ)
    if kind == "card":
        cid = str(body.get("id") or "")
        rating = str(body.get("rating") or "good")
        if not cid:
            return 400, {"ok": False, "error": "缺少卡片 id"}
        project = store.read("project")
        cards = (project.get("analysis") or {}).get("cards", [])
        if not any(c.get("id") == cid for c in cards):
            return 404, {"ok": False, "error": "卡片不存在，可能已重新生成"}
        st = p.setdefault("cards", {}).setdefault(cid, {"seen": 0, "mastery": 0, "correct": 0})
        st["seen"] = int(st.get("seen", 0)) + 1
        st["last"] = now.isoformat(timespec="seconds")
        if rating == "again":
            st["mastery"] = max(0, int(st.get("mastery", 0)) - 8)
            due = now + timedelta(minutes=10)
        elif rating == "hard":
            st["mastery"] = min(100, int(st.get("mastery", 0)) + 4)
            due = now + timedelta(days=1)
        elif rating == "easy":
            st["mastery"] = min(100, int(st.get("mastery", 0)) + 20)
            st["correct"] = int(st.get("correct", 0)) + 1
            due = now + timedelta(days=4)
        else:
            st["mastery"] = min(100, int(st.get("mastery", 0)) + 12)
            st["correct"] = int(st.get("correct", 0)) + 1
            due = now + timedelta(days=2)
        st["due"] = due.isoformat(timespec="seconds")
        p.setdefault("sessions", []).append({"at": now.isoformat(timespec="seconds"), "type": "card", "id": cid, "rating": rating})
    elif kind == "question":
        qid = str(body.get("id") or "")
        if not any(q.get("id") == qid for q in (store.read("project").get("analysis") or {}).get("questions", [])):
            return 404, {"ok": False, "error": "题目不存在，请刷新冲刺包"}
        if not qid:
            return 400, {"ok": False, "error": "缺少题目 id"}
        st = p.setdefault("questions", {}).setdefault(qid, {"attempts": []})
        st.setdefault("attempts", []).append(
            {
                "at": now.isoformat(timespec="seconds"),
                "correct": bool(body.get("correct")),
                "answer": str(body.get("answer") or "")[:2000],
            }
        )
        st["attempts"] = st["attempts"][-30:]
        p.setdefault("sessions", []).append({"at": now.isoformat(timespec="seconds"), "type": "question", "id": qid, "correct": bool(body.get("correct"))})
    elif kind == "mock":
        score = max(0.0, min(100.0, _safe_float(body.get("score"))))
        p.setdefault("mock", {"attempts": []}).setdefault("attempts", []).append(
            {
                "at": now.isoformat(timespec="seconds"),
                "score": score,
                "percent": score,
                "duration_minutes": _safe_float(body.get("duration_minutes")),
                "detail": body.get("detail") if isinstance(body.get("detail"), dict) else {},
            }
        )
        p["mock"]["attempts"] = p["mock"]["attempts"][-50:]
        p.setdefault("sessions", []).append({"at": now.isoformat(timespec="seconds"), "type": "mock", "score": score})
    elif kind == "plan":
        bid = str(body.get("block_id") or body.get("id") or "")
        if not bid:
            return 400, {"ok": False, "error": "缺少计划块 id"}
        if not any(b.get("id") == bid for d in (store.read("project").get("analysis") or {}).get("plan", []) for b in d.get("blocks", [])):
            return 404, {"ok": False, "error": "计划块不存在"}
        p.setdefault("plan", {})[bid] = bool(body.get("done", True))
        p.setdefault("sessions", []).append({"at": now.isoformat(timespec="seconds"), "type": "plan", "id": bid})
    else:
        return 400, {"ok": False, "error": "未知进度类型"}
    p["sessions"] = p.get("sessions", [])[-300:]
    store.write("progress", p)
    project = store.project_with_runtime()
    return 200, {"ok": True, "progress": p, "insights": _build_insights(project, p)}


class ExamSprintServer(ThreadingHTTPServer):
    # Do not silently bind a second server to the same port on Windows.
    allow_reuse_address = False
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    server_version = "ExamSprint/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.environ.get("EXAMSPRINT_VERBOSE"):
            super().log_message(fmt, *args)

    def _check_auth(self) -> bool:
        if not ACCESS_TOKEN:
            return True
        # Cloud platforms need an unauthenticated liveness endpoint.
        if self.path.split("?", 1)[0] == "/api/health":
            return True
        header = self.headers.get("Authorization", "")
        if header.startswith("Basic "):
            try:
                decoded = base64.b64decode(header[6:]).decode("utf-8", "replace")
                _, password = decoded.split(":", 1)
                if hmac.compare_digest(password, ACCESS_TOKEN):
                    return True
            except Exception:
                pass
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="ExamSprint"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    # ------------------------------------------------------------------
    # response helpers
    # ------------------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8", headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, status: int, obj: Any) -> None:
        self._send(status, _json_bytes(obj))

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"ok": False, "error": message})

    def _same_origin(self):
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            return False
        origin = self.headers.get("Origin")
        if not origin:
            return True
        parsed = urllib.parse.urlsplit(origin)
        return parsed.scheme in ("http", "https") and parsed.netloc == self.headers.get("Host")

    def _read_body(self, limit: int = MAX_UPLOAD + 1024) -> bytes:
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n < 0 or n > limit:
            raise ValueError("请求体过大")
        if n <= 0:
            return b""
        return self.rfile.read(n)

    def _read_json(self) -> dict[str, Any]:
        raw = self._read_body(4 * 1024 * 1024)
        if not raw:
            return {}
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("JSON 格式错误") from exc
        if not isinstance(value, dict):
            raise ValueError("请求体必须是 JSON 对象")
        return value

    # ------------------------------------------------------------------
    # routing
    # ------------------------------------------------------------------
    @request_scope
    def do_GET(self) -> None:
        if not self._check_auth():
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            if path in ("/", "/index.html"):
                return self._serve_static("index.html")
            if path.startswith("/static/"):
                return self._serve_static(path[len("/static/") :])
            if path == "/api/health":
                return self._json(200, {"ok": True, "time": _now(), "version": "1.0.0"})
            if path == "/api/state":
                return self._json(200, {"ok": True, **_state_payload()})
            if path == "/api/job":
                p = store.read("project")
                return self._json(200, {"ok": True, "job": p.get("job") or {}})
            if path == "/api/export":
                return self._export(parsed.query)
            return self._error(404, "Not found")
        except Exception as exc:
            return self._error(500, f"服务器错误：{exc}")

    @request_scope
    def do_POST(self) -> None:
        if not self._check_auth():
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/upload":
                return self._upload()
            if path == "/api/import-inbox":
                return self._json(200, _scan_inboxes())
            if path == "/api/analyze":
                status, obj = _api_analyze(self._read_json())
                return self._json(status, obj)
            if path == "/api/settings":
                return self._save_settings()
            if path == "/api/settings/test":
                return self._test_settings()
            if path == "/api/project":
                return self._save_project()
            if path == "/api/courses/create":
                return self._create_course()
            if path == "/api/courses/switch":
                return self._switch_course()
            if path == "/api/progress":
                status, obj = _update_progress(self._read_json())
                return self._json(status, obj)
            if path == "/api/ask":
                return self._ask()
            if path == "/api/reset":
                return self._reset()
            if path == "/api/doc-kind":
                return self._doc_kind()
            if path == "/api/delete-doc":
                return self._delete_doc()
            return self._error(404, "Not found")
        except ValueError as exc:
            return self._error(400, str(exc))
        except LLMError as exc:
            return self._error(502, f"模型调用失败：{exc}")
        except Exception as exc:
            return self._error(500, f"服务器错误：{exc}")

    # ------------------------------------------------------------------
    # endpoint implementations
    # ------------------------------------------------------------------
    def _serve_static(self, relative: str) -> None:
        base = (APP_DIR / "static").resolve()
        target = (base / relative).resolve()
        if base not in target.parents and target != base:
            return self._error(403, "Forbidden")
        if not target.exists() or not target.is_file():
            return self._error(404, "Not found")
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self._send(200, target.read_bytes(), ctype)

    def _upload(self) -> None:
        raw_name = self.headers.get("X-Filename", "")
        name = urllib.parse.unquote(raw_name) if raw_name else "upload"
        if not name:
            raise ValueError("缺少文件名")
        kind = self.headers.get("X-Doc-Kind", "auto")
        body = self._read_body()
        if not body:
            raise ValueError("空文件")
        filename = safe_filename(name)
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED:
            raise ValueError(f"不支持 {ext}，请上传 PPTX / PDF / DOCX / XLSX / TXT / MD")
        tmp_dir = store.DATA / "upload_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(suffix=ext, dir=tmp_dir)
        tmp = Path(tmp_name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(body)
        try:
            result = _ingest_path(tmp, None if kind == "auto" else kind, source="upload", original_name=filename)
        finally:
            try:
                tmp.unlink()
            except Exception:
                pass
        self._json(200, result)

    def _save_settings(self) -> None:
        body = self._read_json()
        s = store.read("settings")
        if "base_url" in body:
            s["base_url"] = str(body.get("base_url") or "").strip()[:400] or "https://api.deepseek.com/v1"
        if "model" in body:
            s["model"] = str(body.get("model") or "").strip()[:120] or "deepseek-chat"
        if body.get("clear_key"):
            s["api_key"] = ""
        elif str(body.get("api_key") or "").strip():
            s["api_key"] = str(body.get("api_key")).strip()[:500]
        store.write("settings", s)
        self._json(200, {"ok": True, "settings": _public_settings()})

    def _test_settings(self) -> None:
        body = self._read_json()
        s = store.read("settings")
        key = str(body.get("api_key") or "").strip() or str(s.get("api_key") or "")
        base = str(body.get("base_url") or s.get("base_url") or "https://api.deepseek.com/v1")
        model = str(body.get("model") or s.get("model") or "deepseek-chat")
        if not key:
            return self._error(400, "请先填写 API Key")
        client = LLMClient(api_key=key, base_url=base, model=model, timeout=45)
        result = client.test()
        self._json(200, {"ok": True, **result})

    def _save_project(self) -> None:
        body = self._read_json()
        p = store.read("project")
        if "course" in body:
            p["course"] = _clean_course(body.get("course"))
        if "exam_date" in body:
            p["exam_date"] = _validate_date(body.get("exam_date"))
        if "days" in body:
            p["days"] = max(1, min(14, int(_safe_float(body.get("days"), 3))))
        if "hours_per_day" in body:
            p["hours_per_day"] = max(0.5, min(16, _safe_float(body.get("hours_per_day"), 5)))
        if "mode" in body:
            p["mode"] = str(body.get("mode") or "sprint")[:20]
        p["updated_at"] = _now()
        store.write("project", p)
        self._json(200, {"ok": True, "project": {k: v for k, v in p.items() if k != "analysis"}})

    def _create_course(self) -> None:
        if _JOB_THREAD and _JOB_THREAD.is_alive():
            return self._error(409, "有分析任务正在运行，先等它结束再新建课程。")
        body = self._read_json()
        name = str(body.get("name") or "").strip()[:60]
        if not name:
            raise ValueError("请输入课程名称")
        course = store.create_course(name)
        self._json(200, {"ok": True, "course": course, "active_course_id": store.active_course_id()})

    def _switch_course(self) -> None:
        if _JOB_THREAD and _JOB_THREAD.is_alive():
            return self._error(409, "有分析任务正在运行，先等它结束再切换课程。")
        body = self._read_json()
        course = store.switch_course(str(body.get("id") or ""))
        self._json(200, {"ok": True, "course": course, "active_course_id": store.active_course_id()})

    def _doc_kind(self) -> None:
        body = self._read_json()
        doc_id = str(body.get("doc_id") or "")
        kind = str(body.get("kind") or "")
        if kind not in ("slides", "homework", "exam", "other"):
            raise ValueError("非法资料类型")
        p = store.read("project")
        found = False
        for d in p.get("docs", []):
            if d.get("doc_id") == doc_id:
                d["kind"] = kind
                found = True
        if not found:
            return self._error(404, "资料不存在")
        if p.get("analysis"):
            p["stale"] = True
        p["updated_at"] = _now()
        store.write("project", p)
        corpus = store.read("corpus")
        for d in corpus.get("docs", []):
            if d.get("doc_id") == doc_id:
                d["kind"] = kind
        store.write("corpus", corpus)
        self._json(200, {"ok": True})

    def _delete_doc(self) -> None:
        body = self._read_json()
        doc_id = str(body.get("doc_id") or "")
        p = store.read("project")
        p["docs"] = [d for d in p.get("docs", []) if d.get("doc_id") != doc_id]
        if p.get("analysis"):
            p["stale"] = True
        p["status"] = "ready" if p["docs"] else "empty"
        p["updated_at"] = _now()
        store.write("project", p)
        corpus = store.read("corpus")
        corpus["docs"] = [d for d in corpus.get("docs", []) if d.get("doc_id") != doc_id]
        store.write("corpus", corpus)
        self._json(200, {"ok": True})

    def _ask(self) -> None:
        body = self._read_json()
        question = str(body.get("question") or "").strip()
        if not question:
            raise ValueError("请输入问题")
        project = store.project_with_runtime()
        docs = _merge_corpus_docs(project)
        if not docs:
            return self._error(400, "还没有资料，先上传课件。")
        contexts = _search_corpus(question, docs, 6)
        settings = store.read("settings")
        key = str(settings.get("api_key") or "")
        if not key:
            if not contexts:
                return self._json(200, {"ok": True, "answer": "资料中没有检索到相关内容。请换一个更具体的术语，或配置 API Key 让教练解释。", "sources": []})
            snippets = "\n\n".join(f"**{c['name']} · {c['locator']}**\n{c['text'][:800]}" for c in contexts[:3])
            return self._json(200, {"ok": True, "answer": "尚未配置 API Key，先给你检索到的原文：\n\n" + snippets, "sources": _public_sources(contexts), "offline": True})
        client = LLMClient(
            api_key=key,
            base_url=str(settings.get("base_url") or "https://api.deepseek.com/v1"),
            model=str(settings.get("model") or "deepseek-chat"),
            timeout=90,
        )
        system, user = ask_prompt(project.get("course", "我的课程"), question, contexts)
        result = client.chat(system, user, max_tokens=1800, temperature=0.25, json_mode=False)
        self._json(200, {"ok": True, "answer": result.content, "sources": _public_sources(contexts)})

    def _reset(self) -> None:
        body = self._read_json()
        scope = str(body.get("scope") or "analysis")
        if scope == "all":
            for d in store.read("project").get("docs", []):
                pass
            store.reset_all(keep_settings=True)
            self._json(200, {"ok": True})
        elif scope == "analysis":
            p = store.read("project")
            p["analysis"] = None
            p["stale"] = False
            p["status"] = "ready" if p.get("docs") else "empty"
            p["job"] = None
            p["updated_at"] = _now()
            store.write("project", p)
            store.write("progress", {"cards": {}, "questions": {}, "mock": {"attempts": []}, "plan": {}, "sessions": []})
            self._json(200, {"ok": True})
        elif scope == "progress":
            store.write("progress", {"cards": {}, "questions": {}, "mock": {"attempts": []}, "plan": {}, "sessions": []})
            self._json(200, {"ok": True})
        else:
            raise ValueError("未知重置范围")

    def _export(self, query: str) -> None:
        params = urllib.parse.parse_qs(query)
        fmt = (params.get("format") or ["md"])[0]
        project = store.read("project")
        if not project.get("analysis"):
            return self._error(400, "尚未生成冲刺包")
        if fmt == "sheet":
            text = exports.to_cheatsheet(project)
            suffix = "考前一张纸"
        else:
            text = exports.to_markdown(project)
            suffix = "考前冲刺包"
        course = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", project.get("course", "课程"))[:40]
        filename = f"{course}_{suffix}_{datetime.now(store.TZ).strftime('%Y%m%d')}.md"
        store.EXPORTS.mkdir(parents=True, exist_ok=True)
        (store.EXPORTS / filename).write_text(text, encoding="utf-8")
        quoted = urllib.parse.quote(filename)
        self._send(
            200,
            text.encode("utf-8"),
            "text/markdown; charset=utf-8",
            {"Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"},
        )


def _public_sources(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "doc_id": c.get("doc_id"),
            "name": c.get("name"),
            "locator": c.get("locator"),
            "quote": c.get("text", "")[:260],
        }
        for c in contexts
    ]


def _repair_interrupted_job() -> None:
    p = store.read("project")
    job = p.get("job") or {}
    if job.get("status") == "running":
        job.update(
            {
                "status": "error",
                "stage": "interrupted",
                "message": "上次任务被中断",
                "error": "应用在生成过程中被关闭。请重新生成；已上传的资料不会丢失。",
                "finished_at": _now(),
            }
        )
        p["job"] = job
        p["status"] = "ready" if p.get("docs") else "empty"
        store.write("project", p)


def main() -> None:
    parser = argparse.ArgumentParser(description="ExamSprint local study agent")
    parser.add_argument("--host", default="127.0.0.1", help="bind address; use 0.0.0.0 on a cloud server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        local_bind = args.host.lower() == "localhost" or ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        local_bind = False
    if not local_bind and not ACCESS_TOKEN:
        parser.error("非本机监听必须配置 EXAMSPRINT_ACCESS_TOKEN")
    store.ensure_dirs()
    _repair_interrupted_job()
    try:
        server = ExamSprintServer((args.host, args.port), Handler)
    except OSError:
        # If a healthy ExamSprint is already running, bring its window forward
        # instead of starting a second copy on a random port.
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/api/health", timeout=2) as resp:
                if resp.status == 200:
                    print(f"ExamSprint 已在运行：http://127.0.0.1:{args.port}")
                    if not args.no_browser:
                        webbrowser.open(f"http://127.0.0.1:{args.port}")
                    return
        except Exception:
            pass
        server = ExamSprintServer((args.host, 0), Handler)
    port = server.server_address[1]
    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    info = {
        "port": port,
        "url": f"http://{display_host}:{port}",
        "pid": os.getpid(),
        "started_at": _now(),
    }
    (store.DATA / "server_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print("=" * 62)
    print("  ExamSprint · 考前冲刺 Agent")
    print(f"  绑定：{args.host}:{port}")
    print(f"  打开：http://{display_host}:{port}")
    print("  关闭此窗口即停止服务；学习进度已自动保存在 data/")
    print("=" * 62)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(f"http://{display_host}:{port}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
