from __future__ import annotations

import json
import argparse
import sys
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import store

STATIC = ROOT / "static"
WEB = ROOT / "web"
ROOT_OUT = ROOT.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="从主课程库生成静态学习包（包含课程文字，请确认公开范围）")
    parser.add_argument("--course", help="课程 id；默认当前课程")
    args = parser.parse_args()
    course_id = args.course or store.active_course_id()
    if not any(c["id"] == course_id for c in store.list_courses()):
        parser.error("课程不存在")
    with store.course_scope(course_id):
        project = store.read("project")
        corpus = store.read("corpus")
    if not project.get("analysis"):
        parser.error("该课程尚未生成冲刺包")
    WEB.mkdir(exist_ok=True)
    for name in ("app.js", "styles.css"):
        shutil.copy2(STATIC / name, WEB / name)

    settings = json.loads((ROOT / "data" / "settings.json").read_text(encoding="utf-8"))
    project["docs"] = [{k: v for k, v in d.items() if k != "source_path"} for d in project.get("docs", [])]
    data = {
        "project": project,
        "corpus": corpus,
        "progress": {"cards": {}, "questions": {}, "mock": {"attempts": []}, "plan": {}, "sessions": []},
        "settings": {
            "base_url": settings.get("base_url", "https://api.deepseek.com/v1"),
            "model": settings.get("model", "deepseek-chat"),
            "has_key": False,
            "key_hint": "",
            "temperature": settings.get("temperature", 0.25),
        },
        "static": True,
    }
    data_js = "window.__EXAMSPRINT_DATA__ = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
    (WEB / "data.js").write_text(data_js, encoding="utf-8")

    html = (STATIC / "index.html").read_text(encoding="utf-8")
    html = html.replace("/static/styles.css", "styles.css")
    html = html.replace(
        '<script src="/static/app.js"></script>',
        '<script src="data.js"></script>\n  <script src="static_bridge.js"></script>\n  <script src="app.js"></script>',
    )
    pwa_head = """  <meta name="theme-color" content="#1f2a24">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta name="apple-mobile-web-app-title" content="ExamSprint">
  <link rel="manifest" href="manifest.webmanifest">
  <link rel="apple-touch-icon" href="icon-180.png">
"""
    html = html.replace('content="width=device-width, initial-scale=1"', 'content="width=device-width, initial-scale=1, viewport-fit=cover"')
    html = html.replace("</head>", pwa_head + "</head>")
    (WEB / "index.html").write_text(html, encoding="utf-8")

    css = (WEB / "styles.css").read_text(encoding="utf-8")
    data_text = (WEB / "data.js").read_text(encoding="utf-8")
    bridge = (WEB / "static_bridge.js").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")
    single = html.replace('<link rel="stylesheet" href="styles.css">', "<style>\n" + css + "\n</style>")
    old = '<script src="data.js"></script>\n  <script src="static_bridge.js"></script>\n  <script src="app.js"></script>'
    new = "<script>\n" + data_text + "\n</script>\n<script>\n" + bridge + "\n</script>\n<script>\n" + app + "\n</script>"
    if old not in single:
        raise SystemExit("static script block not found")
    single = single.replace(old, new)
    single_path = ROOT_OUT / "概率统计冲刺_单文件.html"
    single_path.write_text(single, encoding="utf-8")

    zip_path = ROOT_OUT / "概率统计冲刺_网页版.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in WEB.rglob("*"):
            if not p.is_file():
                continue
            if ".git" in p.parts or "server" in p.parts or p.name.startswith(".upload") or p.name.startswith(".pages") or p.name.startswith(".readme_update"):
                continue
            zf.write(p, p.relative_to(WEB))
    print(f"static built: web/data.js, {single_path.name}, {zip_path.name}")


if __name__ == "__main__":
    main()
