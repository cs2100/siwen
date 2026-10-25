# 思文败类 · 个人网站

Hugo 静态站点：文章、作品（文集）、摄影、音乐、归档、站内搜索、RSS、深色模式。
没有数据库，没有服务器，托管在 GitHub Pages，成本只有域名。

> 里面所有文章、章节、照片、专辑都是**示例**，配图是程序生成的原创占位图，上线前请替换（清单见文末）。

---

## 一、在自己电脑上预览（可选，但建议）

1. 安装 [Hugo extended 版](https://gohugo.io/installation/)（版本 0.139 以上）。
2. 在本文件夹里运行：

```bash
hugo server
```

3. 浏览器打开 http://localhost:1313 。改动文件后页面会自动刷新。
   （站内搜索只在发布后可用，本地想试要先 `hugo --minify && npx pagefind --site public`。）

不想装任何东西也行：直接把整个文件夹传到 GitHub（见第三部分），由 GitHub 替你构建。

## 二、先改这几处配置（`hugo.toml`）

| 配置项 | 说明 |
|---|---|
| `baseURL` | 你的网址。暂时没有域名就写 `https://用户名.github.io/` |
| `params.author` / `authorTitle` / `authorQuote` | 署名、身份、签名语。示例里的那句签名请换成你自己的话 |
| `params.copyright` | 版权声明。全文公开的原创作品建议写清楚，也可以改成 CC 协议 |
| `[[params.social]]` | 邮箱、RSS、Instagram、Bandcamp 等。**邮箱现在是占位的 `you@example.com`，请换成你愿意公开的地址** |
| `params.home` | 首页大图、标题、四张分类卡 |
| `params.audioBase` | 音频放在对象存储时填地址前缀，见“音乐” |

首页“今日阅读”在 `data/reading.yaml`，不想维护就把首页对应模块删掉（`layouts/index.html` 第 70 行的 `side-reading.html` 那一行）。

## 三、发布到 GitHub Pages

1. 注册 GitHub，新建一个仓库（名字随意，公开或私有均可；私有仓库发布 Pages 需要付费版）。
2. 把本文件夹里的**全部文件**（包括隐藏的 `.github` 文件夹）上传到仓库的 `main` 分支。
3. 仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。
4. 以后每次提交，GitHub 会自动：生成 EPUB → 构建站点 → 生成搜索索引 → 发布。进度在仓库的 **Actions** 页签。
5. 几分钟后，网址会出现在 Settings → Pages。

**绑定自己的域名**：在注册商那里把域名指向 GitHub Pages（按 Settings → Pages → Custom domain 的提示填 DNS 记录），
然后把 `hugo.toml` 里的 `baseURL` 改成新域名。域名务必开自动续费。

> 把仓库授权给 AI 代理（如 Grok Bot）代为上传时，只授权这一个仓库，上传完成后在 GitHub 的应用授权里撤销。

## 四、放进你自己的作品

### 文集（作品）

每一部文集是 `content/works/` 下的一个文件夹，文件夹名建议用拼音或英文（会成为网址）：

```
content/works/shanhe-xinzha/
  _index.md        书名、简介、类型、封面、前言
  01.md            第一章
  02.md            第二章
  cover.jpg        封面（可选）
```

**最省事的做法**：用导入脚本把整部稿子（.docx / .txt / .md）自动切章：

```bash
python3 scripts/import_manuscript.py 稿子.docx --slug shanhe-xinzha \
    --title "山河信札" --genre 长篇小说 --desc "一句话简介"
```

脚本会识别“第X章 / 序章 / 楔子 / 后记”等标题；识别不对时用 `--split` 自定义规则。导入后请抽查几章。
`.docx` 需要安装 [pandoc](https://pandoc.org/installing.html)。

`_index.md` 常用字段：`genre`（类型标签）、`completed`（完稿日期）、`status`、`cover`、
`featured: true`（出现在首页“代表作”）、`weight`（书架排序，数字小的在前）。

**诗歌**要保留换行和缩进时，用短代码：

```
{{< poem >}}
夜里的船没有名字
灯在水上走
{{< /poem >}}
```

### 文章（博客）

在 `content/posts/` 新建 `.md` 文件，开头写信息头（参考 `content/posts/daily.md`）。
有配图的文章用文件夹形式（`posts/某篇/index.md` 加图片），参考 `content/posts/bel-lake/`。
`category` 决定首页标签（随笔 / 阅读 / 生活 / 时评……），`draft: true` 表示草稿，不会发布。

### 摄影

每组照片一个文件夹：`content/photography/某相册/index.md` 加上 `cover.jpg` 和其他照片。
网站会自动生成缩略图并压缩。**原图不要放进仓库**（体积大），放压缩后的 2000 像素宽左右的版本即可，原图另行备份。

### 音乐

每张专辑一个文件夹：`content/music/某专辑/index.md` 加 `cover.jpg`，曲目写在信息头的 `tracks:` 里（见示例）。三种放音频的方式：

1. **放在专辑文件夹里**：`file: "01.mp3"`。适合音频不多的情况。GitHub 单个文件不能超过 100 MB，整个仓库建议不超过 1 GB。
2. **放在对象存储**（如 Cloudflare R2）：在 `hugo.toml` 设置 `audioBase = "https://你的存储地址"`，曲目的 `file` 写文件名即可。
3. **嵌入第三方播放器**：在信息头加 `embed: "播放器的嵌入地址"`（Bandcamp、SoundCloud 等）。

### 电子书（EPUB / PDF）

- 发布时 EPUB 会**自动生成**，书页上出现“下载 EPUB”按钮。
- 本地手动生成：`pip install pyyaml` 后运行 `python3 scripts/build_ebooks.py`。
- PDF 需要本机装有 xelatex 和中文字体，运行 `python3 scripts/build_ebooks.py --pdf`，生成的 PDF 放在 `static/downloads/` 后一起提交即可（自动流程只生成 EPUB）。

## 五、上线前清单

删除或替换示例内容：

- [ ] `content/works/` 下四个示例文集
- [ ] `content/posts/` 下的示例文章
- [ ] `content/photography/`、`content/music/` 下的示例相册与专辑（含示例 mp3）
- [ ] `assets/images/` 与 `assets/images/covers/` 下的占位图（首页大图 `hero.jpg`、头像 `avatar.jpg` 等换成你自己的）
- [ ] `data/reading.yaml`
- [ ] `hugo.toml` 里的邮箱、社交链接、签名语、版权声明
- [ ] 确认仓库里没有未完成的草稿和不想公开的文件（Pages 站点内容是公开的）

## 六、可选：繁体版

港台读者可以另做一份繁体站：用 [OpenCC](https://github.com/BYVoid/OpenCC) 把 `content/` 转成繁体，放入第二语言目录。
转换后人名、地名和专有词需要人工校对。建议先上简体，之后再加。

## 目录说明

```
hugo.toml            站点配置
content/             所有内容（文章、作品、摄影、音乐）
layouts/             页面模板
assets/              样式、脚本、图片（构建时处理）
static/              原样发布的文件（favicon、下载文件）
data/reading.yaml    首页“今日阅读”
scripts/             稿件导入、电子书生成
.github/workflows/   自动发布配置
```
