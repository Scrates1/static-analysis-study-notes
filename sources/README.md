# 原始资料与可复现抓取

## 目录

- `wechat-series/README.md`、`wechat-series/index.html`：8 篇微信原文的 GitHub 索引与本地浏览入口；
- `wechat-series/index.json`：官方微信合集元数据、8 篇文章的标题/URL/时间、抽取状态与 HTML 哈希；
- `wechat-series/articles/*/article.html`：保留 `#js_content` 标签层次和内联样式、使用本地图片的安全阅读版；
- `wechat-series/articles/*/original.raw.html`：抓取时收到的完整原始页面 HTML；
- `wechat-series/articles/*/extracted.md`：供检索和审计的规范化正文；
- `wechat-series/articles/*/images/`：正文按出现顺序下载的图片，共 109 张；
- `video-lessons-hd.json`：三节 Bilibili 实验视频的标题、BV/CID、时长、播放地址与本地文件信息；
- `video-lessons.json`：初次低清抓取的元数据，保留作历史记录；
- `yasa-docs/`：21 篇 YASA 官方公开语雀文档的规范化 Markdown 快照、附件/图片链接 sidecar 与来源索引；该目录作为可追踪证据保留在 Git 中。

可重新生成的大体积工作材料位于 `.work/`：

- `.work/video-lessons-hd/`：三段 720p 视频；
- `.work/transcripts/`：无官方字幕情况下生成的带时间戳 ASR 转写；
- `.work/lesson-scenes/`：92 个场景变化帧及 contact sheet；
- `.work/YASA-Engine/`：核验时使用的官方仓库浅克隆。

## 抓取脚本

```bash
python scripts/fetch_series.py
python scripts/fetch_video_lessons.py --output .work/video-lessons-hd \
  --metadata sources/video-lessons-hd.json
python scripts/fetch_yasa_docs.py
.venv/bin/python scripts/transcribe_video_lessons.py \
  --input .work/video-lessons-hd --output .work/transcripts
.venv/bin/python scripts/extract_lesson_slides.py \
  --input .work/video-lessons-hd --output .work/lesson-scenes
python scripts/verify_materials.py                         # Git 中保留的资料
python scripts/verify_materials.py --require-work-evidence # 连同本地视频/ASR/场景
```

## 证据优先级

1. 微信官方合集和文章正文：确定系列范围与课程显式内容；
2. 文章指向的课程视频：补足演示过程和讲解；
3. YASA 官方公开文档与仓库：核对命令、配置、类名和当前实现；
4. 本仓库的技术纠错：用于修正文中有歧义或明显错误的概念、公式和伪代码。

当课程发布时内容与当前仓库不同，笔记会标注“课程时口径”和“当前源码核验”，不把后来的功能倒灌成原课内容。

## 完整性边界

- 官方合集抓取时：`article_count=8`，取得 8 项，`continue_flag=0`；
- 官方课程页列出的 4 次理论课 + 3 次实验课，与合集中的 7 篇课程材料逐一对应，另有 1 篇开课公告；
- 所有 8 篇正文均保留完整抓取页、`#js_content` 本地结构阅读版和规范化文本；
- 所有正文知识图片已被课程笔记的逐图审计覆盖；
- 三篇实验文章链接的三个视频均已获取；视频没有官方字幕；
- 第二、三讲 PDF 的附件名和链接可核验，但匿名请求只返回语雀登录页；无效 HTML 未冒充 PDF 保存，正文不作为证据；
- 合集仍标记 `isupdating=1`，未来新内容需重新运行抓取脚本。

## 使用提醒

- 微信原文阅读优先打开 `article.html`；`original.raw.html` 含微信页面脚本，仅用于原始结构核验，不建议脱离隔离环境直接执行；
- `extracted.md` 是研究用规范化文本，不是重新发布的排版副本；
- `yasa-docs/` 保留每篇文档的原始 URL、更新时间和抽取元数据；它是研究快照，不替代官方在线版本，公开再分发前仍应核对上游许可；
- 最终学习笔记采用结构化转述、公式重建与纠错，不应以笔记替代原作者文章；
- ASR 会把 `UAST`、`Call Graph`、`CheckerPack`、`Source/Sink` 等识别错，不能单独作为 API 证据；
- 视频直链可能过期，重新运行抓取脚本即可刷新。
