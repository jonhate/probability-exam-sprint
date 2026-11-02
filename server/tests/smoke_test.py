from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import exports, store  # noqa: E402


def main() -> int:
    project = store.read("project")
    corpus = store.read("corpus")
    analysis = project.get("analysis") or {}
    assert project.get("status") == "ready", project.get("status")
    assert analysis, "analysis missing"
    topics = analysis["topics"]
    cards = analysis["cards"]
    questions = analysis["questions"]
    assert topics, "topics missing"
    assert cards, "cards missing"
    assert questions, "questions missing"
    topic_ids = {t["id"] for t in topics}
    assert all(c["topic_id"] in topic_ids for c in cards), "bad card topic"
    assert all(q["topic_id"] in topic_ids for q in questions), "bad question topic"
    assert all(t.get("sources") for t in topics), "topic without source"
    assert all(sum(b["minutes"] for b in d["blocks"]) == d["total_minutes"] for d in analysis["plan"])
    assert sum(s["score"] for s in analysis["mock"]["sections"]) == 100
    assert all(q.get("answer") for s in analysis["mock"]["sections"] for q in s["questions"])
    corpus_ids = {d["doc_id"] for d in corpus["docs"]}
    assert {s["doc_id"] for t in topics for s in t["sources"]} <= corpus_ids, "source doc missing from corpus"
    md = exports.to_markdown(project)
    assert project["course"] in md
    sheet = exports.to_cheatsheet(project)
    assert "考前一张纸" in sheet
    print("SMOKE TESTS PASSED")
    print(f"docs={len(project['docs'])} topics={len(topics)} cards={len(cards)} questions={len(questions)} mock={sum(len(s['questions']) for s in analysis['mock']['sections'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
