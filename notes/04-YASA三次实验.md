# YASA 三次实验：从功能体验到 Checker 扩展

> 研究对象：微信公众号合集中的开课公告及三篇实验文章（本地列表位置 01、06、07、08）；课程视频 BV1y1mxBeEJu、BV1RUqhB6EUG、BV1x4BxB5EBH；`sources/yasa-docs/` 内 21 篇语雀公开 Markdown 文档；YASA-Engine/YASA-UAST 公开仓库。代码块、附件名、图示文字及来源信息均以 Markdown 正文和 front matter 为准。
>
> 版本说明：本文核验 `.work/YASA-Engine/` 的提交为 `249420d17656988138831956babebae456bfa6e1`，YASA-UAST 核验提交为 `4adfd7e93724aad1cf0abf2d1e73a29ed3a76c66`。公开仓库和文档会继续演进，因此当前实现不能自动等同于 2025 年课程现场版本；语雀操作文档的语言支持表也可能落后于最新源码。

## 0. 证据分级与阅读约定

全文使用以下标签，避免把后来的仓库实现倒灌成课程原话：

- **【课】**：指定公众号文章，以及三段课程视频的音轨和可辨画面可以直接核验；时间戳 ASR 只用于定位，不单独作为证据。`UAST`、`Call Graph`、`CheckerPack`、`BVT`、hook 名等技术词均以画面、官方文档和源码纠正。
- **【仓】**：YASA-Engine、YASA-UAST 当前公开仓库、`sources/yasa-docs/` 中的官方语雀文档或项目论文可以核验；其中官方项目文档不自动等于课堂逐字内容。
- **【推】**：依据课程主题和仓库实现作出的教学性重建；可能符合课堂展开顺序，但不是逐字转录。
- **【缺】**：视频、公开文档和固定源码仍无法确认的材料，例如完整 UQL 规范、课件 PDF 正文和课程现场精确 commit。

一个结论可以同时带多个标签，例如“YASA 以 UAST 统一多语言表示”既是【课】，也能由【仓】独立核验。

---

## 1. 课程背景与三次实验课在总课程中的位置

### 1.1 合作背景

- **【课】** 2025 年 11 月 7 日，华中科技大学网络空间安全学院与蚂蚁基础安全团队联合开设研究生课程《静态程序分析原理与实践》。理论部分覆盖静态分析概念、基础理论、核心算法和分析技术；实践部分采用开源 YASA。
- **【课】** 课程面向软件安全方向研究生，目标不是只会运行工具，而是同时掌握使用方法、设计原理和架构思想，并能基于 YASA 开展研究或参与社区建设。
- **【课】** 微信文章曾宣布实验部分规划四次：YASA 核心功能体验、YASA/UAST 内部机制、Checker 自定义分析、Web 框架适配。
- **【课】** 但官方教学页 `sources/yasa-docs/21-华中科技大学教学合作课程.md` 截至 2025-12-30 **只登记三次已发布实验课**：12 月 5 日“YASA 原理简介及功能演示”、12 月 12 日“YASA 内部机制深入解析”、12 月 19 日“YASA-Checker 设计和编写”，并只给出这三条视频。第四次 Web 框架适配尚未发布。
- 因此，本章只还原三次已发布实验课。**计划中的第四次 Web 框架课没有单独发布**；但框架适配并非完全缺席：第三讲开场和第二个现场例子明确使用 Go Gorilla/Mux 的 `HandleFunc` 讲解 entrypoint/source 建模。语雀中的 Mux/Django 文档可作实现补充，却不能冒充独立第四课。

### 1.2 YASA 的定位

- **【课】【仓】** YASA 是 Yet Another Static Analyzer，是开源静态程序分析项目。核心思路是定义多语言通用中间表示 UAST，并在其上构建统一、高精度的静态分析框架。
- **【课】【仓】** 用户可通过 Checker 扩展 AST 查询、数据流分析、函数调用图等任务；能力可以通过 SDK、UQL、MCP 等方式开放。
- **【课】【仓】** 污点分析不是独立于 Checker 的另一套系统，而是以内置 Checker 形式提供的重要安全能力。
- **【仓】** 当前项目首页将核心组件列为 YASA-UAST、YASA-Engine、YASA-UQL、YASA-MCP、YASA-SDK，并把 xAST 用作能力评测/回归靶场。
- **【仓】** 论文将 YASA 的工业动机概括为：企业技术栈多语言化，而逐语言建设前端、数据流引擎和规则集的成本不可持续；UAST 试图在统一性和语言特有语义保真之间取平衡。

> 边界提醒：YASA 论文说的是 multi-language analysis，而不是自动完成 cross-language analysis；不要把“同一框架支持多语言”误写成“一条数据流天然跨越多种语言运行时”。此外，2025 年部分操作文档只列 JS/TS、Go、Python，而当前源码已出现 Java、PHP 等支持；涉及支持矩阵时必须标注资料日期与版本。

---

# 第一讲：YASA 原理简介与功能演示

视频：[BV1y1mxBeEJu](https://www.bilibili.com/video/BV1y1mxBeEJu/)（约 30 分 59 秒）  
对应文章：[实验课程—YASA 原理简介及功能演示](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484237&idx=1&sn=10a647b65b32c94f9f40b542ed4d99b2)

## 2. 本讲范围与时间线

- **【课】** YASA 的产生背景、发展目标、整体架构与核心功能。
- **【课】** 现场演示 AST 解析、函数调用图生成、污点链路分析。
- **【课】** 使用 JSON 规则配置和 UQL 声明式查询语言两种方式，展示污点检测规则的编写和执行。
- **【课】** 视频画面与讲解已确认现场操作、示例类型和规则语义；仍【缺】的是可复制的课程完整 UQL 文件、完整 JSON 文件及现场所用精确 commit，而不是课程内容本身。

### 2.1 第一讲时间线（30:55）

| 时间 | 内容 |
|---|---|
| 00:00–04:28 | 静态分析与企业痛点：多语言支持成本、企业级精度/覆盖、开放性与 AI 友好性 |
| 04:28–07:04 | 三层架构：UAST 中间表示层、Engine/Checker 能力层、UQL/MCP 等开放层 |
| 07:04–09:24 | 四次课程规划；安装的 Release 合集与源码构建两种选择；`--help` 验证 |
| 09:24–12:06 | 单文件/工程 AST，现场 dump Python 示例并解释 `CompileUnit`、声明、函数、位置字段 |
| 12:06–13:33 | 生成 Call Graph，检查函数节点、调用边和 callsite |
| 13:33–16:33 | 污点命令；`Checker`、`CheckerPack`、`checker-config.json`、`checker-pack-config.json` |
| 16:33–21:46 | JSON rule-config：Checker IDs、三类 source、sink、sanitizer、entrypoint |
| 21:46–25:51 | SaaS 平台上的 UQL：不安全 URL 校验与内置命令注入规则，展示两条 Flask 污点链 |
| 25:51–29:05 | 自定义 UQL source/sink：节点 API、`from/where/select`、`flowPath` |
| 29:05–30:55 | 同一代码分别用 rule-config/UQL 实验，比较链路并总结 |

## 3. 安装、命令与整体架构

### 3.1 课堂安装选择与当前 CLI 模板

- **【课】【仓】** 课堂给出两条路线：只体验功能可下载 YASA-Engine Release 合集，其中包含 Engine 及 Go/Python UAST 二进制；调试、理解原理或二次开发则克隆 Engine/UAST 源码自行构建。JS parser 集成在 Engine 中；课堂版本的 Go/Python 需用 `--uastSDKPath` 指定 `uast4go`/`uast4py`。
- **【仓】** 当前安装文档要求 Node.js ≥18、TypeScript ≥5.8.3；源码构建的基本链是 `npm install` → `npx tsc` → `npx pkg ...`，而 Release 包只需解压、赋权并用 `--help` 验证。

以下是**当前官方文档/固定提交**可用的命令骨架，不是对 2025 课堂画面逐字符抄录：

```bash
# 安装验证
./yasa-engine-<platform> --help

# 单文件 UAST；Go/Python 指向对应 parser 二进制或其目录，JS/TS 通常不需要
./yasa-engine-<platform> --sourcePath <file> --language <javascript|typescript|golang|python> \
  --uastSDKPath <uast-binary-or-dir> --dumpAST --report <ast.json>

# 工程全部 UAST（当前源码存在；旧操作手册仍称 AST 仅支持单文件）
./yasa-engine-<platform> --sourcePath <project> --language <lang> \
  --uastSDKPath <uast-binary-or-dir> --dumpAllAST --report <report-dir>

# 完整调用图
./yasa-engine-<platform> --sourcePath <project> --analyzer <AnalyzerName> \
  --dumpAllCG --cgAlgo <DEFAULT|CHA> --report <report-dir>

# 污点/自定义 Checker
./yasa-engine-<platform> --sourcePath <project> --analyzer <AnalyzerName> \
  --checkerPackIds <pack-id[,pack-id...]> --checkerIds <checker-id[,checker-id...]> \
  --ruleConfigFile <rules.json> --entrypointMode <BOTH|SELF_COLLECT|ONLY_CUSTOM> \
  --report <report-dir>
```

> **版本漂移警告**：课堂画面、2025 操作手册与当前源码同时出现过位置参数和 `--sourcePath` 两种写法；早期文档还出现过 `-dumpAllCG`、`--checkerPath`，当前源码则是 `--dumpAllCG`、`--checkerIds`/`--checkerPackIds`。`--dumpAllAST` 也属于当前实现而与旧手册的“仅单文件”冲突。复现实验必须先执行目标二进制 `--help`，记录版本，不要混抄模板。

### 3.2 从源代码到结果

可将首讲展示的能力组织为下面的流水线：

```text
多语言源代码
    ↓ 各语言前端/parser
UAST：统一的高层树形表示
    ↓ YASA-Engine 预处理、符号解释和语义建模
抽象值、作用域、符号表、调用关系、数据流/污点状态
    ↓ Checker / JSON rule-config / UQL 查询
AST 结果、Call Graph、污点 Finding/Trace
    ↓ 输出策略或 SDK/MCP/查询接口
机器可读或面向人的报告
```

- **【课】** “UAST—Engine—Checker/查询—结果”是课程明确涉及的组件集合。
- **【仓】** README 明确说明 UAST Parser 把不同语言解析为标准化树结构，Engine 在其上分析，Checker 扩展任务，SDK/UQL/MCP 对外暴露能力。
- **【仓】** 论文图 2 将核心分析链更具体地分成 UAST Frontend Parser、Point-to Analyzer、Taint Checker：前端采用直接映射、结构变换和去语法糖；分析器同时包含通用语义与语言特定语义；污点侧含基础传播规则与框架特定 Checker。
- **【推】** 首讲更可能强调“从功能入口理解系统”，第二讲才深入解释 Engine 的双阶段机制，因此首讲不宜提前塞入过多内部类和方法名。

### 3.3 UAST 在首讲中的角色

- **【课】【仓】** UAST 是统一抽象语法树，不只是某一种语言原生 AST 的别名。
- **【仓】** 当前 UAST 规范把它定义为面向程序分析的高层通用 IR；节点都有 `type`、`loc`、`_meta` 等基础信息（课程图示常简称 meta）。`CompileUnit` 还记录 `body`、`language`、`languageVersion`、`uri` 和规范 `version`。
- **【仓】** 规范明确不承诺可重新编译执行，与程序分析无关的信息可能被删除，因此它是面向分析的有损抽象。

## 4. 三类现场能力

### 4.1 AST 解析与查询

- **【课】** 首讲现场演示 AST 解析。
- **【仓】** `get_file_ast` 是当前仓库中可核验的一个 SDK Checker：分析开始时取得 `analyzer.fileManager` 与 `analyzer.symbolTable`，按输入文件查找对应值，再输出去除 `parent` 环的 AST JSON。
- **【仓】** 官方 AST 查询文档给出 `--dumpAST`（单文件）和 `--dumpAllAST`（工程）两类入口；目标版本的参数和报告路径应以该操作文档/CLI help 为准。
- **【仓】** UAST 规范中的 `loc` 使用 `sourcefile`、起止行列定位源码；这也是查询结果、调用边和污点链回指源码的共同基础。
- **【推】** 教学上应让学生先对一个最小程序比较“源语言原生 AST”和“UAST”，再做节点类型、父子关系和位置查询；否则容易把 AST 演示误解为文本搜索。
- **注意**：当前仓库存在 `get_file_ast` 等具体 Checker，不代表课程首讲一定逐字介绍了该 `checkerId`，故只作仓库补充。

### 4.2 函数调用图

- **【课】** 首讲现场演示函数调用图生成。
- **【仓】** 当前 `CallgraphChecker` 把过程表示为图节点、调用表示为边；可解析出函数定义时，节点可由过程名和定义位置标识，解析不完全时会退回调用点表达式等信息。
- **【仓】** `triggerAtFunctionCallBefore` 在符号解释已经解析出目标函数闭包后，根据当前调用栈确定 caller，根据 `fclos` 确定 callee，并把调用点位置/哈希挂到边上。
- **【仓】** 分析结束时，Call Graph 作为 finding 交给调用图输出策略；官方文档给出 `--dumpAllCG` 与 `--cgAlgo CHA|DEFAULT`，代码中可核验 `CHA` 分支，输出策略生成包含 `nodes`、`edges` 和调用点信息的 `callgraph.json`。文档关于 DEFAULT/CHA 的速度和精度描述属于项目方说明，不能扩写成独立测评结论。
- **【推】** 因为调用边依赖符号解释得到的可能目标，YASA 的调用图不应简单描述成“遍历所有 CallExpression 后按函数名连边”。动态调用、未解析库调用和语言特性会产生近似或退化节点。

### 4.3 污点链路

- **【课】** 首讲现场演示污点链路分析。
- **【仓】** 当前基本污点模型可用 Source—传播—Sink—Sanitizer/过滤描述；测试规则示例把 `__taint_src` 配成 `TaintSource`，把 `__taint_sink` 的第 0 个参数配成 `FuncCallTaintSink`。
- **【仓】** `TaintChecker` 生成 finding 时会恢复 trace，规范化 SOURCE/SINK 边界，附加 sink 规则、调用栈、入口点、匹配到的 sanitizer 标签等信息；当前实现要求可信链首项是 `SOURCE: `、末项是 `SINK: `。
- **【仓】** 官方污点文档说明 SARIF 中 `results[].codeFlows` 保存从 source 开始的逐步传播源码位置，另有 `entrypoint`、`sinkInfo`、`matchedSanitizerTags`；`graphs` 只是污点模拟执行过程中触及的部分调用图，用于位置映射，不能当作 `--dumpAllCG` 的完整调用图。
- **【仓】** 论文列出的基础传播包括赋值、容器字段读写、函数参数/返回；语言特定规则还包括 JavaScript 原型/Promise、Go channel 等。
- **【推】** “污点链”既是数据流证据，也受入口点、调用图、指针/对象解析和框架建模影响；同一 JSON source/sink 规则在入口点或调用目标解析不同的情况下可能得到不同结果。

## 5. JSON 规则配置

### 5.1 可核验的最小结构

当前仓库的最小测试规则形如：

```json
[
  {
    "checkerIds": ["taint_flow_test"],
    "sources": {
      "TaintSource": [
        { "path": "__taint_src", "scopeFile": "all", "scopeFunc": "all" }
      ]
    },
    "sinks": {
      "FuncCallTaintSink": [
        { "fsig": "__taint_sink", "args": [0] }
      ]
    }
  }
]
```

- **【课】** 首讲明确展示了 JSON 方式编写并执行污点规则。
- **【仓】** `checkerIds` 决定一组规则供哪些 Checker 加载；`CheckerBase.loadRuleConfig` 会匹配当前 `checkerId` 并合并规则内容。
- **【仓】** 示例中可核验的键包括 `sources.TaintSource`、`sinks.FuncCallTaintSink`、`path`、`scopeFile`、`scopeFunc`、`fsig`、`args`。更完整的语言规则还出现 `calleeType`、`attribute`、`sanitizers`、`sanitizerIds` 和 `entrypoints`。
- **版本警告**：不要由示例反推出一份稳定、完整的 JSON Schema；字段语义和可用规则种类应以目标版本的 `rules-basic-handler`、source/sink util、官方 `ruleConfig配置` 文档为准。
- **用途警告**：`taint_flow_test` / `TestTaintChecker` 在官方注册配置中明确用于回归测试、不推荐外部使用；这里仅借其最小结构解释字段，真实项目应选目标语言/框架的正式 CheckerPack。

### 5.2 从规则到执行的概念链

```text
规则选择 checkerIds
  → CheckerBase 加载/合并对应 rule-config
  → Checker 在生命周期检查点识别 source、sink、sanitizer、entrypoint
  → Engine 的符号值在解释过程中携带/传播 taint tag 和 trace
  → sink 命中时构造 finding
  → 输出策略去重、格式化和导出
```

其中前两步和当前代码结构是【仓】，课程是否以这套顺序逐项展开属于【推】。

- **【仓】** 官方规则文档推荐顶层使用数组，`checkerIds` 即使只有一个也使用数组；当前基类虽兼容字符串，但这是内部兼容路径，不应当成稳定写法。
- **【仓】** 官方污点规则文档还列出 `FuncCallArgTaintSource`、`FuncCallReturnValueTaintSource`、`sanitizers`、`entrypoints` 等结构；sink 可按文档用 `fsig` 或 `fregex` 匹配，并通过 `args` 指定位置。具体字段仍须跟随目标版本文档。
- **【仓】** 当前 CLI 通过 `--ruleConfigFile` 指定规则文件，并通过 `--checkerIds` 或 `--checkerPackIds` 真正加载对应 Checker；只提供 JSON 文件并不等于 Checker 已启用。

### 5.3 四类污点配置的语义

- **【仓】Source**：官方文档公开三种形式：
  - `TaintSource`：在 `triggerAtMemberAccess` 处把变量或对象属性标为 source；
  - `FuncCallArgTaintSource`：函数调用前把指定实参位置标为 source；
  - `FuncCallReturnValueTaintSource`：函数调用后把指定返回值位置标为 source，多返回值可用 `values` 指定位置。
- **【仓】Sink**：当前文档只公开 `FuncCallTaintSink`；可用 `fsig` 精确匹配，或 `fregex` 匹配复杂/动态调用链，`args` 指明接收污点的参数，强类型场景可结合 `calleeType`。
- **【仓】Sanitizer**：每个 sanitizer 用唯一 `id` 定义，由 sink 的 `sanitizerIds` 引用。文档列出函数调用与二元比较两大类型，以及过滤、校验、初始化安全配置、调用栈包含特定调用、二元比较等 scenario。报告仍可能保留命中过 sanitizer 的链，供消费者根据 `matchedSanitizerTags` 判断，而不是简单把链删除。
- **【仓】EntryPoint**：常见字段为 `filePath`、`functionName`、`attribute`；Go 方法还可用 `funcReceiverType` 区分 receiver。
- **【课】【仓】边界**：课堂 16:33–21:46 已逐项讲 `checkerIds`、三类 source、函数调用 sink、与 sink 绑定的 sanitizer、`filePath/functionName/funcReceiverType` entrypoint；上面的精确字段结构再由 2026-03-13 更新的官方文档核验。课程版本与当前文档仍可能漂移。

## 6. UQL 声明式查询

- **【课】** 21:46 起切到课前开放的 SaaS 平台。规则库分 Data Flow、AST、Security 等类别；课堂先复制一条 AST 规则，查出两处使用 `startswith`/属性判断进行不安全 URL 校验的位置。
- **【课】** 23:47 起演示 Security 中的命令注入规则：在 GitHub 找到一个 Flask 项目，预先运行后得到两条链；结果页逐步展示 `request` 输入如何经过变量/表达式传播到命令执行 sink。规则复用框架库已建模的 remote-flow source 和 command-injection sink，再用 `from / where / select` 查询，`flowPath` 调用 YASA 的数据流能力返回路径。
- **【课】** 25:51 起展示自定义节点建模：平台提供函数调用、函数定义、成员访问、参数、字符串字面量五类节点 API。以 `request.post(...)` 参数为 sink、`flask.request` 成员访问为 source；命令注入小例则用函数调用及 argument API 定位 `os.system` 参数，用 property API 定位 `flask.request`，最后查询二者间 `flowPath`。课程实验要求在同一代码库分别以 JSON rule-config 和 UQL 定义规则并比较链路。
- **【课】【仓】** 课程称 UQL “语法上兼容 CodeQL”，并建议参考语法页及 CodeQL 社区资料；项目首页也作相同定位。这里的“兼容”只能证明课堂所用声明式外形与大量语法可复用，不能外推为完整语言/标准库等价。
- **【仓】** 当前 YASA-Engine 可见一组 AntQL 风格的交互 Checker：`antql_getbaseclass`、`antql_getdefinition`、`antql_getsubclass`、`antql_hasflow`、`antql_hasfunctioncall`、`antql_hasproperty`；`antql_hasflow` 接收 source/sink 位置、选择 entrypoint 并输出污点 finding。
- **【缺】** 课堂画面足以确认上述查询方法，但公开材料仍没有完整 UQL grammar、CodeQL 兼容子集、标准库清单、编译器源码及可复制的课堂查询全文；AntQL Checker 也不能无证据等同于完整 UQL。
- **【推】** JSON 适合配置现成 Checker 的 source/sink/entrypoint 模型；UQL 适合组合 AST 与流关系。两者都可驱动底层分析，不应简单理解为“配置版”和“更精确版”。

## 7. 第一讲建议复现实验

1. 准备一个 10～20 行、包含函数调用和显式 source→sink 的最小样例。
2. 先输出 UAST，确认 `type` 与 `loc`，记录源代码到 UAST 的对应。
3. 生成调用图，检查 caller、callee、调用点位置；再加入一个无法静态解析的调用观察退化结果。
4. 用仓库自带最小 JSON 结构配置 source/sink，检查 trace 是否以 SOURCE 开始、SINK 结束。
5. 在课程 SaaS/等价 UQL 环境可访问时，对同一 source/sink 执行 UQL 查询，比较两种表达方式的输入、结果和可解释性；无法访问时只记录课程已验证的方法，不伪造查询文件。
6. 实验报告必须记录 YASA 提交、UAST parser 版本、语言、命令、规则文件和结果目录。

---

# 第二讲：解码 UAST/YASA 内部机制

视频：[BV1RUqhB6EUG](https://www.bilibili.com/video/BV1RUqhB6EUG/)（约 40 分 56 秒）  
官方教学页所列讲义附件：`HUST-第二次实验课-YASA设计理念.pdf`  
对应文章：[YASA 内部机制深入解析](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484261&idx=1&sn=668fdc83e772d4b68bbfd787e5022385)

## 8. 本讲范围与时间线

- **【课】** YASA-UAST 的设计理念和实现机制：有损统一抽象、节点结构、极大元选取、消除语法糖、parser 选型。
- **【课】** YASA-Engine 的通用层—语言层—框架层，以及预处理与 entrypoint 符号解释双阶段流程。
- **【课】** 课堂逐步演示符号值、BVT 路径值、字段敏感污点传播和工业符号表优化；下文已按画面与源码纠正 ASR 技术词。

### 8.1 第二讲时间线（40:55）

| 时间 | 内容 |
|---|---|
| 00:00–01:27 | UAST/Engine 两仓关系与本讲目标 |
| 01:27–06:52 | UAST 定义、有损抽象；Java/JS/Python `Person` 统一结构；`type/loc/meta` 与 50+ 节点 |
| 06:52–11:24 | 通用性/语言特性权衡；极大元 `RangeStatement`；JS 解构去糖与 Python 列表推导思考题 |
| 11:24–16:46 | AST→UAST 两个关键步骤；官方 parser 与 ANTLR/Tree-sitter 取舍；Go/Python/Java/JS-TS 选择 |
| 16:46–18:24 | Engine 通用层、语言层、框架层，通用层约复用 70% 能力 |
| 18:24–24:53 | 从 Web 污点例反推文件/包、import、entrypoint；预处理→逐入口符号解释→finding 输出 |
| 24:53–28:47 | Primitive/Object/Function/Symbol/Union/BVT/Package/Undefined 等值；BVT 保存左右分支 |
| 28:47–33:06 | 字段敏感数组例：`taint_src`→数组 0 号字段→sink；索引 1 则取安全值 `b` |
| 33:06–35:51 | 新语言接入：UAST parser、语言 Analyzer、可选框架 Analyzer；要点回顾 |
| 35:51–40:44 | 工业优化：树形符号表深拷贝困境→全局表+每 entrypoint 临时表+按需复制 |
| 40:44–40:55 | 实验安排与结束 |

## 9. UAST：为什么是“有损统一”

### 9.1 面向程序分析，而非可逆编译

- **【课】** 课程明确使用“有损统一抽象”。
- **【仓】** UAST 规范把设计目标写为简单、通用、详尽元信息；同时明确不承诺后续可编译执行，与程序分析无关的信息可能被去掉。
- **【仓】** 论文把源语言节点分为三类：
  1. **通用语义节点**：至少两种语言中有等价语义，如 Literal、If、Call、Range；
  2. **语言特有节点**：强行降解会损失关键语义，如 Python Yield、Go ChanType、Python Tuple；
  3. **可约简节点**：可变换为通用组合或与分析无关，如列表推导、箭头函数、包装根节点、注释。
- **【仓】** 论文当前版本称规范含 54 类节点；官方设计文档概称 50+ 类，分为基础、控制流、表达式、声明、类型等组。数量差异反映版本/分类口径，不应写成永久常数。
- **【仓】** 刷新后的官方图示文字给出跨语言类定义的共同骨架：`CompileUnit → ClassDefinition → VariableDeclaration name → FunctionDefinition _CTOR_ / getName → AssignmentExpression / ReturnStatement`，其下再出现 `MemberAccess`、`ThisExpression`、`Identifier`。这比只说“统一 AST”更具体：统一发生在类、字段、构造器、方法和表达式节点层次。

### 9.2 “极大元选取”的官方定义与边界

- **【课】** 文章和视频元数据明确列出“极大元选取”。
- **【仓】** 官方 UAST 设计文档给出的直接定义是：**如果不同语法节点存在语义包含关系，归一化时倾向选择最大包含关系的节点**。示例是把 Java 增强 `for`、JavaScript `for...in`、Go `range` 统一到字段较完整的 `RangeStatement(key, value, right, body)`。
- **【推】** 可以用偏序/最大包含关系帮助理解，但官方文档没有给出自动求极大元的形式算法；它更像 UAST 设计准则，而非已公开的机械化节点选择算法。
- **【仓】** 对通用性与语言特性的权衡是“核心结构用统一节点，语言特性通过 `_meta` 保留，只保存分析需要的信息”。例如 Python `@property` 可作为 decorator 元数据保留。

### 9.3 三种 AST→UAST 转换方式

- **【仓】直接映射**：原生 AST 节点直接映射到通用或保留的特有节点，例如 Python `ast.If` → `IfStatement`、`ast.Yield` → `YieldExpression`。
- **【仓】结构变换**：聚合或重排源 AST 结构，统一到同一高层节点，例如多语言迭代结构统一为 `RangeStatement`。
- **【课】【仓】去语法糖**：把语言便利语法还原为更少的通用节点。官方文档示例包括：JavaScript 解构赋值 `let {x,y}=init` 拆成临时变量和两次属性赋值；Python 列表推导拆为临时列表、循环、条件与 `push`。论文还给出箭头函数归一到 `FunctionDefinition` 的例子。
- **【推】** 转换正确性的评价不应只看 UAST JSON 能否生成，还应看：位置信息是否可追溯、求值顺序是否保持、作用域/绑定是否保持、控制结构是否保持、语言特性是否需要特定语义处理器。

### 9.4 Parser 技术选型

- **【课】** 课程明确讲到“多语言 AST 转换的技术选型标准”。
- **【仓】** 官方 UAST 设计文档比较两类方案：
  - 第三方解析工具（ANTLR、Tree-sitter 等）：统一框架、灵活，但需维护语法文件，语言更新要人工跟进，文档认为实时性/准确性可能受影响；
  - 语言官方 Parser：不同语言实现难统一管理，但稳定性、语言版本同步、特性覆盖和维护成本通常更优。
- **【仓】** 官方选型原则是：优先使用稳定且功能完善的官方 parser；官方无可用实现时，再选成熟第三方工具。判断项包括官方 API 稳定性、功能完善度、第三方成熟度和维护成本。
- **【仓】** 文档列出的当时方案为：Go→`go/parser`→`parser-Go`；Java→ANTLR4→`parser-Java-Js`；JavaScript/TypeScript→Babel→`parser-Java-Js`；Python→官方 `ast`→`parser-Python`。
- **版本边界**：该文档称当时支持四种 parser；最新 Engine/UAST 源码还出现 PHP、Java 等更广支持。学习笔记应同时写明“文档更新时间下的矩阵”和“当前固定提交中的实现”，不能把旧表当作永久支持清单。

## 10. Engine 的双阶段分析

- **【仓】** 官方 Engine 设计文档从端到端角度列出四环：源代码转 UAST；在 UAST 上进行预处理与符号解释；Checker 监听 checkpoint 并记录结果；OutputStrategy 生成结果。课程所谓“双阶段”专指第二环内部的“预处理 + entrypoint 符号解释”，两种划分并不矛盾。
- **【仓】** 刷新后的架构图示文字进一步串起：语言/框架 Analyzer → 模拟执行引擎 → UAST 上的 `checkAtCompileUnit`、`checkAtNewExpr`、`checkAtIdentifier`、`checkAtIfCondition` 等事件 → CheckerManager 注册/触发 → ResultManager → SARIF、JSON 或 console。rule-config 经 `rules-basic-handler` 进入污点等 Checker；调用图则由 CG Checker 产出。

### 10.1 阶段一：预处理（pre-process / initialization）

- **【课】** 课程明确把预处理作为第一阶段。
- **【仓】** 当前 `executeAnalysisPipeline` 先把 `preprocessReady` 设为 false，执行或从缓存恢复 pre-process，再调用 `startAnalyze` 收集入口点等信息。
- **【仓】** `processCompileUnit` 会先处理 `needCompileFirst` 的节点，然后再处理完整 body；注释说明部分需优先编译的元素需要先建立。
- **【仓】** 初始化时建立 AST manager、全局 SymbolTableManager、module/package/file/function 管理结构、全局 top scope 和 AnalysisContext。
- **【推】** 从实现职责看，预处理的教学含义是先建立之后解释所需的“静态世界”：文件/包、声明、函数闭包、类/类型、导入导出、入口点候选和全局符号关系。不同语言的具体预处理内容并不完全相同。

### 10.2 阶段二：符号解释（symbol interpretation）

- **【课】** 课程明确把符号解释作为第二阶段，并演示符号值传播。
- **【仓】** 当前流水线在入口点收集后把 `preprocessReady` 设为 true，切换到临时符号表，执行 `symbolInterpret()`，最后恢复原始符号表并结束分析。
- **【课】【仓】** 课堂值类型页列出 `PrimitiveValue`（数值/字符串/布尔）、`ObjectValue`、`FunctionValue`、`SymbolValue`（无法解析出具体值）、`UnionValue`（多个候选组合）、`BVTValue`、`PackageValue`、`UndefinedValue`。这里存在必须保留的**名称漂移**：课程幻灯片逐字写 **BVT = Bounded Value Type**，而当前固定源码 `bvt.ts` 的类注释写 **BVTValue = Branch Value Tree**。两者都以 L/R 等子节点保存分支值；本文不把当前展开名倒灌成课堂原话。
- **【课】** 课堂随后具体展开：`PrimitiveValue` 的 `vtype/rawValue/sort`，`FunctionValue` 保存函数定义节点并在调用时取回目标；BVT 对 `if` 真分支的 tainted `source` 与假分支安全字符串 `abc` 分开保存，用于分支合并/隔离并支持路径敏感分析。
- **【仓】** 对已知布尔字面量，`processIfStatement` 只走确定分支；未知条件则复制 scope、fork states，为两侧加入正/负路径条件，分别解释后合并值。
- **【仓】** 官方 Engine 文档把“模拟执行”定义为：对代码做符号化（抽象），并逐步解释程序行为直至结束；符号值不是 concrete value。它还明确区分经典符号执行：YASA 不以“求解后选一条分支”为其描述，而是分析各分支并保存分支信息。
- **【仓】** Analyzer 分为基础层、语言层和框架层。官方文档称基础 Analyzer 承担约 70% 的符号解释能力；语言/框架层继承并适配包管理、特有语义或语法糖。这个“70%”是项目方架构说明，不是本章独立测量。
- **【推】** 因此符号解释更接近在 UAST 上的抽象执行/解释，但不能据此宣称它具备 SMT 驱动符号执行的路径可满足性保证。

### 10.3 为什么分两阶段

- **【推】** 预处理先建立可复用的全局环境，符号解释再从一个或多个 entrypoint 进入路径/上下文相关执行，可以降低重复解析和重复建模成本，并允许不同 Checker 在统一生命周期上工作。
- **【仓】** 当前代码支持保存/加载上下文环境缓存；也能只 dump entrypoint 而跳过符号解释。这佐证了预处理产物与入口点解释可以分离。
- **【课】** 课堂用 Web 污点例直接解释阶段划分：先建立全局文件/包结构才能解析 import 和被调函数，先识别 `hello`/`update` 等路由 entrypoint，之后才从每个入口逐句模拟执行并恢复 source→sink 链。它同时服务跨文件解析、不可由普通调用抵达的框架入口和入口间状态隔离。

### 10.4 EntryPoint 为什么是独立概念

- **【仓】** 官方文档把 entrypoint 定义为符号解释起点，它脱离 Checker 存在，但通常由 Checker 指定或消费。
- **【仓】** 三种策略为：`ONLY_CUSTOM`（只用 rule-config 指定入口）、`SELF_COLLECT`（只用 YASA 自采集入口）、`BOTH`（两者并用）。操作文档称默认是 `BOTH`。
- **【仓】** 自采集可来自 Web 框架路由、完整调用图边界、解释型语言文件第一行等；实际是否启用取决于所加载 Checker，不是所有分析都会自动执行所有策略。
- **【仓】** 分两阶段的直接理由包括：预处理先联通 import/包关系以支持跨文件/跨包解析；路由函数等入口没有显式调用，若不额外指定为 entrypoint，普通文件级模拟执行可能到达不了。

## 11. 敏感性如何落到状态与值

### 11.1 上下文敏感

- **【课】** 课程不只作概括性宣传：BVT 例明确展示路径分支隔离，数组字段例明确展示索引/字段区分；上下文、对象和流敏感的更强结论仍应以固定实现与具体配置为准。
- **【仓】** README 声称支持域、上下文、对象、路径、流敏感；论文更严格地说明 Point-to Analyzer 实现上下文、路径、字段敏感。
- **【仓】** 论文用调用栈扩展表示上下文，每次调用形成新状态；有界调用深度避免无限递归。
- **【推】** 不应仅凭“有调用栈”宣称任意深度完全上下文敏感；边界、递归截断、缓存和合并策略决定实际精度。

### 11.2 路径敏感

- **【仓】** 未知条件下 fork state、分别维护正负路径条件、最后合并，是路径敏感的直接实现证据。
- **【仓】** 当前实现中的合并值/union tree 保存不同分支来源；论文用 `Phi(T)` 表达路径相关值。
- **【推】** 这能减少把互斥分支值立即混为一谈的误报，但若路径条件只记录而不由求解器判定可满足性，仍可能保留不可行路径。课程证据不足以宣称完备的 path feasibility checking。

### 11.3 字段/对象敏感

- **【仓】** 论文中的对象值维护字段映射，字段读写按具体字段更新；这属于字段敏感。
- **【仓】** README 额外声称对象敏感和域敏感，但论文主方法部分没有给这两项同等详细的形式化。
- **【推】** 学习笔记应分别解释“区分对象实例”和“区分对象字段”，不要因宣传语将二者混为同义词。

#### 课堂字段敏感例：逐步符号化

**【课】** 28:47–33:06 的例子不是泛泛宣称“字段敏感”，而是逐步走完以下状态：

1. 预处理把源码转为 UAST，建立文件/函数关系，为 `main` 建 `FunctionValue` 并收集它为 entrypoint；
2. 从 `main` 开始解释，变量声明把字面量 `"source"` 的 `PrimitiveValue` 绑定给 `taint_src`，并按规则带上 taint；
3. 字符串数组初始化在 UAST 中被展开为临时对象和对字段 `0/1/2` 的三次赋值，临时对象分别保存 `taint_src`、`"b"`、`"c"`；
4. 整个临时对象赋给 `str`，所以污点只在字段 `str[0]`，并未污染整个数组；
5. 处理 `sink(str[0])` 时按字段 0 取回 tainted `PrimitiveValue`，形成 source→sink 链；若改为 `sink(str[1])`，取到的是安全值 `"b"`，不应报告同一链。

这正是按对象字段/索引区分值的字段敏感证据，也同时展示了“去语法糖后的 UAST 节点 → 符号值写入/读取 → taint finding”的完整链。

### 11.4 流敏感

- **【仓】** 引擎按 UAST 执行次序处理赋值、分支、调用，状态随程序点变化，可视为流敏感实现方向。
- **【推】** 循环展开、合并、摘要与缓存可能影响实际流精度；需要具体配置和样例验证，不应写成无条件的“每条路径每个程序点都完全精确”。

## 12. 符号表：从树状复制到全局表 + 临时表

### 12.1 课程明确结论

- **【课】** 预处理结果必须稳定；每个 entrypoint 都应从同一基线开始，不能受前一入口解释的修改污染。课堂比较“记录全部修改后回滚”和“每次复制后丢弃”两路，指出前者恢复复杂，后者又受树形符号表牵连。
- **【课】** 树形表靠内存引用层层嵌套，复制一个深层值可能牵出整棵树；限制复制深度虽省成本，却会损害敏感性/精度。新版设计将嵌套对象扁平为全局 ID→符号值表，并为每个 entrypoint 创建临时表：先查临时表，未命中才从全局表按需复制/覆盖，入口结束直接丢弃临时表。课堂以“垃圾桶/垃圾袋”作比喻。
- **【课】【仓】** 优化目标因此同时是：降低复制量、保持预处理基线、隔离入口状态并避免用截断深度换精度；当前 `TemporarySymbolTableManager` 可核验这一按需复制路径。

### 12.2 当前仓库可核验机制

- **【仓】** `initValTreeStruct` 创建单个 `SymbolTableManager`，并把它注册为全局符号表；函数符号表的值可存 UUID，再通过全局表解析到对象。
- **【仓】** `TemporarySymbolTableManager` 同时持有原始表和临时表；读取先查临时表，必要时从原始对象复制到临时表，写入临时区域；符号解释结束后恢复原始表并清理临时表。
- **【仓】** 入口点执行相关代码还存在 overlay/copy-on-write 机制，说明当前实现继续围绕“共享基础环境、局部写时复制、入口隔离”演进。
- **【推】** 教学上可以把全局表视为预处理阶段稳定、共享的知识，把临时表视为一次符号解释/入口点的可变覆盖层。这样不必为每条路径深拷贝完整符号树，同时可防止一次入口解释污染下一次。
- **版本警告**：课程文章描述的是设计演进，当前仓库已出现更多 overlay/并发隔离代码；不要反推 2025 课堂版本已有全部当前类。

## 13. 第二讲建议手算实验

使用如下结构的小程序即可覆盖核心概念：

```text
全局函数 source()
函数 f(x):
  if unknown:
    obj.a = x
  else:
    obj.b = "safe"
  return obj
两个不同调用点调用 f(...)
最后把其中一个字段送入 sink
```

要求：

1. 画出预处理后全局环境：文件、函数定义、入口点候选、全局符号。
2. 分别记录两个调用点的调用栈，观察上下文是否区分。
3. 未知分支处画出两个状态、路径条件、对象字段。
4. 合并后说明 `a`、`b` 的可能值以及污点标签。
5. 比较“深拷贝整个树”和“全局只读基础 + 临时覆盖”的复制对象数量。
6. 标出哪些结论来自实际 YASA 输出，哪些只是手算模型。

---

# 第三讲：Checker 机制与编写流程

视频：[BV1x4BxB5EBH](https://www.bilibili.com/video/BV1x4BxB5EBH/)（约 34 分 48 秒）  
官方教学页所列讲义附件：`HUST-第三次实验课-checker原理.pdf`  
对应文章：[掌握 Checker 编写艺术](https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484326&idx=1&sn=b53b2698ab4fc90af2f03156a82a3777)

## 14. 本讲范围与时间线

- **【课】** Checker 的插件化、事件驱动、配置驱动理念；checkpoint、Manager、Finding/ResultManager。
- **【课】** 从加载注册、规则加载、事件调用、结果保存到输出的完整生命周期。
- **【课】** 现场明确讲解两个案例：硬编码密码 Checker，以及 Go Gorilla/Mux `HandleFunc` 框架 Checker；课程画面保留了 hook 选择、finding/输出和注册思路。

### 14.1 第三讲时间线（34:48）

| 时间 | 内容 |
|---|---|
| 00:00–01:08 | 课程目标：设计理念、工作原理、两个编写实例 |
| 01:08–03:37 | Web 污点需求；Mux `HandleFunc` 路由入口与 `r.URL.Query()` source；Gin/Django 对照 |
| 03:37–08:28 | 硬编码进 Engine 的问题；插件化、事件驱动、配置驱动的推导 |
| 08:28–12:14 | Checker 定义；三种理念及 checkpoint 上下文 |
| 12:14–15:39 | 全局/文件/函数/变量/控制流 checkpoint；rule-config 动态加载与 Checker 组合 |
| 15:39–18:11 | CheckerManager、ResultManager、Finding；完整生命周期 |
| 18:11–20:35 | 自动事件注册、`checker-config.json`、CheckerPack |
| 20:35–22:07 | 事件触发→查 checkpoint→逐 Checker 调用→finding 入 ResultManager→回主流程 |
| 22:07–23:34 | 编写 Checker 的五步方法 |
| 23:34–29:05 | 实例一：硬编码密码，变量声明 hook、结束 hook、Finding、自定义 OutputStrategy、注册 |
| 29:05–32:27 | 实例二：Mux `HandleFunc`，函数调用前识别路由、取第二参数为 entrypoint、标 source、注册 |
| 32:27–34:48 | 三理念/生命周期/五步法回顾；个人与小组实验、下次小组分享 |

## 15. Checker 的设计理念

- **【仓】** 官方语雀页面摘要称：如果把各种适配逻辑直接放进主体引擎，代码会臃肿、难维护，因此 YASA 提供类似 hook 的外挂式 Checker 机制；可类比 Web 开发中的 hook/插件，但不能据此假定具体框架 API。
- **【仓】** 论文把 Checker 定义为独立、事件驱动的插件，用户可在不修改核心逻辑的情况下定制分析。
- **【仓】** Checker 不只做漏洞规则：当前配置中能看到 AST 获取、调用图、调用链、污点、安全净化、框架入口点收集和 AntQL 查询等 Checker。
- **【推】** Checker 的核心价值是把“通用解释语义”与“在特定生命周期观察/修改/产出什么”分离：Engine 负责解释 UAST，Checker 订阅事件、读取分析状态、增加模型或输出 finding。

## 16. Checker 的工作原理

### 16.1 基类与规则加载

- **【仓】** `CheckerBase` 保存 `checkerId`、`resultManager`、`checkerRuleConfigContent`；构造时初始化规则并按 `checkerId` 加载配置。
- **【仓】** 一个 rule-config 数组元素的 `checkerIds` 可以是数组或单值；命中后内容合并到 Checker 的规则配置。
- **【仓】** 具体 Checker 通常继承 `Checker`；污点类可继承 `TaintChecker`。例如 `GetFileAstChecker extends Checker`、`TestTaintChecker extends TaintChecker`。

### 16.2 CheckerManager 与生命周期检查点

当前仓库可核验的检查点包括：

- 分析开始/结束；
- 编译单元开始/结束；
- 二元运算、变量声明前后、赋值；
- 调用语法、函数调用前/后；
- new 表达式/对象构建；
- if 条件、语句块结束；
- 函数定义、Identifier、MemberAccess；
- 每个 AST 节点结束；
- entrypoint 符号解释前/后。

- **【仓】** `CheckerManager.doRegister` 不是要求 Checker 显式列出订阅表，而是检查类原型上是否存在相应 `triggerAt...` 方法，存在就加入对应 checkpoint 列表。
- **【仓】** 刷新后的调用图示明确展示：触发 `checkAtFunctionCallBefore` 后，CheckerManager 取出注册到该事件的 Gin、Mux、gRPC 等 Checker，依次调用其 `triggerAtFunctionCallBefore`；没有实现该方法的 Checker 不会出现在此事件列表中。
- **【仓】** Engine 在处理 UAST 节点或调用生命周期时调用 `checkAt...`，Manager 再转发到已注册 Checker 的 `triggerAt...`。
- **【仓】** 官方生命周期概括为：Checker 注册 → 规则加载 → `triggerAtStartOfAnalyze` → 每个 `CompileUnit` → 各节点 `triggerAtXXX` → `triggerAtEndOfAnalyze` → 结果输出。触发时可取得 `analyzer`、`scope`、UAST `node`、执行 `state` 和事件特有的 `info`。
- **【推】** 选择 hook 的原则应是“在所需语义信息刚好可用时触发”：只看调用语法可用 syntax hook；需要已解析 callee 和实参抽象值应选 function-call-before/after；需汇总全局结果则选 end-of-analyze。

### 16.3 注册、规则包和输出

- **【仓】** `resource/checker/checker-config.json` 将 `checkerId` 映射到 `checkerPath`、描述和可选示例规则路径。
- **【仓】** `checker-pack-config.json` 把多个 Checker 组成规则包；例如默认 Java 污点包由 Java taint Checker、callgraph、sanitizer 组成。
- **【仓】** Checker 通过 `resultManager.newFinding(finding, strategyId)` 交付结果；ResultManager 按 `outputStrategyId` 分组保存 findings。AST 交互结果、调用图、污点链可使用不同输出策略。
- **【仓】** 自定义输出策略需定义静态 `outputStrategyId`、输出文件名并实现 `outputFindings`。官方文档称放入 `src/checker/common/output/` 后由引擎自动注册；分析结束时遍历策略输出结果。
- **【仓】** `checker-kit` 当前暴露 logger、AstUtil、valueUtil、stateUtil、SourceLine、Graph、Config 等辅助对象。
- **版本警告**：以上是指定提交的真实名称；写教程时应固定版本，不要宣称这些都是长期稳定的公共 API。

## 17. 五步课堂方法与工程化展开

**【课】课堂五步法**（22:07 的总结页逐项可见）：

1. **确定 Checker 功能**：明确检查目标；
2. **选择合适触发点**：判断所需信息在哪个 checkpoint 可用；
3. **实现触发方法**：在 `triggerAt...` 中完成识别/收集并生成结果；
4. **定义输出策略（如果需要）**：默认输出够用即可跳过；
5. **注册 Checker**：写入 `checker-config.json`，需要组合时再加入 CheckerPack。

下面把这五步按固定仓库实现展开为可执行的工程清单；其中 rule-config、测试和版本固定是必要补充，不改变课堂五步主线。

### 步骤 1：把需求写成事件和数据需求

示例问题：寻找空函数、统计超长文件、收集框架入口、识别 source/sink。

先回答：

- 需要观察哪类 UAST 节点？
- 需要语法信息，还是已解释的抽象值/函数闭包？
- 是边分析边报告，还是结束后汇总？
- 是否需要 rule-config？
- finding 应走何种输出策略？

### 步骤 2：选择基类并设置唯一 `checkerId`

仓库文档摘要和代码都支持如下形态：

```ts
class MyChecker extends Checker {
  constructor(resultManager: any) {
    super(resultManager, 'my_checker_id')
  }
}
```

污点分析扩展可能继承 `TaintChecker`，但不要为了普通 AST 检查引入污点基类。

### 步骤 3：实现最小必要的 `triggerAt...` 方法

真实可核验示例：

- `GetFileAstChecker.triggerAtStartOfAnalyze` 保存 file/symbol managers；
- `CallgraphChecker.triggerAtFunctionCallBefore` 采集调用边；
- `TestTaintChecker.triggerAtIdentifier` 标记 source；
- `TestTaintChecker.triggerAtFunctionCallBefore` 检查函数调用 sink；
- `triggerAtEndOfAnalyze` 可用于提交汇总结果。

不要实现大量空 hook；Manager 只会为原型上存在的方法注册检查点。

### 步骤 4：读取 `info` 前先核验该 hook 的契约

- 不同 hook 的 `info` 字段不同。例如当前调用前事件能看到 `fclos`、`callInfo` 等，赋值事件有 `lscope/lvalue/rvalue`，Identifier 事件有解释结果。
- **禁止**凭相似命名猜字段；应沿 Engine 的 `checkAt...` 调用点和 CheckerManager 转发代码核对目标版本。

### 步骤 5：构造 finding 与输出策略

- finding 至少应包含该输出策略需要的数据；具体字段应参考同类 Checker 和 common types。
- 使用 `resultManager.newFinding` 提交；污点类还需考虑 trace 边界、去重、sanitizer 和 entrypoint。
- 位置尽量来自 UAST `loc`，不要重新按文本行猜测。

### 步骤 6：在 `checker-config.json` 注册

按当前仓库结构填写唯一 `checkerId`、实现路径、描述；需要演示规则时可关联 `demoRuleConfigPath`。

### 步骤 7：需要组合时加入 Checker Pack

当能力依赖 callgraph、sanitizer、框架入口收集等 Checker 时，使用 pack 明确组合关系，而不是在一个类中复制所有逻辑。

### 步骤 8：编写 rule-config（若需要）

让配置中的 `checkerIds` 命中新 Checker；按 source/sink/entrypoint/sanitizer 的真实处理代码填写字段。普通结构检查可能根本不需要规则文件。

### 步骤 9：构建、运行、检查 finding

- **【仓】** 官方文档区分两条扩展路径：只修改 rule-config 时可直接加载 JSON，通常无需重新打包；新增或修改 Checker 代码则需要重新构建/打包目标二进制。
- **【仓】** `CONTRIBUTING.md` 要求本地测试并执行回归验证后再提交 PR。
- 建议至少覆盖：正例、反例、重复 finding、无法解析调用、多个入口点、不同语言/框架边界。

### 步骤 10：回归与版本固定

- 使用 xAST 或对应仓库测试；记录提交、配置和期望结果。
- Checker 依赖内部 hook 时尤其要固定 Engine 版本。

## 18. 两个课堂现场案例与官方补充

### 18.1 实例一：硬编码密码 Checker

- **【课】功能**：检查变量声明的名称是否包含 `password`/`pwd` 等关键词，初始化值是否为字符串字面量，并进一步匹配弱密码、纯数字、纯字母等硬编码模式。
- **【课】触发点**：24:45–28:55 的高清画面确认使用 `triggerAtPreDeclaration` 检查声明，并在 `triggerAtEndOfAnalyze` 汇总输出；这里应以屏幕代码校正 ASR，而不是改写成 `triggerAtVariableDeclaration`。当前固定源码的 CheckerManager 也保留 `checkAtPreDeclaration`→`triggerAtPreDeclaration` 注册/调用链。【仓】
- **【课】实现与结果**：命中项先收集到问题数组，结束时为每项创建 Finding，并按屏幕示意调用 `resultManager.newFinding(finding, 'hardcoded_password_output')`。自定义输出是可选步骤，示意类为 `HardcodedPasswordOutputStrategy extends OutputStrategy`，负责该 strategy ID 对应结果的 JSON 输出；最后在 `checker-config.json` 注册，使用户可按 Checker ID 启用。
- **版本边界**：上述类名、hook、参数和调用形式是**课程屏幕示意及其目标版本 API**；即使当前固定源码能核验部分同名 checkpoint，也不应把整段示意代码宣称为跨版本稳定公共 API。
- **边界**：这是讲解用简化检测器，不等于成熟 secret scanner；变量名和弱密码模式都可能误报/漏报，生产规则还需熵、上下文、白名单与凭据类型建模。【推】

### 18.2 实例二：Go Gorilla/Mux `HandleFunc` 框架 Checker

- **【课】功能**：识别 `router.HandleFunc(path, getUserHandler)` 路由注册，把第二个参数对应函数闭包加入 entrypoints，并标记其 HTTP 请求数据为 source；课堂开场以 `r.URL.Query()` 说明用户输入。
- **【课】触发点与屏幕逻辑**：路由注册是函数调用，因此实现 `triggerAtFunctionCallBefore`；从 `info` 解构 `{ fclos, argvalues }`，用示意辅助判断 `isMuxRouteRegistry` 识别 Mux 路由注册，取第二参数的函数闭包加入 `analyzer.entryPoints`，并给路由参数引入 `'GO_INPUT'`。最后注册 Checker。
- **【仓】实现核验**：官方 Mux 文档代码同样读取 `info.fclos` 与 `argvalues`，以被调对象 `_qid` 和属性名匹配 `NewRouter().HandleFunc`，对函数闭包去重后加入 `analyzer.entryPoints`，并引入 `GO_INPUT` taint；可单独注册，也可加入 `taint-flow-golang-default` pack。
- **版本边界**：`isMuxRouteRegistry`、`info` 形状和 entrypoint/taint 写入方式按**课程屏幕示意及目标版本 API**记录；目标版本变化时必须沿 Engine 触发点与 CheckerManager 契约重新核对。
- **课程定位**：这正是第三讲中的框架适配实例，说明计划第四讲的主题已在第三讲出现；但它仍不构成一节单独发布的“第四课”。

### 18.3 官方文档中的延伸案例

1. **寻找空函数**：继承 `Checker`，在 `triggerAtFunctionDefinition` 检查 `node.body.body.length === 0`，用自定义 OutputStrategy 写 finding，再注册到 `checker-config.json`。
2. **统计每个超过 200 行的文件**：官方案例使用 `triggerAtCompileUnit`，根据 `CompileUnit.loc.end.line - loc.start.line` 判断文件长度，再通过自定义 Strategy 输出。
3. **Python Django 适配**：文档方案以 `triggerAtCompileUnit` 识别导入 Django URL API 的 `urls.py`，再以声明/赋值 hook 处理 `urlpatterns`，识别 `path`、`re_path`、`url` 以及函数视图/`as_view()` 类视图，最后建立 entrypoint 并把 URL 参数登记到 `sourceScope`。

**文档自身的实现边界也必须保留：**

- Django 示例的 `extractParamNames` 只匹配 `<int:id>`、`<str:name>` 等尖括号 converter；它不能提取同页 `re_path(r'...(?P<year>...)...')` 示例中的命名组，因此“支持 `re_path` 路由”不等于“已完整支持其参数取污点”。
- 函数视图与类视图代码都只使用 `targetSrcName[0]`，所以多 URL 参数示例虽能提取数组，实际展示的标记逻辑只处理第一个参数。这是官方案例代码可直接观察到的限制，不应改写为完整多参数支持。
- Mux 的课堂讲解由视频直接确认；Django 和上述完整实现细节则来自官方项目文档。官方教学页没有第四课日期、讲义或视频，故仍不能把这些材料改写成一节已发布的独立第四课。

## 19. Checker 与 JSON、UQL 的关系

- **【仓】** Checker 是执行/扩展机制；rule-config 是向 Checker 注入 sources、sinks、sanitizers、entrypoints 等外部规则的一种配置载体。
- **【仓】** 当前 Engine 的 AntQL 风格交互查询由 Checker 支撑，例如 `antql_hasflow` 继承 TaintChecker；但证据不足以把这套 AntQL 交互层直接等同于完整 UQL。
- **【推】** 因此三者不是简单的三选一：
  - 只改规则数据时，优先 JSON；
  - 能用声明式关系表达时，使用 UQL；
  - 需要新的生命周期事件处理、框架语义或输出行为时，编写 Checker。
- **【缺】** 公开材料没有稳定的官方决策树，也无法确认 UQL 是否能调用任意自定义 Checker；这属于完整 UQL 规范缺口，不能从课堂演示外推。

---

# 20. 三讲之间的统一知识图

```text
第一讲：看见能力
  源代码 → UAST/AST → 调用图 → 污点链
                 ↘ JSON / UQL 表达分析需求

第二讲：理解能力为什么成立
  AST→UAST 统一原则
  预处理建立全局环境
  entrypoint 上进行符号解释
  抽象值 + 作用域 + 调用栈 + 路径条件 + 字段映射
  全局符号表 + 临时覆盖降低复制并隔离执行

第三讲：学会扩展能力
  CheckerBase / TaintChecker
  CheckerManager 生命周期 hook
  checker-config / checker-pack / rule-config
  finding + output strategy
  测试和回归
```

核心依赖链为：

```text
UAST 的归一质量
  → Engine 能否正确解释声明、赋值、分支、调用和语言特性
  → points-to/callee/entrypoint 是否准确
  → 调用图与污点传播是否连续
  → Checker 能否在正确 hook 拿到正确语义信息
  → finding/trace 是否可信
```

任何一层的缺口都可能表现为“规则没报”或“污点断链”，因此排错时不能只改 JSON。

---

# 21. 证据索引

## 21.0 本地固化证据

- 21 篇语雀文档及来源 front matter：`sources/yasa-docs/README.md`、`sources/yasa-docs/01-*.md`～`21-*.md`
- 官方教学页：`sources/yasa-docs/21-华中科技大学教学合作课程.md`
- 三段公开视频：[BV1y1mxBeEJu](https://www.bilibili.com/video/BV1y1mxBeEJu/)、[BV1RUqhB6EUG](https://www.bilibili.com/video/BV1RUqhB6EUG/)、[BV1x4BxB5EBH](https://www.bilibili.com/video/BV1x4BxB5EBH/)
- 时间戳 ASR（仅作定位，术语经画面/源码纠正）：`.work/transcripts/lesson-1-BV1y1mxBeEJu.md`、`lesson-2-BV1RUqhB6EUG.md`、`lesson-3-BV1x4BxB5EBH.md`
- 92 个 720p 场景帧与 contact sheets：`.work/lesson-scenes/lesson-*`
- 当前 Engine 源码快照：`.work/YASA-Engine/`（提交 `249420d17656988138831956babebae456bfa6e1`）
- 重点项目文档：`sources/yasa-docs/10-YASA-UAST设计.md`、`11-YASA-Engine设计.md`、`12-Checker设计.md`、`14-Checker与rule-config设计.md`

## 21.1 课程文章与视频

- 课程开篇文章：<https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247483856&idx=1&sn=b2d22f2b375edf8c0394b95b7a5e379f>
- 第一讲文章：<https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484237&idx=1&sn=10a647b65b32c94f9f40b542ed4d99b2>
- 第二讲文章：<https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484261&idx=1&sn=668fdc83e772d4b68bbfd787e5022385>
- 第三讲文章：<https://mp.weixin.qq.com/s?__biz=MzU1NTc1NDMxMQ==&mid=2247484326&idx=1&sn=b53b2698ab4fc90af2f03156a82a3777>
- 第一讲视频：<https://www.bilibili.com/video/BV1y1mxBeEJu/>
- 第二讲视频：<https://www.bilibili.com/video/BV1RUqhB6EUG/>
- 第三讲视频：<https://www.bilibili.com/video/BV1x4BxB5EBH/>
- 官方教学发布清单（仅登记三次实验课）：<https://www.yuque.com/u22090306/bebf6g/sr0y5fqg0kcua5nf>

## 21.2 项目与规范

- YASA-Engine README（固定提交）：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/README_ZH.md>
- YASA-UAST README（固定提交）：<https://github.com/antgroup/YASA-UAST/blob/4adfd7e93724aad1cf0abf2d1e73a29ed3a76c66/README_ZH.md>
- UAST 规范：<https://github.com/antgroup/YASA-UAST/blob/4adfd7e93724aad1cf0abf2d1e73a29ed3a76c66/specification/specification.md>
- YASA 论文：<https://arxiv.org/abs/2601.17390>
- 官方语雀文档首页：<https://www.yuque.com/u22090306/bebf6g>
- UAST 设计文档：<https://www.yuque.com/u22090306/bebf6g/wtucc3wf7gzwkuhs>
- 名词解释（含 UQL 官方定位）：<https://www.yuque.com/u22090306/bebf6g/qgswkd2qa07yr5z2>
- Engine 设计文档：<https://www.yuque.com/u22090306/bebf6g/idrc3p344fz19h4g>
- Checker 工作原理：<https://www.yuque.com/u22090306/bebf6g/lwe1xqg1nw1gh1u8>
- Checker 与 rule-config：<https://www.yuque.com/u22090306/bebf6g/axsqw5texifp1mmq>
- 污点分析操作文档：<https://www.yuque.com/u22090306/bebf6g/okuzgsdc66gbmk39>
- ruleConfig 配置文档：<https://www.yuque.com/u22090306/bebf6g/zkw8i3ffw8n884sd>
- 内置 Checker 文档：<https://www.yuque.com/u22090306/bebf6g/ouenen3i3en236ek>
- AST 查询文档：<https://www.yuque.com/u22090306/bebf6g/mzaslh9b1hook19l>
- Call Graph 文档：<https://www.yuque.com/u22090306/bebf6g/ahif12ik3vnapoin>
- 自定义分析文档：<https://www.yuque.com/u22090306/bebf6g/dgyshe6zve9tuef2>
- 空函数 Checker 案例：<https://www.yuque.com/u22090306/bebf6g/tzw6osk2hh5wst22>
- Go Mux Checker 案例：<https://www.yuque.com/u22090306/bebf6g/kf9yhos9qxhtflos>

## 21.3 Engine 实现核验点（固定提交）

- Checker 基类与规则加载：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/checker/common/checker.ts>
- CheckerManager 检查点与注册：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/engine/analyzer/common/checker-manager.ts>
- 分析流水线、全局/临时符号表：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/engine/analyzer/common/analyzer.ts>
- AST Checker：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/checker/sdk/get-file-ast-checker.ts>
- Call Graph Checker：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/checker/callgraph/callgraph-checker.ts>
- Taint Checker：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/checker/taint/taint-checker.ts>
- 最小污点 Checker 示例：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/checker/taint/test-taint-checker.ts>
- 最小 JSON 规则：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/resource/example-rule-config/rule_config_test.json>
- Checker 注册配置：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/resource/checker/checker-config.json>
- Checker Pack 配置：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/resource/checker/checker-pack-config.json>
- AntQL 交互命令路由：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/client.ts>
- AntQL flow Checker 实现：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/src/checker/antql/rules/antql-hasflow.ts>
- 贡献与回归要求：<https://github.com/antgroup/YASA-Engine/blob/249420d17656988138831956babebae456bfa6e1/CONTRIBUTING.md>

---

# 22. 媒体覆盖审计与证据边界

## 22.1 三篇实验文章的 8 张图片

已逐张打开 `06/07/08` 三篇实验文章的全部图片；**8/8 均为头像或二维码，没有知识图、架构图、代码图或课件图**，因此不从它们提取技术结论：

| 文章 | 图片 | 内容 | 处理 |
|---|---|---|---|
| 实验 2（06） | image-01 | 作者头像 | 非知识图，排除 |
| 实验 2（06） | image-02、image-03 | 问卷/联系引流二维码 | 非知识图，排除 |
| 实验 1（07） | image-01 | 作者头像 | 非知识图，排除 |
| 实验 1（07） | image-02 | 联系引流二维码 | 非知识图，排除 |
| 实验 3（08） | image-01 | 作者头像 | 非知识图，排除 |
| 实验 3（08） | image-02、image-03 | 问卷/联系引流二维码 | 非知识图，排除 |

合计：**3 张重复作者头像 + 5 张二维码 = 8 张；知识图 0 张**。课程知识来自文章正文、视频画面、官方文档与源码，而不是这 8 张宣传素材。

## 22.2 三段视频的 92 个场景

已核对 `.work/lesson-scenes/lesson-*` 的全部 **43 + 30 + 19 = 92** 个 720p 场景帧，并结合 contact sheets 与时间戳 ASR 建立前三节的时间线：

- **第一讲 43 场**：覆盖背景/架构、安装文档、`--help`、AST/Call Graph 命令与输出、Checker 配置、JSON rule-config、UQL SaaS、不安全 URL 与命令注入链、结尾二维码；知识已进入第 2–7 节。
- **第二讲 30 场**：覆盖 UAST 节点、极大元、去语法糖、parser 选型、Engine 分层、双阶段、值类型/BVT、字段敏感例、全局+临时符号表；知识已进入第 8–13 节。
- **第三讲 19 场**：覆盖三种设计理念、checkpoints、生命周期、注册/调用流程、五步法、硬编码密码、Mux `HandleFunc` 与总结；知识已进入第 14–19 节。

场景切分用于覆盖核验，不把“每一帧”误当成独立论据；命令、类名和字段均继续以官方文档/源码校正 ASR。

## 22.3 仍然真实不可得的信息

仅保留以下【缺】项，不再把已取得的视频转写、场景或现场案例列为缺失：

1. **完整 UQL 公开规范**：缺 grammar、精确 CodeQL 兼容子集、完整标准库 API、编译流程和可复制的课堂查询文件。
2. **课程课件 PDF 正文**：教学页公开第二、三讲附件名/链接，但本地材料没有 PDF 正文；视频画面已覆盖讲授内容，不等于拿到了原 PDF。
3. **课程精确版本**：未公开课堂二进制对应的 commit/tag；本文固定 Engine/UAST 提交仅用于实现核验，故 CLI/hook/rule 字段均标注版本漂移。
4. **第一讲完整实验资产**：视频确认了 AST/Call Graph/JSON/UQL/Flask 命令注入的过程和语义，但完整示例仓库快照、完整 JSON/UQL 文件及逐字符现场命令不可得。
5. **符号表迁移量化数据**：视频确认树形表问题与新设计，当前源码确认全局/临时表；仍无旧实现固定提交、迁移 benchmark 或精度对比数据。
6. **独立第四课**：计划中的 Web 框架课没有单独发布；第三讲已现场讲 Mux 适配，但不能据此虚构第四讲视频、讲义或日期。
