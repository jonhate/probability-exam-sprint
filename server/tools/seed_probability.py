from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))

from engine import store  # noqa: E402
from engine.parsers import parse_file  # noqa: E402
from engine.textutil import norm_space  # noqa: E402
from tools import seed_content as C  # noqa: E402
from tools.zero_base_content import ZERO_BASE  # noqa: E402

COURSE_DIR = ROOT.parent / "概率统计"

PPT_FILES = [
    ("d_ch1", "第一章 -.pptx"),
    ("d_ch2", "Ch2 一维随机变量及其分布 .pptx"),
    ("d_ch3", "第三章 多维随机变量.pptx"),
    ("d_ch4", "Ch4 随机变量的数字特征 .pptx"),
]
PDF_FILES = [
    ("d_exam2024", "2024-2025-1 期中概率统计答案 (1).pdf"),
    ("d_exam2022", "概率统计期中试卷学生版答案2022.10 (1).pdf"),
    ("d_exam2021", "概率统计期中试卷2021.10 (1).pdf"),
]

HOMEWORK_PAGES = [
    {
        "locator": "第1页",
        "title": "分布函数基础判断",
        "text": "作业截图整理：\n1. 判断：设离散型随机变量 X 的分布律为 P(X=1)=0.5，P(X=2)=0.5，则其分布函数在区间 [1,2) 上的取值为 0.5。答案：对。因为 1≤x<2 时 F(x)=P(X≤x)=P(X=1)=0.5。\n2. 填空：P(X=0)=0.3，P(X=1)=0.5，P(X=2)=0.2，则 F(1.5)=0.8。因为 F(1.5)=P(X≤1.5)=P(X=0)+P(X=1)。\n3. 判断：由离散型随机变量的分布律推导分布函数时，需要将所有小于等于 x 的可能取值对应的概率累加。答案：对。\n易错点：分布函数是“≤x 的累计概率”，不是某一点的概率；离散型在跳跃点按右连续取值。",
    },
    {
        "locator": "第2页",
        "title": "由分布函数求常数与密度",
        "text": "简答题：设连续型随机变量 X 的分布函数为 F(x)=A+B e^(−λx)（x>0），F(x)=0（x≤0），其中 λ>0。先确定 A、B，再求概率密度 f(x)。\n解答：由 F(+∞)=1 得 A=1；由 x=0 处右连续，F(0+)=A+B=0，得 B=−1。所以 F(x)=1−e^(−λx)（x>0），0（x≤0）。逐段求导：f(x)=λe^(−λx)（x>0），0（x≤0）。\n考点：分布函数的规范性 F(+∞)=1、右连续性、由 F 求 f。\n易错点：只由 F(+∞)=1 求出 A，忘记用 x=0 处右连续求 B；求导时漏掉 x=0 的分段说明。",
    },
    {
        "locator": "第3页",
        "title": "由密度求分布函数",
        "text": "简答题：设连续型随机变量 X 的概率密度为 f(x)=1/2 e^(−x/2)（x≥0），0（x<0）。求分布函数 F(x)。\n解答：x<0 时 F(x)=0；x≥0 时 F(x)=∫₀^x 1/2 e^(−t/2)dt=1−e^(−x/2)。所以 F(x)=0（x<0），1−e^(−x/2)（x≥0）。\n考点：指数分布 E(1/2) 的分布函数；分段积分。\n易错点：积分下限写成 −∞ 却忘记 x<0 段密度为 0；指数参数是 1/2，均值为 2。",
    },
    {
        "locator": "第4页",
        "title": "分布函数性质与正态线性变换",
        "text": "1. 判断：若函数 F(x) 单调不减、右连续，且 F(−∞)=0、F(+∞)=1，则对 F 逐段求导得到的函数一定是某连续型随机变量的概率密度。答案：错。还需要 F 绝对连续；奇异型/离散型的分布函数不能通过逐段求导得到密度。\n2. 判断：设 X~N(μ,σ²)，则线性函数 Y=aX+b（a≠0）也服从正态分布。答案：对。Y~N(aμ+b, a²σ²)。\n3. 单选：设 X 的分布函数为 F(x)，下列结论一定正确的是（B）。A. F 严格单调递增；B. F 右连续；C. P(a<X<b)=F(b)−F(a) 对任意 X 成立；D. F(−∞)=1。\n考点：分布函数四条性质；正态分布线性不变性。\n易错点：把“单调不减”说成“严格递增”；忘记方差前的 a²。",
    },
    {
        "locator": "第5页",
        "title": "由分段分布函数反推分布律",
        "text": "简答题：设离散型随机变量 X 的分布函数为 F(x)=0（x<−1），0.2（−1≤x<2），0.7（2≤x<4），1（x≥4）。求 X 的分布律。\n解答：跳跃点为 −1、2、4。P(X=−1)=F(−1)−F(−1−)=0.2−0=0.2；P(X=2)=0.7−0.2=0.5；P(X=4)=1−0.7=0.3。分布律：X=−1,2,4；P=0.2,0.5,0.3。\n考点：离散型分布律是分布函数的跳跃高度。\n易错点：只写概率不写 X 的取值；用 F(2)=0.7 当 P(X=2)，忘记减左极限。",
    },
    {
        "locator": "第6页",
        "title": "二维离散联合分布归一化",
        "text": "简答题：设二维离散型随机变量 (X,Y) 的联合分布律为 p(X=i,Y=j)=c(i+j)，i=0,1；j=0,1,2。（1）求 c；（2）求 P(X≤Y)。\n解答：所有格子概率和 = c[(0+0)+(0+1)+(0+2)+(1+0)+(1+1)+(1+2)]=9c=1，所以 c=1/9。P(X≤Y) 对应 (0,0),(0,1),(0,2),(1,1),(1,2)，概率和 = (1/9)(0+1+2+2+3)=8/9。\n考点：联合分布律归一化、事件区域枚举。\n易错点：漏掉 (0,0) 的概率为 0 也要计入；把 X≤Y 写成 X<Y。",
    },
    {
        "locator": "第7页",
        "title": "二维均匀分布与条件概率",
        "text": "简答题：设二维随机变量 (X,Y) 在区域 D={0<x<1, |y|<x} 上服从均匀分布。（1）写出联合概率密度并验证归一性；（2）求条件概率 P(X>1/2 | Y>0)。\n解答：D 是三角形，面积 ∫₀¹2x dx=1，所以 f(x,y)=1（D 内），其他 0；∫∫_D 1=1。P(Y>0)=1/2；P(X>1/2,Y>0)=∫_{1/2}¹∫₀^x 1 dy dx=∫_{1/2}¹ x dx=3/8；条件概率=(3/8)/(1/2)=3/4。\n考点：二维均匀分布、面积、条件概率。\n易错点：忘记条件概率要除以 P(Y>0)；积分区域没有按 |y|<x 分上下界。",
    },
    {
        "locator": "第8页",
        "title": "作业错因总结（老师批语提炼）",
        "text": "从 19 张作业截图看，主要丢分不是不会算，而是：\n1. 分布律只写概率，不写 X 的取值，格式不完整。\n2. 由 F 求 f 忘记分段，尤其 x=0、x=1 等分界点。\n3. 二维题不画区域，积分限靠猜。\n4. 条件概率忘记除以条件事件的概率。\n5. 变量函数只写公式，不写 Y 的取值范围。\n6. 独立性只检查一个格子，或把“不相关”当“独立”。\n复习时应把每道题的最后三行写成“支持/范围 + 公式 + 结论”，避免会做但扣格式分。",
    },
]


def make_homework_doc() -> dict:
    text_chars = sum(len(p["text"]) for p in HOMEWORK_PAGES)
    return {
        "doc_id": "d_hw",
        "name": C.DOC_NAMES["d_hw"],
        "kind": "homework",
        "ext": ".md",
        "size": text_chars,
        "sha256": "curated-homework",
        "pages": [
            {**p, "index": i + 1, "text": norm_space(p["text"])}
            for i, p in enumerate(HOMEWORK_PAGES)
        ],
        "page_count": len(HOMEWORK_PAGES),
        "chars": text_chars,
        "warnings": [
            "作业原图为手机截图，本文件是人工转录与错因整理；公式与答案以老师批阅为准。",
        ],
    }


def main() -> None:
    store.ensure_dirs()
    settings = store.read("settings")
    project_docs = []
    corpus_docs = []

    for doc_id, filename in PPT_FILES + PDF_FILES:
        path = COURSE_DIR / filename
        if not path.exists():
            raise SystemExit(f"missing source: {path}")
        kind = "exam" if doc_id.startswith("d_exam") else "slides"
        parsed = parse_file(path, filename, kind, doc_id)
        parsed["name"] = filename
        parsed["doc_id"] = doc_id
        parsed["kind"] = kind
        parsed["chars"] = sum(len(p.get("text", "")) for p in parsed.get("pages", []))
        parsed["page_count"] = len(parsed.get("pages", []))
        corpus_docs.append(parsed)
        project_docs.append(
            {
                "doc_id": doc_id,
                "name": filename,
                "kind": kind,
                "ext": path.suffix.lower(),
                "size": path.stat().st_size,
                "page_count": parsed["page_count"],
                "chars": parsed["chars"],
                "warnings": parsed.get("warnings", []),
                "uploaded_at": datetime.now(store.TZ).isoformat(timespec="seconds"),
                "source_path": str(path),
                "curated": True,
            }
        )
        print(f"parsed {filename}: {parsed['page_count']} pages, {parsed['chars']} chars")

    hw = make_homework_doc()
    corpus_docs.append(hw)
    project_docs.append(
        {
            "doc_id": "d_hw",
            "name": hw["name"],
            "kind": "homework",
            "ext": ".md",
            "size": hw["size"],
            "page_count": hw["page_count"],
            "chars": hw["chars"],
            "warnings": hw["warnings"],
            "uploaded_at": datetime.now(store.TZ).isoformat(timespec="seconds"),
            "source_path": str(COURSE_DIR),
            "curated": True,
        }
    )

    topics = json.loads(json.dumps(C.TOPICS, ensure_ascii=False))
    cards = C.build_cards()
    questions = C.build_questions()
    mock = C.build_mock()
    zero_base = json.loads(json.dumps(ZERO_BASE, ensure_ascii=False))
    plan = json.loads(json.dumps(zero_base["plan"], ensure_ascii=False))
    exam_profile = json.loads(json.dumps(C.EXAM_PROFILE, ensure_ascii=False))

    analysis = {
        "version": 2,
        "course": "概率统计（期中冲刺）",
        "exam_date": (datetime.now(store.TZ).date() + timedelta(days=3)).isoformat(),
        "days": 3,
        "hours_per_day": 6,
        "course_summary": C.COURSE_SUMMARY,
        "exam_strategy": C.EXAM_STRATEGY,
        "zero_base": zero_base,
        "exam_profile": exam_profile,
        "blueprint": {
            "duration_minutes": 100,
            "total_score": 100,
            "confidence": "高",
            "sections": exam_profile["question_types"],
            "style_notes": exam_profile["notes"],
        },
        "topics": topics,
        "cards": cards,
        "questions": questions,
        "mock": mock,
        "plan": plan,
        "coverage": [
            {"doc_id": d["doc_id"], "name": d["name"], "included": 1, "total": 1, "truncated": False}
            for d in project_docs
        ],
        "generation": {
            "mode": "curated",
            "provider": "本地精编",
            "model": "ExamSprint Probability Pack v1",
            "doc_count": len(project_docs),
            "total_chars": sum(d["chars"] for d in project_docs),
            "doc_stats": [
                {"name": d["name"], "kind": d["kind"], "pages": d["page_count"], "chars": d["chars"]}
                for d in project_docs
            ],
            "warnings": [
                "零基础模式已启用：先补 6 个数学工具，再学 4–5 个保分模板；目标调整为保 60、冲 75。",
                "本冲刺包依据 2021/2022/2024 期中真题、19 张作业截图和 Ch1–Ch4 课件目录人工精编；原始 PDF/PPT 中大量公式是图片，所以采用逐题转录 + 题型分析，而非直接 OCR。",
                "期中范围按 Ch1–Ch4 处理；如果老师给出的范围不同，以老师为准。",
                "作业小册子是 38 页扫描版，未逐页 OCR；冲刺包以 19 张作业截图的转录为主，建议遇到小册子原题时按老师答案复核。",
                "题目为仿真练习，不保证命中原题。",
            ],
            "usage": {},
            "generated_at": datetime.now(store.TZ).isoformat(timespec="seconds"),
        },
    }

    project = {
        "version": 1,
        "course": "概率统计（期中冲刺）",
        "exam_date": analysis["exam_date"],
        "days": 3,
        "hours_per_day": 6,
        "zero_base_mode": True,
        "mode": "sprint",
        "created_at": datetime.now(store.TZ).isoformat(timespec="seconds"),
        "updated_at": datetime.now(store.TZ).isoformat(timespec="seconds"),
        "status": "ready",
        "stale": False,
        "docs": project_docs,
        "analysis": analysis,
        "job": None,
    }
    store.write("project", project)
    store.write("corpus", {"docs": corpus_docs})
    store.write(
        "progress",
        {"cards": {}, "questions": {}, "mock": {"attempts": []}, "plan": {}, "sessions": []},
    )
    store.write("settings", settings)
    print(f"seeded project: {len(topics)} topics, {len(cards)} cards, {len(questions)} questions, mock {sum(len(s['questions']) for s in mock['sections'])} questions")


if __name__ == "__main__":
    main()
