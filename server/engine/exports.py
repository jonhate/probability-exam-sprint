from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")


def _doc_name_map(project: dict[str, Any]) -> dict[str, str]:
    return {d["doc_id"]: d.get("name", "") for d in project.get("docs", [])}


def to_markdown(project: dict[str, Any]) -> str:
    a = project.get("analysis") or {}
    if not a:
        return "# ExamSprint\n\n尚未生成冲刺包。\n"
    names = _doc_name_map(project)
    lines: list[str] = []
    title = a.get("course") or project.get("course") or "课程"
    lines.append(f"# {title} · 考前冲刺包")
    lines.append("")
    lines.append(f"> 考试日期：{a.get('exam_date', '')} ｜ 计划：{a.get('days', 3)} 天 × 每天 {a.get('hours_per_day', 5)} 小时 ｜ 生成：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## 0. 先看结论")
    lines.append("")
    lines.append(a.get("course_summary", ""))
    lines.append("")
    lines.append(f"**冲刺策略**：{a.get('exam_strategy', '')}")
    lines.append("")
    topics_all = a.get("topics", [])
    tiers = [
        ("S · 必拿", [t for t in topics_all if (t.get("priority") or 0) >= 94]),
        ("A · 补漏", [t for t in topics_all if 84 <= (t.get("priority") or 0) < 94]),
        ("B · 最后学 / 可战略放弃", [t for t in topics_all if (t.get("priority") or 0) < 84]),
    ]
    lines.append("## 0.5 性价比分层（先保 S，再补 A，B 只学模板）")
    lines.append("")
    for label, items in tiers:
        lines.append(f"**{label}**：" + "；".join(t.get("name", "") for t in items))
        lines.append("")
    profile = a.get("exam_profile", {})
    lines.append("## 1. 考试蓝图（从资料反推，非押题）")
    lines.append("")
    lines.append(f"- 形式：{profile.get('paper_format', '')}")
    lines.append(f"- 时长：{profile.get('duration_minutes', '?')} 分钟；总分：{profile.get('total_score', '?')}")
    lines.append(f"- 置信度：{profile.get('confidence', '低')}（资料不足时必须自行核对）")
    qt = profile.get("question_types") or []
    if qt:
        lines.append("")
        lines.append("| 题型 | 题量 | 分值 | 命题特点 |")
        lines.append("|---|---:|---:|---|")
        for x in qt:
            lines.append(f"| {x.get('type','')} | {x.get('count','')} | {x.get('score_each','')} | {x.get('pattern','')} |")
    lines.append("")
    lines.append("## 2. 高频考点与 2 分钟速学卡")
    lines.append("")
    for i, t in enumerate(a.get("topics", []), 1):
        g = t.get("guide", {})
        lines.append(f"### {i}. {t.get('name','')}　`优先级 {t.get('priority', '')}`")
        lines.append("")
        lines.append(f"**为什么现在学**：{t.get('why','')}")
        lines.append("")
        if g.get("two_minute"):
            lines.append(f"**2 分钟讲解**：{g['two_minute']}")
            lines.append("")
        if g.get("core"):
            lines.append("**必须掌握**：")
            for p in g["core"]:
                lines.append(f"- {p}")
            lines.append("")
        formula = g.get("formula") or t.get("formula")
        if formula:
            lines.append(f"**公式/框架**：`{formula}`")
            lines.append("")
        if g.get("memory_hook"):
            lines.append(f"**记忆钩子**：{g['memory_hook']}")
            lines.append("")
        if g.get("traps"):
            lines.append("**易错点**：")
            for p in g["traps"]:
                lines.append(f"- {p}")
            lines.append("")
        if g.get("answer_template"):
            lines.append(f"**答题模板**：{g['answer_template']}")
            lines.append("")
        if t.get("sources"):
            src = "；".join(f"{names.get(s.get('doc_id'), s.get('doc_name',''))} {s.get('locator','')}" for s in t["sources"][:3])
            lines.append(f"**原文位置**：{src}")
            lines.append("")
    lines.append("## 3. 三天作战计划")
    lines.append("")
    for day in a.get("plan", []):
        lines.append(f"### {day.get('label', '')}：{day.get('theme', '')}")
        lines.append("")
        lines.append(f"> {day.get('goal', '')}")
        lines.append("")
        for b in day.get("blocks", []):
            lines.append(f"- [ ] {b.get('time','')}　**{b.get('minutes',0)} min**　{b.get('activity','')} → {b.get('output','')}")
        lines.append("")
    lines.append("## 4. 主动回忆卡")
    lines.append("")
    for c in a.get("cards", []):
        lines.append(f"- **{c.get('topic','')}**｜{c.get('front','')}")
        lines.append(f"  - {c.get('back','')}")
    lines.append("")
    lines.append("## 5. 仿真卷")
    lines.append("")
    mock = a.get("mock") or {}
    lines.append(f"### {mock.get('title','仿真卷')}")
    lines.append("")
    lines.append(f"时长 {mock.get('duration_minutes','?')} 分钟｜总分 {mock.get('total_score','?')}")
    for ins in mock.get("instructions", []):
        lines.append(f"- {ins}")
    lines.append("")
    n = 0
    for sec in mock.get("sections", []):
        lines.append(f"#### {sec.get('name','')}")
        lines.append("")
        for q in sec.get("questions", []):
            n += 1
            lines.append(f"**{n}. {q.get('stem','')}**")
            for opt in q.get("options", []):
                lines.append(f"- {opt}")
            lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### 参考答案与评分点")
    lines.append("")
    n = 0
    for sec in mock.get("sections", []):
        for q in sec.get("questions", []):
            n += 1
            ans = q.get("answer", "")
            if isinstance(ans, list):
                ans = "、".join(str(x) for x in ans)
            lines.append(f"**{n}. {ans}**")
            if q.get("rubric"):
                lines.append(f"评分：{q['rubric']}")
            if q.get("explanation"):
                lines.append(f"解析：{q['explanation']}")
            lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("生成工具：ExamSprint。题目为仿真练习，不保证命中真题；请以老师范围和教材为准。")
    return "\n".join(lines)


def to_cheatsheet(project: dict[str, Any]) -> str:
    a = project.get("analysis") or {}
    if not a:
        return "# 考前一张纸\n\n尚未生成。\n"
    lines = [f"# {a.get('course', project.get('course',''))} · 考前一张纸", ""]
    for t in a.get("topics", []):
        g = t.get("guide", {})
        formula = g.get("formula") or t.get("formula") or ""
        points = g.get("core") or t.get("key_points") or []
        lines.append(f"## {t.get('name','')}")
        if formula:
            lines.append(f"**{formula}**")
        for p in points[:3]:
            lines.append(f"- {p}")
        if g.get("traps"):
            lines.append(f"- ⚠ {g['traps'][0]}")
        lines.append("")
    return "\n".join(lines)
