#!/usr/bin/env python3
"""把 content/works/ 下的每一部文集生成 EPUB（以及可选的 PDF）。

用法：
    python3 scripts/build_ebooks.py            # 只生成 EPUB
    python3 scripts/build_ebooks.py --pdf      # 同时生成 PDF（需要 xelatex 和中文字体）
    python3 scripts/build_ebooks.py hankou-air-raid   # 只处理指定的一部

输出到 static/downloads/<文件夹名>.epub，书页会自动出现下载按钮。
依赖：pandoc、PyYAML（pip install pyyaml）。
"""
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKS = ROOT / "content" / "works"
OUT = ROOT / "static" / "downloads"
FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
SHORTCODE = re.compile(r"\{\{<\s*/?\s*poem\s*>\}\}\s*\n?")


def split_front_matter(text):
    m = FM.match(text)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


def find_cover(meta, book_dir):
    cover = meta.get("cover")
    if not cover:
        return None
    for base in (book_dir, ROOT / "assets", ROOT / "static"):
        p = base / cover
        if p.exists() and p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            return p
    return None


def build(book_dir, want_pdf, cfg):
    book_id = book_dir.name
    meta, preface = split_front_matter((book_dir / "_index.md").read_text(encoding="utf-8"))
    chapters = []
    for f in book_dir.glob("*.md"):
        if f.name == "_index.md":
            continue
        m, body = split_front_matter(f.read_text(encoding="utf-8"))
        chapters.append((m.get("weight") or 9999, f.name, m.get("title") or f.stem, body))
    chapters.sort(key=lambda c: (c[0], c[1]))
    if not chapters:
        print(f"跳过 {book_id}：没有章节")
        return

    author = cfg.get("params", {}).get("author", "")
    copyright_line = cfg.get("params", {}).get("copyright", "")
    parts = []
    if preface.strip():
        parts.append("# 前言\n\n" + SHORTCODE.sub("", preface).strip())
    for _, _, title, body in chapters:
        parts.append(f"# {title}\n\n" + SHORTCODE.sub("", body).strip())
    if copyright_line:
        parts.append("# 版权\n\n" + copyright_line)

    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "book.md"
        src.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        common = [
            "pandoc", str(src),
            "-f", "markdown+hard_line_breaks-smart",
            "--toc", "--toc-depth=1",
            "--metadata", f"title={meta.get('title', book_id)}",
            "--metadata", f"author={author}",
            "--metadata", "lang=zh-CN",
        ]
        if meta.get("description"):
            common += ["--metadata", f"subtitle={meta['description']}"]
        cmd = common + ["-o", str(OUT / f"{book_id}.epub"), "--split-level=1"]
        cover = find_cover(meta, book_dir)
        if cover:
            cmd += [f"--epub-cover-image={cover}"]
        subprocess.run(cmd, check=True)
        print(f"已生成 {OUT / (book_id + '.epub')}")

        if want_pdf:
            pdf_cmd = common + [
                "-o", str(OUT / f"{book_id}.pdf"),
                "--pdf-engine=xelatex",
                "-V", "CJKmainfont=Noto Serif CJK SC",
                "-V", "documentclass=book",
                "-V", "geometry:margin=2.5cm",
                "-V", "fontsize=12pt",
            ]
            subprocess.run(pdf_cmd, check=True)
            print(f"已生成 {OUT / (book_id + '.pdf')}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_pdf = "--pdf" in sys.argv
    if not shutil.which("pandoc"):
        sys.exit("没有找到 pandoc，请先安装：https://pandoc.org/installing.html")
    cfg = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))
    books = [d for d in sorted(WORKS.iterdir()) if d.is_dir() and (d / "_index.md").exists()]
    if args:
        books = [d for d in books if d.name in args]
    for d in books:
        build(d, want_pdf, cfg)


if __name__ == "__main__":
    main()
