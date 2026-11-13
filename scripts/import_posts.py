#!/usr/bin/env python3
"""把一个文件里的多篇博客文章（.docx / .txt / .md）拆成 content/posts/ 下的独立文章。

文件格式：每篇以“# 标题”开头，标题下面紧跟几行信息，再空一行写正文：

    # 慢写作的一点想法
    日期：2026-10-20
    分类：时评
    标签：写作，生活
    简介：一句话摘要（可省略）
    网址：slow-writing（可省略，不写则用日期编号）

    正文第一段……

    正文第二段……  需要配图的地方写 [图：贝尔湖.jpg]

用法：
    python3 scripts/import_posts.py 博客.docx
    python3 scripts/import_posts.py 博客.docx --images 图片文件夹

Word 稿请把每篇标题设成“标题 1”样式。日期是必填项。
带配图的文章会生成“文章文件夹”（index.md + 图片），第一张图自动作为题图。
不会覆盖已存在的同名文章；有问题的篇目会列出来，其余照常导入。
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_manuscript import normalize_paragraphs, read_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
KEYS = {"日期": "date", "分类": "category", "标签": "tags", "简介": "description", "网址": "slug"}
META = re.compile(r"^\s*(日期|分类|标签|简介|网址)\s*[:：]\s*(.*?)\s*$")
IMG = re.compile(r"\\?\[图[:：]\s*([^\]\\]+?)\s*\\?\]")
DATE = re.compile(r"^(\d{4})\s*[-./年]?\s*(\d{1,2})\s*[-./月]?\s*(\d{1,2})\s*日?$")
DATE8 = re.compile(r"^(\d{4})(\d{2})(\d{2})$")  # 20260101


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def split_posts(text):
    posts, cur = [], None
    for line in text.split("\n"):
        m = re.match(r"^#(?!#)\s*(.+?)\s*$", line)
        if m:
            cur = {"title": m.group(1), "lines": []}
            posts.append(cur)
        elif cur is not None:
            cur["lines"].append(line)
    return posts


KEYSPLIT = re.compile(r"(?=(?:日期|分类|标签|简介|网址)\s*[:：])")


def parse_post(p):
    # Word 转换后，信息行末尾可能带 “\”（Shift+Enter 软换行），或多个信息被并在同一行，这里一并兼容
    lines = [l.rstrip().rstrip("\\").rstrip() for l in p["lines"]]
    meta, i = {}, 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        if not META.match(lines[i]):
            break
        for piece in KEYSPLIT.split(lines[i].strip()):
            m = META.match(piece)
            if m:
                meta[KEYS[m.group(1)]] = m.group(2)
        i += 1
    body = "\n".join(lines[i:]).strip()
    return meta, re.sub(r"\n{3,}", "\n\n", body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--images", help="存放配图的文件夹")
    ap.add_argument("--out", default=str(ROOT / "content" / "posts"))
    a = ap.parse_args()

    out, img_dir = Path(a.out), Path(a.images) if a.images else None
    posts = split_posts(normalize_paragraphs(read_text(Path(a.file))))
    if not posts:
        sys.exit("没有找到“# 标题”开头的文章。Word 稿请用“标题 1”样式，TXT 请在标题前加 “# ”。")

    done, problems, per_day = [], [], {}
    for p in posts:
        meta, body = parse_post(p)
        title = p["title"]
        m = DATE8.match(meta.get("date", "").strip()) or DATE.match(meta.get("date", "").strip())
        if not m:
            problems.append(f"《{title}》：缺少或无法识别日期（请写成 日期：2026-10-20）")
            continue
        y, mo, d = (int(x) for x in m.groups())
        date = f"{y:04d}-{mo:02d}-{d:02d}"
        per_day[date] = per_day.get(date, 0) + 1
        slug = re.sub(r"[^A-Za-z0-9_-]+", "-", meta.get("slug", "")).strip("-").lower() \
            or f"{date}-{per_day[date]}"

        images = [x.strip() for x in IMG.findall(body)]
        missing = [x for x in images if not (img_dir and (img_dir / x).exists())]
        if images and missing:
            problems.append(f"《{title}》：找不到配图 {', '.join(missing)}（用 --images 指定图片文件夹）")
            continue
        body = IMG.sub(lambda mm: f"![]({mm.group(1).strip()})", body)

        tags = [t.strip() for t in re.split(r"[,，、;；\s]+", meta.get("tags", "")) if t.strip()]
        fm = ["---", f"title: {q(title)}", f"date: {date}"]
        if meta.get("description"):
            fm.append(f"description: {q(meta['description'])}")
        fm.append(f"category: {q(meta.get('category') or '随笔')}")
        if tags:
            fm.append("tags:")
            fm += [f"  - {q(t)}" for t in tags]
        if images:
            fm.append(f"cover: {q(images[0])}")
        fm += ["---", ""]
        text = "\n".join(fm) + "\n" + body + "\n"

        target = out / slug if images else out / f"{slug}.md"
        if target.exists():
            problems.append(f"《{title}》：{target.name} 已存在，已跳过")
            continue
        if images:
            target.mkdir(parents=True)
            (target / "index.md").write_text(text, encoding="utf-8")
            for x in set(images):
                shutil.copy2(img_dir / x, target / x)
        else:
            out.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        done.append(f"{date}  {title}  →  {slug}")

    print(f"成功导入 {len(done)} 篇：")
    for x in done:
        print("  " + x)
    if problems:
        print(f"\n有 {len(problems)} 篇需要处理：")
        for x in problems:
            print("  - " + x)


if __name__ == "__main__":
    main()
