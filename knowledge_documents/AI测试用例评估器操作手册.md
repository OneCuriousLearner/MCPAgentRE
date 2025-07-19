# AI 测试用例评估器操作手册

## 目录

1. [系统概述](#1-系统概述)
2. [组件介绍](#2-组件介绍)
   - [测试用例规则自定义配置（test_case_rules_customer.py）](#21-测试用例规则自定义配置test_case_rules_customerpy)
   - [需求单知识库（test_case_require_list_knowledge_base.py）](#22-需求单知识库test_case_require_list_knowledge_basepy)
   - [测试用例评估器（test_case_evaluator.py）](#23-测试用例评估器test_case_evaluatorpy)
3. [使用流程](#3-使用流程)
   - [准备工作](#31-准备工作)
   - [规则配置](#32-规则配置)
   - [需求单管理](#33-需求单管理)
   - [执行评估](#34-执行评估)
   - [结果解读](#35-结果解读)
4. [高级功能](#4-高级功能)
   - [批量处理优化](#41-批量处理优化)
   - [Token 管理策略](#42-token-管理策略)
   - [结果数据分析](#43-结果数据分析)
5. [常见问题与解决方案](#5-常见问题与解决方案)
6. [开发者文档](#6-开发者文档)

## 1. 系统概述

AI 测试用例评估器是一个综合性工具集，用于自动评估测试用例的质量并提供改进建议。系统基于大型语言模型（LLM）对测试用例进行分析，支持批量处理大量测试用例，并通过自定义规则和需求单关联来保证评估的准确性和相关性。

### 核心优势：

- **自动化评估**：无需人工逐条审核，大幅提高测试质量管理效率
- **一致性标准**：基于可配置的规则，确保所有测试用例遵循统一标准
- **需求关联**：通过需求单知识库，确保测试用例与业务需求的紧密关联
- **详细建议**：针对每个测试用例提供具体、可操作的改进建议
- **批量处理**：智能 Token 管理，支持大量测试用例的批次处理
- **性能统计**：提供优先级分布分析、处理时间等统计信息

### 系统架构：

系统由三个主要组件组成，各司其职，协同工作：

1. **规则配置模块**（test_case_rules_customer.py）：管理评估标准
2. **需求单知识库**（test_case_require_list_knowledge_base.py）：提供业务背景知识
3. **评估引擎**（test_case_evaluator.py）：执行评估、解析结果并生成报告

## 2. 组件介绍

### 2.1 测试用例规则自定义配置（test_case_rules_customer.py）

#### 功能概述

该组件提供了一个灵活的配置管理系统，允许用户自定义测试用例评估的规则参数。

#### 主要功能：

- **参数配置**：标题长度限制、步骤数上限、各优先级占比范围
- **持久化存储**：配置保存至 local_data/test_case_rules.json
- **交互式界面**：支持命令行交互式修改配置
- **配置验证**：确保所有参数在合理范围内

#### 数据结构：

```json
{
  "title_max_length": 40,       // 标题最大字符数
  "max_steps": 10,              // 测试步骤最大数量
  "priority_ratios": {          // 优先级占比配置
    "P0": {"min": 10, "max": 20},
    "P1": {"min": 60, "max": 70},
    "P2": {"min": 10, "max": 30}
  },
  "version": "1.0",
  "last_updated": "2025-07-19T10:30:45.123456"
}
```

#### 使用方法：

```bash
# 查看当前配置
python mcp_tools/test_case_rules_customer.py

# 交互式修改配置
python mcp_tools/test_case_rules_customer.py --config

# 重置为默认配置
python mcp_tools/test_case_rules_customer.py --reset
```

#### 代码架构：

- `TestCaseRulesCustomer` 类：规则配置管理的核心类
  - `load_config()`: 从文件加载配置或使用默认配置
  - `save_config()`: 保存配置到文件
  - `_validate_config()`: 验证配置有效性
  - `interactive_config()`: 交互式配置界面
  - `reset_to_default()`: 重置为默认配置
  - `_display_config()`: 展示配置信息

- `get_test_case_rules()`: 供其他模块调用的接口函数

### 2.2 需求单知识库（test_case_require_list_knowledge_base.py）

#### 功能概述

需求单知识库用于管理与测试用例相关的业务需求信息，为测试用例评估提供业务背景。

#### 主要功能：

- **需求数据管理**：添加、查看、删除需求单信息
- **数据提取**：从 local_data/msg_from_fetcher.json 自动提取需求单
- **数据格式化**：将需求单内容格式化为评估系统可用的格式
- **持久化存储**：保存至 local_data/require_list_config.json

#### 数据结构：

```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "title": "用户登录功能",
      "description": "实现用户账号密码登录系统的功能",
      "priority": "高",
      "local_created_time": "2025-07-19 10:30:45"
    },
    // 更多需求...
  ]
}
```

#### 使用方法：

```bash
# 启动需求单知识库管理界面
python mcp_tools/test_case_require_list_knowledge_base.py
```

交互式菜单选项：
1. 从本地JSON提取需求单
2. 手动添加需求单
3. 查看所有需求单
4. 删除需求单
5. 清空需求单
0. 退出

#### 代码架构：

- `RequirementKnowledgeBase` 类：需求单知识库的核心类
  - `_load_requirements()`: 加载需求单数据
  - `_save_requirements()`: 保存需求单数据
  - `extract_from_local_data()`: 从本地JSON提取需求单
  - `add_manual_requirement()`: 手动添加需求单
  - `show_requirements()`: 显示所有需求单
  - `delete_requirements()`: 删除指定需求单
  - `clear_all_requirements()`: 清空需求单
  - `get_requirements_for_evaluation()`: 格式化需求单以供评估使用

- `main()`: 启动交互式命令行界面

### 2.3 测试用例评估器（test_case_evaluator.py）

#### 功能概述

测试用例评估器是系统的核心引擎，负责读取测试用例、分批处理、调用 AI 进行评估，并解析评估结果。

#### 主要功能：

- **数据处理**：Excel 文件转换为 JSON 格式
- **Token 管理**：智能分批处理测试用例以适应 LLM 上下文窗口
- **AI 评估**：构建动态提示词，调用 AI API 进行评估
- **结果解析**：将 AI 返回的 Markdown 表格转换为结构化数据
- **优先级分析**：分析测试用例优先级分布是否符合规则要求
- **时间统计**：记录处理时间，计算平均处理速度

#### 类与模块：

1. **TokenCounter**：负责计算文本的 token 数量
   - 优先使用本地 `transformers` tokenizer 进行精确计算
   - 如无法使用，则使用改进的预估模式

2. **TestCaseProcessor**：处理 Excel 测试用例数据
   - 将 Excel 转换为 JSON 格式
   - 处理字段映射和数据清理

3. **TestCaseEvaluator**：核心评估器类
   - 根据规则动态构建提示词模板
   - 估算批次 token 数量
   - 分割测试用例到适当批次
   - 执行评估并解析结果

#### Token 管理策略：

评估器采用多层次的 Token 管理策略：
- **总上下文分配**：从总上下文中预留 25% 作为缓冲
- **可用 Token 分配**：
  - 25% 用于请求（测试用例数据）
  - 50% 用于响应（AI 评估结果）
  - 25% 作为缓冲
- **批次安全阈值**：请求 Token 的 75% 作为批次阈值，增加安全余量

#### 使用方法：

```bash
# 运行评估器处理所有测试用例
python mcp_tools/test_case_evaluator.py

# 测试模式（仅处理一批）可通过修改代码 main_process(test_batch_count=1) 实现
```

#### 处理流程：

1. 读取测试用例数据（Excel 或已转换的 JSON）
2. 分析测试用例优先级分布
3. 自动将测试用例分割为多个批次
4. 对每个批次进行 AI 评估
5. 解析评估结果
6. 汇总结果并保存

#### 评估结果格式：

```json
{
  "evaluation_results": [
    {
      "test_case_id": "TC-001",
      "evaluations": [
        {
          "field": "用例标题",
          "content": "验证用户登录",
          "score": "8",
          "suggestion": "改为\"验证错误密码登录的失败提示\""
        },
        // 更多评估项...
      ]
    },
    // 更多测试用例...
  ],
  "total_count": 50,
  "generated_at": "20250717141033-32202633",
  "process_start_time": "2025-07-19 10:30:45",
  "process_end_time": "2025-07-19 10:35:12",
  "priority_analysis": {
    "distribution": {
      "P0": 15.0,
      "P1": 65.0,
      "P2": 20.0
    },
    "compliance": {
      "P0": {
        "count": 7,
        "percentage": 15.0,
        "is_compliant": true,
        "reason": "符合要求：10% ~ 20%"
      },
      // 更多优先级合规性信息...
    },
    "rules": {
      // 规则配置参考
    }
  }
}
```

## 3. 使用流程

### 3.1 准备工作

1. **测试用例准备**
   - 准备符合格式的 Excel 文件，放置在 local_data 目录下
   - 文件命名格式为 "TestCase_[时间戳].xlsx"
   - Excel 必须包含以下列：用例ID、用例标题、前置条件、步骤描述、预期结果、等级（优先级）

2. **环境配置**
   - 确保已安装所需依赖包（pandas、aiohttp 等）
   - 设置正确的 API 密钥（用于调用 AI 模型）
   - 可选：下载 DeepSeek tokenizer 以提高 token 计算精度

### 3.2 规则配置

1. 查看当前评估规则
   ```bash
   python mcp_tools/test_case_rules_customer.py
   ```

2. 根据项目需求修改规则
   ```bash
   python mcp_tools/test_case_rules_customer.py --config
   ```
   
   关注以下关键配置：
   - 标题长度限制：推荐设置为 30-50 字符
   - 步骤数上限：根据项目复杂度设置，通常为 8-12 步
   - 优先级占比：根据项目质量要求和测试策略设置

### 3.3 需求单管理

1. 启动需求单知识库管理界面
   ```bash
   python mcp_tools/test_case_require_list_knowledge_base.py
   ```

2. 从 TAPD 数据中提取需求单（选项 1）
   - 确保 local_data/msg_from_fetcher.json 文件存在且包含最新需求数据
   - 系统将自动提取需求 ID、标题和描述

3. 查看已添加的需求单（选项 3）
   - 确认提取的需求单数量和内容是否符合预期

4. 必要时手动添加额外需求单（选项 2）
   - 输入需求 ID、标题和描述信息

### 3.4 执行评估

1. 运行评估器
   ```bash
   python mcp_tools/test_case_evaluator.py
   ```

2. 评估过程中观察输出信息：
   - 测试用例优先级分布分析
   - 批次处理进度
   - Token 使用情况
   - 处理时间统计

3. 等待评估完成
   - 评估结果将保存到 local_data/Proceed_TestCase_[时间戳].json 文件

### 3.5 结果解读

评估结果包含以下关键部分：

1. **测试用例评估详情**
   - 每个测试用例的各个方面（标题、前置条件、步骤、预期结果）的评分
   - 针对性的改进建议

2. **优先级分布分析**
   - 各优先级（P0、P1、P2）的数量和百分比
   - 与规则要求的符合度分析

3. **处理性能数据**
   - 开始和结束时间
   - 总处理时间
   - 平均每条数据处理时间

## 4. 高级功能

### 4.1 批量处理优化

对于大量测试用例（>100 条），可以考虑以下优化：

1. **修改 Token 阈值**：
   - 调整 `self.token_threshold` 的计算比例（默认为 `max_request_tokens` 的 75%）
   - 更大的阈值可以增加每批处理的测试用例数量，但增加失败风险

2. **上下文窗口扩大**：
   - 修改 `main_process` 中的 `max_context_tokens` 参数（默认为 12000）
   - 对于支持更大上下文的模型，可以适当增加

3. **批次间延迟调整**：
   - 修改 `evaluate_test_cases` 方法中的 `await asyncio.sleep(1)` 参数
   - 根据 API 限制调整，避免触发频率限制

### 4.2 Token 管理策略

系统采用三层 Token 管理策略：

1. **总量分配**：
   - 总上下文 = 请求 tokens + 响应 tokens + 缓冲
   - 提示词模板基础 tokens 从总量中预先扣除

2. **比例分配**：
   - 25% 用于请求（测试用例数据）
   - 50% 用于响应（AI 生成结果）
   - 25% 留作缓冲

3. **批次安全阈值**：
   - 实际添加测试用例时使用 `token_threshold`（请求 tokens 的 75%）
   - 为单个批次提供额外安全边界

### 4.3 结果数据分析

评估结果提供多维度分析：

1. **分数分布**：
   - 可计算各评估项目（标题、步骤等）的平均分数
   - 识别团队共同的薄弱环节

2. **优先级合规性**：
   - `priority_analysis.compliance` 字段提供详细的合规分析
   - 根据分析结果调整测试策略

3. **性能指标**：
   - 通过平均处理时间估算大批量评估的时间成本
   - 优化 Token 管理策略和批次大小

## 5. 常见问题与解决方案

### 问题：评估结果为空或解析失败

**可能原因**：
- AI 返回格式不符合预期
- 提示词模板可能需要调整
- Token 限制过严导致截断

**解决方案**：
1. 检查 AI 返回的原始结果（控制台输出）
2. 调整 `max_response_tokens` 参数
3. 修改 `parse_evaluation_result` 方法以适应不同格式

### 问题：批次处理中断或失败

**可能原因**：
- API 调用限制或网络问题
- Token 超限
- 服务端错误

**解决方案**：
1. 增加 `asyncio.sleep()` 延迟
2. 减小批次大小（调整 `token_threshold`）
3. 实现断点续传功能（保存处理进度）

### 问题：需求单提取数量不足

**可能原因**：
- local_data/msg_from_fetcher.json 数据不完整
- 需求数据格式与预期不符

**解决方案**：
1. 检查 msg_from_fetcher.json 文件内容
2. 手动添加关键需求单
3. 调整提取逻辑以适应不同格式

### 问题：优先级分布不符合规则要求

**可能原因**：
- 测试用例等级设置不合理
- 规则配置与项目实际情况不符

**解决方案**：
1. 根据分析结果调整测试用例优先级
2. 修改规则配置以适应项目需求
3. 针对特定模块重新设计测试策略

## 6. 开发者文档

### 系统扩展点

1. **提示词模板扩展**：
   - 修改 `_build_dynamic_prompt_template` 方法可自定义评估标准
   - 添加新的评估维度

2. **结果解析扩展**：
   - 增强 `parse_evaluation_result` 方法以解析更复杂的返回格式
   - 提取更多评估指标

3. **批量处理机制**：
   - 实现断点续传功能
   - 添加并行处理多个批次的能力

### 代码优化建议

1. **异常处理增强**：
   - 为每个 API 调用添加重试机制
   - 更详细的错误日志记录

2. **结果输出多样化**：
   - 支持导出为 Excel、HTML 等格式
   - 生成可视化评估报告

3. **性能优化**：
   - 使用异步批处理增加并发能力
   - 本地缓存 tokenizer 模型减少加载时间

### 集成指南

将评估器集成到现有系统：

1. **作为模块导入**：
   ```python
   from mcp_tools.test_case_evaluator import TestCaseEvaluator
   
   # 初始化评估器
   evaluator = TestCaseEvaluator(max_context_tokens=12000)
   
   # 读取测试用例
   # ...
   
   # 执行评估
   evaluations = await evaluator.evaluate_test_cases(test_cases)
   ```

2. **命令行调用**：
   ```bash
   python -c "from mcp_tools.test_case_evaluator import main_process; \
              import asyncio; \
              asyncio.run(main_process(test_batch_count=None))"
   ```

3. **API 化**：
   - 考虑将评估器包装为 REST API 服务
   - 添加 API 身份验证和限流机制

---

## 附录

### 相关配置文件路径

- **规则配置**：local_data/test_case_rules.json
- **需求单知识库**：local_data/require_list_config.json
- **输入数据**：local_data/TestCase_[时间戳].xlsx
- **输出结果**：local_data/Proceed_TestCase_[时间戳].json
- **TAPD 数据**：local_data/msg_from_fetcher.json

### 命令速查表

```bash
# 查看规则配置
python mcp_tools/test_case_rules_customer.py

# 修改规则配置
python mcp_tools/test_case_rules_customer.py --config

# 管理需求单知识库
python mcp_tools/test_case_require_list_knowledge_base.py

# 运行评估器
python mcp_tools/test_case_evaluator.py
```

---

文档版本：1.0  
最后更新：2025年7月19日
