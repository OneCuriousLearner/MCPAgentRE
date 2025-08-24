# TAPD数据词频分析工具使用手册

## 功能概述

词频分析工具(`analyze_word_frequency`)是一个专门为TAPD数据设计的关键词提取和统计分析工具。它能够从TAPD需求和缺陷数据中智能提取关键词，统计词频分布，并为搜索功能提供精准的关键词建议。

**最新优化**: 经过2025年7月的停用词优化，工具现在能更好地保留TAPD业务相关的关键词，如"缺陷"、"需求"、"功能"、"测试"等，词频分析的准确性和实用性得到显著提升。

## 主要特性

### 1. 智能中文分词

- 使用jieba分词库进行中文文本处理
- 自动识别和分割中文词汇
- 支持中英文混合文本处理

### 2. 精准停用词过滤

- **优化后的停用词策略**: 只过滤真正无意义的高频词汇，保留所有业务价值词汇
- **保留的关键词类型**:
  - 缺陷相关: 问题、解决、修复、bug、缺陷、错误、异常、故障
  - 需求相关: 需求、功能、特性、模块、系统、平台、服务、接口、API
  - 角色相关: 用户、客户、管理员、开发、测试、运维、产品
  - 流程相关: 业务、流程、步骤、进行、实现、完成、处理、操作
- **过滤的无意义词**: 语言连词、代词、时间副词等真正的停用词

### 3. 多字段文本提取

- **核心字段**：name、description、test_focus、label
- **扩展字段**：acceptance、comment、status、priority、iteration_id
- 支持灵活配置字段范围

### 4. 频次统计与分析

- 可配置最小频次阈值
- 生成详细的频次分布统计
- 按词频排序，突出高频关键词

### 5. 增强的关键词分类

- **问题缺陷类**: 问题、解决、修复、bug、缺陷、错误、异常、故障等
- **需求功能类**: 需求、功能、特性、优化、改进、新增、删除、变更等
- **技术实现类**: 模块、系统、平台、服务、接口、API、数据库、框架等
- **角色人员类**: 用户、客户、管理员、开发、测试、运维、产品等
- **业务流程类**: 业务、流程、步骤、环节、阶段、过程、方案、策略等
- **状态描述类**: 完成、待处理、进行中、成功、失败、正常、异常等

## 使用方法

### 基本调用

```json
{
  "tool": "analyze_word_frequency"
}
```

### 带参数调用

```json
{
  "tool": "analyze_word_frequency",
  "arguments": {
    "min_frequency": 5,
    "use_extended_fields": true,
    "data_file_path": "local_data/msg_from_fetcher.json"
  }
}
```

## 参数说明

### min_frequency (整数，默认3)

设置最小词频阈值，只返回出现次数不少于此值的词汇。

**推荐设置：**

- 小型项目（<100条数据）：min_frequency = 2
- 中型项目（100-1000条数据）：min_frequency = 3-5
- 大型项目（>1000条数据）：min_frequency = 5-10

### use_extended_fields (布尔值，默认True)

控制是否使用扩展字段进行分析。

**True**：分析所有字段（name、description、test_focus、label、acceptance、comment、status、priority、iteration_id）
**False**：仅分析核心字段（name、description、test_focus、label）

### data_file_path (字符串，默认"local_data/msg_from_fetcher.json")

指定TAPD数据文件路径。

## 返回结果结构

### 成功响应

```json
{
  "status": "success",
  "analysis_config": {
    "min_frequency": 3,
    "use_extended_fields": true,
    "analyzed_fields": ["name", "description", "test_focus", "label", "acceptance", "comment", "status", "priority", "iteration_id"]
  },
  "statistics": {
    "total_words": 15432,
    "unique_words": 3241,
    "high_frequency_words": 156,
    "stories_count": 245,
    "bugs_count": 312,
    "total_items": 557
  },
  "word_frequency": {
    "high_frequency_words": {
      "用户": 89,
      "系统": 76,
      "功能": 65,
      "订单": 54,
      "...": "..."
    },
    "frequency_distribution": {
      "100+": 3,
      "50-99": 8,
      "20-49": 15,
      "10-19": 28,
      "5-9": 45,
      "1-4": 3142
    },
    "top_20_words": {
      "用户": 89,
      "系统": 76,
      "...": "..."
    }
  },
  "search_suggestions": {
    "recommended_keywords": ["用户", "系统", "功能", "订单", "支付"],
    "category_keywords": {
      "技术相关": ["接口", "数据库", "算法"],
      "业务功能": ["订单", "支付", "用户"],
      "状态描述": ["完成", "待处理", "异常"]
    }
  }
}
```

### 错误响应

```json
{
  "status": "error",
  "message": "数据文件不存在: local_data/msg_from_fetcher.json",
  "suggestion": "请先调用 get_tapd_data 工具获取数据"
}
```

## 应用场景

### 1. 搜索关键词优化

使用分析结果中的`recommended_keywords`来改进`simple_search_data`和`advanced_search_data`的查询准确性。

### 2. 项目词云可视化

基于`word_frequency`数据生成词云图，直观展示项目重点关注领域。

### 3. 业务领域分析

通过`category_keywords`了解项目在技术、业务、流程等各方面的分布情况。

### 4. 质量分析报告

结合词频统计生成项目质量分析报告，识别常见问题和关注点。

## 最佳实践

### 1. 数据预处理

在进行词频分析前，确保已通过`get_tapd_data`获取最新数据。

### 2. 参数调优

根据项目规模调整`min_frequency`参数：

- 数据量少时降低阈值，避免漏掉重要关键词
- 数据量大时提高阈值，聚焦高频核心词汇

### 3. 字段选择

- 追求完整性时使用`use_extended_fields=true`
- 关注核心内容时使用`use_extended_fields=false`

### 4. 结果应用

- 将`recommended_keywords`作为搜索查询的参考
- 使用`category_keywords`进行分类搜索
- 结合`frequency_distribution`了解词汇分布特征

## 注意事项

1. **依赖项**：工具依赖jieba分词库，首次使用时会自动安装
2. **中文优化**：停用词和分词策略专门针对中文优化
3. **性能考虑**：大数据量分析可能需要较长时间，建议合理设置阈值
4. **更新频率**：当TAPD数据更新后，建议重新进行词频分析以获取最新关键词

## 故障排除

### 问题1：数据文件不存在

**解决方案**：先调用`get_tapd_data`工具获取TAPD数据

### 问题2：分析结果为空

**可能原因**：min_frequency设置过高或数据量不足
**解决方案**：降低min_frequency参数值

### 问题3：中文分词效果不理想

**解决方案**：检查输入数据的编码格式，确保为UTF-8

### 问题4：内存使用过高

**解决方案**：设置更高的min_frequency阈值，减少低频词的处理
