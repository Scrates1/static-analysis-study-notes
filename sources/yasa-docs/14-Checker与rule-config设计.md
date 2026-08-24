---
title: "Checker与rule-config设计"
slug: axsqw5texifp1mmq
source_url: https://www.yuque.com/u22090306/bebf6g/axsqw5texifp1mmq
updated_at: 2025-11-12T09:04:26.000Z
word_count: 1913
image_count: 0
card_count: 8
---

# Checker与rule-config设计

名词解释
Checker
Checker主要负责提供挂载到引擎之上的规则检查器，包括规则及规则相关的检查器实现及管理。
值得注意的是：很多其他底层引擎能力提供的功能，在这里都可以通过checker完成配置实现，从而具备了更多的灵活性。例如污点追踪、构建CG，接口统计、获取类型、获取函数调用语句对应的函数定义等功能都可以通过编写不同的checker实现。
所有checker都需要在resource/checker/checker-config.json 中进行注册才可以通过命令行参数--checkerIds使用。在你共建checker时，需要外部传入ruleconfig的checker建议提供一个demoRuleConfigPath供其他人参考，YASA中默认的checker都已提供。
CheckerPack
包含一组checker的包，由于很多checker需要配合使用，如污点追踪规则包中，有的checker负责污点检测，有的checker负责额外采集entrypoint，有的checker负责检测sanitizer，有的checker负责构建并输出callgraph，将他们打成一个包，更易用户进行调用。
所有checkerPack都需要在resource/checker/checker-pack-config.json 中进行注册才可以通过命令行参数--checkerPackIds使用。
Checkpoint
YASA默认提供了以下checkpoints供checker访问

[[CARD_01]]
```plain
this.checkpoints = {
check_at_start_analyze: [], // 开始分析前
check_at_end_analyze: [], // 分析完成后
check_at_compile_unit: [], // 每个文件分析前
check_at_end_compileunit: [], // 每个文件分析后
check_at_binary_operation: [], // 二元表达式开始分析前
check_at_pre_declaration: [], // 每个变量定义之前
check_at_funccall_syntax: [], // 函数调用时，分析目标对象前
check_at_function_call_before: [], // 函数调用时，分析出目标函数后，实际模拟执行这个函数前
check_at_function_call_after: [], // 函数调用时，分析出目标函数后，实际模拟执行这个函数后
check_at_new_expr: [], // new操作时，分析new目标对象前
check_at_new_object: [], // new操作时，分析new目标对象后，模拟执行new操作前
check_at_new_expr_after: [], // new操作整体分析完后
check_at_ifcondition: [], // if语句开始分析前
check_at_assignment: [], // 赋值操作前
check_at_end_block: [], // 每一个语句块分析后
check_at_function_definition: [], // 分析完函数定义语句后
check_at_variable_declaration: [], // 分析完变量定义语句后
check_at_identifier: [], // 分析完identifier后
check_at_member_access: [], // 分析完MemberAccess后
check_at_end_of_node: [], // 分析完每一个ast node后
check_at_symbol_execute_of_entrypoint_before: [], // 在模拟执行一个entrypoint前
check_at_symbol_execute_of_entrypoint_after: [], // 在模拟执行一个entrypoint后
}
```
CheckerManager
CheckManager模块提供检查器（checker）模块的管理，包括注册管理以及程序点挂载管理功能。
引擎提供灵活的注册管理功能，检查器开发者仅需要按照Checker类编写对应规则，作对应命名，并且将其放置在指定目录，引擎就会自动加载检查器，从而完成注册。不需要对检查器进行硬编码或者配置，减少开发和维护成本。
Checker本身可以理解成程序hook点集合，每个checker根据需要，都可以实现不同的程序点hook api。通过hook api获取程序运行时状态，并且通过前面介绍的state管理器，完成对需要状态的记录，最后通过判断状态，产出检查结果。
RuleConfig
Checker中需要的信息可以通过ruleconfig提供，如污点分析的checker需要用户指定的source、sink、sanitizer等内容，就可以通过rule_config文件来指定。YASA提供了每个需要用户输入的checker的rule_config示例，可以查看resources中的示例。为污点追踪指定rule_config的方式详见污点分析和ruleConfig配置部分。
注意：rule_config文件中的checkerIds字段声明的是哪些checker具有处理该规则的能力，对应的checker需通过命令行参数--checkerIds或--checkerPackIds指定加载才会生效
ruleconfig文件的结构如下：

[[CARD_02]]
```plain
[
{
"checkerIds":[
"taint_flow_go_input",
"taint_flow_gin_input"
],
"sources":{
"TaintSource":[],
"..."
},
"sinks":{
"FuncCallTaintSink":[]
},
"sanitizers":[],
"entrypoints":[]
},
{
"checkerIds":[
"taint_flow_python_input"
],
"sources":{},
"sinks":{},
"sanitizers":[],
"entrypoints":[]
},
...

]
```
ResultManager、Finding与Strategy
YASA将如何记录finding、打印finding的权利都交给了用户，可以灵活的打印自己需要的格式。在checker中记录finding时，可以自主定义一个任意结构的finding，通过this.resultManager.newFinding写入，在传入时除了finding外，还需要传入一个strategyId，就是结果的打印策略。有输出需求的checker需要实现一个strategy，放在src/checker/common/output 目录下，引擎会自动加载所有的策略。可以参考污点追踪/callgraph的checker或checker研发案例中的示例。
【checker保存结果】类resultManager提供了newFinding()方法，checker中需要保存结果的时候，先按需构造finding，并做去重处理，最后调用resultManager的newFinding(), 以污点追踪输出策略为例，为了在加载多个污点追踪checker后，可以统一进行finding的去重与打印，所有污点追踪checker共用一个输出策略：
其中参数TaintOutputStrategy.outputStrategyId为输出策略的id

[[CARD_03]]
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
resultManager中，字段findings用于保存所有checker的结果，outputStrategyId作为key，如下所示：

[[CARD_04]]
```json
{
outputStrategyId1 : [finding1, finding2,...],
outputStrategyId2 : [finding1, finding2,...]
}
```
【OutputStrategy输出结果设置】Checker如需自定义输出，需要新建一个OutputStrategy的子类，设置outputStrategyId和outputFilePath，并实现outputFindings方法，在方法实现中可自定义输出格式、内容和路径。outputFindings方法中，还可以通过resultManager获取其他OutputStrategy的findings输出。
【YASA整体结果输出】yasa在输出结果的时候（starter.js中），会遍历各OutputStrategy，并执行对应的outputFindings方法，输出结果

[[CARD_05]]
```plain
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
如何编写Checker
Checker编写步骤
步骤1：确定Checker的功能
明确Checker要实现的功能：
污点追踪
调用图构建
代码质量检查
安全漏洞检测
等等
步骤2：选择合适的触发点
根据功能需求，选择合适的触发时机：
需要全局初始化 → triggerAtStartOfAnalyze
需要跟踪函数调用 → triggerAtFunctionCallBefore/ triggerAtFunctionCallAfter等
需要跟踪变量 → triggerAtPreDeclaration/triggerAtAssignment等
等等
步骤3：实现触发方法
在触发方法中实现检查逻辑：

[[CARD_06]]
```typescript
triggerAtFunctionCallBefore(analyzer: any, scope: any, node: any, state: any, info: any) {
const { fclos, argvalues } = info // 1. 获取相关信息

const functionName = fclos?.ast?.id?.name

// 2. 检查条件
if (isTargetFunction(functionName)) {
// 3. 执行检查逻辑
const finding = this.checkFunction(node, argvalues)

// 4. 记录结果
if (finding) {
this.resultManager.newFinding(finding, 'output_strategy_id')
}
}
}
```
步骤4：定义输出策略
如果需要自定义输出格式，实现OutputStrategy：

[[CARD_07]]
```typescript
class MyOutputStrategy extends OutputStrategy {
static outputStrategyId = 'my_output'

outputFindings(resultManager: any, outputFilePath: string, config: any, printf: any) {
// 输出逻辑
}
}
```
步骤5：注册Checker
在checker-config.json中注册Checker：

[[CARD_08]]
```json
{
"checkerId": "my_checker_id",
"checkerPath": "checker/my-checker.ts",
"description": "My custom checker"
}
```
如果您希望使用策略包，可以同时在checker-pack-config.json中注册Checker
注：污点追踪的checker使用，ruleconfig中的source/sink/sanitizer/entrypoint配置污点分析和ruleConfig配置部分。
了解更多Checker编写案例，您可以查看这里。
