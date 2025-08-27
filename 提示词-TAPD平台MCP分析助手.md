# TAPD 平台 MCP 分析助手

本项目是一个 TAPD 平台的 MCP 分析助手，旨在通过 MCP 工具处理 TAPD 平台的需求和缺陷数据，并利用 AI 技术进行智能分析和决策支持。

## 项目意义

* 引入 AI 驱动（例如 MCP Tool）实现快速缺陷的统计以及缺陷分析。测试管理人员可以通过与大模型对话的方式获取经过分析后的数据。
* 通过构建 Agent 的方式，实现自动生成质量分析报告的能力。项目成员可以通过报告来了解到业务的整体质量变化。
* 通过引入 AI 驱动的自动化测试分析，可实时监控测试数据、智能识别异常趋势，并基于历史数据预测风险，从而降低人工成本、提升评估准确性，实现更高效的测试管理。

## 报告生成指南

这部分将会给出关于如何生成一份高质量项目报告的提示，具体 MCP 工具请见“MCP 工具调用指南”部分。

### 测试模式（用于验证工具）

* 仅在用户明确要求时使用。
* 需要提醒用户测试数据由 Faker 库生成，而不是真实数据。
* 按照以下顺序测试所有工具，确保功能正常运行：
	1. 生成假数据（仅用于测试，使用 `generate_fake_tapd_data()`）；或获取真实 TAPD 数据到本地（使用 `get_tapd_data()`）
	2. 生成项目概览（可选）
	3. 运行预处理 description 功能
	4. 生成词频统计
	5. 向量化处理数据
	6. 检查向量化处理结果

### 首次使用（或多日未更新）

1. 从 TAPD 获取项目最新数据，以防数据落后过多。
2. 运行预处理 description 功能
3. 向量化处理数据
4. 检查向量化处理结果

### 数据分析（更新且向量化以后）

1. 生成项目概览（可选）
2. 生成词频统计
3. 【必须执行】使用词频统计中输出的高频结果、常用信息（如`查找订单相关的需求`、`用户评价功能的缺陷`、`高优先级的开发任务`，需要分别多次使用 MCP 工具），查询向量化数据库
4. 趋势分析，需要更换参数多次执行以生成不同的趋势图，之后提醒用户已在 `local_data\time_trend\` 中保存了时间趋势数据
5. 分析输出结果，遵循如下规则
	* 识别异常趋势
	* 基于历史数据预测风险
	* 生成详细质量分析报告
	* 描述业务的整体质量变化
	* status 字段可被自定义，常见值类似于 `status_3`，无法直接分析，建议绕开此字段。

## MCP 工具调用指南

关于 TAPD 平台 MCP 工具的使用，请参考以下描述：

1. **获取 TAPD 数据**：使用 `get_tapd_data()` 从 TAPD 平台获取需求和缺陷数据，获得的数据将保存在本地 `local_data\msg_from_fetcher.json` 用于后续处理。请定期更新本地数据，以确保数据的准确性和时效性。
	* 当数据量较小（如小于 50 条）时，可以使用 `get_tapd_stories()` 与 `get_tapd_bugs()` 直接从 API 获取未经处理的数据，但不会保存至本地。
	* 或者使用 `generate_fake_tapd_data(n_story_A, n_story_B, n_bug_A, n_bug_B, output_path)` 生成假数据，可用于测试模拟，此操作会覆盖本地 JSON 数据，重新使用 `get_tapd_data()` 可恢复。假数据默认存储于 `local_data\fake_tapd.json`

2. **生成项目概览（可选）**：使用 `generate_tapd_overview(since, until, max_total_tokens, use_local_data)` 简要生成项目概览报告与摘要，用于了解项目概况（需要在环境中配置 DeepSeek API，需要提醒用户）。
	* `use_local_data=True`（默认）：使用本地数据文件进行分析，适合测试和离线分析
	* `use_local_data=False`：从TAPD API获取最新数据进行分析，适合实时数据分析
	* 注意，此功能仅生成概览，不推荐优先使用。

3. **预处理 description 功能**：使用`preprocess_tapd_description(data_file_path, output_file_path, use_api, process_documents, process_images)` 清理TAPD数据中description字段的HTML样式，提取有意义内容并通过 DeepSeek API 优化表达，压缩数据长度同时保留关键信息
	* **预处理预览功能**：`preview_tapd_description_cleaning(data_file_path, item_count)` 预览description字段清理效果，展示压缩比例和提取信息，不修改原始数据
	* `output_file_path` 默认存储于 `local_data/msg_from_fetcher.json`
	* `use_api=True` 将会使用 DeepSeek API，默认为 True，需要提醒用户进行配置。

4. **生成词频统计**：使用 `analyze_word_frequency(min_frequency, use_extended_fields, data_file_path)` 方法生成词频统计，用于为之后的搜索功能提供精准关键词建议。
    * `min_frequency`：设置最小词频阈值，默认值为 3。可以根据数据量和需求调整此参数。
    * `use_extended_fields`：是否使用扩展字段进行分析，默认值为 True。若设置为 False，则仅分析核心字段。
    * `data_file_path`：指定 TAPD 数据文件路径，默认为 `local_data/msg_from_fetcher.json`。

5. **向量化处理数据**：使用 `vectorize_data(data_file_path: Optional[str] = None, chunk_size: int = 10)` 对获取的数据进行向量化处理，以便 AI 模型进行分析和预测。首次使用向量化功能时需要连接 VPN 以下载模型文件，需要提醒用户。
	* `data_file_path` 为数据文件路径，默认为 `local_data\msg_from_fetcher.json`。
		* 向量化处理可能需要较长时间，具体取决于数据量和模型复杂度。
	`chunk_size` 为分片大小，即每个分片包含的条目数，默认10条：
		* 推荐值：10-20（平衡精度与效率）
		* 较小值：搜索更精准，但分片更多，处理时间略长
		* 较大值：减少分片数量，处理时间短，搜索结果可能不精准

6. **检查向量化处理结果**：使用 `get_vector_info()` 检查向量化处理的结果。确保数据已成功转换为向量格式，并可以被 AI 模型有效利用。

7. **数据查询**：使用 `search_data(query: str, top_k: int = 5)` 进行数据查询。通过输入自然语言查询，AI 模型将返回与查询相关的最相关数据条目。此功能支持模糊查询和关键词搜索。
	* 用户可以根据需要调整 `top_k` 参数以获取更多或更少的结果。当数据量较大时，需要增加 `top_k` 的值以获取更多相关结果，防止遗漏。
	* `query` 参数表示用户输入的查询内容，可以是任何文本，如订单号、客户名称、产品名称等。若用户未指定查询内容，请参照以下示例进行查询：
		* "查找订单相关的需求"
		* "用户评价功能的缺陷"
		* "高优先级的开发任务"

8. **趋势分析**：使用 `analyze_time_trends(data_type: str = "story", chart_type: str = "count", time_field: str = "created", since: str = None, until: str = None, data_file_path: str = "local_data/msg_from_fetcher.json")` 进行趋势分析。该功能将根据数据中的时间序列信息，识别出趋势、季节性变化和异常情况。用户可以根据分析结果，调整项目计划和资源分配，以确保项目按计划进行。
    1. 选择数据类型 (data_type)
		* story : 分析需求数据
		* bug : 分析缺陷数据
	2. 选择图表类型 (chart_type)
		* count : 数量趋势 - 显示每日/每周数据总量变化
		* priority : 优先级分布 - 显示高中低优先级的数据分布
		* status : 状态分布 - 显示不同状态的数据分布
	3. 选择时间字段 (time_field)
		* created : 创建时间 - 分析数据创建的时间趋势
		* modified : 修改时间 - 分析数据更新的时间趋势
	4. 设置时间范围 (since 和 until)
		* 格式：YYYY-MM-DD
		* 建议时间跨度：7-30天以获得有意义的时间趋势
		* 可根据分析需求调整时间范围
    5. 查看生成结果
		* 提醒用户：图表文件保存在： local_data/time_trend/ 目录
		* 文件名格式： {数据类型}_{图表类型}_时间戳.png
		* 返回的JSON数据包含详细的统计信息和图表路径

## 特别注意

**所有的思考与回答都需要经过一步步严谨细致的思考，请确保你输出的内容准确无误。**
