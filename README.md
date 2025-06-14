# MCP_Agent:RE 项目迁移指南

## 项目背景
MCP_Agent:RE是一个用于从TAPD平台获取需求和缺陷数据的Python项目，旨在为AI客户端提供数据支持。

## 项目结构
- `knowledge_documents`：包含项目相关的知识文档（Github版本已隐去）
- `tapd_data_fetcher.py`：包含从TAPD API获取需求和缺陷数据的逻辑
- `tapd_mcp_server.py`：MCP服务器启动脚本，用于启动数据获取服务
- `main.py`：项目入口文件，无实际作用
- `requirements.txt`：项目依赖列表
- `pyproject.toml`：Python项目配置文件
- `msg_from_fetcher.json`：从 tapd_data_fetcher.py 获取的数据，运行 tapd_data_fetcher.py 后自动生成
- `msg_from_server.json`：从 tapd_mcp_server.py 获取的数据，运行 tapd_mcp_server.py 后自动生成（已弃用）
- `README.md`：项目说明文档

## 迁移步骤
以下是将项目移植到其他Windows电脑的详细步骤，确保通用性验证：

### 一、环境准备
1. **安装Python 3.10**
   - 从[Python官网](https://www.python.org/downloads/windows/)下载Python 3.10.x安装包（建议3.10.11，与原环境一致）
   - 安装时勾选 Add Python to PATH （关键！否则需手动配置环境变量）
   - 验证安装：终端运行 python --version ，应输出`Python 3.10.11`

2. **安装uv工具**
   - 终端运行（需确保pip已随Python安装）：
   ```
   pip install uv
   ```
   - 验证安装：运行 uv --version ，应显示版本信息

### 二、项目文件迁移
1. **复制项目目录**
   - 将原项目目录 D:\MiniProject\MCPAgentRE 完整复制到目标电脑（建议路径无中文/空格，如 D:\MCPAgentRE ）

### 三、依赖安装
1. **安装项目依赖**
   - 终端进入项目目录： cd D:\MCPAgentRE （根据实际路径调整）
   - 运行依赖安装命令：
     ```bash
     uv add mcp[cli] aiohttp requests
     ```
   - 该命令会根据 pyproject.toml 或 requirements.txt 安装所有依赖（包括MCP SDK、aiohttp等）

### 四、配置调整
1. **TAPD API配置**
   - 编辑 tapd_data_fetcher.py 文件，替换以下配置为目标TAPD项目的真实值：
     ```python
     API_USER = '替换为你的TAPD API用户名'
     API_PASSWORD = '替换为你的TAPD API密码'
     WORKSPACE_ID = '替换为你的TAPD项目ID'
     ```

### 五、测试运行
1. **在终端进入项目文件夹**
   - 终端运行： cd D:\MCPAgentRE （根据实际路径调整）

#### 测试模式：
1. 如果需要验证 tapd_data_fatcher.py 是否正常获取数据，请运行以下指令：
   ```bash
   uv run tapd_data_fetcher.py
   ```

   - 预期输出：
     ```text
     ===== 开始获取需求数据 =====
     需求数据获取完成，共获取X条
     ===== 开始获取缺陷数据 =====
     缺陷数据获取完成，共获取Y条
     数据已成功保存至msg_from_fetcher.json文件。
     ```

2. 如果需要验证 tapd_mcp_server.py 是否正常获取数据，请将主函数中的以下代码解除注释：
   ```python
    import asyncio
    
    print('===== 开始获取需求数据 =====')
    stories = asyncio.run(get_tapd_stories())
    print('===== 开始获取缺陷数据 =====')
    bugs = asyncio.run(get_tapd_bugs())

    # 打印需求数据结果
    print('===== 需求数据获取结果 =====')
    print(stories)
    # 打印缺陷数据结果
    print('===== 缺陷数据获取结果 =====')
    print(bugs)
   ```

   - 预期输出：
     ```text
     ===== 开始获取需求数据 =====
     需求数据获取完成，共获取X条
     ===== 开始获取缺陷数据 =====
     缺陷数据获取完成，共获取Y条
     ===== 需求数据获取结果 =====
     [具体JSON数据...]
     ===== 缺陷数据获取结果 =====
     [具体JSON数据...]
     ```

#### 正常模式：
1. 确保 tapd_mcp_server.py 的主函数中中相关代码已注释或删除
   ```python
    # import asyncio
    
    # print('===== 开始获取需求数据 =====')
    # stories = asyncio.run(get_tapd_stories())
    # print('===== 开始获取缺陷数据 =====')
    # bugs = asyncio.run(get_tapd_bugs())

    # # 打印需求数据结果
    # print('===== 需求数据获取结果 =====')
    # print(stories)
    # # 打印缺陷数据结果
    # print('===== 缺陷数据获取结果 =====')
    # print(bugs)
   ```

2. 运行MCP服务器：
   ```bash
   uv run tapd_mcp_server.py
   ```

### 六、常见问题排查
- **依赖缺失**：若提示 ModuleNotFoundError ，检查是否执行 uv add 命令，或尝试`uv add <缺失模块名>`
- **API连接失败**：确认 API_USER / API_PASSWORD / WORKSPACE_ID 正确，且TAPD账号有对应项目的读取权限
- **Python版本不匹配**：确保目标电脑Python版本为3.10.x（通过 python --version 验证）

---

# 如何将项目连接到AI客户端

## 前提条件
- 已在本地电脑上完成项目的迁移和验证
- 已安装并运行MCP服务器
- 已在本地电脑上安装并运行AI客户端（以Claude Desktop为例）

## 连接步骤
1. **打开Claude Desktop**
   - 启动Claude Desktop客户端

2. **配置MCP服务器**
   - 使用快捷键“Ctrl + ,”打开设置页面（或者点击左上角菜单图标 - File - Settings）
   - 选择“Developer”选项卡
   - 点击“Edit Config”按钮，将会弹出文件资源管理器
   - 编辑高亮提示的 claude_desktop_config.json 文件，添加以下内容（注意层级关系）：
   ```json
   {
		"mcpServers": {
			"tapd_data_fetcher": {
				"command": "uv",
				"args": [
					"--directory",
					"D:\\MiniProject\\MCPAgentRE",
					"run",
					"tapd_mcp_server.py"
				]
			}
		}
   }
   ```

   - 注意：
      -  command 字段指定了运行MCP服务器的命令（通常为 uv ）
      -  args 字段指定了运行MCP服务器的参数，包括项目目录（--directory）和运行的脚本文件（run tapd_mcp_server.py）
      - 确保 --directory 指向的是MCP服务器所在的目录，即 D:\MiniProject\MCPAgentRE （请按照实际目录修改）
   - 保存并关闭文件

## 测试连接
   - 点击Claude Desktop界面左上角的“+”按钮，选择“New Chat”
   - 在新的聊天窗口中，输入以下内容：
     ```text
     请使用tapd_data_fetcher插件获取TAPD项目的需求和缺陷数据
     ```
   - 点击发送按钮，等待MCP服务器返回数据
   - 检查返回的数据是否符合预期，包括需求和缺陷的数量和内容

## 注意事项
- 确保MCP服务器的路径和参数配置正确
- 如果MCP服务器运行时出现错误，检查MCP服务器的日志文件（通常位于 %APPDATA%\Claude\logs ）以获取更多信息
- 如果AI客户端无法识别MCP插件，可能需要重新安装或更新AI客户端
- 您可以运行以下命令列出最近的日志并跟踪任何新日志（在 Windows 上，它只会显示最近的日志）：
    ```bash
    # Windows
    type "%APPDATA%\Claude\logs\mcp*.log"
    ```

---

# 相关文档或网址

- [TAPD帮助文档](https://www.tapd.cn/help/show#1120003271001000137)
- [TAPD开放平台文档](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/%E4%BD%BF%E7%94%A8%E5%BF%85%E8%AF%BB.html)
- [MCP中文站](https://mcpcn.com/docs/introduction/)
- [Model Context Protocol](https://modelcontextprotocol.io/introduction)
