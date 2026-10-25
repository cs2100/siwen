#!/usr/bin/env python3
"""把一部完稿的稿子（.docx / .txt / .md）切成章节，放进 content/works/<文件夹名>/。

用法：
    python3 scripts/import_manuscript.py 稿子.docx --slug shanhe-xinzha \
        --title "山河信札" --genre 长篇小说 --desc "一句话简介"

    --slug   文件夹名，建议用拼音或英文（会成为网址的一部分）
    --genre  类型标签：长篇小说 / 中短篇集 / 随笔集 / 书评集 等
    --split  自定义章节标题的正则（默认识别“第X章/回/节”“序章”“楔子”“后记”等，
             以及 Markdown 的一、二级标题）

不会覆盖已存在的文件夹；如需重来，请先自己删除。导入后请抽查几章。
依赖：.docx 需要 pandoc。
"""
import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPLIT = (
    r"^\s*(?:#{1,2}\s+.+"
    r"|第[零〇一二三四五六七八九十百千两\d]+[章回节篇卷部集].*"
    r"|(?:序章|序言|序|楔子|引子|前言|后记|尾声|终章|番外.*|附录.*))\s*$"
)


def read_text(path):
    if path.suffix.lower() in (".docx", ".doc", ".odt", ".rtf"):
        out = subprocess.run(
            ["pandoc", str(path), "-t", "markdown", "--wrap=none"],
            check=True, capture_output=True,
        )
        return out.stdout.decode("utf-8")
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "gb18030", "big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    sys.exit("无法识别文件编码，请另存为 UTF-8 文本后再试。")


def normalize_paragraphs(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    nonblank = [l for l in lines if l.strip()]
    blank = len(lines) - len(nonblank)
    # 纯文本稿常常“一行一段”且段间不空行，这时给每一行补上空行，段落才不会被并成一大段
    if nonblank and blank <= len(nonblank) * 0.1:
        return "\n\n".join(l.strip() for l in nonblank)
    return "\n".join(lines)


def split_chapters(text, pattern):
    rx = re.compile(pattern)
    chapters, title, buf = [], None, []
    preface = []
    for line in text.split("\n"):
        if rx.match(line) and len(line.strip()) <= 40:
            if title is None and buf:
                preface = buf
            elif title is not None:
                chapters.append((title, buf))
            title = re.sub(r"^#{1,2}\s+", "", line.strip())
            buf = []
        else:
            buf.append(line)
    if title is not None:
        chapters.append((title, buf))
    elif buf:
        chapters.append(("正文", buf))
    return preface, chapters


def clean(lines):
    body = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", body)


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--genre", default="长篇小说")
    ap.add_argument("--desc", default="")
    ap.add_argument("--split", default=DEFAULT_SPLIT)
    ap.add_argument("--out", default=str(ROOT / "content" / "works"))
    a = ap.parse_args()

    out = Path(a.out) / a.slug
    if out.exists():
        sys.exit(f"{out} 已存在，为避免覆盖已停止。")
    text = normalize_paragraphs(read_text(Path(a.file)))
    preface, chapters = split_chapters(text, a.split)
    if not chapters:
        sys.exit("没有切出任何章节，请检查 --split 规则。")

    out.mkdir(parents=True)
    width = max(2, len(str(len(chapters))))
    for i, (title, lines) in enumerate(chapters, 1):
        name = f"{i:0{width}d}.md"
        (out / name).write_text(
            f"---\ntitle: {q(title)}\nweight: {i}\n---\n\n{clean(lines)}\n", encoding="utf-8"
        )
    (out / "_index.md").write_text(
        "---\n"
        f"title: {q(a.title)}\n"
        f"description: {q(a.desc)}\n"
        f"genre: {q(a.genre)}\n"
        f"completed: {date.today().isoformat()}\n"
        'status: "已完稿"\n'
        "# cover: \"cover.jpg\"      # 把封面图放进同一文件夹后取消注释\n"
        "# featured: true            # 取消注释后会出现在首页“代表作”\n"
        "weight: 10\n"
        "---\n\n"
        f"{clean(preface)}\n",
        encoding="utf-8",
    )
    print(f"完成：{out}（{len(chapters)} 章）。请抽查章节标题和段落，再运行 hugo server 预览。")


if __name__ == "__main__":
    main()
