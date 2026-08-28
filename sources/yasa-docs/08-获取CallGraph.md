---
title: "获取call graph"
slug: ahif12ik3vnapoin
source_url: https://www.yuque.com/u22090306/bebf6g/ahif12ik3vnapoin
updated_at: 2025-12-30T04:25:07.000Z
word_count: 475
image_count: 1
card_count: 5
---

# 获取call graph

执行命令

```plain
# 命令示例
/Users/yasa-macos-arm64
--dumpAllCG
--sourcePath /Users/xxx/ant-application-security-testing-benchmark
--language golang
--uastSDKPath /Users/uast4go
--report ./report
--cgAlgo CHA
```
说明：
执行go或则python语言分析时，需指定uast4go和uast4python的二进制路径。js已集成在yasa内，不需要指定
参数说明

```javascript
--help 打印帮助
--sourcePath 将要分析的目标文件
--language 设定语言，单选，目前支持'javascript', 'typescript', 'golang', 'python'
--analyzer 设定分析器，单选，目前支持 EggAnalyzer (Egg框架) | JavaScriptAnalyzer | GoAnalyzer（支持gin、mux、grpc、go-restful） | PythonAnalyzer (支持flask、Django、fastmcp、Triton框架)。如果设置了analyzer，就无需要再设置language
--report 指定输出报告目录（callgraph是目录）
--uastSDKPath go/python语言分析时必填，指定uast4go和uast4py的二进制路径
--dumpAllCG dump出全部的callgraph，输出callgraph.json
--cgAlgo 使用特定算法生成CG，现在可填CHA|DEFAULT，若不指定--cgAlgo，则使用模拟执行(DEFAULT模式)构建CG（更慢、更准）
```
预期输出示例
终端输出：

```plain
main file:/Users/main.js
source path: /Users/.../ant-application-security-testing-benchmark
Report directory: /Users/report
Analyze Language: golang
Analyze Analyer: GoAnalyzer
===================== Register rules ======================
Attention: no ruleConfig found
load checkers: [ 'callgraph' ]
===========================================================

start preProcess...
Attention: no ruleConfig found
makeAllCG-start
makeAllCG-10%
makeAllCG-30%
makeAllCG-70%
makeAllCG-100%
preProcess done...
preProcess cost: 961
[symbolInterpret]：EntryPoints are not found
start dump CG to /Users/report/callgraph.json
CG info is write to /Users/report/callgraph.json
analyze done
```
报告输出
未指定输出地点时，会默认输出到当前目录下

![image.png](https://cdn.nlark.com/yuque/0/2025/png/59228126/1757554134110-9b08f7c9-bf0b-4f23-b494-0017d69b5edd.png)
call graph结果说明

```json
{
nodes:{
key:{// key:函数签名摘要，包含位置关系,funcname [file : linenum]
id:key
opts:{
funcDef: fclos的AST，即fdef，可能为空，为空代表代码内没有其函数定义
funcSymbol: fclos符号值，不会为空
}
}
...
},
edges:{
key:{// key:函数调用语句的摘要，包含位置关系，为node1->node2
id:key
sourceNodeId: nodes1.id
targetNodeId: nodes2.id
opts:{
callSite: 调用点的ast
}
},
....
}
```
