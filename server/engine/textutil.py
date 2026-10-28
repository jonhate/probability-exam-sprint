from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

CJK = re.compile(r"[\u3400-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}")
QUESTION_NO = re.compile(r"(?m)^\s*(?:第\s*)?(\d{1,3})\s*[.、．)）]\s*")
MARKS = re.compile(r"[（(]\s*(\d{1,3})\s*分\s*[)）]")
_STOP = {
    "的", "了", "和", "与", "及", "或", "在", "是", "为", "对", "中", "上", "下",
    "一个", "一种", "可以", "通过", "进行", "具有", "以及", "我们", "你", "我",
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "were",
}


def norm_space(text: str) -> str:
    text = text.replace("\x00", " ").replace("\r", "\n")
    text = re.sub(r"[ \t\u3000]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_title(text: str, fallback: str = "") -> str:
    text = norm_space(text).replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip(" -—·|")
    return text[:120] or fallback


def safe_filename(name: str) -> str:
    name = Path(name).name
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip(" .")
    return (name or "document")[:160]


def doc_id_for(name: str, size: int, salt: str = "") -> str:
    h = hashlib.sha1(f"{name}|{size}|{salt}".encode("utf-8", "ignore")).hexdigest()
    return "d_" + h[:12]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_filename(name: str) -> str:
    s = name.lower()
    if any(k in s for k in ("真题", "试卷", "期中", "期末", "考试", "模拟卷", "pastpaper", "past-paper", "pyq", "exam", "quiz")):
        return "exam"
    if any(k in s for k in ("作业", "习题", "练习", "题库", "homework", "assignment", "exercise", "problem", "hw")):
        return "homework"
    if any(k in s for k in ("课件", "讲义", "ppt", "slide", "lecture", "chapter", "章节", "笔记", "note", "课程")):
        return "slides"
    return "other"


def split_sentences(text: str) -> list[str]:
    text = norm_space(text)
    if not text:
        return []
    chunks = re.split(r"(?<=[。！？!?；;])\s*|\n+", text)
    return [c.strip(" \t-•·") for c in chunks if len(c.strip()) >= 3]


def _tokens(text: str) -> list[str]:
    text = text.lower()
    words = [w.lower() for w in LATIN_WORD.findall(text) if w.lower() not in _STOP and len(w) > 1]
    cjk = "".join(CJK.findall(text))
    grams: list[str] = []
    for i in range(max(0, len(cjk) - 1)):
        g = cjk[i : i + 2]
        if g not in _STOP:
            grams.append(g)
    return words + grams


def keyword_overlap(query: str, text: str) -> float:
    q = set(_tokens(query))
    if not q:
        return 0.0
    t = set(_tokens(text))
    return len(q & t) / max(1, len(q))


def source_snippet(text: str, topic_name: str, max_len: int = 180) -> str:
    text = norm_space(text).replace("\n", " ")
    if not text:
        return ""
    tokens = [t for t in _tokens(topic_name) if len(t) >= 2]
    best = 0
    best_score = -1
    sentences = split_sentences(text)
    for i, sent in enumerate(sentences):
        score = sum(1 for t in tokens if t in sent.lower())
        if score > best_score:
            best, best_score = i, score
    if not sentences:
        return text[:max_len]
    start = max(0, best)
    combined = " ".join(sentences[start : start + 2])
    if len(combined) < 20 and best > 0:
        combined = sentences[best - 1] + " " + combined
    return combined[:max_len]


def extract_paper_stats(texts: Iterable[str]) -> dict[str, Any]:
    joined = "\n".join(texts)
    q_nums = [int(x) for x in QUESTION_NO.findall(joined)]
    marks = [int(x) for x in MARKS.findall(joined)]
    type_words = {
        "单选": ("单项选择", "单选", "single choice"),
        "多选": ("多项选择", "多选", "multiple choice"),
        "判断": ("判断题", "判断", "true or false"),
        "填空": ("填空题", "填空", "fill in the blank"),
        "简答": ("简答题", "简答", "short answer"),
        "计算": ("计算题", "计算", "calculation"),
        "论述": ("论述题", "论述", "essay", "discussion"),
        "案例": ("案例分析", "案例", "case study"),
    }
    found = []
    low = joined.lower()
    for label, keys in type_words.items():
        if any(k.lower() in low for k in keys):
            found.append(label)
    return {
        "numbered_questions": max(q_nums) if q_nums else 0,
        "marks_found": marks[:30],
        "estimated_total_marks": sum(marks) if marks else 0,
        "question_types_found": found,
    }


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
