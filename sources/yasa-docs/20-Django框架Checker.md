---
title: "案例二-Python语言Django框架支持Checker"
slug: tsxs2vcvs5aq5xym
source_url: https://www.yuque.com/u22090306/bebf6g/tsxs2vcvs5aq5xym
updated_at: 2025-12-17T13:28:08.000Z
word_count: 2482
image_count: 0
card_count: 17
---

# 案例二-Python语言Django框架支持Checker

需求分析
功能需求
需要实现一个Django框架的污点分析Checker，能够：
自动识别Django路由入口点
识别Django的urls.py配置文件
解析urlpatterns路由配置
支持path、re_path、url三种路由定义方式
支持函数视图（Function-based Views）和类视图（Class-based Views）
自动识别污点源（Source）
从路由参数中提取URL参数名
将URL参数标记为污点源
支持Django的URL参数模式（如<int:id>、<str:name>等）
污点流追踪
追踪从URL参数到危险操作（Sink）的数据流
技术挑战
Django路由配置的多样性
路由可以定义在多个urls.py文件中
支持函数视图和类视图两种方式
类视图需要调用as_view()方法
路由参数可以从URL路径中提取
污点源的精确识别
URL参数名需要从路由字符串中提取
需要将参数名映射到视图函数的参数
支持不同类型的URL参数（int、str等）
设计方案
架构设计
Django Checker采用分层设计：

```plain
DjangoTaintChecker (Django特定逻辑)
↓ 继承
PythonTaintAbstractChecker (Python通用污点逻辑)
↓ 继承
TaintChecker (污点分析基类)
↓ 继承
Checker (Checker基类)
```
核心流程设计

```plain
1. 识别urls.py文件
↓
2. 解析urlpatterns配置
↓
3. 提取路由定义（path/re_path/url）
↓
4. 识别视图函数/类
↓
5. 提取URL参数名
↓
6. 创建EntryPoint并标记Source
↓
7. 污点流追踪
```
关键技术点
路由识别策略
文件识别：通过文件名urls.py识别
导入识别：检查是否导入了django.urls相关模块
变量识别：识别urlpatterns变量
视图识别策略
函数视图：直接识别函数引用
类视图：识别as_view()调用，提取类中的HTTP方法
参数提取策略
正则表达式：使用正则表达式从路由字符串中提取参数名
详细实现
类结构设计

```typescript
const registerFile = new Set<string>() // 注册的urls.py文件集合
class DjangoTaintChecker extends PythonTaintAbstractChecker {
// 核心方法
triggerAtCompileUnit() // 识别urls.py文件
triggerAtPreDeclaration() // 处理urlpatterns变量声明
triggerAtAssignment() // 处理urlpatterns赋值
}
```
实现步骤详解
步骤1：识别Django的urls.py文件
触发点：triggerAtCompileUnit
实现逻辑：

```typescript
triggerAtCompileUnit(analyzer: any, scope: any, node: any, state: any, info: any) {
const fileName = node.loc?.sourcefile
if (!fileName) return
// 1. 检查文件名是否为urls.py
if (!fileName.endsWith('/urls.py')) return

// 2. 检查是否导入了Django相关模块
node.body.forEach((exp: any) => {
if (exp.type === 'VariableDeclaration') {
if (exp.init.type !== 'ImportExpression') return
const str = AstUtil.prettyPrint(exp)
// 检查导入语句是否包含django.urls
if (str.includes('django') && str.includes('urls') &&
(str.includes('re_path') || str.includes('path'))) {
registerFile.add(fileName) // 注册该文件
} else if (str.includes('django') && str.includes('conf') &&
str.includes('urls') && str.includes('url')) {
registerFile.add(fileName) // 兼容旧版本django.conf.urls.url
}
}
})
}
```
关键点：
通过文件名后缀识别urls.py
通过导入语句确认是Django项目
支持新版本（django.urls.path）和旧版本（django.conf.urls.url）
示例代码：

```python
# urls.py
from django.urls import path, re_path
from django.conf.urls import url # 旧版本
```
步骤2：识别urlpatterns变量
触发点：triggerAtAssignment
实现逻辑：

```typescript
// 处理 urlpatterns = [...]和urlpatterns += [...]
triggerAtAssignment(analyzer: any, scope: any, node: any, state: any, info: any): boolean | undefined {
const fileName = node.loc?.sourcefile
if (!fileName) return
if (registerFile.size === 0 || !registerFile.has(fileName)) {
return
}

if (node.left.name === 'urlpatterns') {
const { right } = node
this.collectDjangoEntrypointAndSource(analyzer, scope, state, right)
}
}
```
关键点：
同时处理初始声明和增量赋值
只处理已注册的urls.py文件中的urlpatterns
示例代码：

```python
# urls.py
urlpatterns = [
path('user/<int:id>', views.user_detail),
]

# 增量添加路由
urlpatterns += [
path('admin/', admin.site.urls),
]
```
步骤3：解析路由配置
核心方法：collectDjangoEntrypointAndSource
实现逻辑：

```typescript
collectDjangoEntrypointAndSource(analyzer: any, scope: any, state: any, value: any) {
const elementGroups: any[] = []
// 1. 从AST节点中提取所有路由元素
this.extractElementsFromNode(elementGroups, value)

// 2. 遍历每个路由元素
for (const element of elementGroups) {
if (element.type === 'CallExpression' && element.callee) {
const { callee } = element

// 3. 识别路由函数名（path/re_path/url）
let methodName: string | null = null
if (callee.type === 'MemberAccess' && callee.property?.name) {
// 处理 django.urls.path 形式
methodName = callee.property.name
} else if (callee.type === 'Identifier') {
// 处理直接导入的 path 形式
methodName = callee.name || null
}

// 4. 只处理path/re_path/url三种路由函数
if (methodName !== 'path' && methodName !== 're_path' && methodName !== 'url') {
continue
}

// 5. 获取路由参数
if (element.arguments && element.arguments.length >= 2) {
// 第一个参数：路由字符串，如 'user/<int:id>'
const targetSrcName = this.extractParamNames(element.arguments[0].value)
// 第二个参数：视图函数或类
const viewFunction = element.arguments[1]

// 6. 根据视图类型分别处理
if (viewFunction.type === 'Identifier' || viewFunction.type === 'MemberAccess') {
// 函数视图
this.collectFuncViewEntrypointAndSource(
analyzer, scope, state, viewFunction, targetSrcName
)
} else if (viewFunction.type === 'CallExpression' && viewFunction.callee) {
// 类视图（通过as_view()调用）
if (viewFunction.callee.type === 'MemberAccess' &&
viewFunction.callee.property.name === 'as_view') {
this.collectClassViewEntrypointAndSource(
analyzer, scope, state, viewFunction, targetSrcName
)
}
}
}
}
}
}
```
关键点：
支持数组和二元表达式（urlpatterns = [] + [...]）
识别三种路由函数：path、re_path、url
区分函数视图和类视图
示例代码：

```python
# urls.py
urlpatterns = [
# 函数视图
path('user/<int:id>', views.user_detail),
# 类视图
path('article/<int:pk>', ArticleView.as_view()),
# 正则路由
re_path(r'^articles/(?P<year>[0-9]{4})/$', views.year_archive),
]
```
步骤4：提取URL参数名
核心方法：extractParamNames
实现逻辑：

```typescript
extractParamNames(route: string): string[] {
// 匹配 <type:param> 或 <param> 格式
// 例如：'user/<int:id>' 匹配到 'id'
// 'article/<slug:slug>' 匹配到 'slug'
const regex = /<(?:(?:\w+):)?(\w+)>/g
const params: string[] = []
let match: RegExpExecArray | null
while ((match = regex.exec(route)) !== null) {
params.push(match[1]) // 提取参数名
}
return params
}
```
正则表达式说明：
<(?:(?:\w+):)?(\w+)> 匹配：
<int:id> → 提取 id
<str:name> → 提取 name
<slug> → 提取 slug
<year> → 提取 year
示例：

```python
# 路由：'user/<int:id>/profile/<str:name>'
# 提取参数：['id', 'name']
```
步骤5：处理函数视图
核心方法：collectFuncViewEntrypointAndSource
实现逻辑：

```typescript
collectFuncViewEntrypointAndSource(
analyzer: any,
scope: any,
state: any,
viewFunction: ASTObject,
targetSrcName: string[]
) {
// 1. 解析视图函数，获取函数定义
const ep = analyzer.processInstruction(scope, viewFunction, state)
if (ep.vtype === 'fclos') {
// 2. 创建EntryPoint
analyzer.entryPoints.push(completeEntryPoint(ep))

// 3. 如果路由中有参数，标记为污点源
if (targetSrcName.length > 0) {
const targetName = targetSrcName[0] // 取第一个参数名
// 4. 在函数参数中查找匹配的参数
for (const param of ep.fdef.parameters) {
if (param.id.name === targetName) {
// 5. 添加污点源，后续在处理该参数时则会被标记为污点
this.sourceScope.value.push({
path: param.id.name,
kind: 'PYTHON_INPUT',
scopeFile: extractRelativePath(param?.loc?.sourcefile, Config.maindir),
scopeFunc: ep.fdef?.id?.name,
locStart: param.loc.start.line,
locEnd: param.loc.end.line,
})
}
}
}
}
}
```
关键点：
使用analyzer.processInstruction解析视图函数引用
将URL参数名映射到函数参数
创建EntryPoint并标记污点源
示例代码：

```python
# urls.py
urlpatterns = [
path('user/<int:id>', views.user_detail),
]

# views.py
def user_detail(request, id): # id参数会被标记为污点源
user = User.objects.get(id=id) # 污点流追踪
return render(request, 'user.html', {'user': user})
```
步骤6：处理类视图
核心方法：collectClassViewEntrypointAndSource
实现逻辑：

```typescript
collectClassViewEntrypointAndSource(
analyzer: any,
scope: any,
state: any,
viewFunction: ASTObject,
targetSrcName: string[]
) {
// 1. 提取类对象
const clsObj = viewFunction.callee.object
const clsSymVal = analyzer.processInstruction(scope, clsObj, state)

// 2. 定义HTTP方法集合
const httpMethods = new Set(['get', 'post', 'put', 'delete', 'patch', 'head', 'options'])

// 3. 从类中提取所有HTTP方法
const entrypoints = Object.entries(clsSymVal.value)
.filter(([key, value]: [string, any]) =>
httpMethods.has(key) && value.vtype === 'fclos'
)
.map(([, value]: [string, any]) => value)

// 4. 如果有URL参数，为每个HTTP方法标记污点源
if (targetSrcName.length > 0) {
const targetName = targetSrcName[0]
for (const ep of entrypoints as any[]) {
// 在方法参数中查找匹配的参数
for (const param of ep.fdef.parameters) {
if (param.id.name === targetName) {
this.sourceScope.value.push({
path: param.id.name,
kind: 'PYTHON_INPUT',
scopeFile: extractRelativePath(param?.loc?.sourcefile, Config.maindir),
scopeFunc: ep.fdef?.id?.name,
locStart: param.loc.start.line,
locEnd: param.loc.end.line,
})
}
}
// 创建EntryPoint
analyzer.entryPoints.push(completeEntryPoint(ep))
}
} else {
// 没有URL参数，直接创建EntryPoint
for (const ep of entrypoints as any[]) {
analyzer.entryPoints.push(completeEntryPoint(ep))
}
}
}
```
关键点：
识别类视图的as_view()调用
提取类中的所有HTTP方法（get、post等）
为每个HTTP方法创建EntryPoint
支持URL参数映射到类方法参数
示例代码：

```python
# urls.py
urlpatterns = [
path('article/<int:pk>', ArticleView.as_view()),
]

# views.py
class ArticleView(View):
def get(self, request, pk): # pk参数会被标记为污点源
article = Article.objects.get(pk=pk)
return render(request, 'article.html', {'article': article})

def post(self, request, pk): # pk参数会被标记为污点源
# ...
pass
```
步骤7：注册到checker-config.json和checker-pack-config.json
实现Checker后，需要将其注册到YASA的Checker配置系统中，这样YASA才能识别和加载该Checker。
Checker配置文件位于：resource/checker/checker-config.json
在配置数组中添加新的配置项：

```json
{
"checkerId": "taint_flow_python_django_input",
"checkerPath": "checker/taint/python/django-taint-checker.ts",
"description": "python Django框架 entrypoint采集以及框架source添加"
}
```
配置项说明：
checkerId：Checker的唯一标识符，必须与Checker类构造函数中的ID一致
格式：通常使用下划线分隔的命名方式
示例：taint_flow_python_django_input
注意：必须与DjangoTaintChecker构造函数中的super(resultManager, 'taint_flow_python_django_input')保持一致
checkerPath：Checker文件的相对路径（相对于项目根目录）
路径格式：checker/taint/python/django-taint-checker.ts
注意：路径不需要包含src/前缀，YASA会自动处理
description：Checker的描述信息
用于说明Checker的功能和用途
会在日志和帮助信息中显示
demoRuleConfigPath（可选）：示例规则配置文件的路径
如果提供了示例配置，可以帮助用户快速上手
示例："demoRuleConfigPath": "resource/example-rule-config/rule_config_python.json"
如果您希望以checker策略包的方式使用，可以同步将您的checker添加到checker-pack-config.json中

```json
{
"checkerPackId": "taint-flow-python-default",
"checkerIds": [
"taint_flow_python_input",
"taint_flow_python_django_input",
"callgraph",
"sanitizer"
],
"description": "python污点追踪-对外默认使用的规则包"
},
```
继承关系说明
PythonTaintAbstractChecker
DjangoTaintChecker继承自PythonTaintAbstractChecker，复用了以下功能：
污点标记：
triggerAtIdentifier：在标识符访问时标记污点
triggerAtFunctionCallBefore：在函数调用前处理污点
triggerAtFunctionCallAfter：在函数调用后处理返回值污点
Sink检测：
checkByNameMatch：通过函数名匹配Sink
checkByFieldMatch：通过字段匹配Sink
findArgsAndAddNewFinding：查找污点参数并生成Finding
污点源管理：
sourceScope：管理污点源作用域
污点标签：PYTHON_INPUT
TaintChecker基类
提供污点分析的基础功能：
Finding构建
污点流追踪
结果输出
