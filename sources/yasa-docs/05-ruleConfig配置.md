---
title: "ruleConfig配置"
slug: zkw8i3ffw8n884sd
source_url: https://www.yuque.com/u22090306/bebf6g/zkw8i3ffw8n884sd
updated_at: 2026-03-13T09:04:56.000Z
word_count: 3162
image_count: 0
card_count: 41
---

# ruleConfig配置

ruleconfig是YASA中为checker提供用户指定的输入的配置模块，通过一个json文件指定，在YASA中每一个需要用户指定信息的checker（如污点追踪需要source、sink等）都会自动去加载ruleconfig中的配置。
污点追踪场景需要用户提供的source、sink、sanitizer以及自定义entrypoint的配置如下。也可以参考YASA源码中的resource/example-rule-config 目录中的ruleconfig示例。

[[CARD_01]]
```json
[
{
"checkerIds": [
...
],
"sources":{
"FuncCallReturnValueTaintSource": [
{
...
}
],
"FuncCallArgTaintSource": [
{
...
}
],
"TaintSource": [
{
...
}
]
},
"sinks":{
"FuncCallTaintSink": [
{
...
}
]
},
"sanitizers": [
{
...
}
],
"entrypoints": [
{
...
}
]
},
]
```
关于ruleconfig与checker的更多介绍，见这里。
checkerIds
checkerIds 是 rule-config.json 配置文件中的一个必需字段，用于指定当前规则配置对哪些安全检查器（Checker）生效。需要和您执行污点追踪命令时传入的--checkerIds或--checkerPackIds参数对应。该字段将规则配置与特定的检查器进行关联，确保每个检查器只加载和使用与其相关的规则。

[[CARD_02]]
```json
{
"checkerIds": ["checker_id_1", "checker_id_2", "checker_id_3"]
}
```
工作原理
规则匹配: 当 YASA 引擎加载规则配置时，会检查每个规则配置对象的 checkerIds 字段
检查器关联: 如果某个检查器的 ID 在 checkerIds 数组中，则该规则配置会被加载到该检查器
配置合并: 一个检查器可以匹配多个规则配置，这些配置会被合并使用
内置checker
请参考这里
使用场景
场景 1: 单一检查器配置
为单个检查器配置规则：

[[CARD_03]]
```json
[
{
"checkerIds": ["taint_flow_python_input"],
"sources": { ... },
"sinks": { ... }
}
]
```
场景 2: 多检查器共享配置
多个检查器共享相同的规则配置：

[[CARD_04]]
```json
[
{
"checkerIds": [
"taint_flow_python_input",
"taint_flow_python_input_inner",
"taint_flow_python_django_input"
],
"sources": { ... },
"sinks": { ... }
}
]
```
场景 3: 分离配置
为不同的检查器配置不同的规则：

[[CARD_05]]
```json
[
{
"checkerIds": ["taint_flow_java_input"],
"sources": { ... },
"sinks": { ... }
},
{
"checkerIds": ["taint_flow_spring_input"],
"sources": { ... },
"sinks": { ... }
}
]
```
注意事项
ID 必须匹配: checkerIds 中的 ID 必须与系统中注册的检查器 ID 完全匹配，否则该规则配置不会被加载
区分大小写: 检查器 ID 区分大小写，请确保拼写正确
数组格式: 即使只有一个检查器，也必须使用数组格式：["checker_id"]，而不是字符串格式
配置合并: 如果多个规则配置包含相同的 checkerId，它们的配置会被合并，后加载的配置会覆盖先加载的配置（取决于合并策略）
source
支持的source形式
目前支持指定三种形式的source，分别体现在rule-config的三个字段中：TaintSource、FuncCallArgTaintSource和FuncCallReturnValueTaintSource

[[CARD_06]]
```json
"sources": {
"TaintSource": [
{
...
}
],
"FuncCallArgTaintSource": [
{
...
}
],
"FuncCallReturnValueTaintSource": [
{
...
}
]
}
```
TaintSource (对象属性访问污点源)
触发时机：成员访问时（triggerAtMemberAccess）
作用：直接标记某个变量或者某个类型对象的特定属性为source
配置示例：

[[CARD_07]]
```json
{
"className": "*gin.Context", // 对象类型（可填）
"path": "Params", // 属性路径/字段名
"kind": "GO_INPUT" // 污点标签类型
}
```
工作原理：当访问 *gin.Context 类型的 Params 属性时（如 ctx.Params），将结果值标记为污点源
FuncCallArgTaintSource (函数调用参数source)
触发时机：函数调用前（triggerAtFunctionCallBefore）
作用：将函数调用的指定参数标记为source
配置示例：

[[CARD_08]]
```json
{
"args": ["0"], // 指定第0个参数（第一个参数）
"calleeType": "*gin.Context", // 调用对象的类型
"fsig": "BindJSON", // 函数签名
"kind": "GO_INPUT" // 污点标签类型
}
```
工作原理：当检测到 *gin.Context 类型的对象调用 BindJSON 方法时，将第一个参数（索引0）标记为污点源
FuncCallReturnValueTaintSource (函数返回值污点源)
触发时机：函数调用后（triggerAtFunctionCallAfter）
作用：将函数调用的返回值标记为source
配置示例：

[[CARD_09]]
```json
{
"calleeType": "*gin.Context", // 调用对象的类型
"fsig": "Query", // 函数签名
"kind": "GO_INPUT", // 污点标签类型
"values": ["0"] // 返回值索引（通常为["0"]）
}
```
工作原理：当检测到 *gin.Context 类型的对象调用 Query 方法时，将返回值标记为source
总结对比
|
类型
|
触发时机
|
标记对象
|
配置关键字
|
TaintSource
|
变量访问时
|
函数参数
|
className, path, kind
|
FuncCallArgTaintSource
|
函数调用前
|
变量或者某个类型对象的属性
|
args, calleeType, fsig, kind
|
FuncCallReturnValueTaintSource
|
函数调用后
|
函数返回值
|
calleeType, fsig, values, kind
使用场景
对象的名称_全局
代码示例

[[CARD_10]]
```plain
export default class LevelTestBank extends Controller {
async bankTest(advisorId, instId): Promise<any> {
const req: any = this.ctx.query.a; // this.ctx.query是source
this.ctx.body = await this.ctx.proxy.xxxListFacade.queryList(req);
return this.ctx.body;
}
}
```
source配置

[[CARD_11]]
```plain
"TaintSource": [
{
"path": "this.ctx.query",
"scopeFile": "all",
"scopeFunc": "all"
},
...
]
```
对象的名称_特定范围
代码示例

[[CARD_12]]
```plain
import { Controller } from 'chain';

export default class LevelTestBank extends Controller {
async bankTest(advisorId, instId): Promise<any> { //advisorId是source
const req: any = this.ctx.query.a;
this.ctx.body = await this.ctx.proxy.AdvisorRankListFacade.queryAdvisorRankList(req);
return this.ctx.body;
}
}

```
source配置

[[CARD_13]]
```plain
"TaintSource": [
{
"path": "advisorId",
"scopeFile": "/app/controller/VariableCover/LevelTestBank.js", //相对路径
"scopeFunc": "bankTest"
},
...
]
```
强类型对象的属性
代码示例

[[CARD_14]]
```plain
func main() {
router := gin.Default()

router.GET("/user/:id", func(c *gin.Context) {
// 从 Params 读取 id 参数
id := c.Params.ByName("id") // C.Params是source

// 从 Accepted 读取客户端接受的内容类型
accepted := c.Accepted[0]

// 其他逻辑...
c.JSON(200, gin.H{
"id": id,
"accepted": accepted,
})
})

router.Run()
}

```
source配置

[[CARD_15]]
```plain
"TaintSource": [
{
"path": "Params",
"className": "*gin.Context",
"scopeFile": "all",
"scopeFunc": "all"
},
...
]
```
强类型对象方法调用的参数
代码示例

[[CARD_16]]
```plain
func main() {
route := gin.Default()
route.GET("/:name/:id", func(c *gin.Context) {
var person Person
//c.ShouldBindUri函数的参数为source
if err := c.ShouldBindUri(&person); err != nil {
c.JSON(400, gin.H{"msg": err.Error()})
return
}
c.JSON(200, gin.H{"name": person.Name, "uuid": person.ID})
})
route.Run(":8088")
}

```
source配置

[[CARD_17]]
```plain
"FuncCallArgTaintSource":[
{
"fsig": "ShouldBindUri",
"calleeType": "*gin.Context",
"args": [
"0"
],
"scopeFile": "all",
"scopeFunc": "all"
},
...
]
```
强类型对象函数调用的返回值
代码示例

[[CARD_18]]
```plain
func main() {
router := gin.Default()

router.POST("/post", func(c *gin.Context) {
id := c.Query("id") //定义c.Query的返回值为source
page := c.DefaultQuery("page", "0")
name := c.PostForm("name")
message := c.PostForm("message")

fmt.Printf("id: %s; page: %s; name: %s; message: %s", id, page, name, message)
})
router.Run(":8080")
}

```
source配置
其中，为了适配多返回值场景，values字段用于指代返回值的位置，例如以下示例中values值为0，指代标记第一个返回值为source

[[CARD_19]]
```plain
"FuncCallReturnValueTaintSource":[
{
"fsig": "Query",
"calleeType": "*gin.Context",
"values": [
"0"
],
"scopeFile": "all",
"scopeFunc": "all"
},
...
]
```
sink
支持的sink形式
目前只支持函数调用形式的sink点，用于标记接受污点数据的危险函数调用，支持全类名精确匹配和正则形式模糊匹配。

[[CARD_20]]
```json
"sinks": {
"FuncCallTaintSink": [
{
"args": [
"0"
],
"attribute": "GoSqlInjection",
"calleeType": "",
"fregex": "squirrel[\\s\\S]*?Select\\([^)]*\\)(?:\\.\\w+\\([^)]*\\))*\\s*\\.Where",
"kind": "GO_INPUT"
},
{
"args": [
"0"
],
"attribute": "GoSqlInjection",
"calleeType": "*pg.Conn",
"fsig": "Query",
"kind": "GO_INPUT"
}
]
}
```
使用fsig全类名精确匹配
含义：精确匹配函数签名，用于标识特定的函数调用。
匹配方式：
精确字符串匹配
支持点号分隔的完整路径（如 "requests.get"、"ctx.query"）
强类型语言支持 calleeType 结合使用，精确匹配对象类型和方法名
使用fregex函数正则表达式模糊匹配
含义：使用正则表达式匹配函数调用模式，用于匹配复杂或动态的函数调用链。要求必须严格满足正则表达式形式的语法要求。
匹配方式：
正则表达式模糊匹配
适用于链式调用参数不确定、动态方法名等场景
使用场景
弱类型对象/普通函数调用
代码示例

[[CARD_21]]
```plain
export default class LevelTestBank extends Controller {
async bankTest(advisorId, instId): Promise<any> {
const req: any = this.ctx.query.a;
// this.ctx.proxy.AdxxxxxxxFacade.queryList 是sink
this.ctx.body = await this.ctx.proxy.AdxxxxxxxFacade.queryList(req);
return this.ctx.body;
}
}

```

[[CARD_22]]
```plain
const mysql2 = require("mysql2");

exports.getConn = function () {
return mysql2.createConnection({
user: config.user,
password: config.password,
host: config.host,
port: config.port,
database: config.database,
});
}

class mysql2Test extends Controller {
async test1(sql): Promise<unknown> {
var conn = exports.getConn();

return new Promise(function (resolve, reject): void {
//这里我要定义的其实是mysql2.createConnection.query是sink
conn.query(sql, function (err, result): void {
conn.end();

if (err) {
reject(err);
}

resolve(result);
});
});
}
}

```

[[CARD_23]]
```plain
async case0502(): Promise<void> {
const payload: any = this.ctx.query.a;
import SlarkService from '@alipay/egg-slark';
let slarkService = new SlarkService();
//我的sink点是'@alipay/egg-slark'包的generate函数
slarkService.generate(payload);
}
```
sink配置

[[CARD_24]]
```plain
"FuncCallTaintSink": [
{
"args": [
"*"
],
"attribute": "NodejsLevelAuthority",
"fsig": "ctx.proxy.AdxxxxxxxFacade.queryList",
},
{
"args": [
"0"
],
"attribute": "NodejsSqlInjection",
"fsig": "mysql2.createConnection.query",
},
{
"args": [
"0"
],
"attribute": "NodejsVm2Run",
"fsig": "@alipay/egg-slark.generate",
},
...
]
```
强类型对象函数调用
代码示例

[[CARD_25]]
```plain
func (d *DataSelector) Parse(db *gorm.DB) *gorm.DB {
exps := d.OrderBy.Parse()
for i := range exps {
// db.Statement.AddClause 是sink
db.Statement.AddClause(exps[i])
}

if exps == nil {
db.Order("id desc")
}

db = db.Offset(d.Pagination.Offset).Limit(d.Pagination.Limit)
fexp := d.Filter.Parse()
if fexp != nil {
db.Statement.AddClause(clause.Where{Exprs: fexp})
}

return db.Debug()
}

```
sink配置
注：这里的sink是db.statement.addclause，我能知道db的类型是 *grom.DB ，而Statement的返回值我不知道类型，所以我可以把规则写为calleeType的类型是*gorm.DB，而fsig是Statement.AddClause

[[CARD_26]]
```plain
"FuncCallTaintSink": [
{
"args": [
"0"
],
"attribute": "GoSqlInjection",
"calleeType": "*gorm.DB",
"fsig": "Statement.AddClause",
"kind": "GO_INPUT"
},
...
]
```
链式调用模糊匹配
代码示例

[[CARD_27]]
```go
// GetProductByName retrieves a product by name using Squirrel but still vulnerable
func (db *DB) GetProductByName(name string) (*model.Product, error) {
// SECURITY WARNING: Still vulnerable to SQL injection via string concatenation in Where clause!

query, args, err := squirrel.StatementBuilder.PlaceholderFormat(squirrel.Question).Select("id", "name", "description", "price").
From("products").
Where("name = '" + name + "'"). // 🔓 SQL injection vulnerability here
ToSql()

if err != nil {
return nil, err
}

//row := db.Conn.QueryRow(query, args...)
product := &model.Product{}

err = row.Scan(&product.ID, &product.Name, &product.Description, &product.Price)
if err != nil {
return nil, err
}

return product, nil
}
```
sink配置
由于这里链式调用的参数是变量（无法唯一确定），因此可以使用正则匹配的形式匹配sink函数

[[CARD_28]]
```json
"FuncCallTaintSink": [
{
"args": [
"0"
],
"attribute": "GoSqlInjection",
"calleeType": "",
"fregex": "squirrel[\\s\\S]*?Select\\([^)]*\\)(?:\\.\\w+\\([^)]*\\))*\\s*\\.Where",
"kind": "GO_INPUT"
},
]
```
Sanitizer
基本说明
Sanitizer在规则文件中定义，Sanitizer的id在文件中需唯一。sink可通过sanitizer的id引用一个或多个sanitizer
规则示例

[[CARD_29]]
```json
{
"FuncCallTaintSink": [
{
"args": [
"0"
],
"calleeType": "",
"fsig": "Runtime.getRuntime().exec",
"sanitizerIds": [
"SANITIZER_1", "SANITIZER_2"
]
},
{
"args": [
"0"
],
"calleeType": "javax.script.ScriptEngine",
"fsig": "eval",
"sanitizerIds": [
"SANITIZER_3"
]
},
{
"args": [
"0"
],
"calleeType": "java.sql.Statement",
"fsig": "executeQuery",
"sanitizerIds": [
"SANITIZER_4"
]
},
{
"args": [
"0"
],
"calleeType": "org.yaml.snakeyaml.Yaml",
"fsig": "loadAll",
"sanitizerIds": [
"SANITIZER_5"
]
}
],
"Sanitizers": [
{
"id": "SANITIZER_1",
"sanitizerType": "BinaryOperationSanitizer",
"sanitizerScenario": "SANITIZER.VALIDATE_BY_BINARYOPERATION",
"operator": "==",
"targetValue": ".*",
},
{
"id": "SANITIZER_2",
"sanitizerType": "FunctionCallSanitizer",
"sanitizerScenario": "SANITIZER.VALIDATE_BY_FUNCTIONCALL",
"calleeType": "com.alipay.common.security.util.secutils.cmd.CmdParameterChecker",
"fsig": "checkCmdParameter",
"args": [
"0"
]
},
{
"id": "SANITIZER_3",
"sanitizerType": "FunctionCallSanitizer",
"sanitizerScenario": "SANITIZER.CALLSTACK_HAS_FUNCTIONCALL",
"calleeType": "com.alipay.common.security.util.secutils.cmd.AlipayCmdChecker",
"fsig": "hookStart",
},
{
"id": "SANITIZER_4",
"sanitizerType": "FunctionCallSanitizer",
"sanitizerScenario": "SANITIZER.FILTER_BY_FUNCTIONCALL",
"calleeType": "com.alipay.common.security.util.sqlutils.AlipaySqlEscapeUtil",
"fsig": "escapeSql",
"args": [
"0"
]
},
{
"id": "SANITIZER_5",
"sanitizerType": "FunctionCallSanitizer",
"sanitizerScenario": "SANITIZER.CONFIG_BY_FUNCTIONCALL",
"calleeType": "org.yaml.snakeyaml.constructor.SafeConstructor",
"fsig": "SafeConstructor",
}
]
}
```
Sanitizer字段说明

[[CARD_30]]
sanitizerType
目前支持以下值：
（1）FunctionCallSanitizer，表示Sanitizer通过函数调用实现
（2）BinaryOperationSanitizer，表示Sanitizer通过逻辑比较实现
sanitizerScenario
（1）SANITIZER.FILTER_BY_FUNCTIONCALL
过滤用户输入中的危险字符，过滤后的结果用于后续其他操作

[[CARD_31]]
```java
String escapedUserName = AlipaySqlEscapeUtil.escapeSql(userName, new MySQLCodec(MySQLCodec.Mode.STANDARD));
String sql = "select * from user where username='" + escapedUserName + "'";
```
（2）SANITIZER.VALIDATE_BY_FUNCTIONCALL
调用特定API校验输入内容，通常情况下校验失败抛异常或返回

[[CARD_32]]
```java
...
String gitUrl = request.getParameter("gitUrl");
if (!CmdParameterChecker.checkCmdParameter(gitUrl, null)) {
//阻断业务
}
String cmd = "git clone " + gitUrl;
Runtime.getRuntime().exec(cmd);
```

[[CARD_33]]
```java
if (!AlipaySSRFChecker.isHostVaild(host)) {
//阻断业务
......
}
URL url = new URL(host);
URLConnection urlConnection = url.openConnection();
```
（3）SANITIZER.CONFIG_BY_FUNCTIONCALL
在组件初始化配置中加入安全选项

[[CARD_34]]
```java
if (engine instanceof org.codehaus.groovy.jsr223.GroovyScriptEngineImpl) {
CompilerConfiguration config = new CompilerConfiguration();
config.addCompilationCustomizers(GroovySandboxExpressionChecker.getSecureASTCustomizer());
URLClassLoader urlClassLoader = URLClassLoaderUtil.getUrlClassLoader(this.getClass().getClassLoader(), "compileScript-脚本编译器");
GroovyClassLoader loader = new GroovyClassLoader(urlClassLoader, config);
loader.parseClass(input);
}
```

[[CARD_35]]
```java
public static List<Object> loadYaml(InputStream in) throws YAMLException
{
// SafeConstructor because we may not trust the server or a moderator
Yaml yaml = new Yaml(new SafeConstructor());
List<Object> ret = new ArrayList<>();
// parse the documents immediately (by invoking the iterator)
for (Object o : yaml.loadAll(in)) {
ret.add(o);
}
return ret;
}
```
（4）SANITIZER.CALLSTACK_HAS_FUNCTIONCALL
sanitizer和sink在同一个调用栈中，hook特定操作

[[CARD_36]]
```java
ScriptEngineManager manager = new ScriptEngineManager();
ScriptEngine engine = manager.getEngineByName("JavaScript");
try {
AlipayCmdChecker.hookStart();
engine.eval(code);
} catch (ScriptException e) {
e.printStackTrace();
} catch (UnsafeCmdExecError error) {
System.err.println("cmd exec denied!");
} finally {
AlipayCmdChecker.hookStop();
}
```
（5）SANITIZER.VALIDATE_BY_BINARYOPERATION
sanitizer为二元操作符，检查输入内容与其他特定内容的关系

[[CARD_37]]
```java
String safeCmd = "ls";
if (cmd == safeCmd) {
Runtime.getRuntime.exec(cmd)
}
```
（6）SANITIZER.DEFAULT
同SANITIZER.CALLSTACK_HAS_FUNCTIONCALL
EntryPoint
基本属性
代码示例

[[CARD_38]]
```plain
const Client = require('ssh2-sftp-client');

class File extends Controller {
async upload2SftpWhite() : Promise<void> { //从这个函数开始模拟执行
const { path } = this.ctx.request;
const sftp = new Client();
const sftpConfig = this.config.xxxx;
const stream = await ctx.getFileStream();

const fileName = path;
const reqParam = helper.getReqParameter();
const { bizType, instId } = reqParam;

const Path : string = `${bizType}/${instId}/creditmng/${moment().format('YYYYMMDD')}/${uuid()}/${fileName}`;
try {
// 文件安全检查
helper.checkFileName(Path);
} catch (error) {
await sendToWormhole(stream);
throw error;
}
}
}

```
EntryPoint配置

[[CARD_39]]
```plain
"entrypoints": [
{
"attribute": "HTTP",
"filePath": "/app/controller/File.js",
"functionName": "upload2SftpWhite"
},
...
]
```
Go语言特有属性-funcReceiverType
代码示例

[[CARD_40]]
```plain
func (d *DataSelector) Parse(db *gorm.DB) *gorm.DB { //DataSelector为接收器类型
exps := d.OrderBy.Parse()
for i := range exps {
db.Statement.AddClause(exps[i])
}

if exps == nil {
db.Order("id desc")
}

db = db.Offset(d.Pagination.Offset).Limit(d.Pagination.Limit)
fexp := d.Filter.Parse()
if fexp != nil {
db.Statement.AddClause(clause.Where{Exprs: fexp})
}

return db.Debug()
}

func ConvertStringSliceToInterfaceSlice(source []string) []interface{} {
r := make([]interface{}, 0, 1)
for i := range source {
r = append(r, source[i])
}
return r
}

```
EntryPoint配置

[[CARD_41]]
```plain
"entrypoints": [
{
"attribute": "HTTP",
"filePath": "/core/service/impl/dockerfile.go",
"functionName": "Parse",
"funcReceiverType": "DataSelector"
},
...
]
```
