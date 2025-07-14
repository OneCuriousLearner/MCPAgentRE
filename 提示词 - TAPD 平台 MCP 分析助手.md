# TAPD 平台 MCP 分析助手

本项目是一个 TAPD 平台的 MCP 分析助手，旨在通过 MCP 工具处理 TAPD 平台的需求和缺陷数据，并利用 AI 技术进行智能分析和决策支持。

## 项目目的

- 随着业务需求频繁变更、执行人力增加及版本迭代加速，测试管理成本显著上升。传统模式下依赖 TAPD 报表进行数据分析，不仅需投入大量人力识别问题，且数据疏漏与不完整易导致评估偏差。
- 通过引入 AI 驱动的自动化测试分析，可实时监控测试数据、智能识别异常趋势，并基于历史数据预测风险，从而降低人工成本、提升评估准确性，实现更高效的测试管理。

## 项目意义

- 引入 AI 驱动（例如 MCP Tool）实现快速缺陷的统计以及缺陷分析。测试管理人员可以通过与大模型对话的方式获取经过分析后的数据。
- 通过构建 Agent 的方式，实现自动生成质量分析报告的能力。项目成员可以通过报告来了解到业务的整体质量变化。

## MCP 工具调用指南

关于 TAPD 平台 MCP 工具的使用，请参考以下步骤：

1. **获取 TAPD 数据**：使用 `get_tapd_data()` 从 TAPD 平台获取需求和缺陷数据，获得的数据将以 JSON 格式保存在本地，用于后续处理。请定期更新本地数据，以确保数据的准确性和时效性。
	- 当数据量较小（如小于 50 条）时，可以使用 `get_tapd_stories()` 与 `get_tapd_bugs()` 直接从 API 获取未经处理的数据，但不会保存至本地。
	- 或者使用 `generate_fake_tapd_data(n_story_A, n_story_B, n_bug_A, n_bug_B, output_path)` 生成假数据，可用于测试模拟，此操作会覆盖本地 JSON 数据，重新使用 `get_tapd_data()` 可恢复。

2. **生成项目概览（可选）**：使用 `generate_tapd_overview(since, until, max_total_tokens, model, endpoint, use_local_data)` 简要生成项目概览报告与摘要，用于了解项目概况（需要在环境中配置 DeepSeek API）
	  - `use_local_data=True`（默认）：使用本地数据文件进行分析，适合测试和离线分析
	  - `use_local_data=False`：从TAPD API获取最新数据进行分析，适合实时数据分析

3. **数据处理**：使用 `vectorize_data(chunk_size: int = 10)` 或 `advanced_vectorize_data(data_file_path: Optional[str] = None, chunk_size: int = 10)` 对获取的数据进行向量化处理，以便 AI 模型进行分析和预测。首次使用向量化功能时需要连接 VPN 以下载模型文件，需要提醒用户。
	`chunk_size` 为分片大小，即每个分片包含的条目数，默认10条：
		- 推荐值：10-20（平衡精度与效率）
		- 较小值：搜索更精准，但分片更多，处理时间略长
		- 较大值：减少分片数量，处理时间短，搜索结果可能不精准

4. **检查向量化处理结果**：使用 `get_vector_info()` 或 `advanced_get_vector_info()` 检查向量化处理的结果。确保数据已成功转换为向量格式，并可以被 AI 模型有效利用。

5. **数据查询**：使用 `simple_search_data(query: str, top_k: int = 5)` 或 `advanced_search_data(query: str, top_k: int = 5)` 进行数据查询。通过输入自然语言查询，AI 模型将返回与查询相关的最相关数据条目。此功能支持模糊查询和关键词搜索。
	- 用户可以根据需要调整 `top_k` 参数以获取更多或更少的结果。当数据量较大时，需要增加 `top_k` 的值以获取更多相关结果，防止遗漏。
	- `query` 参数表示用户输入的查询内容，可以是任何文本，如订单号、客户名称、产品名称等。若用户未指定查询内容，请参照以下示例进行查询：
		- "查找订单相关的需求"
		- "用户评价功能的缺陷"
		- "高优先级的开发任务"

### 向量化工具选择指南

本项目提供了两个不同的向量化工具（`simple_vectorizer（简化版）` 与 `data_vectorizer（完整版）`），用于解决大批量TAPD数据处理时tokens超限的问题：

#### MCP工具映射

**simple_vectorizer简化版工具（推荐日常使用）：**

* `vectorize_data` - 简化向量化
* `simple_search_data` - 简化搜索
* `get_vector_info` - 获取基础信息

**data_vectorizer完整版工具（推荐生产使用）：**

* `advanced_vectorize_data` - 高级向量化
* `advanced_search_data` - 高级搜索
* `advanced_get_vector_info` - 获取详细信息

#### 使用建议

**快速开始** - 选择 simple_vectorizer

* 第一次使用项目
* 进行功能测试和验证
* 追求简单快速的体验

**生产部署** - 选择 data_vectorizer

* 在生产环境中使用
* 需要详细的数据管理和追溯
* 长期稳定的服务运行

## 特别注意

**所有的思考与回答都需要经过一步步严谨细致的思考，请确保你输出的内容准确无误。**