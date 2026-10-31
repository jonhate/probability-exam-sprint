from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .textutil import (
    clean_title,
    extract_paper_stats,
    keyword_overlap,
    norm_space,
    source_snippet,
    split_sentences,
)

TZ = ZoneInfo("Asia/Shanghai")


def _important_lines(page: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for raw in page.get("text", "").splitlines():
        ln = norm_space(raw).strip(" -•·\t")
        if len(ln) < 5 or len(ln) > 260:
            continue
        lines.append(ln)
    return lines


def extract_candidates(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extractive fallback used without an LLM (and as a safety net)."""
    candidates: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}

    for doc in docs:
        if doc.get("kind") not in ("slides", "other", "homework", "exam"):
            continue
        for page in doc.get("pages", []):
            text = page.get("text", "")
            if len(text) < 20:
                continue
            title = clean_title(page.get("title", ""))
            generic = not title or re.match(r"^(第\s*\d+|正文|内容|目录|谢谢|thank)", title, re.I)
            lines = _important_lines(page)
            if generic:
                # Prefer a line that looks like a definition or labelled concept.
                title = ""
                for ln in lines:
                    if re.search(r"(是指|定义|称为|公式|定理|法则|模型|:)", ln) and len(ln) <= 50:
                        title = ln
                        break
                if not title and lines:
                    title = lines[0]
            topic = _normalise_topic_name(title)
            if not topic or len(topic) < 2:
                continue
            points = []
            for ln in lines:
                if ln == title:
                    continue
                if re.search(r"(定义|是指|称为|公式|=|注意|区别|步骤|条件|性质|定理|法则|优点|缺点|适用)", ln) or len(points) < 3:
                    if ln not in points:
                        points.append(ln[:220])
                if len(points) >= 6:
                    break
            formula = ""
            for ln in lines:
                if "=" in ln or "＝" in ln:
                    formula = ln[:180]
                    break
            key = _topic_key(topic)
            if key in seen:
                item = seen[key]
                for p in points:
                    if p not in item["key_points"]:
                        item["key_points"].append(p)
                item["emphasis"] = min(3, item["emphasis"] + 1)
                item["source_doc_ids"] = list(dict.fromkeys(item["source_doc_ids"] + [doc["doc_id"]]))
                item["evidence"].append({"doc_id": doc["doc_id"], "locator": page.get("locator", ""), "quote": source_snippet(text, topic, 160)})
            else:
                item = {
                    "name": topic[:40],
                    "summary": f"来自《{doc.get('name')}》的 {page.get('locator', '')}",
                    "key_points": points[:6],
                    "formula": formula,
                    "emphasis": 2 if doc.get("kind") in ("homework", "exam") else 1,
                    "source_doc_ids": [doc["doc_id"]],
                    "evidence": [{"doc_id": doc["doc_id"], "locator": page.get("locator", ""), "quote": source_snippet(text, topic, 160)}],
                    "origin": "heuristic",
                }
                seen[key] = item
                candidates.append(item)

    # Remove near-duplicates and rank with cheap signals.
    merged: list[dict[str, Any]] = []
    for cand in sorted(candidates, key=lambda x: (-len(x["key_points"]), -x["emphasis"], x["name"])):
        dup = None
        for existing in merged:
            a, b = _topic_key(cand["name"]), _topic_key(existing["name"])
            if a == b or (len(a) >= 4 and len(b) >= 4 and (a in b or b in a)):
                dup = existing
                break
        if dup:
            for p in cand["key_points"]:
                if p not in dup["key_points"] and len(dup["key_points"]) < 8:
                    dup["key_points"].append(p)
            dup["emphasis"] = max(dup["emphasis"], cand["emphasis"])
            dup["source_doc_ids"] = list(dict.fromkeys(dup["source_doc_ids"] + cand["source_doc_ids"]))
        else:
            merged.append(cand)
    return merged


def _normalise_topic_name(text: str) -> str:
    text = norm_space(text).replace("\n", " ")
    text = re.sub(r"^[\d一二三四五六七八九十]+[.、．)）]\s*", "", text)
    text = re.sub(r"^[（(][^)）]{1,8}[)）]\s*", "", text)
    text = re.sub(r"^(重点|考点|知识点|本章|第\d+章)[:：\s]*", "", text)
    text = text.strip("：:;；,，。. ")
    return text[:48]


def _topic_key(text: str) -> str:
    return re.sub(r"[\s\-_/\\（）()【】\[\]：:，,。.\"'“”‘’]", "", text).lower()


def make_exam_profile(docs: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    stats = extract_paper_stats([p.get("text", "") for d in docs if d.get("kind") in ("exam", "homework") for p in d.get("pages", [])])
    types = stats.get("question_types_found") or ["单选", "简答"]
    total = stats.get("estimated_total_marks") or 100
    numbered = stats.get("numbered_questions") or 0
    n = max(4, min(20, numbered or len(types) * 4))
    per = round(total / n, 1) if n else 5
    question_types = []
    for t in types:
        question_types.append({"type": t, "count": max(1, n // len(types)), "score_each": per, "pattern": "从本地资料规则推断"})
    high = []
    for c in candidates[:10]:
        if any(d.get("kind") == "exam" for d in docs):
            high.append({"name": c["name"], "evidence": "名称在真题资料中出现/相关", "frequency": c.get("emphasis", 1), "likely_types": ["综合"]})
    return {
        "paper_format": f"约 {n} 题，总分约 {total:g} 分（本地规则推断）",
        "duration_minutes": 120,
        "total_score": int(total) if total else 100,
        "confidence": "低",
        "question_types": question_types,
        "high_frequency_topics": high,
        "question_style": "以课件中的定义、条件、步骤与作业题型为主；建议用真题核对。",
        "strategy": "先做一套限时模拟暴露问题，再按错题回到高频考点，最后只背公式/条件/易错点。",
        "notes": ["当前为离线/降级分析：只做文本抽取和规则排序，不生成高质量讲解。", "没有配置大模型时，建议把本工具当作“资料整理 + 组卷框架”，不要依赖自动解析。"],
    }


def rank_candidates(docs: list[dict[str, Any]], candidates: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    has_exam = any(d.get("kind") == "exam" for d in docs)
    for c in candidates:
        name = c["name"]
        def hits(kind):
            return sum(name in p.get("text", "") for d in docs if d.get("kind") == kind for p in d.get("pages", []))
        hw = min(1.0, hits("homework") / 3)
        slide_hits = hits("slides")
        slides = min(1.0, slide_hits / 3)
        if has_exam:
            c["_priority"] = 100 * (0.55 * min(1, hits("exam") / 2) + 0.25 * hw + 0.20 * slides)
            c["_why"] = "真题重复55% + 作业重复25% + 课件覆盖20%（规则分，非命中概率）"
        else:
            # Only explicit prerequisites are evidence. Missing evidence contributes zero.
            prerequisite = min(1.0, sum(name in x.get("prerequisites", []) for x in candidates) / 3)
            c["_priority"] = 100 * (0.4 * hw + 0.4 * slides + 0.2 * prerequisite)
            c["_why"] = "推断/低置信度：作业重复40% + PPT覆盖40% + 明确先修依赖20%；缺失信号不补分"
    return sorted(candidates, key=lambda c: (-c["_priority"], len(c["name"])))[:target]


def build_topics(docs: list[dict[str, Any]], candidates: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    ranked = rank_candidates(docs, candidates, target)
    topics = []
    for i, c in enumerate(ranked, 1):
        sources = find_topic_sources(c["name"], docs, 3)
        topics.append(
            {
                "id": f"t{i:02d}",
                "name": c["name"],
                "priority": max(0, min(100, round(c.get("_priority", 0)))),
                "why": c.get("_why") or c.get("summary") or "资料中的候选考点",
                "difficulty": 3,
                "key_points": c.get("key_points", [])[:6],
                "formula": c.get("formula", ""),
                "question_types": ["单选", "简答"],
                "prerequisites": [],
                "sources": sources,
                "guide": {
                    "two_minute": c.get("summary") or "资料中的核心知识单元。",
                    "core": c.get("key_points", [])[:5],
                    "formula": c.get("formula", ""),
                    "worked_example": "资料未展开。复习时用“定义→条件→反例→一个应用题”的顺序自检。",
                    "memory_hook": f"把「{c['name']}」压缩成 3 个得分关键词。",
                    "traps": ["注意适用条件与符号，不要只背结论。"],
                    "answer_template": "先给定义/结论；再列条件；最后结合题目信息写应用或反例。",
                },
            }
        )
    return topics


def find_topic_sources(topic: str, docs: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in docs:
        kind_boost = {"exam": 1.25, "homework": 1.15, "slides": 1.0}.get(doc.get("kind"), 0.9)
        for page in doc.get("pages", []):
            text = page.get("text", "")
            if not text:
                continue
            exact = text.count(topic)
            overlap = keyword_overlap(topic, text)
            if exact == 0 and overlap < 0.35:
                continue
            score = kind_boost * (exact * 4 + overlap * 2 + min(len(text), 2000) / 5000)
            scored.append(
                (
                    score,
                    {
                        "doc_id": doc["doc_id"],
                        "doc_name": doc.get("name", ""),
                        "kind": doc.get("kind", ""),
                        "locator": page.get("locator", ""),
                        "quote": source_snippet(text, topic, 220),
                    },
                )
            )
    scored.sort(key=lambda x: -x[0])
    out = []
    seen = set()
    for _, s in scored:
        key = (s["doc_id"], s["locator"])
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= limit:
            break
    return out


def build_plan(topics: list[dict[str, Any]], days: int, hours: float, mock_minutes: int = 120) -> list[dict[str, Any]]:
    days = max(1, min(14, int(days)))
    total_minutes = max(30, round(float(hours) * 60))
    topic_ids = [t["id"] for t in topics]
    # Split topics across learning days, weighted by priority.
    if days == 1:
        groups = [topic_ids]
    else:
        learn_days = max(1, days - 1)
        groups = [[] for _ in range(learn_days)]
        for idx, tid in enumerate(topic_ids):
            groups[idx % learn_days].append(tid)
    plan = []
    for d in range(1, days + 1):
        is_last = d == days
        group = groups[min(d - 1, len(groups) - 1)] if not is_last else []
        remaining = topic_ids if days == 1 or (not group and not is_last) else group
        blocks_spec: list[tuple[str, int, list[str], str]]
        if days == 1:
            blocks_spec = [
                ("诊断：先做 5 道代表题，标出卡点", 15, [], "一张卡点清单"),
                ("核心速学：只学最高频 3–4 个考点", int(total_minutes * 0.30), remaining[: max(1, len(remaining) // 2)], "每个考点一张 5 行速记"),
                ("主动回忆：合上资料复述", int(total_minutes * 0.18), remaining, "口述/默写，不看答案"),
                ("题组训练：按题型做 2 组", int(total_minutes * 0.25), remaining, "正确率 + 错因"),
                ("错题回炉 + 公式清单", int(total_minutes * 0.17), remaining, "考前一张纸"),
            ]
        elif d == 1:
            blocks_spec = [
                ("诊断：先做 5 道代表题，确定起点", int(total_minutes * 0.08), [], "卡点清单"),
                ("核心速学：建立课程骨架", int(total_minutes * 0.42), remaining, "每个考点 5 行笔记"),
                ("主动回忆：遮住答案复述", int(total_minutes * 0.18), remaining, "回忆卡正确率"),
                ("题组训练：先做基础题", int(total_minutes * 0.22), remaining, "正确率 + 错因"),
                ("收尾：写下今天最难的 3 个点", int(total_minutes * 0.10), [], "明日复习清单"),
            ]
        elif is_last:
            blocks_spec = [
                ("考前一张纸：公式/条件/易错点", int(total_minutes * 0.10), topic_ids, "1 页 A4"),
                ("全真模拟：严格计时，不查资料", int(total_minutes * 0.38), topic_ids, "得分 + 超时题"),
                ("对答案：只记录错因，不抄题", int(total_minutes * 0.18), [], "错因分类"),
                ("错题回炉：回到对应考点", int(total_minutes * 0.20), topic_ids, "二次作答"),
                ("最终回忆：高频卡快速过一遍", int(total_minutes * 0.14), topic_ids, "仍模糊的 5 条"),
            ]
        else:
            blocks_spec = [
                ("晨间回忆：先测昨天内容", int(total_minutes * 0.08), topic_ids[:3], "回忆正确率"),
                ("高频考点速学", int(total_minutes * 0.35), remaining, "每个考点 5 行笔记"),
                ("真题/作业题型拆解", int(total_minutes * 0.22), remaining, "题型→步骤模板"),
                ("限时题组：混合题型", int(total_minutes * 0.22), remaining, "正确率 + 用时"),
                ("错题回炉 + 卡片复习", int(total_minutes * 0.13), remaining, "错题本更新"),
            ]
        # Reserve a minimum block, then allocate the remaining minutes proportionally.
        raw = sum(x[1] for x in blocks_spec)
        minimum = min(5, total_minutes // len(blocks_spec))
        remainder = total_minutes - minimum * len(blocks_spec)
        scaled = [minimum + int(x[1] * remainder / raw) for x in blocks_spec]
        for idx in range(total_minutes - sum(scaled)):
            scaled[idx % len(scaled)] += 1
        blocks = []
        for i, (title, minutes, tids, output) in enumerate(blocks_spec, 1):
            if "全真模拟" in title and scaled[i - 1] < mock_minutes:
                title = f"限时诊断：抽取代表题（整卷需 {mock_minutes} 分钟，另排时间）"
                output = "抽题得分 + 错因；本块不要求完成整卷"
            blocks.append(
                {
                    "id": f"d{d}b{i}",
                    "time": f"学习块 {i}",
                    "minutes": scaled[i - 1],
                    "activity": title,
                    "topic_ids": [x for x in tids if x],
                    "output": output,
                    "done": False,
                }
            )
        plan.append(
            {
                "day": d,
                "label": "今天" if d == 1 else f"第 {d} 天",
                "theme": "诊断 + 搭骨架" if d == 1 and days > 1 else ("全真模拟 + 错题回收" if is_last else "高频考点 + 题型训练"),
                "goal": "把最多时间花在能覆盖多个题型的高频点上；每个学习块都必须有可检查的输出。",
                "blocks": blocks,
                "total_minutes": total_minutes,
            }
        )
    return plan


def _block_time(index: int) -> str:
    starts = ["08:30", "09:20", "10:30", "14:00", "15:10", "16:20", "19:30"]
    return starts[min(index - 1, len(starts) - 1)]


def build_cards(topics: list[dict[str, Any]], count: int = 36) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    per = max(1, math.ceil(count / max(1, len(topics))))
    for topic in topics:
        points = topic.get("key_points") or topic.get("guide", {}).get("core") or []
        for j in range(per):
            if len(cards) >= count:
                break
            if j == 0:
                front = f"【核心】{topic['name']}：考试要写出哪 3 个得分关键词？"
                back = "；".join(points[:3]) or "资料未展开"
                typ = "definition"
            elif j == 1 and len(points) > 2:
                front = f"【辨析】关于「{topic['name']}」，下面哪个条件最容易漏？（先自己答）"
                back = points[2]
                typ = "trap"
            elif topic.get("formula") and j == 2:
                front = f"【公式】{topic['name']} 的公式/判定式是什么？变量各代表什么？"
                back = topic["formula"]
                typ = "formula"
            else:
                front = f"【应用】遇到「{topic['name']}」的题，第一步做什么？"
                back = (topic.get("guide", {}).get("answer_template") or "先写定义/条件，再代入题目信息。")
                typ = "process"
            cards.append(
                {
                    "id": f"c{len(cards) + 1:03d}",
                    "topic_id": topic["id"],
                    "topic": topic["name"],
                    "type": typ,
                    "front": front,
                    "back": back,
                }
            )
    return cards


def build_questions(topics: list[dict[str, Any]], count: int = 18) -> list[dict[str, Any]]:
    questions = []
    for i in range(count):
        topic = topics[i % len(topics)] if topics else None
        if not topic:
            break
        points = topic.get("key_points") or topic.get("guide", {}).get("core") or ["资料未展开"]
        questions.append(
            {
                "id": f"q{i + 1:03d}",
                "topic_id": topic["id"],
                "topic": topic["name"],
                "type": "short",
                "stem": f"请写出「{topic['name']}」的定义/判定条件/关键步骤（至少 3 点），并指出一个易错点。",
                "options": [],
                "answer": "；".join(points[:4]),
                "rubric": "定义/结论 1 分；条件或步骤 2 分；易错点 1 分。意思正确即可。",
                "explanation": "按“定义→条件→应用→易错点”的顺序作答。",
                "difficulty": 2,
                "source": "离线生成",
            }
        )
    return questions


def build_mock(topics: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    questions = build_questions(topics, min(8, max(4, len(topics))))
    total = 100
    each = round(total / max(1, len(questions)), 1)
    for q in questions:
        q["score"] = each
    if questions:
        questions[-1]["score"] = round(total - each * (len(questions) - 1), 1)
    return {
        "title": "期中仿真卷（离线框架）",
        "duration_minutes": int(profile.get("duration_minutes", 120) or 120),
        "total_score": total,
        "instructions": ["闭卷，限时完成。", "先做会做的题，最后回来处理卡住的题。", "简答题按“定义—条件—应用—易错点”作答。"],
        "sections": [
            {
                "name": "一、简答与要点题",
                "type": "short",
                "score": total,
                "questions": questions,
            }
        ],
        "note": "这是无 API 时的结构模板，不是高质量仿真卷；配置模型后会按真题蓝图重新生成。",
    }
