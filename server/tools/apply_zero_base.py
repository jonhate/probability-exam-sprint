from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import store  # noqa: E402
from tools.zero_base_content import ZERO_BASE  # noqa: E402


def main() -> None:
    # Use the active course, not the legacy single-course mirror.
    project = store.read("project")
    a = project["analysis"]
    a["zero_base"] = json.loads(json.dumps(ZERO_BASE, ensure_ascii=False))
    a["plan"] = a["zero_base"]["plan"]
    a["hours_per_day"] = 6
    project["hours_per_day"] = 6
    project["zero_base_mode"] = True
    a["generation"]["zero_base"] = True
    warnings = a["generation"].setdefault("warnings", [])
    msg = "零基础三级模式已启用：先补 6 个数学工具，再按 60 → 80 → 100 逐级过关。"
    if msg not in warnings:
        warnings.insert(0, msg)
    store.write("project", project)
    print("zero base applied; plan minutes:", [sum(b["minutes"] for b in d["blocks"]) for d in a["plan"]])


if __name__ == "__main__":
    main()
