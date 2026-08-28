# 学习资料来源（精简版）

`sources/` 只保留能够在 GitHub 直接阅读的 Markdown，以及 Markdown 正文必须引用的本地图片。

## 保留内容

- `wechat-series/README.md`：8 篇微信公众号课程文章的 Markdown 阅读索引；
- `wechat-series/articles/*/article.md`：整理后的公众号正文；
- `wechat-series/articles/*/images/`：上述正文引用的 109 张本地图片；
- `yasa-docs/README.md`：YASA 官方文档索引说明；
- `yasa-docs/01-*.md`～`21-*.md`：21 篇 YASA 官方公开文档的 Markdown 快照。

微信文章和 YASA 文档都在正文中保留官方来源链接。三个实验视频使用永久 Bilibili 页面链接，直接写在对应文章和课程笔记中。

## 刷新与校验

```bash
python scripts/fetch_series.py
python scripts/fetch_yasa_docs.py
python scripts/verify_materials.py
```

抓取脚本默认只写入 Markdown 阅读材料和其必要图片，不再保存完整网页 HTML、重复纯文本、JSON sidecar 或视频元数据到 `sources/`。可重新生成的视频、转写、场景帧和临时元数据统一放在被 Git 忽略的 `.work/`。

## 完整性边界

- 当前微信合集快照包含 8 篇文章，Markdown 引用与本地图片均为 109/109；
- 当前保留 YASA 官方 Markdown 文档 21/21；
- 微信返回的 3 个 MathJax SVG 曾缺少字形引用，当前图片已修复并可正常渲染；
- 微信合集仍标记为持续更新，后续新增内容需重新运行抓取脚本；
- 这些文件是学习快照，不替代官方在线版本。
