---
title: "YASA-UAST设计"
slug: wtucc3wf7gzwkuhs
source_url: https://www.yuque.com/u22090306/bebf6g/wtucc3wf7gzwkuhs
updated_at: 2025-12-11T06:20:10.000Z
word_count: 1464
image_count: 0
card_count: 4
---

# YASA-UAST设计

什么是UAST
UAST全称为统一语法树中间表示（Unified Abstract Syntax Tree ），即将不同语言的代码解析为一套统一的中间表达，以便在此基础上进行通用的分析能力建设。
UAST节点描述链接：[点我跳转](https://github.com/antgroup/YASA-UAST/blob/main/specification/specification.md)

例如，针对同样语义使用Java/Javascript/Python三种语言编写的一段类定义代码，在UAST上将会被统一转换为：

[图示文字：CompileUnit → ClassDefinition → VariableDeclaration name → FunctionDefinition _CTOR_ → FunctionDefinition getName → AssignmentExpression → MemberAccess → ThisExpression → Identifier name → ReturnStatement → UAST Parser]
UAST设计原则
极大元选取
如果不同的语法节点有语义包含关系，在归一化过程当中，倾向选择最大包含关系的节点
|
高级循环迭代方式
|
语言
|
示例
|
定义
|
java
|
for(element: elements) {
}
|
interface RangeStatement <: Statement {
type: "RangeStatement";
key: Expression | null;
value: Expression | null;
right: Expression;
body: Statement;
}
|
js
|
for (index in elements) {
}
|
golang
|
for i, v := range arr {
}
去语法糖
去除语言特有语法糖，保持UAST节点的简洁
|
语法糖拆解
|
语言
|
示例
|
UAST 去糖(desugar)
|
js
|
let { x, y } = init;
|
VarDecl tmp = init;
VarDecl x = tmp.x;
VarDecl y = tmp.y;
|
python
|
[i for i in range(k) if condition]
|
(()=>{
VarDecl tmpList = [];
for(VarDecl i=0; i<len(k); i++) {
if (condition) {
tmpList.push(i);
}
}
return tmpList;
})()
设计权衡
权衡一-通用性和语言特性
挑战：如何在保持通用性的同时，不丢失重要的语言特性？
解决方案：
核心结构统一（通过统一节点类型）
语言特性保留（通过meta字段）
明确设计边界（只保留分析需要的信息）
示例：

```json
// 注解信息可通过meta字段保留,例如python的@property
{
"type": "FunctionDefinition",
"_meta": {
"decorators": [
{
"type": "Identifier",
"name": "property"
}
]
}
}
```
权衡二-简单性和完整性
重要概念：UAST的转换本质是一种有损统一抽象
含义：
不同语言的语法语义信息在程序分析层面进行有损统一抽象
目的是用尽可能简单的语法信息做统一表达
与程序分析无关的信息会被去掉
UAST节点结构介绍
节点基本结构
每个UAST节点包含以下基本字段：

```json
{
"type": "节点类型",
"loc": {
"sourcefile": "源文件路径",
"start": { "line": 行号, "column": 列号 },
"end": { "line": 行号, "column": 列号 }
},
"
"_meta": {
// 语言特定的元数据，补充信息等，不同语言可以自行扩展
},
// 节点特定的字段...
}
```
常见节点
UAST 定义了 50+ 种节点类型，主要包括：
基础节点
Noop：空操作节点
Literal：字面量（null、number、string、boolean）
Identifier：标识符
CompileUnit：编译单元（文件级别）
控制流节点
IfStatement：条件语句
SwitchStatement：开关语句
ForStatement：for 循环
WhileStatement：while 循环
RangeStatement：范围循环（for-range）
BreakStatement / ContinueStatement：跳转语句
ReturnStatement：返回语句
TryStatement / CatchClause：异常处理
表达式节点
BinaryExpression：二元表达式
UnaryExpression：一元表达式
AssignmentExpression：赋值表达式
CallExpression：函数调用
NewExpression：对象创建
MemberAccess：成员访问
ConditionalExpression：条件表达式
Sequence：序列表达式
ImportExpression：导入表达式
ExportStatement：导出语句
ObjectExpression / ObjectProperty：对象表达式
TupleExpression：元组表达式
SliceExpression：切片表达式
SpreadElement：展开元素
YieldExpression：生成器表达式
ThisExpression / SuperExpression：this/super 表达式
DereferenceExpression / ReferenceExpression：解引用/引用表达式
CastExpression：类型转换表达式
声明节点
FunctionDefinition：函数定义
ClassDefinition：类定义
VariableDeclaration：变量声明
PackageDeclaration：包声明
类型节点
PrimitiveType：基本类型
ArrayType：数组类型
PointerType：指针类型
MapType：映射类型
FuncType：函数类型
TupleType：元组类型
ChanType：通道类型（Go）
ScopedType：作用域类型
DynamicType：动态类型
VoidType：空类型
解析器
为了快速支持新语言到UAST，目前UAST 解析器的实现方式为针对每一种语言，选用业界支持较好的解析器生成AST，并将其进一步转化为UAST。目前已支持的解析器包括Java、Js、Go、Python四种语言。
UAST解析器：[点我跳转](https://github.com/antgroup/YASA-UAST/)

[图示文字：source code(js ) → source code(golang) → source code(xxx) → . . . → AST → UAST Parser → UAST-Node → → js AST parser → golang AST parser → xxx AST parser → UAST-Spec]
技术选型 - 两种方案
方案一：第三方解析工具
代表：ANTLR、Tree-sitter等
缺点
❌ 需要维护语法文件：语法更新需要手动跟进和维护
❌ 实时性和准确性不佳：可能存在解析延迟或精度问题
优点
✅ 便于管理和维护：统一框架和实现语言，无需不同语言分别维护
✅ 灵活度高：可自定义语法
方案二：语言官方Parser
代表：Go的go/parser、Python的ast模块
缺点
❌ 不利于统一管理：不同语言的parser需使用不同的语言来实现
优点
✅ 稳定性保障：经过充分验证，可靠性高
✅ 语法更新同步：及时跟进语言新版本
✅ 解析精度：对语言特性支持更完整
✅ 维护成本低：无需维护语法文件

技术选型原则
核心原则：
优先使用官方parser，如果官方不提供或不够完善，则选择成熟的第三方工具
判断标准：
✅ 官方是否提供稳定的parser API？
✅ 官方parser是否功能完善？
✅ 第三方工具是否成熟可靠？
✅ 维护成本如何？

基于这个原则，我们在四种语言的技术选型为：
|
语言
|
AST parser
|
UAST parser
|
Go
|
go/parser（官方）
|
parser-Go
|
Java
|
ANTLR4
|
parser-Java-Js
|
JavaScript/TypeScript
|
Babel
|
parser-Java-Js
|
Python
|
ast模块（官方）
|
parser-Python
