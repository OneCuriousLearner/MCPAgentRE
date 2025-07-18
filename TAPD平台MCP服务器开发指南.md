# TAPD 平台 MCP 服务器开发指南

本项目使用 MCP 作为开发框架，主要用于获取 TAPD 平台的需求和缺陷数据，并使用 AI 进行需求和缺陷的识别和决策。

## 项目意义

* 引入 AI 驱动（例如 MCP Tool）实现快速缺陷的统计以及缺陷分析。测试管理人员可以通过与大模型对话的方式获取经过分析后的数据。
* 通过构建 Agent 的方式，实现自动生成质量分析报告的能力。项目成员可以通过报告来了解到业务的整体质量变化。
* 通过引入 AI 驱动的自动化测试分析，可实时监控测试数据、智能识别异常趋势，并基于历史数据预测风险，从而降低人工成本、提升评估准确性，实现更高效的测试管理。

## 开发标准

* 项目使用 Python 语言开发，依赖于 MCP 的 CLI 工具和其他相关库。虚拟环境与包管理器则是由 uv 提供的。
* 若需要添加或更新依赖，可以使用 `uv add` 或 `uv sync` 命令。
* 所有 Python 程序在执行时都应当使用 `uv run <file>` 命令来运行程序，以确保使用正确的虚拟环境和依赖。运行程序前终端应当位于项目根目录，之后使用例如 `uv run mcp_tools\example_tool.py` 的命令格式。
* 除了专门从 API 获取数据的脚本外，所有的程序都应当优先使用本地数据文件进行分析。若需要最新的 API 数据，请调用 `tapd_data_fetcher.py` 脚本来获取最新数据。

### 目录标准

```text
MCPAgentRE\
├─knowledge_documents\      # 知识文档
├─mcp_tools\                # MCP 工具目录
├─local_data\               # 本地数据目录，用于存储从 TAPD 获取的数据、数据库等
├─test\                     # 测试目录
├─models\                   # 模型目录
├─.gitignore                # Git 提交时遵守的过滤规则
├─.python-version           # 记录 Python 版本（3.10）
├─api.txt                   # 包含 API 密钥信息
├─pyproject.toml            # 现代的 Python 依赖管理文件
├─README.md                 # 项目说明文档，所有功能与使用步骤都在这里
├─tapd_data_fetcher.py      # 包含从 TAPD API 获取需求和缺陷数据的逻辑
├─tapd_mcp_server.py        # MCP 服务器启动脚本，包含各类 MCP 工具
└─uv.lock                   # UV 包管理器使用的锁定文件
```

* 若要添加 MCP 工具，请存储于 `mcp_tools` 文件夹中，并在 `tapd_mcp_server.py` 中注册。注册方法请见 `README.md` 文件的“扩展MCP服务器功能”部分，之后你可以自行测试此 MCP 工具。
* 所有来自 TAPD 平台的数据都应存储在 `local_data` 文件夹中，包括后续创建的数据库文件等。向量数据库文件则存储于 `local_data\vector_data` 文件夹中。
* 所有测试类的文件都应存储在 `test` 文件夹中，测试文件名应以 `test_` 开头。
* 所有新文档都应存储在 `knowledge_documents` 文件夹中，若为项目添加了新功能，请在 `knowledge_documents` 文件夹中创建或更新对应的使用手册文档，之后使用简洁的语言更新在 `README.md` 文档中。
* 所有模型文件都应存储在 `models` 文件夹中，若需要为项目添加新模型，请指定下载在 `models` 文件夹中。

### 统一接口脚本

* 位于 `mcp_tools\common_utils.py`
* 提供统一的工具接口，简化 MCP 工具的注册和调用
* 包含的工具如下：

#### MCPToolsConfig 类

* **`__init__()`** - 初始化配置管理器，自动创建项目所需的目录结构（local_data、models、vector_data）
* **`_get_project_root()`** - 获取项目根目录的绝对路径
* **`get_data_file_path(relative_path)`** - 获取数据文件的绝对路径，支持相对路径自动转换
* **`get_vector_db_path(name)`** - 获取向量数据库文件路径，默认为"data_vector"
* **`get_model_cache_path()`** - 获取模型缓存目录路径

#### ModelManager 类

* **`__init__(config)`** - 初始化模型管理器，依赖MCPToolsConfig实例
* **`get_project_model_path(model_name)`** - 检测本地是否存在指定模型，返回模型路径或None
* **`get_model(model_name)`** - 获取SentenceTransformer模型实例，优先使用本地模型，支持自动下载和缓存
* **`clear_cache()`** - 清除全局模型缓存，释放内存资源

#### TextProcessor 类

* **`extract_text_from_item(item, item_type)`** - 从TAPD数据项（需求/缺陷）中提取关键文本信息，支持不同类型的字段提取策略

#### FileManager 类

* **`__init__(config)`** - 初始化文件管理器，依赖MCPToolsConfig实例
* **`load_tapd_data(file_path)`** - 加载TAPD JSON数据文件，支持绝对路径和相对路径
* **`load_json_data(file_path)`** - 加载JSON数据文件，支持错误处理，文件不存在时返回空字典
* **`save_json_data(data, file_path)`** - 保存数据为JSON格式，自动创建目录结构

#### APIManager 类

* **`__init__()`** - 初始化API管理器，从环境变量读取DeepSeek API配置
* **`get_headers()`** - 构建API请求头，验证API密钥是否已设置
* **`call_llm(prompt, session, model, endpoint, max_tokens)`** - 调用在线LLM API，支持DeepSeek-Reasoner的reasoning_content字段

#### 全局实例管理函数

* **`get_config()`** - 获取全局MCPToolsConfig实例（单例模式）
* **`get_model_manager()`** - 获取全局ModelManager实例（单例模式）
* **`get_file_manager()`** - 获取全局FileManager实例（单例模式）
* **`get_api_manager()`** - 获取全局APIManager实例（单例模式）

## 最终验收要求及评价指标

* 缺陷数据、需求数据拉取正确率 100%
* 涉及到数据的计算准确率达 100%
* MCP\Agent（质量报告生成相关）的调用稳定性大于 99%

## 特别注意

**所有的思考与回答都需要经过一步步严谨细致的思考，请确保你输出的内容准确无误。**
