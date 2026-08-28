---
title: "案例一-Go语言mux框架支持checker"
slug: kf9yhos9qxhtflos
source_url: https://www.yuque.com/u22090306/bebf6g/kf9yhos9qxhtflos
updated_at: 2025-12-17T03:47:38.000Z
word_count: 1067
image_count: 0
card_count: 8
---

# 案例一-Go语言mux框架支持checker

本文将以实际例子展示，如何从零开始实现并注册一个checker实现go语言mux框架支持。
step 1️⃣：创建并配置checker类
首先，您需要新建一个xxx_checker.js，并配置checker类的必要信息。checkerManager以checkerId唯一标识一个checker，故新建checker时，您需要设置唯一的checkerId，并只需继承基类Checker即可。本例中，checkerId为gorilla-mux-entrypoint-collect-checker

```javascript
//gorilla-mux-entrypoint-collect-checker.js
class MuxEntryPointCollectChecker extends Checker {
/**
* constructor
* @param resultManager
*/
constructor(resultManager) {
super(resultManager, 'gorilla-mux-entrypoint-collect-checker')
}

//不同事件处理逻辑...
}
```
随后，您需要将定义的checker添加到resource/checker/checker-config.json中，其中checkerPath为您定义的checker相对YASA-Engine的项目根目录。

```json
...
{
"checkerId": "gorilla-mux-entrypoint-collect-checker",
"checkerPath": "src/checker/taint/go/gorilla-mux-entrypoint-collect-checker.ts",
"description": "Mux entryPoint采集以及框架source添加"
},
...
```
YASA 除了支持指定单一checker独立执行外，也支持以checker-pack的形式绑定多个checker一并执行。若您希望该checker可以和其他checker绑定一并执行，那么可以同步将该checker添加到resource/checker/checker-pack-config.json中，例如：

```json
{
"checkerPackId": "taint-flow-golang-default",
"checkerIds": [
"taint_flow_gin_input",
"taint_flow_go_input",
"cobra.Command-builtIn",
"gorilla-mux-entrypoint-collect-checker",
"gRpc-entryPoint-collect-checker",
"go-main-entryPoints-collection",
"sync.Once.Do-builtIn",
"urfave-cli-builtIn",
"callgraph",
"sanitizer"
],
"description": "golang污点追踪-对外默认使用规则包"
},
```
您所定义的checker可以通过命令行参数的形式指定具体执行生效方式。具体指定方式可参考：
|
参数名
|
参数说明
|
--checkerIds
|
指定需加载的checker列表
|
--checkerPackIds
|
指定需加载的checkerPackId列表
初始化时，checkerManager会扫描基于您传入的参数，注册相应的checker或checker-pack。
例如，您所注册的checker可以在命令行通过传入参数 --checkerIds gorilla-mux-entrypoint-collect-checker指定独立执行，也可以将通过传入参数 --checkerPackIds taint-flow-golang-default和该checker-pack下其他checker绑定配合使用。
step 2️⃣：实现web框架适配逻辑
要做的事：选取合适的生命周期事件 & 实现该事件的处理逻辑
以mux框架为例，典型的路由注册方式如下，其中r.HandleFunc()为函数调用语句：

```go
r := mux.NewRouter()
// 注册 GET 请求路由，HandlerFClos即被注册的api处理函数(我们要的entrypoint)
r.HandleFunc("/api_path",HandlerFClos).Methods("GET")
```
故：
应该选取的生命周期事件为：FunctionCallBefore (函数调用事件)
事件处理逻辑为：如果当前语句是一条路由注册语句，则将被注册的路由函数采集为一个entrypoint，并将参数标记为source。

```javascript
// gorilla-mux-entrypoint-collect-checker.js

// 在函数调用时check，是否是一句函数调用语句
triggerAtFunctionCallBefore(analyzer, scope, node, state, info) {
const { fclos, argvalues } = info
this.collectRouteRegistry(node, fclos, argvalues, scope, info)
}
```

```javascript
// gorilla-mux-entrypoint-collect-checker.js
collectRouteRegistry(callExpNode, calleeFClos, argValues, scope, info) {
const { analyzer, state } = info
// 用户不开启路由自采集模式
if (config.entryPointMode === 'ONLY_CUSTOM') return

// 判空，减少不必要匹配
if (!(calleeFClos && calleeFClos.object && calleeFClos.property)) return
const { object, property } = calleeFClos
if (!object._qid || !property.name) return
const objectQid = object._qid
const propertyName = property.name

// 关键：用来判断当前语句是否是mux框架的路由注册语句
// mux中的注册语句形如object.property，其中object的全类名以'github.com/gorilla/mux.NewRouter()'开头，prop为'HandleFunc'
if (
RouteRegistryObject.some((muxPrefix) => objectQid.startsWith(muxPrefix)) &&
RouteRegistryProperty.includes(propertyName)
) {
// 若是路由注册语句，取出参数中的函数定义
for (const arg of argValues) {
if (arg?.vtype === 'fclos' && arg?.ast.loc) {
// 避免重复采集同一个entrypoint
const hash = JSON.stringify(arg.ast.loc)
if (!processedRouteRegistry.has(hash)) {
processedRouteRegistry.add(hash)

// 将entrypoint的特定位置参数标记为source
IntroduceTaint.introduceFuncArgTaintBySelfCollection(arg, state, analyzer, '1:', 'GO_INPUT')
// 作为一个entrypoint函数添加
const entryPoint = completeEntryPoint(arg)
analyzer.entryPoints.push(entryPoint)
}
}
}
}
}
```
如<[Checker的注册](https://www.yuque.com/u22090306/bebf6g/lwe1xqg1nw1gh1u8#w66yK)>中所述，只要您在checker中实现某个事件处理函数(如triggerAtFunctionCallBefore)，CheckerManager就会自动将该checker注册至对应的事件(如check_at_function_call_before)。

```javascript
// checker-manager.js
doRegister(CheckerClass, self, resultManager) {
...
// 注册check_at_function_call_before事件的checker
if (CheckerClass.prototype.triggerAtFunctionCallBefore) {
self.checkpoints.check_at_function_call_before.push(checker)
}
}
```
在该事件发生时，您的checker会从该事件的注册表中取出，并执行您定义的事件处理函数triggerAtFunctionCallBefore。

```javascript
// checker-manager.js
checkAtFunctionCall(node, calleeFClos, argvalues, scope, info) {
...
// 取出当前checkPoint的所有checker，依次执行事件处理函数(triggerAtFunctionCall)
const { check_at_function_call_before } = this.checkpoints
for (const i in check_at_function_call_before) {
if (this.isCheckOn(check_at_function_call_before[i].getCheckerId())) {
check_at_function_call_before[i].triggerAtFunctionCallBefore(analyzer, scope, node, state, info)
stat.numChecks++
}
}
}
```
