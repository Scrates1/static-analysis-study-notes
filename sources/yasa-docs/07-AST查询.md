---
title: "AST查询"
slug: mzaslh9b1hook19l
source_url: https://www.yuque.com/u22090306/bebf6g/mzaslh9b1hook19l
updated_at: 2025-11-17T10:52:20.000Z
word_count: 424
image_count: 1
card_count: 6
---

# AST查询

参数说明

```plain
--help 打印帮助
--sourcePath 将要分析的目标文件
--dumpAST 单文件使用，dump出单个目标文件的AST
--dumpAllAST 整个工程使用，dump出整个工程的AST
--report 指定输出报告目录/文件（污点追踪、callgraph是目录，AST是文件），默认输出到当前目录下
--uastSDKPath go/python语言分析时必填，指定uast4go和uast4python的二进制路径
--language 指定待分析的语言（支持: javascript/typescript/golang/python）
```
解析单文件
执行命令

```plain
# 命令示例
/Users/yasa-macos-arm64
--dumpAST
--sourcePath ./.../root.go
--uastSDKPath ./uast4go
--language go
--report /Users/xxx/root.json
```
说明：
执行go或则python语言分析时，需指定uast4go和uast4python的二进制路径。js已集成在yasa内，不需要指定
预期输出示例
结果文件将会输出到--report指定的路径/Users/xxx/root.json下：

```javascript
main file:/snapshot/yasa2/dist/main.js
source path: /Users/xxx/root.go
Report File: /Users/xxx/root.json
```
未指定输出地点时，会默认输出到当前目录的uast.json下
UAST结果说明
UAST 结果结构详见[UAST节点说明](https://github.com/antgroup/YASA-UAST/blob/main/specification/specification.md)

解析整个工程
执行命令

```plain
# 命令示例
/Users/yasa-macos-arm64
--dumpAllAST
--sourcePath /Users/xxx/myproject/
--uastSDKPath ./uast4go
--language go
--report /Users/xxx/myproject/uastdump
```
说明：
执行go或则python语言分析时，需指定uast4go和uast4python的二进制路径。js已集成在yasa内，不需要指定
预期输出示例
结果文件将会输出到--report指定的路径/Users/xxx/myproject/uastdump下：

```javascript
main file:/snapshot/yasa2/dist/main.js
source path: /Users/xxx/myproject/
Report directory: /Users/xxx/myproject/uastdump
parseDirectory UAST success!
```
报告输出
未指定输出地点时，会默认输出到当前目录下

![image.png](https://cdn.nlark.com/yuque/0/2025/png/59228126/1757554101350-1f08e7d9-44da-4473-931c-fb29014dbd27.png)
UAST结果说明
UAST 结果结构详见[UAST节点说明](https://github.com/antgroup/YASA-UAST/blob/main/specification/specification.md)
