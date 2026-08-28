---
title: "YASA-Engine设计"
slug: idrc3p344fz19h4g
source_url: https://www.yuque.com/u22090306/bebf6g/idrc3p344fz19h4g
updated_at: 2025-12-25T10:36:29.000Z
word_count: 1754
image_count: 0
card_count: 2
---

# YASA-Engine设计

总体架构

[图示文字：Analyze → js-analyze → go-analyze → ...... → egg-analyze → 分析器规则配置文件(rule_config) → 规则解析 rules-basic-handler → → 污点追踪分析器 → js-taint-checker → egg-taint-checker → go-taint-checker → ..... → 模拟执行引擎 → 分析器（checkers） → UAST → checkAtCompileUnit → checkAtNewExpr → checkAtIdentifier → checkAtIfCondition → 事件管理器 checkerManager → 结果管理resultManager → Sarif → console → 结果输出 → 事件注册 doRegister → 事件触发 → Java → JS → Go → Python → Framework → Lang → Base → 事件监听 → CG分析器 → JSON → .......]
总体分析流程
YASA对程序的分析，主要可分成以下四个环节：
将待分析的程序代码转换成UAST
该步骤主要是将编译器前端输出的特定格式AST结构数据转换成UAST统一表达，这部分会对具有相同语义的语法节点进行归一化，并且完成诸如：语法简化、改写等步骤。
基于UAST，进行符号解释
在符号解释过程中，会构建内存对象模型，并且管理执行时程序状态，如变量访问域scope、程序运行状态state（例如执行路径，callstack等）， 模拟执行会在执行程序点（checkpoint）触发各类事件。符号解释又整体分为两个步骤：
对代码库进行预处理，通过模拟执行分析包结构、类、函数、变量定义，建立符号值结构、包/模块结构、符号表等信息。
从entrypoint开始对程序进行模拟执行。
分析器监听事件，在模拟执行过程中执行对应的检测逻辑
分析器Checker一方面读取分析配置信息获取分析规则，另一方面通过获取当前程序点的上下文从而执行对应的检测逻辑（例如执行点处绑定的内存对象，程序状态及对应执行时的UAST节点信息），最后将分析结果记录。
依据分析器的配置，输出分析结果
符号解释引擎
符号化
YASA会在分析代码的过程中建立如下的符号值，不一定与AST节点一一对应，当然，有的表示变量值、函数定义的符号值、字面量等类型的符号值可以和AST节点进行对应。

```json
unit 符号值的基类
- ObjectValue 对象类型的符号值
- SymbolValue 未分析出指向变量的符号值
- Scoped 表示作用域的符号值
- PackageValue 包的符号值
- FunctionValue 函数的符号值
- PrimitiveValue 字面量类型的符号值
- UndefinedValue 空符号值
- UninitializedValue 未初始化变量的符号值
- UnionValue 组合类型的符号值
- BVT 带有分支路径信息的符号值
```
模拟执行
“模拟执行”即模拟程序的执行，指的是分析引擎模拟程序的“动态”执行过程，一步一步的分析，直至程序结束。包含对代码的符号化（抽象）以及对程序行为的模拟（解释）。
YASA使用analyzer进行模拟执行。分为基础analyzer、语言层analyzer和框架层analyzer。基础analyzer承载了70%符号解释的能力，是YASA多语言统一分析并快速扩展新语言的基础，语言层analyzer和框架层analyzer继承自基础analyzer，是针对特定语言/框架内的特定语法与设计等进行的符号解释上的适配，如包管理适配、方言的语法糖适配等。在模拟执行过程中，YASA会构造内存空间（Scope），将程序模拟执行的过程和状态（如变量/参数类型、分支、value、污点标记）等信息记录，在检查器checker触发时进行使用。程序空间会由analyzer与checker共同影响。
需要注意的是，与程序真实运行相比，模拟执行主要有如下几个区别：
（1）模拟执行过程中，符号值中存储的不是concrete value，而是符号值（symbolic value）
（2）不同于“符号执行”技术会对程序分支进行求解并选择一条分支进行分析，YASA的模拟执行会分析每一条分支，并保存每条分支的模拟执行信息。
模拟执行过程
在模拟执行过程中，会构建内存对象模型，并且管理执行时程序状态，如变量访问域scope、程序运行状态state（例如执行路径，callstack等）， 模拟执行会在执行程序点（checkpoint）触发各类事件。整体分为两个步骤：
对代码库进行预处理，通过模拟执行分析包结构、类、函数、变量定义，建立符号值结构、包/模块结构、符号表等信息。
从entrypoint开始对程序进行模拟执行。此时在污点分析checker中，会进行污点匹配、sink匹配等操作。污点也会随着模拟执行在符号值中流转传播。
为什么要分成预处理和entrypoint开始的模拟执行
直接对程序的每一个函数都进行执行分析是不合理的，需要优先对程序进行整体的符号分析，才能处理import等包引入语句，完成模块之间的数据联通。构建整个代码库整体的符号值树，以便可以完成跨文件/跨包的分析。
代码库不是每一个函数都会被调用到的，如web框架的router，并不存在显式调用的地方，直接模拟程序文件的执行是不会访问到的，因此需要指定其为entrypoint来进行分析。
EntryPoint设计
entrypoint在YASA中是脱离于checker存在的，虽然它更多的在checker中被指定与消费。它表明YASA对程序模拟执行的入口。YASA当前对entrypoint有三种使用策略：
ONLY_CUSTOM: 只选用用户在rule_config中指定的entrypoint进行模拟执行。
SELF_COLLECT：只选用YASA自采集的entrypoint进行模拟执行。YASA的entrypoint采集会在startofAnalyze阶段进行，在checker中的triggerAtStartOfAnalyze中进行采集。
当前entrypoint采集的策略：
YASA支持框架的entrypoint采集：egg（js）、gin（go）、mux（go）、grpc（go）、go-restful（go）、flask（python）、django（python）、mcp（python）、Triton（python）、Spring MVC（Java）
默认entrypoint采集策略：完整callgraph的边界、所有file的第一行（解释型语言会选用，如python、js）。使用getAllEntryPointsUsingCallGraph、getAllFileEntryPointsUsingFileManager 即可
注：自采集行为不是全部分析都会默认触发，而是在checker中的triggerAtStartOfAnalyze中进行使用，可以看各language的污点追踪default checker来参考。
BOTH：包含用户在rule_config中指定的entrypoint进行模拟执行与YASA自采集的entrypoint。
多语言语义建模
详见[这里](https://www.yuque.com/u22090306/bebf6g/mucotdkpwzg1gn8e)
