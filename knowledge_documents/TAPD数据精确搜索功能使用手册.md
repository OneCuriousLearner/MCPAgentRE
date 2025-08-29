# TAPD数据精确搜索功能使用手册

## 功能概述

TAPD数据精确搜索功能提供了强大的数据检索能力，支持对TAPD需求和缺陷数据进行精确匹配搜索。该功能包含三个主要MCP工具，可以满足不同的搜索需求。

## 功能特性

### 🔍 核心功能
- **精确字段匹配搜索** - 支持对任何字段进行精确或模糊搜索
- **优先级筛选** - 快速筛选高、中、低优先级数据
- **数据统计分析** - 提供全面的数据分布统计信息
- **灵活搜索选项** - 支持大小写敏感、精确匹配等选项
- **结果导出** - 支持将搜索结果导出为JSON文件

### 📊 支持的数据类型
- **需求数据 (stories)** - 项目需求、任务、用户故事等
- **缺陷数据 (bugs)** - 缺陷报告、问题记录等
- **混合搜索 (both)** - 同时搜索需求和缺陷数据

## MCP工具详解

### 1. precise_search_tapd_data - 精确搜索工具

#### 功能描述
对TAPD数据进行精确的字段搜索，支持全字段搜索或指定字段搜索。

#### 参数说明
```
search_value (str): 搜索值，要查找的内容
search_field (str, optional): 搜索字段，None表示搜索所有字段
data_type (str): 数据类型 - 'stories'(需求), 'bugs'(缺陷), 'both'(两者)
exact_match (bool): 是否精确匹配 - True=完全相等, False=包含匹配
case_sensitive (bool): 是否区分大小写
```

#### 支持的搜索字段

**需求字段 (stories)**
- `id` - 需求ID
- `name` - 需求名称
- `description` - 需求描述
- `creator` - 创建者
- `priority` - 优先级数值 (1-4)
- `priority_label` - 优先级标签 (Nice To Have, Low, Middle, High)
- `status` - 状态
- `created` - 创建时间
- `modified` - 修改时间
- `begin` - 开始时间
- `due` - 截止时间

**缺陷字段 (bugs)**
- `id` - 缺陷ID
- `title` - 缺陷标题
- `description` - 缺陷描述
- `reporter` - 报告者
- `priority` - 优先级 (insignificant, low, medium, high, urgent)
- `severity` - 严重程度 (advice, prompt, normal, serious, fatal)
- `status` - 状态 (new, in_progress, resolved, closed, rejected, reopened)
- `created` - 创建时间
- `modified` - 修改时间

#### 使用示例

**1. 根据ID精确查找**
```json
{
  "search_value": "1148591566001000001",
  "search_field": "id",
  "data_type": "both",
  "exact_match": true
}
```

**2. 搜索特定创建者的所有任务**
```json
{
  "search_value": "张凯晨",
  "search_field": "creator",
  "data_type": "stories"
}
```

**3. 模糊搜索包含关键词的标题**
```json
{
  "search_value": "登录",
  "search_field": "name",
  "exact_match": false,
  "case_sensitive": false
}
```

**4. 搜索所有字段包含特定关键词**
```json
{
  "search_value": "前端开发",
  "search_field": null,
  "exact_match": false
}
```

### 2. search_tapd_by_priority - 优先级搜索工具

#### 功能描述
根据优先级快速筛选TAPD数据，支持预设优先级和具体优先级标签。

#### 参数说明
```
priority_filter (str): 优先级过滤器
data_type (str): 数据类型
```

#### 优先级映射

**需求优先级 (数字越大越紧急)**
- `1` → Nice To Have (最低)
- `2` → Low (低)
- `3` → Middle (中)
- `4` → High (高)

**缺陷优先级**
- `insignificant` → 微不足道
- `low` → 低
- `medium` → 中
- `high` → 高
- `urgent` → 紧急

#### 预设过滤器
- `high` - 高优先级 (需求: 3,4; 缺陷: high,urgent)
- `medium` - 中优先级 (需求: 3; 缺陷: medium)
- `low` - 低优先级 (需求: 1,2; 缺陷: low,insignificant)
- `all` - 所有优先级

#### 使用示例

**1. 查找所有高优先级项目**
```json
{
  "priority_filter": "high",
  "data_type": "both"
}
```

**2. 查找紧急缺陷**
```json
{
  "priority_filter": "urgent",
  "data_type": "bugs"
}
```

**3. 查找特定优先级标签的需求**
```json
{
  "priority_filter": "High",
  "data_type": "stories"
}
```

### 3. get_tapd_data_statistics - 数据统计工具

#### 功能描述
提供TAPD数据的全面统计分析，包含数量分布、优先级分布、状态分布等。

#### 参数说明
```
data_type (str): 数据类型 - 'stories', 'bugs', 'both'
```

#### 统计内容

**需求统计**
- 总数量
- 优先级分布
- 状态分布
- 创建者分布
- 最近项目数 (7天内)
- 已完成项目数
- 高优先级项目数

**缺陷统计**
- 总数量
- 优先级分布
- 严重程度分布
- 状态分布
- 报告者分布
- 最近缺陷数 (7天内)
- 已解决缺陷数
- 高优先级缺陷数

#### 使用示例

**1. 获取全部数据统计**
```json
{
  "data_type": "both"
}
```

**2. 仅获取需求统计**
```json
{
  "data_type": "stories"
}
```

## 返回结果格式

### 搜索结果结构
```json
{
  "stories": [
    {
      "id": "需求ID",
      "name": "需求名称",
      "description": "需求描述",
      "_match_info": {
        "matched_fields": [
          {
            "field": "匹配字段",
            "value": "字段值",
            "match_type": "exact|partial"
          }
        ],
        "match_count": 1
      }
    }
  ],
  "bugs": [
    {
      "id": "缺陷ID",
      "title": "缺陷标题",
      "description": "缺陷描述",
      "_match_info": {
        "matched_fields": [...],
        "match_count": 1
      }
    }
  ],
  "summary": {
    "total_stories": 10,
    "total_bugs": 5,
    "total_items": 15,
    "search_params": {
      "search_value": "搜索值",
      "search_field": "搜索字段",
      "data_type": "both",
      "exact_match": true,
      "case_sensitive": false
    }
  }
}
```

### 统计结果结构
```json
{
  "stories": {
    "total_count": 44,
    "priority_distribution": {
      "1 (Nice To Have)": 6,
      "2 (Low)": 0,
      "3 (Middle)": 10,
      "4 (High)": 28
    },
    "status_distribution": {
      "status_4": 15,
      "status_5": 18,
      "status_6": 11
    },
    "creator_distribution": {
      "张凯晨": 9,
      "TAPD": 35
    },
    "recent_items": 6,
    "completed_items": 11,
    "high_priority_items": 38
  },
  "bugs": {
    "total_count": 22,
    "priority_distribution": {
      "insignificant": 1,
      "low": 3,
      "medium": 10,
      "high": 3,
      "urgent": 5
    },
    "severity_distribution": {
      "advice": 3,
      "prompt": 4,
      "normal": 6,
      "serious": 5,
      "fatal": 4
    },
    "status_distribution": {
      "new": 16,
      "in_progress": 1,
      "resolved": 1,
      "closed": 1,
      "rejected": 1,
      "reopened": 1
    },
    "recent_items": 16,
    "resolved_items": 2,
    "high_priority_items": 8
  }
}
```

## 高级功能

### 搜索结果导出
搜索器还提供了结果导出功能，可以将搜索结果保存为JSON文件：

```python
from mcp_tools.data_precise_searcher import get_searcher

searcher = get_searcher()
results = searcher.search_by_field("前端", exact_match=False)
export_result = searcher.export_results(results, "search_results.json")
```

### 高级搜索参数
搜索器的 `advanced_search` 方法支持更多高级参数：

```python
search_params = {
    'text_search': '前端',                    # 文本搜索
    'search_fields': ['name', 'description'], # 搜索字段列表
    'data_type': 'both',                      # 数据类型
    'priority_filter': 'high',                # 优先级过滤
    'status_filter': 'status_4',              # 状态过滤
    'creator_filter': '张凯晨',               # 创建者过滤
    'date_range': {                           # 日期范围
        'start': '2025-08-01',
        'end': '2025-08-31'
    },
    'exact_match': False,                     # 精确匹配
    'case_sensitive': False,                  # 大小写敏感
    'sort_by': 'created',                     # 排序字段
    'sort_order': 'desc',                     # 排序顺序
    'limit': 10                               # 结果限制
}

results = searcher.advanced_search(search_params)
```

## 使用场景

### 1. 项目管理场景
- **查找特定人员的任务**: 搜索creator或reporter字段
- **跟踪高优先级项目**: 使用优先级搜索快速定位重要任务
- **状态监控**: 搜索特定状态的项目，了解项目进展

### 2. 质量管理场景
- **缺陷分析**: 按严重程度、优先级筛选缺陷
- **趋势监控**: 统计数据分布，了解质量趋势
- **问题定位**: 精确搜索特定ID的缺陷记录

### 3. 数据分析场景
- **工作负载分析**: 统计不同人员的任务分布
- **项目健康度评估**: 分析高优先级项目占比
- **时间分析**: 结合时间字段进行趋势分析

## 注意事项

1. **数据文件依赖**: 需要先调用 `get_tapd_data` 工具获取最新数据
2. **大小写处理**: 默认不区分大小写，可通过参数调整
3. **日期格式**: 支持 'YYYY-MM-DD' 和 'YYYY-MM-DD HH:MM:SS' 格式
4. **性能考虑**: 大数据集建议使用精确匹配而非模糊搜索
5. **字段名称**: 请使用正确的字段名称，区分needs和bugs的不同字段

## 错误处理

工具提供了完善的错误处理机制：

- **文件不存在**: 提示先获取TAPD数据
- **参数错误**: 提供参数格式说明
- **搜索无结果**: 返回空结果集但不报错
- **字段不存在**: 自动忽略不存在的字段

## 更新记录

- **2025-08-29**: 初始版本发布
  - 支持精确字段搜索
  - 支持优先级筛选
  - 支持数据统计分析
  - 提供完整的MCP工具接口
