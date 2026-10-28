from __future__ import annotations

import hashlib
import html
import os
import re
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Any

from .store import DATA, ROOT
from .textutil import clean_title, norm_space, safe_filename, sha256_file

SUPPORTED = {".pptx", ".pdf", ".docx", ".txt", ".md", ".markdown", ".csv", ".xlsx"}
LEGACY = {".ppt": "请用 PowerPoint 另存为 .pptx", ".doc": "请用 Word 另存为 .docx"}

CACHE = DATA / "parse_cache"
CACHE.mkdir(parents=True, exist_ok=True)


def _cache_path(file_hash: str, ext: str) -> Path:
    return CACHE / f"{file_hash}{ext}.json"


def parse_file(path: Path, name: str, kind: str, doc_id: str) -> dict[str, Any]:
    ext = path.suffix.lower()
    if ext in LEGACY:
        raise ValueError(f"暂不支持旧版 {ext}：{LEGACY[ext]}")
    if ext not in SUPPORTED:
        raise ValueError(f"不支持 {ext}，请上传 PPTX / PDF / DOCX / XLSX / TXT / MD")

    file_hash = sha256_file(path)
    cache_file = _cache_path(file_hash, ext)
    if cache_file.exists():
        import json

        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            cached["doc_id"] = doc_id
            cached["name"] = name
            cached["kind"] = kind
            cached["size"] = path.stat().st_size
            cached["sha256"] = file_hash
            return cached
        except Exception:
            pass

    warnings: list[str] = []
    if ext == ".pptx":
        pages = _parse_pptx(path, warnings)
    elif ext == ".pdf":
        pages = _parse_pdf(path, warnings)
    elif ext == ".docx":
        pages = _parse_docx(path, warnings)
    elif ext in {".txt", ".md", ".markdown"}:
        pages = _parse_text(path, warnings)
    elif ext == ".csv":
        pages = _parse_text(path, warnings)
    elif ext == ".xlsx":
        pages = _parse_xlsx(path, warnings)
    else:
        pages = []

    pages = [p for p in pages if norm_space(p.get("text", "")) or p.get("title")]
    for i, p in enumerate(pages, 1):
        p["index"] = i
        p["text"] = norm_space(p.get("text", ""))
        p["title"] = clean_title(p.get("title", ""), f"第 {i} 部分")
        if not p["text"] and p["title"]:
            p["text"] = p["title"]

    total_chars = sum(len(p["text"]) for p in pages)
    if total_chars < 80:
        warnings.append("可提取文字很少，可能是扫描版/图片型资料；本工具不做 OCR，建议先导出可复制文字的 PDF。")
    elif any(len(p["text"]) < 30 for p in pages):
        n = sum(1 for p in pages if len(p["text"]) < 30)
        warnings.append(f"有 {n} 页几乎无文字（可能是图片或公式），这些页不会进入 AI 分析。")

    result = {
        "doc_id": doc_id,
        "name": name,
        "kind": kind,
        "ext": ext,
        "size": path.stat().st_size,
        "sha256": file_hash,
        "pages": pages,
        "page_count": len(pages),
        "chars": total_chars,
        "warnings": warnings,
    }
    import json

    cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


def _parse_pptx(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    prs = Presentation(str(path))
    pages: list[dict[str, Any]] = []

    def shape_text(shape: Any) -> list[str]:
        out: list[str] = []
        try:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                for child in shape.shapes:
                    out.extend(shape_text(child))
            elif getattr(shape, "has_table", False) and shape.has_table:
                for row in shape.table.rows:
                    cells = [norm_space(c.text).replace("\n", " ") for c in row.cells]
                    if any(cells):
                        out.append(" | ".join(cells))
            elif getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    t = norm_space(para.text)
                    if t:
                        level = int(getattr(para, "level", 0) or 0)
                        out.append(("  " * min(level, 3)) + t)
        except Exception:
            pass
        return out

    for i, slide in enumerate(prs.slides, 1):
        title = ""
        try:
            if slide.shapes.title is not None:
                title = clean_title(slide.shapes.title.text)
        except Exception:
            title = ""
        body: list[str] = []
        for shape in slide.shapes:
            body.extend(shape_text(shape))
        # The title is already represented; remove an exact duplicate.
        if title and body and body[0].strip() == title:
            body = body[1:]
        notes = ""
        try:
            if slide.has_notes_slide:
                notes = norm_space(slide.notes_slide.notes_text_frame.text)
        except Exception:
            notes = ""
        text = "\n".join(body)
        if notes and notes not in text:
            text += "\n\n[备注] " + notes
        pages.append(
            {
                "locator": f"第{i}张幻灯片",
                "title": title or f"第 {i} 张",
                "text": text,
                "notes": notes,
            }
        )
    if not pages:
        warnings.append("PPTX 中没有找到幻灯片。")
    return pages


def _parse_docx(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    from docx import Document

    doc = Document(str(path))
    sections: list[dict[str, Any]] = []
    current_title = "正文"
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        text = "\n".join(buf).strip()
        if text:
            sections.append({"title": current_title, "text": text})
        buf = []

    def para_text(p: Any) -> str:
        t = p.text or ""
        # python-docx omits OMML equations; recover their text nodes.
        try:
            xml = p._p.xml
            maths = re.findall(r"<m:t[^>]*>(.*?)</m:t>", xml, flags=re.S)
            if maths:
                extra = "".join(html.unescape(m) for m in maths)
                if extra and extra not in t:
                    t = (t + " " + extra).strip()
        except Exception:
            pass
        return norm_space(t)

    for p in doc.paragraphs:
        text = para_text(p)
        if not text:
            continue
        style = (getattr(p.style, "name", "") or "").lower()
        if style.startswith("heading") or style.startswith("标题"):
            flush()
            current_title = clean_title(text, "正文")
        else:
            buf.append(("  " if p.paragraph_format.left_indent else "") + text)
        if sum(len(x) for x in buf) > 5000:
            flush()
    for table in doc.tables:
        rows = []
        for row in table.rows:
            cells = [norm_space(c.text).replace("\n", " ") for c in row.cells]
            if any(cells):
                rows.append(" | ".join(cells))
        if rows:
            buf.append("\n[表格]\n" + "\n".join(rows))
    flush()

    # Split very long sections so retrieval and citations stay useful.
    pages: list[dict[str, Any]] = []
    for sec in sections:
        text = sec["text"]
        parts = [text[i : i + 5000] for i in range(0, len(text), 5000)] or [""]
        for j, part in enumerate(parts):
            title = sec["title"] if len(parts) == 1 else f"{sec['title']}（{j + 1}）"
            pages.append({"locator": f"第{len(pages) + 1}节", "title": title, "text": part})
    return pages


def _parse_text(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    text = ""
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if not text:
        text = raw.decode("utf-8", "replace")
        warnings.append("文本编码无法确定，已用替换字符读取。")
    text = norm_space(text)
    pages = []
    for i in range(0, len(text), 6000):
        part = text[i : i + 6000]
        first = next((ln.strip("# ").strip() for ln in part.splitlines() if ln.strip()), "")
        pages.append(
            {
                "locator": f"第{i // 6000 + 1}段",
                "title": clean_title(first, f"第{i // 6000 + 1}段"),
                "text": part,
            }
        )
    return pages


def _parse_xlsx(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    try:
        from openpyxl import load_workbook
    except Exception:
        warnings.append("缺少 openpyxl，无法读取 XLSX。")
        return []
    wb = load_workbook(str(path), read_only=True, data_only=True)
    pages = []
    for ws in wb.worksheets:
        rows: list[str] = []
        for row in ws.iter_rows(values_only=True):
            vals = [str(v).strip() for v in row if v is not None and str(v).strip()]
            if vals:
                rows.append(" | ".join(vals))
            if sum(len(x) for x in rows) > 6000:
                pages.append(
                    {
                        "locator": f"{ws.title} 第{len(pages) + 1}段",
                        "title": ws.title,
                        "text": "\n".join(rows),
                    }
                )
                rows = []
        if rows:
            pages.append({"locator": f"{ws.title} 第{len(pages) + 1}段", "title": ws.title, "text": "\n".join(rows)})
    return pages


# ---------------------------------------------------------------------------
# PDF: pypdf if present -> built-in extractor -> Microsoft Word fallback
# ---------------------------------------------------------------------------


def _parse_pdf(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    pages = _parse_pdf_pypdf(path, warnings)
    if _good_pdf_text(pages):
        return pages

    builtin = _parse_pdf_builtin(path, warnings)
    if _good_pdf_text(builtin) and sum(len(p["text"]) for p in builtin) > sum(len(p["text"]) for p in pages):
        pages = builtin
    if _good_pdf_text(pages):
        return pages

    # Word COM needs an interactive desktop and can block for minutes under a
    # background service. Only use it when explicitly requested by the user.
    if os.environ.get("EXAMSPRINT_WORD_PDF") == "1":
        word_pages = _parse_pdf_with_word(path, warnings)
        if word_pages and sum(len(p["text"]) for p in word_pages) > sum(len(p["text"]) for p in pages):
            return word_pages
    return pages


def _good_pdf_text(pages: list[dict[str, Any]]) -> bool:
    total = sum(len(p.get("text", "")) for p in pages)
    bad = sum(p.get("text", "").count("\ufffd") for p in pages)
    return total >= 80 and bad <= max(5, total * 0.02)


def _parse_pdf_pypdf(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return []
    try:
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            pages.append({"locator": f"第{i}页", "title": f"第 {i} 页", "text": norm_space(text)})
        return pages
    except Exception as exc:
        warnings.append(f"pypdf 解析失败：{exc}")
        return []


def _decode_pdf_literal(raw: bytes) -> str:
    out = bytearray()
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == 0x5C and i + 1 < len(raw):  # backslash
            n = raw[i + 1]
            simple = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}
            if n in simple:
                out.append(simple[n])
                i += 2
            elif 0x30 <= n <= 0x37:
                j = i + 1
                oct_digits = b""
                while j < len(raw) and len(oct_digits) < 3 and 0x30 <= raw[j] <= 0x37:
                    oct_digits += bytes([raw[j]])
                    j += 1
                out.append(int(oct_digits, 8) & 0xFF)
                i = j
            elif n in (10, 13):
                i += 2
            else:
                out.append(n)
                i += 2
        else:
            out.append(c)
            i += 1
    b = bytes(out)
    if b.startswith(b"\xfe\xff"):
        return b[2:].decode("utf-16-be", "replace")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("latin-1", "replace")


def _parse_cmap(data: bytes) -> tuple[dict[str, str], set[int]]:
    text = data.decode("latin-1", "ignore")
    mapping: dict[str, str] = {}
    widths: set[int] = set()

    def add(src: str, dst: str) -> None:
        src = re.sub(r"[^0-9A-Fa-f]", "", src)
        if not src:
            return
        widths.add(len(src))
        try:
            dst_bytes = bytes.fromhex(re.sub(r"[^0-9A-Fa-f]", "", dst))
            if len(dst_bytes) % 2 == 0:
                decoded = dst_bytes.decode("utf-16-be", "ignore")
            else:
                decoded = dst_bytes.decode("latin-1", "ignore")
        except Exception:
            decoded = ""
        if decoded:
            mapping[src.upper()] = decoded

    for block in re.findall(r"beginbfchar(.*?)endbfchar", text, flags=re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>", block):
            add(src, dst)
    for block in re.findall(r"beginbfrange(.*?)endbfrange", text, flags=re.S):
        for src1, src2, dst in re.findall(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block
        ):
            try:
                a, b = int(src1, 16), int(src2, 16)
                start = int(dst, 16)
                width = len(src1)
                for off, code in enumerate(range(a, min(b, a + 512) + 1)):
                    mapping[f"{code:0{width}X}"] = chr(start + off)
            except Exception:
                pass
    return mapping, widths


def _parse_pdf_builtin(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    """Small, dependency-free extractor for ordinary text PDFs.

    It understands Flate-compressed content streams and ToUnicode CMaps. It is a
    fallback only; complex layouts may require Microsoft Word conversion.
    """
    try:
        data = path.read_bytes()
        cmap: dict[str, str] = {}
        widths: set[int] = set()
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, flags=re.S):
            raw = m.group(1)
            try:
                dec = zlib.decompress(raw)
            except Exception:
                continue
            if b"beginbfchar" in dec or b"beginbfrange" in dec:
                mp, ws = _parse_cmap(dec)
                cmap.update(mp)
                widths |= ws
        streams: list[bytes] = []
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, flags=re.S):
            raw = m.group(1)
            try:
                dec = zlib.decompress(raw)
            except Exception:
                dec = raw
            if b"BT" in dec and (b"Tj" in dec or b"TJ" in dec):
                streams.append(dec)

        def decode_hex(h: str) -> str:
            h = re.sub(r"[^0-9A-Fa-f]", "", h)
            if not h:
                return ""
            # Prefer the dominant 2-byte CID width when a ToUnicode map exists.
            if cmap and (len(h) % 4 == 0):
                out = "".join(cmap.get(h[i : i + 4].upper(), "") for i in range(0, len(h), 4))
                if out:
                    return out
            try:
                b = bytes.fromhex(h if len(h) % 2 == 0 else h + "0")
                if b.startswith(b"\xfe\xff"):
                    return b[2:].decode("utf-16-be", "replace")
                return b.decode("latin-1", "replace")
            except Exception:
                return ""

        def decode_literal(raw: bytes) -> str:
            s = _decode_pdf_literal(raw)
            if cmap and s and all(ord(ch) < 256 for ch in s):
                hx = "".join(f"{ord(ch):02X}" for ch in s)
                if len(hx) % 4 == 0:
                    mapped = "".join(cmap.get(hx[i : i + 4], "") for i in range(0, len(hx), 4))
                    if mapped:
                        return mapped
            return s

        page_texts: list[str] = []
        for stream in streams:
            text = stream.decode("latin-1", "ignore")
            pieces: list[str] = []
            # literal strings followed by Tj / TJ arrays
            token_re = re.compile(r"\((?:\\.|[^\\)])*\)\s*Tj|\[(.*?)\]\s*TJ|<([0-9A-Fa-f\s]+)>\s*Tj", flags=re.S)
            for m in token_re.finditer(text):
                token = m.group(0)
                if token.startswith("["):
                    arr = m.group(1) or ""
                    for lm in re.finditer(r"\((?:\\.|[^\\)])*\)|<([0-9A-Fa-f\s]+)>", arr):
                        lit = lm.group(0)
                        if lit.startswith("("):
                            pieces.append(decode_literal(lit[1:-1].encode("latin-1", "ignore")))
                        else:
                            pieces.append(decode_hex(lm.group(1) or ""))
                elif token.startswith("<"):
                    pieces.append(decode_hex(m.group(2) or ""))
                else:
                    lit = re.match(r"\((.*)\)\s*Tj", token, flags=re.S)
                    if lit:
                        pieces.append(decode_literal(lit.group(1).encode("latin-1", "ignore")))
                if pieces and pieces[-1] and not pieces[-1].endswith((" ", "\n")):
                    pieces.append(" ")
            joined = norm_space("".join(pieces))
            if joined:
                page_texts.append(joined)

        if not page_texts:
            return []
        # Without page boundaries, estimate page breaks by form-feed or equal chunks.
        all_text = "\n\f\n".join(page_texts)
        parts = [p.strip() for p in all_text.split("\f") if p.strip()]
        if len(parts) <= 1:
            # Keep one citation unit per extracted content stream.
            parts = page_texts
        pages = []
        for i, part in enumerate(parts, 1):
            pages.append({"locator": f"第{i}部分", "title": f"第 {i} 部分", "text": norm_space(part)})
        if pages:
            warnings.append("PDF 使用内置轻量解析，页边界可能不精确；请以引用的原文片段为准。")
        return pages
    except Exception as exc:
        warnings.append(f"内置 PDF 解析失败：{exc}")
        return []


def _parse_pdf_with_word(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    """Convert a PDF through Microsoft Word when available (Windows only)."""
    if os.name != "nt":
        return []
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        return []
    script = ROOT / "tools" / "pdf_to_text.ps1"
    if not script.exists():
        return []
    out = Path(tempfile.gettempdir()) / f"examsprint_{hashlib.sha1(str(path).encode()).hexdigest()[:10]}.txt"
    try:
        proc = subprocess.run(
            [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-InputPath", str(path), "-OutputPath", str(out)],
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if proc.returncode != 0 or not out.exists():
            warnings.append("Microsoft Word PDF 转换未成功，将只使用可提取的文字。")
            return []
        text = out.read_text(encoding="utf-8-sig", errors="replace")
        parts = [p.strip() for p in text.split("\f") if p.strip()]
        if len(parts) <= 1:
            parts = [text[i : i + 4500] for i in range(0, len(text), 4500)]
        pages = [
            {"locator": f"第{i}页", "title": f"第 {i} 页", "text": norm_space(p)}
            for i, p in enumerate(parts, 1)
        ]
        if pages:
            warnings.append("PDF 通过 Microsoft Word 转换提取，页码为近似值。")
        return pages
    except Exception as exc:
        warnings.append(f"Word PDF 转换失败：{exc}")
        return []
    finally:
        try:
            if out.exists():
                out.unlink()
        except Exception:
            pass
