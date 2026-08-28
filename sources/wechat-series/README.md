# 微信公众号原文归档

本目录同时保留四种形态：

- `article.md`：段落化并嵌入本地原图的 GitHub 直接阅读版；
- `article.html`：保留公众号正文 `#js_content` 标签层次和内联样式，图片已本地化；适合克隆后用浏览器阅读；
- `original.raw.html`：抓取时收到的完整原始页面 HTML，用于结构核验；可能依赖微信远程资源，不建议直接执行其中脚本；
- `extracted.md`：供检索、审计和脚本处理的规范化纯文本，不追求还原公众号排版。

本地阅读入口：直接用浏览器打开本目录的 `index.html`，或运行：

```bash
python -m http.server 8000 --directory sources/wechat-series
```

然后访问 <http://127.0.0.1:8000/>。

| # | 标题 | GitHub 阅读 | 本地 HTML | 原始页面 HTML | 规范化文本 | 官方页面 |
|---:|---|---|---|---|---|---|
| 1 | 开课啦 \| 华中科技大学与蚂蚁基础安全团队联合开设《静态程序分析原理与实践》课程 | [直接阅读](articles/01-开课啦-华中科技大学与蚂蚁基础安全团队联合开设-静态程序分析原理与实践-课程/article.md) | [结构视图](articles/01-开课啦-华中科技大学与蚂蚁基础安全团队联合开设-静态程序分析原理与实践-课程/article.html) | [原页](articles/01-开课啦-华中科技大学与蚂蚁基础安全团队联合开设-静态程序分析原理与实践-课程/original.raw.html) | [文本](articles/01-开课啦-华中科技大学与蚂蚁基础安全团队联合开设-静态程序分析原理与实践-课程/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247483856&idx=1&sn=b2d22f2b375edf8c0394b95b7a5e379f&chksm=fbce37f8ccb9beeed3edd35a67b02baefb2960c4c0a02c6289193437e79920ec8436b05399b9) |
| 2 | 高校教学系列：程序分析-基础概念 | [直接阅读](articles/02-程序分析-基础概念/article.md) | [结构视图](articles/02-程序分析-基础概念/article.html) | [原页](articles/02-程序分析-基础概念/original.raw.html) | [文本](articles/02-程序分析-基础概念/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484014&idx=1&sn=626a0e866cf890a19b5335cc5bbb555b&chksm=fbce3446ccb9bd5075f64695eeedcb2104bee408b186aa336c77d181c65ad5c2e01bc384eb3e) |
| 3 | 高校教学系列：程序分析——中间表示 | [直接阅读](articles/03-程序分析-中间表示/article.md) | [结构视图](articles/03-程序分析-中间表示/article.html) | [原页](articles/03-程序分析-中间表示/original.raw.html) | [文本](articles/03-程序分析-中间表示/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484022&idx=1&sn=76fa95ff85549754bad3bc3a505b713f&chksm=fbce345eccb9bd4884e5b19e9ff19edfb697a5e69f5389b16b0f1f8eec0926d60686d7338b87) |
| 4 | 高校教学系列：程序分析—数据流分析 | [直接阅读](articles/04-程序分析-数据流分析/article.md) | [结构视图](articles/04-程序分析-数据流分析/article.html) | [原页](articles/04-程序分析-数据流分析/original.raw.html) | [文本](articles/04-程序分析-数据流分析/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484230&idx=1&sn=6a2191643d461d8d8585bc24c02ec136&chksm=fbce356eccb9bc783b460f2994ae1043e0de257204bb39bacaa4e06437bcaedc2e9987c2d7e0) |
| 5 | 高校教学系列：程序分析—指针分析及抽象解释 | [直接阅读](articles/05-程序分析-指针分析及抽象解释/article.md) | [结构视图](articles/05-程序分析-指针分析及抽象解释/article.html) | [原页](articles/05-程序分析-指针分析及抽象解释/original.raw.html) | [文本](articles/05-程序分析-指针分析及抽象解释/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484320&idx=1&sn=f306868888b67d001729ff18ef5abadc&chksm=fbce3588ccb9bc9e900831b3670b3bb609b078e7425c6fccc2b68366172997dafbd79ce8bf73) |
| 6 | 高校教学系列：实验课程—YASA内部机制深入解析 | [直接阅读](articles/06-实验课程-YASA内部机制深入解析/article.md) | [结构视图](articles/06-实验课程-YASA内部机制深入解析/article.html) | [原页](articles/06-实验课程-YASA内部机制深入解析/original.raw.html) | [文本](articles/06-实验课程-YASA内部机制深入解析/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484261&idx=1&sn=668fdc83e772d4b68bbfd787e5022385&chksm=fbce354dccb9bc5bdd74f7aa4251f14f8da97b4902e560cb40a28f92405921731320efbfa07f) |
| 7 | 高校教学系列：实验课程—YASA原理简介及功能演示 | [直接阅读](articles/07-实验课程-YASA原理简介及功能演示/article.md) | [结构视图](articles/07-实验课程-YASA原理简介及功能演示/article.html) | [原页](articles/07-实验课程-YASA原理简介及功能演示/original.raw.html) | [文本](articles/07-实验课程-YASA原理简介及功能演示/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484237&idx=1&sn=10a647b65b32c94f9f40b542ed4d99b2&chksm=fbce3565ccb9bc73866013fe7f1dd649103e633983d25467cced5125ab2b4546d12fa4febff5) |
| 8 | 高校教学系列：实验课程—掌握Checker编写艺术 | [直接阅读](articles/08-实验课程-掌握Checker编写艺术/article.md) | [结构视图](articles/08-实验课程-掌握Checker编写艺术/article.html) | [原页](articles/08-实验课程-掌握Checker编写艺术/original.raw.html) | [文本](articles/08-实验课程-掌握Checker编写艺术/extracted.md) | [微信](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484326&idx=1&sn=b53b2698ab4fc90af2f03156a82a3777&chksm=fbce358eccb9bc982fd0d06b012b0af7cceddb891e8badbfaa87437b2fa756be438a4f27e86e) |
