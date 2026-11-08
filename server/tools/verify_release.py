from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
ANDROID = ROOT.parent / "mobile" / "android" / "app" / "src" / "main" / "assets"
NAMES = ("index.html", "app.js", "data.js", "static_bridge.js", "styles.css", "manifest.webmanifest")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest_path = WEB / "release-manifest.json"
    if not manifest_path.exists():
        print("FAIL: missing web/release-manifest.json; run tools/build_static.py first")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = []
    if int(manifest.get("questions", 0)) != 57:
        failures.append(f"manifest question count is {manifest.get('questions')}, expected 57")
    for name in NAMES:
        source = WEB / name
        if not source.exists():
            failures.append(f"missing web/{name}")
            continue
        if name in manifest.get("assets", {}) and digest(source) != manifest["assets"][name]:
            failures.append(f"manifest hash mismatch: web/{name}")
        target = ANDROID / name
        if not target.exists():
            failures.append(f"missing Android asset: {name}")
        elif digest(source) != digest(target):
            failures.append(f"Android asset drift: {name}")
    print(json.dumps({"ok": not failures, "questions": manifest.get("questions"), "failures": failures}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
