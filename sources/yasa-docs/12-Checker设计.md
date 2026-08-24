---
title: "Checker工作原理详解"
slug: lwe1xqg1nw1gh1u8
source_url: https://www.yuque.com/u22090306/bebf6g/lwe1xqg1nw1gh1u8
updated_at: 2025-11-12T04:45:27.000Z
word_count: 2098
image_count: 0
card_count: 10
---

# Checker工作原理详解

Checker是什么
YASA 作为一款统一的多语言分析引擎，具备高扩展能力，可满足用户不同的需求。但如果直接将适配逻辑放在主体逻辑中，代码将变得臃肿且难以维护和扩展。为此，需要采取易于扩展的外挂式方案。
YASA中提供了类似"hook(钩子)机制"的Checker机制，您可以类比成web开发中的事件监听——addXXXListener，允许开发者在事件发生时执行自定义代码。

[[CARD_01]]
```javascript
// 在页面DOM加载完成时进行初始化
document.addEventListener('DOMContentLoaded', function() {
initPageComponents();
});
// 当某组件获取焦点时，弹出提示
document.getElementById("xxx").addEventListener('focus', function() {
showHelpTips();
});
```
YASA的分析流程中也提供了许多事件(例如，AtFunctionCallBefore, AtMemberAccess, AtEndOfAnalyze, ...)。Checker机制允许开发者为这些事件注册钩子(回调)函数，在事件发生时自动执行定制化的逻辑。

[[CARD_02]]
```javascript
// 事件钩子函数
checkAtFunctionCallBefore(analyzer, scope, node, state, info) //当分析到函数调用前
checkAtAssignment(analyzer, scope, node, state, info) //当分析到赋值语句
checkAtEndOfAnalyze(analyzer, scope, node, state, info) //当此轮分析结束
...
```
然而，二者的不同之处在于，YASA在事件处并非直接注册钩子函数，而是注册一个个"checker"。
Checker的设计理念
Checker是YASA框架中用于执行程序分析任务的核心组件，其设计遵循以下理念：
插件化设计
解耦分析逻辑：将不同的分析任务（污点追踪、调用图构建、其他自定义分析能力等）封装为独立的Checker
灵活组合：可以根据需要启用或禁用特定的Checker
易于扩展：新增分析功能只需实现新的Checker，无需修改核心框架分析层实现逻辑
事件驱动机制
触发时机：Checker在分析过程的特定时机被触发
非侵入性：Checker不干扰核心分析流程，只在关键节点执行检查逻辑
信息丰富：触发时提供完整的上下文信息（analyzer、scope、node、state等）
Checker的工作原理
Checker的生命周期

[[CARD_03]]
```plain
Checker注册
↓
规则配置加载
↓
分析开始 → triggerAtStartOfAnalyze
↓
文件分析 → triggerAtCompileUnit
↓
节点分析 → triggerAtXXX (各种触发点)
↓
分析结束 → triggerAtEndOfAnalyze
↓
结果输出
```
Checker的触发时机
YASA提供了丰富的触发点（Checkpoint），Checker可以在这些时机执行检查逻辑：
|
触发点
|
说明
|
使用场景
|
triggerAtStartOfAnalyze
|
分析开始时
|
初始化、收集入口点
|
triggerAtEndOfAnalyze
|
分析结束时
|
输出结果、清理资源
|
triggerAtCompileUnit
|
每个文件分析前
|
文件级别的预处理
|
triggerAtEndOfCompileUnit
|
每个文件分析后
|
文件级别的后处理
|
triggerAtFunctionDefinition
|
函数定义时
|
收集函数信息
|
triggerAtFunctionCallBefore
|
函数调用前
|
污点追踪识别危险函数、调用图构建
|
triggerAtFunctionCallAfter
|
函数调用后
|
返回值分析
|
triggerAtPreDeclaration
|
变量声明时
|
变量分析
|
triggerAtMemberAccess
|
成员访问时
|
对象属性分析
|
triggerAtAssignment
|
赋值操作时
|
变量分析
|
triggerAtIfCondition
|
if条件判断时
|
条件分析
在触发时，Checker可以获取以下信息：
analyzer：分析器实例，可以访问全局状态、作用域等
scope：当前作用域
node：当前UAST节点
state：当前执行状态（变量值、调用栈等）
info：额外信息（函数调用信息、参数值等）
Checker的注册机制
Checker通过CheckerManager进行注册和管理：
自动注册：通过checker-config.json及 checker-pack-config.json配置文件自动注册
手动注册：在代码中通过doRegister方法手动注册
触发点绑定：根据Checker类中实现的方法自动绑定到对应的触发点
YASA初始化时，checkerManager会为每个事件注册checker：只要一个checker实现了某个事件的处理函数，YASA就会为该事件注册当前checker。
以FunctionCallBefore事件举例，只要您实现的checker中定义了triggerAtFunctionCallBefore函数(即调用FunctionCall事件前的处理函数)，那么在初始化时，YASA的checkerManager就会将您的checker注册在check_at_function_call_before这个事件中。
注册逻辑如下所示：

[[CARD_04]]
```javascript
// YASA初始化时，遍历所有checker类
doRegister(CheckerClass, self, resultManager, desc) {
const checker = new CheckerClass(resultManager)
checker.desc = desc
const checkerId = checker.getCheckerId()
if (!checkerId) {
logger.warn(`Checker-- ${checker.constructor.name} does not set checkerId. Ignore!!`)
return
}
const checkerName = checker.getCheckerId()

if (self.registered_checkers.hasOwnProperty(checkerName)) {
logger.warn(`${checkerName} is already registered, new one will override the previous`)
}
self.registered_checkers[checkerName] = checker

// 如果checker实现了某个事件的处理函数，就将该checker注册到该事件(checkpoint)
if (CheckerClass.prototype.triggerAtFunctionCallBefore) {
self.checkpoints.check_at_function_call_before.push(checker)
}
// 其他checker注册逻辑，此处省略...
}
```
Checker的调用流程

[[CARD_05]] [图示文字：扫描开始 → 加载checker → 加载checker-pack → 语言及框架识别 → 语言1-Analyzer初始化 → 语言N-Analyzer执行 → 卸载语言checker → CheckerManager.constructor → CheckManager.checkAtEndOfAnalyze → 扫描结束 → 语言1 Analyzer结束 → 语言N Analyzer结束 → 语言1-Analyzer执行 → 语言N-Analyzer初始化]
在analyzer进行符号解释的过程中，如果触发了某一事件，checkerManager会将注册在当前的事件的所有checker取出，依次遍历并执行该checker的事件处理方法。以FunctionCallBefore事件为例，在checkpoint会逐一执行每个checker，完成相应的逻辑处理，具体的工作流如下：

[[CARD_06]] [图示文字：checkAtFunctionCallBefore → GinDefaultTaintChecker → MuxEntryPointCollectChecker → GRpcEntrypointCollectChecker → xxChecker → triggerAtFunctionCallBefore → 1 FunctionCallBefore 事件checkpoint → 2 checkerManager取出所有注册了该事件的checker → 3 执行每个checker的事件处理函数（若有） → xxChecker 中没有实现triggerAtFunctionCallBefore 函数， 故未在FunctionCallBefore事件处注册，不会被取到]
Checker的结果保存与输出
设计目标
灵活的结果输出
YASA允许每个 checker 独立自定义输出内容，包括输出格式（如 SARIF 文件）、数据结构（如数据流追踪 trace、调用图 call graph 等），以及输出文件名。同时也支持无需输出结果，满足不同场景下的定制化需求。
高度解耦与组合能力
不同的checker 之间彼此独立，输出结果互不依赖，确保即使部分 checker 结果生成异常也不影响其他 checker 的正常工作。同时，系统也支持在单个 checker 实现中复用和聚合其他 checker 的分析结果，例如在 taint-checker 中同时输出 callgraph-checker 的结果，提升了扩展和复用能力。
实现方案
YASA中将保存结果逻辑和输出结果逻辑分离，checker只负责保存结果到resultManager中，结果的输出形式则由outputStrategy负责。
Checker保存结果
类resultManager提供了newFinding()方法，checker中需要保存结果的时候，先按需构造finding，最后调用resultManager的newFinding(),其中参数TaintOutputStrategy.outputStrategyId为输出策略的id

[[CARD_07]]
```javascript
const taintFlowFinding = this.buildTaintFinding(
this.getCheckerId(),
this.desc,
node,
nd,
fclos,
TAINT_TAG_NAME,
ruleName,
matchedSanitizerTags
)
if (!TaintOutputStrategy.isNewFinding(this.resultManager, taintFlowFinding)) continue
this.resultManager.newFinding(taintFlowFinding, TaintOutputStrategy.outputStrategyId)
```
所有checker的结果都将被保存在resultManager的findings字段中，以outputStrategyId作为key，如下所示：

[[CARD_08]]
```json
{
outputStrategyId1 : [finding1, finding2,...],
outputStrategyId2 : [finding1, finding2,...]
}
```
OutputStrategy输出结果设置
Checker如需自定义输出，需要新建一个OutputStrategy的子类，设置outputStrategyId和outputFilePath，并实现outputFindings方法，在方法实现中可自定义输出格式、内容和路径。outputFindings方法中，还可以通过resultManager获取其他OutputStrategy的findings输出。

[[CARD_09]]
```javascript
outputFindings(resultManager, outputFilePath, config, printf) {
let reportFilePath
if (resultManager) {
const allFindings = resultManager.getFindings()
const taintFindings = allFindings[TaintOutputStrategy.outputStrategyId]
let callgraphFindings
if (taintFindings) {
callgraphFindings = allFindings[CallgraphOutputStrategy.outputStrategyId]
const results = this.getTaintFlowAsSarif(taintFindings, callgraphFindings)
reportFilePath = pathMod.join(Config.reportDir, outputFilePath)
FileUtil.writeJSONfile(reportFilePath, results)
}
}
```
YASA整体结果输出
YASA在输出结果的时候（starter.js中），会遍历各OutputStrategy，并执行对应的outputFindings方法，输出结果

[[CARD_10]]
```javascript
const outputStrategyAutoRegister = new OutputStrategyAutoRegister()
outputStrategyAutoRegister.autoRegisterAllStrategies()
allFindings = resultManager.getFindings()
for (const outputStrategyId in allFindings) {
const strategy = outputStrategyAutoRegister.getStrategy(outputStrategyId)
if (strategy && typeof strategy.outputFindings === 'function') {
strategy.outputFindings(resultManager, strategy.getOutputFilePath(), Config, printf)
}
}
```
OutputStrategy自动注册
OutputStrategy类需要和OutputStrategyId建立相关关系，为了简化用户开发成本，用户新开发一个OutputStrategy的时候，只需要把实现了OutputStrategy的类放在/src/checker/common/output/目录下，yasa会在执行过程中自动注册该目录下的所有OutputStrategy类。
如果您需要自定义checker的输出，可以follow以下步骤：
在/src/checker/common/output/目录下新建一个OutputStrategy子类，如AbcOutputStrategy，设定输出策略类id（static变量outputStrategyId）和输出文件名（成员变量outputFilePath），并实现outputFindings方法。
checker检测到结果时，调用resultManager的new Finding方法，然后传入结果finding和输出策略的id（AbcOutputStrategy.outputStrategyId）。

更多checker研发的细节，可参考Checker开发文档目录下的文档。
