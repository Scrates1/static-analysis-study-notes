---
title: "内置checker介绍"
slug: ouenen3i3en236ek
source_url: https://www.yuque.com/u22090306/bebf6g/ouenen3i3en236ek
updated_at: 2025-11-18T08:46:04.000Z
word_count: 307
image_count: 0
card_count: 0
---

# 内置checker介绍

查看可用的checkerId
可以通过以下方式查看系统中可用的checkerId：
查看 resource/checker/checker-config.json 文件
查看 resource/checker/checker-pack-config.json 文件（检查器组配置）
参考 resource/example-rule-config/ 目录下的示例配置文件
checker-pack
|
cherker-pack
|
checker-pack介绍
|
包含checker
|
checker介绍
|
taint-flow-golang-default
|
golang污点追踪内置规则包
|
taint_flow_gin_input
|
Gin taint_flow checker，不会使用CallGraph边界制作entrypoint
|

|

|
taint_flow_go_input
|
Go framework checker，会使用CallGraph边界制作entrypoint
|

|

|
cobra.Command-builtIn
|
为第三方库方法cobra.command 的 entryPoints
|

|

|
go-restful-entryPoints-collect-checker
|
go-restful 框架entryPoint采集以及source添加
|

|

|
gorilla-mux-entrypoint-collect-checker
|
Mux entryPoint采集以及框架source添加
|

|

|
gRpc-entryPoint-collect-checker
|
gRpc entrypoint采集以及框架source添加
|

|

|
go-main-entryPoints-collection
|
go-main-entryPoints-collection
|

|

|
sync.Once.Do-builtIn
|
为Go内置库方法sync.Once.Do做建模，执行且只执行一次传给Do方法的funcDef
|

|

|
urfave-cli-builtIn
|
为第三方库方法urfave.cli做建模，添加entryPoints
|

|

|
callgraph
|
CallGraph采集checker
|

|

|
sanitizer
|
sanitizer 的 checker
|
taint-flow-javascript-default
|
js/ts污点追踪内置规则包
|
taint_flow_js_input
|
JavaScript原生污点分析checker，会使用CallGraph边界制作entrypoint
|

|

|
taint_flow_egg_input
|
JavaScript Egg框架污点分析checker
|

|

|
callgraph
|
CallGraph采集checker
|

|

|
sanitizer
|
sanitizer 的 checker
|
taint-flow-python-default
|
python污点追踪内置规则包
|
taint_flow_python_input
|
Python污点分析checker，会使用CallGraph边界制作entrypoint
|

|

|
taint_flow_python_django_input
|
Python Django框架 entryPoint采集以及source添加
|

|

|
callgraph
|
CallGraph采集checker
|

|

|
sanitizer
|
sanitizer 的 checker
