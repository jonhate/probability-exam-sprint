from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

from . import offline
from .llm import LLMClient, LLMError, safe_int
from .prompts import (
    cards_prompt,
    exam_analysis_prompt,
    extraction_prompt,
    guides_prompt,
    mock_prompt,
    questions_prompt,
    synthesis_prompt,
)
from .store import read, write
from .textutil import extract_paper_stats, norm_space, source_snippet, split_sentences

TZ = ZoneInfo("Asia/Shanghai")
Emit = Callable[[str, int, str], None]


class AnalysisError(RuntimeError):
    pass


class Pipeline:
    def __init__(
        self,
        project: dict[str, Any],
        docs: list[dict[str, Any]],
        settings: dict[str, Any],
        emit: Emit | None = None,
        allow_fallback: bool = True,
        force_offline: bool = False,
    ):
        self.project = project
        self.docs = docs
        self.settings = settings
        self.emit = emit or (lambda *_: None)
        self.allow_fallback = allow_fallback
        self.force_offline = force_offline
        self.warnings: list[str] = []
        self.usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.llm: LLMClient | None = None
        self.mode = "offline"
        self.coverage: list[dict[str, Any]] = []

    def run(self) -> dict[str, Any]:
        if not self.docs:
            raise AnalysisError("还没有资料。请先上传 PPT / 作业 / 真题。")
        api_key = str(self.settings.get("api_key") or "").strip()
        use_llm = bool(api_key) and not self.force_offline
        if use_llm:
            try:
                self.llm = LLMClient(
                    api_key=api_key,
                    base_url=str(self.settings.get("base_url") or "https://api.deepseek.com/v1"),
                    model=str(self.settings.get("model") or "deepseek-chat"),
                )
                self.mode = "llm"
                self.emit("start", 3, "正在整理资料结构…")
                analysis = self._run_llm()
            except Exception as exc:
                if not self.allow_fallback:
                    raise
                self.warnings.append(f"大模型生成失败，已自动切换离线模式：{exc}")
                self.emit("fallback", 66, "模型调用失败，正在生成离线冲刺框架…")
                analysis = self._run_offline(extra_warnings=self.warnings)
                analysis["generation"]["fallback_error"] = str(exc)
                self.mode = "fallback"
        else:
            self.emit("offline", 8, "未配置模型，正在生成离线冲刺框架…")
            analysis = self._run_offline()
            self.mode = "offline"
        analysis["generation"]["mode"] = self.mode
        analysis["generation"]["generated_at"] = datetime.now(TZ).isoformat(timespec="seconds")
        analysis["generation"]["usage"] = self.usage
        analysis["generation"]["warnings"] = list(dict.fromkeys(self.warnings + analysis["generation"].get("warnings", [])))
        return analysis

    # ------------------------------------------------------------------
    # LLM pipeline
    # ------------------------------------------------------------------
    def _run_llm(self) -> dict[str, Any]:
        assert self.llm is not None
        self.emit("extract", 10, "正在从课件中抽取可考考点…")
        llm_candidates, coverage = self._extract_candidates()
        self.coverage = coverage
        offline_candidates = offline.extract_candidates(self.docs)
        candidates = _merge_candidate_pool(llm_candidates + offline_candidates)
        if not candidates:
            raise AnalysisError("资料中可提取的知识点太少，无法生成有效分析。")

        self.emit("exam", 44, "正在逆向分析真题与作业题型…")
        exam_profile = self._analyze_exam(candidates)
        self.emit("synthesize", 56, "正在压缩考点，生成作战地图…")
        synthesis = self._synthesize(candidates, exam_profile)
        topics = self._sanitize_topics(synthesis.get("topics"), candidates, exam_profile)
        if len(topics) < 3:
            raise AnalysisError("模型给出的有效考点不足，已切换到离线结果。")

        target_cards = max(24, min(48, len(topics) * 3))
        target_questions = max(12, min(24, len(topics) + 8))

        self.emit("guides", 64, "正在写每考点的 2 分钟速学卡…")
        self._generate_guides(topics, exam_profile)

        self.emit("cards", 76, "正在生成主动回忆卡…")
        cards = self._generate_cards(topics, target_cards)
        if len(cards) < max(6, len(topics)):
            cards = _merge_cards(cards, offline.build_cards(topics, target_cards), target_cards)

        self.emit("questions", 85, "正在按真题风格出练习题…")
        questions = self._generate_questions(topics, target_questions, exam_profile)
        if len(questions) < 6:
            questions = _merge_questions(questions, offline.build_questions(topics, target_questions), target_questions)

        self.emit("mock", 93, "正在组装限时仿真卷…")
        mock = self._generate_mock(topics, exam_profile, questions)

        self.emit("plan", 97, "正在排 3 天冲刺计划…")
        days = safe_int(self.project.get("days"), 3, 1, 14)
        hours = safe_int(self.project.get("hours_per_day"), 5, 1, 16)
        plan = offline.build_plan(topics, days, hours)
        analysis = self._assemble(
            topics=topics,
            cards=cards,
            questions=questions,
            mock=mock,
            plan=plan,
            exam_profile=exam_profile,
            course_summary=str(synthesis.get("course_summary") or "").strip(),
            exam_strategy=str(synthesis.get("exam_strategy") or "").strip(),
            mode="llm",
            warnings=[],
        )
        self.emit("done", 100, "冲刺包已生成")
        return analysis

    def _extract_candidates(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        assert self.llm is not None
        chunks, coverage = _build_chunks(self.docs, max_chars=11500, max_per_doc=7, max_total=14)
        all_topics: list[dict[str, Any]] = []
        for i, ch in enumerate(chunks, 1):
            pct = 10 + int(30 * (i - 1) / max(1, len(chunks)))
            self.emit("extract", pct, f"抽取考点 {i}/{len(chunks)}：{ch['doc_name'][:24]}")
            system, user = extraction_prompt(ch["doc_name"], ch["kind"], ch["locator_range"], ch["text"])
            try:
                data = self.llm.complete_json(system, user, max_tokens=5200, temperature=0.15)
                self._track_usage(data)
            except Exception as exc:
                self.warnings.append(f"《{ch['doc_name']}》{ch['locator_range']} 抽取失败：{exc}")
                continue
            for raw in data.get("topics", []) or []:
                if not isinstance(raw, dict):
                    continue
                name = _clean_topic_name(raw.get("name"))
                if not name:
                    continue
                points = _as_str_list(raw.get("key_points"), 8)
                locators = [str(x) for x in raw.get("source_locators", []) if str(x).strip()][:4]
                evidence = []
                for loc in locators:
                    page = next((p for p in ch["pages"] if p.get("locator") == loc), None)
                    if page:
                        evidence.append(
                            {
                                "doc_id": ch["doc_id"],
                                "locator": loc,
                                "quote": source_snippet(page.get("text", ""), name, 200),
                            }
                        )
                all_topics.append(
                    {
                        "name": name,
                        "summary": str(raw.get("summary") or "").strip()[:300],
                        "key_points": points,
                        "formula": str(raw.get("formula") or "").strip()[:400],
                        "emphasis": safe_int(raw.get("emphasis"), 2, 1, 3),
                        "likely_question_types": _as_str_list(raw.get("likely_question_types"), 5),
                        "evidence": evidence,
                        "source_doc_ids": [ch["doc_id"]],
                        "origin": "llm",
                    }
                )
        return all_topics, coverage

    def _analyze_exam(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        exam_docs = [d for d in self.docs if d.get("kind") == "exam"]
        hw_docs = [d for d in self.docs if d.get("kind") == "homework"]
        stats = extract_paper_stats(
            [p.get("text", "") for d in exam_docs + hw_docs for p in d.get("pages", [])]
        )
        fallback = offline.make_exam_profile(self.docs, candidates)
        if not exam_docs and not hw_docs:
            self.warnings.append("没有上传真题或作业：考试蓝图按课件推断，可靠性较低。")
            return fallback
        if not exam_docs:
            self.warnings.append("没有真题：题型、分值和重点按作业 + PPT 推断，可靠性中低；请优先看老师明确强调的内容和作业错题。")
        assert self.llm is not None
        system, user = exam_analysis_prompt(self.project.get("course", "我的课程"), exam_docs, hw_docs, stats)
        try:
            data = self.llm.complete_json(system, user, max_tokens=5000, temperature=0.15)
            self._track_usage(data)
            if not isinstance(data.get("question_types"), list) or not data.get("question_types"):
                raise ValueError("缺少 question_types")
            data.setdefault("notes", [])
            data["confidence"] = str(data.get("confidence") or "低")
            return data
        except Exception as exc:
            self.warnings.append(f"真题分析失败，改用规则推断：{exc}")
            return fallback

    def _synthesize(self, candidates: list[dict[str, Any]], exam_profile: dict[str, Any]) -> dict[str, Any]:
        assert self.llm is not None
        days = safe_int(self.project.get("days"), 3, 1, 14)
        target = min(14, max(6, days * 3 + 3))
        slim = []
        for i, c in enumerate(candidates[:45], 1):
            slim.append(
                {
                    "candidate_id": i,
                    "name": c.get("name", ""),
                    "summary": c.get("summary", ""),
                    "key_points": c.get("key_points", [])[:5],
                    "formula": c.get("formula", ""),
                    "emphasis": c.get("emphasis", 1),
                    "likely_question_types": c.get("likely_question_types", []),
                    "docs": c.get("source_doc_ids", []),
                }
            )
        system, user = synthesis_prompt(
            self.project.get("course", "我的课程"), days, self.project.get("hours_per_day", 5), slim, exam_profile, target
        )
        data = self.llm.complete_json(system, user, max_tokens=7600, temperature=0.15)
        self._track_usage(data)
        return data

    def _sanitize_topics(
        self, raw_topics: Any, candidates: list[dict[str, Any]], exam_profile: dict[str, Any]
    ) -> list[dict[str, Any]]:
        cand_by_name = {_key(c.get("name", "")): c for c in candidates}
        topics: list[dict[str, Any]] = []
        for raw in (raw_topics or []):
            if not isinstance(raw, dict):
                continue
            name = _clean_topic_name(raw.get("name"))
            if not name:
                continue
            if any(_key(t["name"]) == _key(name) for t in topics):
                continue
            cand = cand_by_name.get(_key(name))
            if not cand:
                cand = next((c for c in candidates if _key(c.get("name", "")) in _key(name) or _key(name) in _key(c.get("name", ""))), None)
            points = _as_str_list(raw.get("key_points"), 8)
            if not points and cand:
                points = cand.get("key_points", [])
            formula = str(raw.get("formula") or (cand or {}).get("formula") or "").strip()
            sources = offline.find_topic_sources(name, self.docs, 3)
            if not sources and cand:
                sources = _sources_from_evidence(cand.get("evidence", []), self.docs)
            topics.append(
                {
                    "id": f"t{len(topics) + 1:02d}",
                    "name": name,
                    "priority": safe_int(raw.get("priority"), 70, 1, 100),
                    "why": str(raw.get("why") or (cand or {}).get("summary") or "").strip()[:300],
                    "difficulty": safe_int(raw.get("difficulty"), 3, 1, 5),
                    "key_points": points[:8],
                    "formula": formula[:500],
                    "question_types": _as_str_list(raw.get("question_types") or (cand or {}).get("likely_question_types"), 6),
                    "prerequisites": _as_str_list(raw.get("prerequisites"), 4),
                    "sources": sources,
                    "guide": _default_guide(name, points, formula),
                }
            )
        topics.sort(key=lambda t: -t["priority"])
        for i, t in enumerate(topics, 1):
            t["id"] = f"t{i:02d}"
        return topics[:16]

    def _generate_guides(self, topics: list[dict[str, Any]], exam_profile: dict[str, Any]) -> None:
        assert self.llm is not None
        batches = [topics[i : i + 6] for i in range(0, len(topics), 6)]
        for bi, batch in enumerate(batches, 1):
            self.emit("guides", 64 + bi * 2, f"写速学卡 {bi}/{len(batches)}…")
            payload = [
                {
                    "name": t["name"],
                    "key_points": t["key_points"],
                    "formula": t["formula"],
                    "question_types": t["question_types"],
                }
                for t in batch
            ]
            system, user = guides_prompt(self.project.get("course", "我的课程"), payload, exam_profile)
            try:
                data = self.llm.complete_json(system, user, max_tokens=7000, temperature=0.25)
                self._track_usage(data)
                by_name = {_key(g.get("name", "")): g for g in data.get("topics", []) if isinstance(g, dict)}
                for t in batch:
                    g = by_name.get(_key(t["name"]))
                    if not g:
                        g = next((v for k, v in by_name.items() if k and (k in _key(t["name"]) or _key(t["name"]) in k)), None)
                    if g:
                        t["guide"] = {
                            "two_minute": str(g.get("two_minute") or "").strip(),
                            "core": _as_str_list(g.get("core"), 8),
                            "formula": str(g.get("formula") or t["formula"] or "").strip(),
                            "worked_example": str(g.get("worked_example") or "").strip(),
                            "memory_hook": str(g.get("memory_hook") or "").strip(),
                            "traps": _as_str_list(g.get("traps"), 5),
                            "answer_template": str(g.get("answer_template") or "").strip(),
                        }
            except Exception as exc:
                self.warnings.append(f"第 {bi} 组速学卡生成失败：{exc}")

    def _generate_cards(self, topics: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
        assert self.llm is not None
        payload = [
            {"name": t["name"], "priority": t["priority"], "key_points": t["key_points"], "formula": t["formula"]}
            for t in topics
        ]
        system, user = cards_prompt(self.project.get("course", "我的课程"), payload, count)
        try:
            data = self.llm.complete_json(system, user, max_tokens=7500, temperature=0.35)
            self._track_usage(data)
            cards = []
            for raw in data.get("cards", []) or []:
                if not isinstance(raw, dict):
                    continue
                front = str(raw.get("front") or "").strip()
                back = str(raw.get("back") or "").strip()
                if not front or not back:
                    continue
                topic = _match_topic(str(raw.get("topic") or ""), topics)
                cards.append(
                    {
                        "id": f"c{len(cards) + 1:03d}",
                        "topic_id": topic["id"] if topic else (topics[0]["id"] if topics else ""),
                        "topic": topic["name"] if topic else str(raw.get("topic") or ""),
                        "type": str(raw.get("type") or "definition"),
                        "front": front[:500],
                        "back": back[:700],
                    }
                )
            return _dedupe_cards(cards)[:count]
        except Exception as exc:
            self.warnings.append(f"回忆卡生成失败，使用离线卡片：{exc}")
            return []

    def _generate_questions(self, topics: list[dict[str, Any]], count: int, exam_profile: dict[str, Any]) -> list[dict[str, Any]]:
        assert self.llm is not None
        payload = [
            {
                "name": t["name"],
                "priority": t["priority"],
                "key_points": t["key_points"],
                "formula": t["formula"],
                "question_types": t["question_types"],
                "guide": t["guide"],
            }
            for t in topics
        ]
        system, user = questions_prompt(self.project.get("course", "我的课程"), payload, count, exam_profile)
        try:
            data = self.llm.complete_json(system, user, max_tokens=8000, temperature=0.45)
            self._track_usage(data)
            return _sanitize_questions(data.get("questions"), topics, count, "仿真练习")
        except Exception as exc:
            self.warnings.append(f"练习题生成失败，使用离线题：{exc}")
            return []

    def _generate_mock(
        self, topics: list[dict[str, Any]], exam_profile: dict[str, Any], questions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        assert self.llm is not None
        payload = [
            {
                "name": t["name"],
                "priority": t["priority"],
                "key_points": t["key_points"],
                "formula": t["formula"],
                "question_types": t["question_types"],
            }
            for t in topics
        ]
        system, user = mock_prompt(self.project.get("course", "我的课程"), payload, exam_profile)
        try:
            data = self.llm.complete_json(system, user, max_tokens=8000, temperature=0.4)
            self._track_usage(data)
            mock = _sanitize_mock(data, topics)
            if mock:
                return mock
        except Exception as exc:
            self.warnings.append(f"仿真卷生成失败，改用练习题组卷：{exc}")
        return _mock_from_questions(questions, exam_profile)

    def _track_usage(self, data: dict[str, Any]) -> None:
        if not self.llm:
            return
        usage = getattr(self.llm, "last_usage", {}) or {}
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            try:
                self.usage[key] = int(self.usage.get(key, 0)) + int(usage.get(key, 0) or 0)
            except (TypeError, ValueError):
                pass

    def _assemble(
        self,
        *,
        topics: list[dict[str, Any]],
        cards: list[dict[str, Any]],
        questions: list[dict[str, Any]],
        mock: dict[str, Any],
        plan: list[dict[str, Any]],
        exam_profile: dict[str, Any],
        course_summary: str,
        exam_strategy: str,
        mode: str,
        warnings: list[str],
    ) -> dict[str, Any]:
        if not course_summary:
            course_summary = f"本课程浓缩为 {len(topics)} 个高产出考点。先建立骨架，再用题目暴露漏洞。"
        if not exam_strategy:
            exam_strategy = "先做诊断，优先攻高优先级考点；每天至少一次闭卷回忆；最后一天只做模拟和错题回炉。"
        return {
            "version": 2,
            "course": self.project.get("course", "我的课程"),
            "exam_date": self.project.get("exam_date", ""),
            "days": self.project.get("days", 3),
            "hours_per_day": self.project.get("hours_per_day", 5),
            "course_summary": course_summary,
            "exam_strategy": exam_strategy,
            "exam_profile": exam_profile,
            "blueprint": {
                "duration_minutes": safe_int(exam_profile.get("duration_minutes"), 120, 30, 300),
                "total_score": safe_int(exam_profile.get("total_score"), 100, 10, 300),
                "confidence": exam_profile.get("confidence", "低"),
                "sections": exam_profile.get("question_types", []),
                "style_notes": exam_profile.get("notes", []),
            },
            "topics": topics,
            "cards": cards,
            "questions": questions,
            "mock": mock,
            "plan": plan,
            "coverage": self.coverage,
            "generation": {
                "mode": mode,
                "provider": _provider_name(str(self.settings.get("base_url") or "")),
                "model": str(self.settings.get("model") or ""),
                "doc_count": len(self.docs),
                "total_chars": sum(d.get("chars", 0) for d in self.docs),
                "doc_stats": [{"name": d.get("name"), "kind": d.get("kind"), "pages": d.get("page_count"), "chars": d.get("chars")} for d in self.docs],
                "warnings": warnings,
                "usage": self.usage,
            },
        }

    # ------------------------------------------------------------------
    # Offline fallback
    # ------------------------------------------------------------------
    def _run_offline(self, extra_warnings: list[str] | None = None) -> dict[str, Any]:
        self.emit("offline", 20, "正在抽取标题与关键句…")
        candidates = offline.extract_candidates(self.docs)
        if not candidates:
            raise AnalysisError("从资料中提取不到足够文字。请确认文件不是扫描图片，或先转成可复制文字的 PDF/PPTX。")
        profile = offline.make_exam_profile(self.docs, candidates)
        days = safe_int(self.project.get("days"), 3, 1, 14)
        hours = safe_int(self.project.get("hours_per_day"), 5, 1, 16)
        target = min(14, max(6, days * 3 + 3))
        self.emit("offline", 45, "正在按真题/作业信号排序考点…")
        topics = offline.build_topics(self.docs, candidates, target)
        self.emit("offline", 65, "正在生成回忆卡与练习…")
        cards = offline.build_cards(topics, max(24, len(topics) * 3))
        questions = offline.build_questions(topics, max(12, len(topics) + 6))
        mock = offline.build_mock(topics, profile)
        plan = offline.build_plan(topics, days, hours)
        warnings = list(extra_warnings or [])
        warnings.append("当前为离线模式：考点来自标题/关键句抽取，题目为框架题；配置 DeepSeek/OpenAI 兼容 API 后会重新生成高质量讲解、仿真题和仿真卷。")
        analysis = self._assemble(
            topics=topics,
            cards=cards,
            questions=questions,
            mock=mock,
            plan=plan,
            exam_profile=profile,
            course_summary=f"从 {len(self.docs)} 份资料中抽取 {len(topics)} 个考点。离线模式先保证结构和复习闭环，不保证讲解深度。",
            exam_strategy="先做一套题定位漏洞；用速学卡建立最小知识骨架；每 25 分钟必须闭卷输出一次；最后一天只做模拟卷和错题。",
            mode="offline",
            warnings=warnings,
        )
        self.emit("done", 100, "离线冲刺框架已生成")
        return analysis


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _provider_name(base_url: str) -> str:
    low = base_url.lower()
    if "deepseek" in low:
        return "DeepSeek"
    if "openai" in low:
        return "OpenAI"
    if "ollama" in low or "localhost" in low or "127.0.0.1" in low:
        return "Local / Ollama"
    return "OpenAI-compatible"


def _build_chunks(
    docs: list[dict[str, Any]], max_chars: int = 11500, max_per_doc: int = 7, max_total: int = 14
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chunks: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for doc in docs:
        pages = [p for p in doc.get("pages", []) if p.get("text")]
        if not pages:
            coverage.append({"doc_id": doc["doc_id"], "name": doc.get("name"), "included": 0, "total": 0, "truncated": False})
            continue
        local: list[dict[str, Any]] = []
        cur: list[dict[str, Any]] = []
        cur_len = 0
        for page in pages:
            header = f"\n[{page.get('locator','')} | {page.get('title','')}]\n"
            body = page.get("text", "")
            if cur and cur_len + len(body) + len(header) > max_chars:
                local.append({"pages": cur, "text": _chunk_text(cur), "locator_range": _locator_range(cur)})
                cur, cur_len = [], 0
            if len(body) + len(header) > max_chars:
                body = body[:max_chars]
            cur.append({**page, "text": body})
            cur_len += len(body) + len(header)
        if cur:
            local.append({"pages": cur, "text": _chunk_text(cur), "locator_range": _locator_range(cur)})
        original = len(local)
        if len(local) > max_per_doc:
            # Keep first/last and evenly sample the middle.
            idx = sorted(set([0, len(local) - 1] + [round(i * (len(local) - 1) / (max_per_doc - 1)) for i in range(max_per_doc)]))
            local = [local[i] for i in idx][:max_per_doc]
        for ch in local:
            ch.update({"doc_id": doc["doc_id"], "doc_name": doc.get("name", ""), "kind": doc.get("kind", "other")})
            chunks.append(ch)
        coverage.append(
            {
                "doc_id": doc["doc_id"],
                "name": doc.get("name"),
                "included": len(local),
                "total": original,
                "truncated": original > len(local),
            }
        )
    if len(chunks) > max_total:
        idx = sorted(set([0, len(chunks) - 1] + [round(i * (len(chunks) - 1) / (max_total - 1)) for i in range(max_total)]))
        chunks = [chunks[i] for i in idx][:max_total]
    return chunks, coverage


def _chunk_text(pages: list[dict[str, Any]]) -> str:
    parts = []
    for p in pages:
        parts.append(f"\n[{p.get('locator', '')} | {p.get('title', '')}]\n{p.get('text', '')}")
    return "\n".join(parts).strip()


def _locator_range(pages: list[dict[str, Any]]) -> str:
    if not pages:
        return ""
    first = pages[0].get("locator", "")
    last = pages[-1].get("locator", "")
    return first if first == last else f"{first}–{last}"


def _clean_topic_name(value: Any) -> str:
    text = norm_space(str(value or "")).replace("\n", " ")
    text = re.sub(r"^[\d一二三四五六七八九十]+[.、．)）]\s*", "", text)
    text = text.strip("：:;；,，。. -")
    return text[:60]


def _as_str_list(value: Any, limit: int) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    out = []
    for x in value:
        s = str(x or "").strip()
        if s and s not in out:
            out.append(s[:500])
        if len(out) >= limit:
            break
    return out


def _key(text: str) -> str:
    return re.sub(r"[\s\-_/\\（）()【】\[\]：:，,。.\"'“”‘’]", "", text or "").lower()


def _merge_candidate_pool(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for cand in sorted(items, key=lambda x: (0 if x.get("origin") == "llm" else 1, -len(x.get("key_points", [])), x.get("name", ""))):
        key = _key(cand.get("name", ""))
        if not key:
            continue
        dup = next((x for x in merged if x["_key"] == key or (len(key) >= 4 and (key in x["_key"] or x["_key"] in key))), None)
        if dup:
            for p in cand.get("key_points", []):
                if p not in dup["key_points"] and len(dup["key_points"]) < 10:
                    dup["key_points"].append(p)
            dup["emphasis"] = max(dup.get("emphasis", 1), cand.get("emphasis", 1))
            dup["source_doc_ids"] = list(dict.fromkeys(dup.get("source_doc_ids", []) + cand.get("source_doc_ids", [])))
            dup.setdefault("evidence", []).extend(cand.get("evidence", []))
            if cand.get("origin") == "llm" and dup.get("origin") != "llm":
                dup["origin"] = "llm"
            if not dup.get("formula") and cand.get("formula"):
                dup["formula"] = cand["formula"]
        else:
            c = dict(cand)
            c["_key"] = key
            c["key_points"] = list(dict.fromkeys(c.get("key_points", [])))[:10]
            c["source_doc_ids"] = list(dict.fromkeys(c.get("source_doc_ids", [])))
            c.setdefault("evidence", [])
            merged.append(c)
    for c in merged:
        c.pop("_key", None)
    return merged


def _sources_from_evidence(evidence: list[dict[str, Any]], docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {d["doc_id"]: d for d in docs}
    out = []
    for e in evidence:
        doc = by_id.get(e.get("doc_id"))
        if not doc:
            continue
        out.append(
            {
                "doc_id": doc["doc_id"],
                "doc_name": doc.get("name", ""),
                "kind": doc.get("kind", ""),
                "locator": e.get("locator", ""),
                "quote": e.get("quote", ""),
            }
        )
        if len(out) >= 3:
            break
    return out


def _default_guide(name: str, points: list[str], formula: str) -> dict[str, Any]:
    return {
        "two_minute": f"先把「{name}」压缩成“定义—条件—用途—易错点”四格；考试时先写定义，再代入题目条件。",
        "core": points[:6],
        "formula": formula,
        "worked_example": "资料未展开。可用最小例子自检：写出定义，构造一个满足条件的例子，再构造一个反例。",
        "memory_hook": "定义→条件→例子→反例，四步过一遍。",
        "traps": ["注意适用条件和符号，不要只背结论。"],
        "answer_template": "结论；关键条件；结合题目信息推导；检查单位/边界。",
    }


def _match_topic(name: str, topics: list[dict[str, Any]]) -> dict[str, Any] | None:
    key = _key(name)
    if not key:
        return None
    exact = next((t for t in topics if _key(t["name"]) == key), None)
    if exact:
        return exact
    return next((t for t in topics if key and (key in _key(t["name"]) or _key(t["name"]) in key)), None)


def _dedupe_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for c in cards:
        k = _key(c.get("front", ""))
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(c)
    for i, c in enumerate(out, 1):
        c["id"] = f"c{i:03d}"
    return out


def _merge_cards(primary: list[dict[str, Any]], fallback: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return _dedupe_cards(primary + fallback)[:limit]


def _merge_questions(primary: list[dict[str, Any]], fallback: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for q in primary + fallback:
        k = _key(q.get("stem", ""))
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(q)
        if len(out) >= limit:
            break
    for i, q in enumerate(out, 1):
        q["id"] = f"q{i:03d}"
    return out


def _sanitize_questions(raw: Any, topics: list[dict[str, Any]], limit: int, source: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out = []
    allowed = {"single", "multiple", "judge", "short", "calculation", "essay"}
    for item in raw:
        if not isinstance(item, dict):
            continue
        stem = str(item.get("stem") or "").strip()
        answer = item.get("answer")
        if not stem or answer is None:
            continue
        qtype = str(item.get("type") or "short").lower().strip()
        qtype = qtype if qtype in allowed else ("single" if item.get("options") else "short")
        options = _as_str_list(item.get("options"), 6) if isinstance(item.get("options"), list) else []
        if qtype == "single" and len(options) < 3:
            qtype = "short"
        if qtype == "single":
            ans = str(answer).strip()
            m = re.match(r"^([A-Fa-f])", ans)
            if m:
                answer = m.group(1).upper()
            else:
                # If the answer is the full option text, map it back to a letter.
                for idx, opt in enumerate(options):
                    if _key(opt).endswith(_key(ans)) or _key(ans) in _key(opt):
                        answer = chr(65 + idx)
                        break
        topic = _match_topic(str(item.get("topic") or ""), topics)
        out.append(
            {
                "id": f"q{len(out) + 1:03d}",
                "topic_id": topic["id"] if topic else (topics[0]["id"] if topics else ""),
                "topic": topic["name"] if topic else str(item.get("topic") or ""),
                "type": qtype,
                "stem": stem[:1600],
                "options": options,
                "answer": answer if isinstance(answer, list) else str(answer)[:1800],
                "rubric": str(item.get("rubric") or "").strip()[:1200],
                "explanation": str(item.get("explanation") or "").strip()[:1600],
                "difficulty": safe_int(item.get("difficulty"), 2, 1, 5),
                "source": source,
            }
        )
        if len(out) >= limit:
            break
    return out


def _sanitize_mock(data: dict[str, Any], topics: list[dict[str, Any]]) -> dict[str, Any] | None:
    sections_raw = data.get("sections")
    if not isinstance(sections_raw, list) or not sections_raw:
        return None
    sections = []
    qnum = 0
    for s in sections_raw:
        if not isinstance(s, dict):
            continue
        qs = _sanitize_questions(s.get("questions"), topics, 40, "仿真卷")
        if not qs:
            continue
        for q in qs:
            qnum += 1
            q["id"] = f"m{qnum:02d}"
        sections.append(
            {
                "name": str(s.get("name") or f"第{len(sections) + 1}部分")[:80],
                "type": str(s.get("type") or "mixed"),
                "score": safe_int(s.get("score"), 0, 0, 200),
                "questions": qs,
            }
        )
    if not sections:
        return None
    total = safe_int(data.get("total_score"), 100, 10, 300)
    return {
        "title": str(data.get("title") or "期中仿真卷")[:120],
        "duration_minutes": safe_int(data.get("duration_minutes"), 120, 20, 300),
        "total_score": total,
        "instructions": _as_str_list(data.get("instructions"), 8),
        "sections": sections,
        "generated": True,
    }


def _mock_from_questions(questions: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    picked = questions[: min(10, len(questions))]
    if not picked:
        return {
            "title": "期中仿真卷",
            "duration_minutes": 120,
            "total_score": 100,
            "instructions": ["闭卷完成。"],
            "sections": [],
            "generated": False,
        }
    each = round(100 / len(picked), 1)
    picked = [dict(q, score=each) for q in picked]
    return {
        "title": "期中仿真卷（练习重组）",
        "duration_minutes": safe_int(profile.get("duration_minutes"), 120, 30, 300),
        "total_score": 100,
        "instructions": ["闭卷，限时完成。", "先易后难，最后检查公式与单位。"],
        "sections": [
            {
                "name": "一、综合题组",
                "type": "mixed",
                "score": 100,
                "questions": picked,
            }
        ],
        "generated": False,
    }
