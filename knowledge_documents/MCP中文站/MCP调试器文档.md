# 调试器 Inspector

以下是使用 MCP 调试器（Inspector）测试和调试模型上下文协议（MCP）服务器的深度指南。

[MCP 调试器](https://github.com/modelcontextprotocol/inspector)是一个交互式的开发者工具，用于测试和调试 MCP 服务器。 虽然[调试指南](https://modelcontextprotocol.io/docs/tools/debugging) 将调试器作为整体调试工具包的一部分进行了介绍，但本文档将详细探讨 Inspector 的特性和功能。

## [入门](https://modelcontextprotocol.io/docs/tools/inspector#getting-started)

### [安装和基本用法](https://modelcontextprotocol.io/docs/tools/inspector#installation-and-basic-usage)

调试器通过 `npx` 直接运行，无需安装：

```bash
npx @modelcontextprotocol/inspector <command>
```

```bash
npx @modelcontextprotocol/inspector <command> <arg1> <arg2>
```

#### [从 NPM 或 PyPi 检查服务器](https://modelcontextprotocol.io/docs/tools/inspector#inspecting-servers-from-npm-or-pypi)

一种常见的启动来自 [NPM](https://npmjs.com/) 或 [PyPi](https://pypi.com/) 的服务器包的方式。

- NPM 包

```bash
npx -y @modelcontextprotocol/inspector npx <package-name> <args>
# 例如
npx -y @modelcontextprotocol/inspector npx server-postgres postgres://127.0.0.1/testdb
```

- PyPi 包

```bash
npx @modelcontextprotocol/inspector uvx <package-name> <args>
# 例如
npx @modelcontextprotocol/inspector uvx mcp-server-git --repository ~/code/mcp/servers.git
```

#### [检查本地开发的服务器](https://modelcontextprotocol.io/docs/tools/inspector#inspecting-locally-developed-servers)

要检查本地开发或作为存储库下载的服务器，最常见的方式是：

- TypeScript

```bash
npx @modelcontextprotocol/inspector node path/to/server/index.js args...
```

- Python

```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory path/to/server \
  run \
  package-name \
  args...
```

请仔细阅读任何随附的 README 文件，以获取最准确的说明。

## [功能概述](https://modelcontextprotocol.io/docs/tools/inspector#feature-overview)

![img](https://mintlify.s3.us-west-1.amazonaws.com/mcp/images/mcp-inspector.png)

MCP 调试器界面

调试器提供了多个与 MCP 服务器交互的功能：

### [服务器连接面板](https://modelcontextprotocol.io/docs/tools/inspector#server-connection-pane)

- 允许选择用于连接到服务器的[传输方式](https://modelcontextprotocol.io/docs/concepts/transports)（transport）
- 对于本地服务器，支持自定义命令行参数和环境变量

### [资源选项卡](https://modelcontextprotocol.io/docs/tools/inspector#resources-tab)

- 列出所有可用资源（resource）
- 显示资源元数据（MIME 类型、描述）
- 允许资源内容检查
- 支持订阅测试

### [提示选项卡](https://modelcontextprotocol.io/docs/tools/inspector#prompts-tab)

- 显示可用的提示模板（prompt template）
- 显示提示参数和描述
- 启用带有自定义参数的提示测试
- 预览生成的消息

### [工具选项卡](https://modelcontextprotocol.io/docs/tools/inspector#tools-tab)

- 列出可用的工具（tool）
- 显示工具模式（schema）和描述
- 启用带有自定义输入的工具测试
- 显示工具执行结果

### [通知面板](https://modelcontextprotocol.io/docs/tools/inspector#notifications-pane)

- 显示从服务器记录的所有日志
- 显示从服务器收到的通知

## [最佳实践](https://modelcontextprotocol.io/docs/tools/inspector#best-practices)

### [开发工作流程](https://modelcontextprotocol.io/docs/tools/inspector#development-workflow)

1. 开始开发
   - 使用您的服务器启动调试器
   - 验证基本连接
   - 检查能力协商（capability negotiation）
2. 迭代测试
   - 更改服务器
   - 重新构建服务器
   - 重新连接调试器
   - 测试受影响的功能
   - 监控消息
3. 测试边缘情况
   - 无效输入
   - 缺少提示参数
   - 并发操作
   - 验证错误处理和错误响应