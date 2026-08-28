# 高校教学系列：实验课程—掌握Checker编写艺术

[← 返回微信原文目录](../../README.md)

> **归档信息**
>
> **发布时间**：2025-12-23T18:19:52+08:00<br>
> **公众号原文**：[打开官方页面](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484326&idx=1&sn=b53b2698ab4fc90af2f03156a82a3777&chksm=fbce358eccb9bc982fd0d06b012b0af7cceddb891e8badbfaa87437b2fa756be438a4f27e86e)<br>
> **配套视频**：[在 Bilibili 观看](https://www.bilibili.com/video/BV1x4BxB5EBH/)<br>
> **归档说明**：正文顺序和原图来自原文；代码块由 HTML 结构恢复。复杂装饰样式可对照 [`article.html`](article.html)。

---

华中科技大学与蚂蚁基础安全团队联合开设的[《静态程序分析原理与实践》课程](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247483856&idx=1&sn=b2d22f2b375edf8c0394b95b7a5e379f&scene=21#wechat_redirect)已正式开课。该课程主要面向华科软件安全方向的研究生，采用理论与实践相结合的教学方式，培养具备扎实理论基础和强实践能力的网络安全专业人才。

作者及实验课程主讲人信息如下：

<p align="center"><img src="images/image-01.png" alt="图片" width="96"></p>

王雅仪

蚂蚁集团安全工程师，统一多语言程序分析YASA团队核心成员。

主要从事静态程序分析及其相关技术的研究工作，专注于运用静态分析技术解决多语言场景下的安全漏洞发现与风险识别等关键问题，致力于提升软件代码质量和系统安全性。

GitHub主页：

https://github.com/Arielwyy

实验课程作为华中科技大学网络空间安全学院与蚂蚁集团合作开设的《静态程序分析原理与实践》的重要组成部分，旨在通过企业级技术实践深化学生对理论知识的理解，并强化工程实践与创新能力。

课程共安排四次实验课，内容循序渐进，涵盖：

- 功能体验：YASA核心功能演示
- 原理探索：YASA内部机制深入解析
- 自定义分析任务：编写Checker来完成基础的代码分析
- 分析能力拓展实践：Web框架适配

本次是第三次实验课程，围绕Checker机制展开，从Checker的设计理念和工作原理出发，通过实际案例讲解了如何通过Checker机制扩展YASA引擎的分析能力。

课程重点包括：

- Checker的设计理念
- Checker的工作原理
- Checker的编写步骤和思路

详情见下方视频：

视频已同步于bilibili平台发布，可点击文末“阅读原文”，跳转观看。 [点击观看配套视频](https://www.bilibili.com/video/BV1x4BxB5EBH/)

YASA用户调研邀请

亲爱的社区伙伴们

感谢大家对YASA项目的关注与支持！

为了更好地了解大家的需求，优化产品体验

我们准备了一份简短的调研问卷

（填写约需2-3分钟）

扫描下方二维码完成问卷填写即可参与抽奖

有机会获得精美礼品！

如中奖请截图保存结果，添加 YASA 小助手微信（YASA1024）兑奖～

<p align="center"><img src="images/image-02.png" alt="图片" width="140"></p>

您的每一份反馈都对我们非常重要

期待听到您的宝贵建议！

## 关联阅读

- [开课啦 | 华中科技大学与蚂蚁基础安全团队联合开设《静态程序分析原理与实践》课程](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247483856&idx=1&sn=b2d22f2b375edf8c0394b95b7a5e379f&scene=21#wechat_redirect)
- [高校教学系列：程序分析—基础概念](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484014&idx=1&sn=626a0e866cf890a19b5335cc5bbb555b&scene=21#wechat_redirect)
- [高校教学系列：程序分析—中间表示](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484022&idx=1&sn=76fa95ff85549754bad3bc3a505b713f&scene=21#wechat_redirect)
- [高校教学系列：程序分析—数据流分析](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484230&idx=1&sn=6a2191643d461d8d8585bc24c02ec136&scene=21#wechat_redirect)
- [高校教学系列：实验课程—YASA原理简介及功能演示](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484237&idx=1&sn=10a647b65b32c94f9f40b542ed4d99b2&scene=21#wechat_redirect)
- [高校教学系列：实验课程—YASA内部机制深入解析](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484261&idx=1&sn=668fdc83e772d4b68bbfd787e5022385&scene=21#wechat_redirect)
- [高校教学系列：程序分析—指针分析及抽象解释](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484320&idx=1&sn=f306868888b67d001729ff18ef5abadc&scene=21#wechat_redirect)

长按识别二维码

关注“开放式安全基础设施”

<p align="center"><img src="images/image-03.png" alt="图片" width="176"></p>

在这里与上千名技术精英

交流技术干货&程序分析

---

[← 返回微信原文目录](../../README.md) · [查看公众号原文](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484326&idx=1&sn=b53b2698ab4fc90af2f03156a82a3777&chksm=fbce358eccb9bc982fd0d06b012b0af7cceddb891e8badbfaa87437b2fa756be438a4f27e86e)
