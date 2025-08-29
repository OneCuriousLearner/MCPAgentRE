# TAPD时间趋势分析工具使用手册

## 概述

TAPD时间趋势分析工具是TAPD平台MCP服务器的核心功能模块，专门用于分析需求（story）和缺陷（bug）数据的时间趋势，并生成高质量的可视化图表。该工具支持多种统计维度和图表类型，为项目管理和质量分析提供数据支撑。

## 主要功能

### 1. 数据类型支持
- **需求数据（story）**: 分析用户故事、需求的时间趋势
- **缺陷数据（bug）**: 分析软件缺陷的时间趋势

### 2. 图表类型
- **总数趋势图（count）**: 显示每日数据总量变化
- **优先级分布图（priority）**: 显示高、中、低优先级数据的时间分布
- **状态分布图（status）**: 显示不同状态数据的时间变化趋势

### 3. 时间字段支持
- **created**: 创建时间（默认）
- **modified**: 修改时间
- **begin**: 开始时间（仅需求数据）
- **due**: 截止时间（仅需求数据）

### 4. 时间范围筛选
- 支持自定义开始时间（since）和结束时间（until）
- 时间格式：YYYY-MM-DD
- 不指定时间范围则分析全部数据

## 使用方法

### MCP工具调用

在MCP环境中，使用 `analyze_time_trends` 工具：

```json
{
  "name": "analyze_time_trends",
  "arguments": {
    "data_type": "story",
    "chart_type": "count",
    "time_field": "created",
    "since": "2025-01-01",
    "until": "2025-08-29",
    "data_file_path": "local_data/msg_from_fetcher.json"
  }
}
```

### 参数说明

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `data_type` | string | "story" | 数据类型：'story'（需求）或 'bug'（缺陷） |
| `chart_type` | string | "count" | 图表类型：'count'（总数）、'priority'（优先级）、'status'（状态） |
| `time_field` | string | "created" | 时间字段：'created'、'modified'、'begin'、'due' |
| `since` | string | null | 开始时间，格式YYYY-MM-DD |
| `until` | string | null | 结束时间，格式YYYY-MM-DD |
| `data_file_path` | string | "local_data/msg_from_fetcher.json" | 数据文件路径 |

### 直接脚本调用

```python
from mcp_tools.time_trend_analyzer import analyze_time_trends

# 分析需求的优先级分布趋势
result = await analyze_time_trends(
    data_type="story",
    chart_type="priority", 
    time_field="created",
    since="2025-01-01",
    until="2025-08-29"
)
```

## 使用场景示例

### 1. 监控项目进度
分析需求创建趋势，了解项目开发节奏：
```json
{
  "data_type": "story",
  "chart_type": "count",
  "time_field": "created",
  "since": "2025-01-01",
  "until": "2025-08-29"
}
```

### 2. 质量分析
分析缺陷发现和解决趋势：
```json
{
  "data_type": "bug", 
  "chart_type": "status",
  "time_field": "created",
  "since": "2025-07-01",
  "until": "2025-08-29"
}
```

### 3. 优先级管理
分析高优先级任务的分布情况：
```json
{
  "data_type": "story",
  "chart_type": "priority",
  "time_field": "begin",
  "since": "2025-06-01",
  "until": "2025-08-29"
}
```

### 4. 里程碑跟踪
分析任务完成情况：
```json
{
  "data_type": "story",
  "chart_type": "count",
  "time_field": "due",
  "since": "2025-08-01",
  "until": "2025-08-31"
}
```

## 输出结果说明

### 成功返回格式
```json
{
  "status": "success",
  "data_type": "story",
  "chart_type": "count", 
  "time_field": "created",
  "time_range": "2025-01-01 到 2025-08-29",
  "total_count": 1250,
  "date_range": {
    "start": "2025-01-15",
    "end": "2025-08-29", 
    "days_count": 156
  },
  "daily_stats": {
    "2025-01-15": {
      "date": "2025-01-15",
      "total_count": 5,
      "completed_count": 2,
      "new_count": 3,
      "high_priority_count": 1,
      "medium_priority_count": 2,
      "low_priority_count": 2,
      "status_counts": {
        "status_1": 2,
        "status_5": 3
      }
    }
  },
  "chart_path": "D:\\...\\local_data\\time_trend\\story_count_20250829_143052.png",
  "chart_url": "file:///D:/.../local_data/time_trend/story_count_20250829_143052.png",
  "generated_at": "2025-08-29 14:30:52"
}
```

### 关键字段解释

- **daily_stats**: 每日统计详情，包含各种维度的计数
- **chart_path**: 生成图表的本地文件路径
- **chart_url**: 图表的文件URL，可直接在浏览器中查看
- **total_count**: 分析期间内的数据总量
- **date_range**: 实际数据的时间范围和天数

## 数据字段映射

### 需求数据（Story）字段
- **name**: 需求名称
- **description**: 需求描述
- **status**: 状态（如status_1, status_5等）
- **priority**: 优先级（1=高，2=中，3=低）
- **priority_label**: 优先级标签（如"Nice To Have"）
- **created**: 创建时间
- **modified**: 修改时间
- **begin**: 开始时间
- **due**: 截止时间

### 缺陷数据（Bug）字段
- **title**: 缺陷标题
- **description**: 缺陷描述
- **status**: 状态（如new, rejected, resolved等）
- **priority**: 优先级（如high, medium, low）
- **severity**: 严重程度
- **created**: 创建时间
- **modified**: 修改时间

## 图表特性

### 1. 中文支持
- 自动配置中文字体（SimHei、Microsoft YaHei）
- 支持中文标题、标签和图例
- 正确处理中文负号显示

### 2. 图表样式
- **尺寸**: 12x6英寸，适合报告展示
- **分辨率**: 300 DPI，高清输出
- **格式**: PNG格式，兼容性好
- **网格**: 半透明网格线，便于读数

### 3. 时间轴处理
- 自动格式化日期显示（MM-DD格式）
- 智能调整日期标签间隔
- 45度旋转避免重叠

### 4. 颜色方案
- **总数趋势**: 蓝色线条+圆点标记
- **高优先级**: 红色线条+圆点标记
- **中优先级**: 黄色线条+方块标记
- **低优先级**: 绿色线条+三角标记
- **状态分布**: 多色方案循环使用

## 优先级识别规则

### 需求优先级
- **高优先级**: 包含"high"、"紧急"、"1"
- **中优先级**: 包含"medium"、"中"、"2"  
- **低优先级**: 包含"low"、"低"、"3"

### 缺陷优先级
- **高优先级**: 包含"high"、"紧急"、"1"
- **中优先级**: 包含"medium"、"中"、"2"
- **低优先级**: 包含"low"、"低"、"3"

## 状态识别规则

### 完成状态识别
自动识别包含以下关键词的状态为"已完成"：
- 英文: "closed", "resolved", "done"
- 中文: "完成", "已解决", "已关闭"

### 新建状态识别  
自动识别包含以下关键词的状态为"新建"：
- 英文: "new", "open"
- 中文: "创建", "新建"

## 文件输出

### 存储位置
所有生成的图表文件保存在：
```
项目根目录/local_data/time_trend/
```

### 文件命名规则
```
{data_type}_{chart_type}_{timestamp}.png
```

示例：
- `story_count_20250829_143052.png`
- `bug_priority_20250829_143125.png`
- `story_status_20250829_143200.png`

### 自动目录创建
工具会自动创建必要的目录结构，无需手动创建。

## 错误处理

### 常见错误及解决方案

1. **数据文件不存在**
   ```json
   {
     "status": "error",
     "message": "数据加载失败或数据为空",
     "suggestion": "请先调用 get_tapd_data 工具获取数据"
   }
   ```

2. **时间格式错误**
   ```json
   {
     "status": "error", 
     "message": "时间趋势分析失败：时间格式不正确",
     "suggestion": "请检查时间格式是否正确(YYYY-MM-DD)"
   }
   ```

3. **筛选后数据为空**
   ```json
   {
     "status": "error",
     "message": "筛选后数据为空，请检查时间范围",
     "suggestion": "请调整时间范围或检查数据中是否包含指定时间段的记录"
   }
   ```

4. **不支持的数据类型**
   ```json
   {
     "status": "error",
     "message": "不支持的数据类型: invalid_type",
     "suggestion": "data_type参数只支持'story'或'bug'"
   }
   ```

## 性能优化建议

### 1. 数据量控制
- 大数据集建议使用时间范围筛选
- 单次分析建议不超过10万条记录
- 优先分析关键时间段

### 2. 图表性能
- 使用Agg后端避免GUI依赖
- 大时间跨度时自动调整标签密度
- 状态分布图自动限制显示的状态数量

### 3. 内存管理
- 图表生成后自动关闭matplotlib对象
- 避免在循环中重复调用
- 建议分批处理大量图表

## 扩展功能

### 1. 自定义图表标题
```python
result = await analyze_time_trends(
    data_type="story",
    chart_type="count",
    chart_title="Q3季度需求创建趋势分析"
)
```

### 2. 多时间字段对比
分别分析不同时间字段的趋势：
```python
# 分析需求创建趋势
created_trend = await analyze_time_trends(
    data_type="story", 
    time_field="created"
)

# 分析需求完成趋势  
due_trend = await analyze_time_trends(
    data_type="story",
    time_field="due"
)
```

### 3. 批量生成报告
```python
# 生成完整的趋势分析报告
data_types = ["story", "bug"]
chart_types = ["count", "priority", "status"]

for data_type in data_types:
    for chart_type in chart_types:
        result = await analyze_time_trends(
            data_type=data_type,
            chart_type=chart_type,
            since="2025-01-01",
            until="2025-08-29"
        )
```

## 注意事项

### 1. 前置条件
- 确保已调用 `get_tapd_data` 工具获取最新数据
- 确保数据文件格式正确（JSON格式）
- 确保系统已安装matplotlib依赖

### 2. 时间格式要求
- 严格按照YYYY-MM-DD格式输入时间
- since时间必须早于until时间
- 数据中的时间字段支持YYYY-MM-DD和YYYY-MM-DD HH:MM:SS格式

### 3. 数据质量
- 缺失时间字段的记录会被自动跳过
- 状态和优先级字段为空时不影响总数统计
- 优先级识别基于关键词匹配，建议保持数据标准化

### 4. 文件权限
- 确保local_data目录有写入权限
- 确保time_trend子目录可以创建
- 生成的PNG文件需要有读取权限

### 5. 中文环境
- 推荐在支持中文的环境中运行
- 图表标题和标签会自动使用中文
- 字体加载失败时会降级到英文字体

## 技术架构

### 核心模块
- **time_trend_analyzer.py**: 主要分析逻辑
- **common_utils.py**: 通用工具函数
- **tapd_mcp_server.py**: MCP工具接口

### 依赖库
- **matplotlib**: 图表生成
- **numpy**: 数值计算
- **datetime**: 时间处理
- **json**: 数据解析

### 设计模式
- 异步函数支持并发调用
- 统一错误处理和返回格式
- 模块化设计便于扩展和维护

## 未来扩展

### 计划中的功能
1. **更多图表类型**: 饼图、堆叠图、热力图
2. **交互式图表**: 支持Plotly等交互式图表库
3. **导出格式**: 支持PDF、SVG、Excel等格式
4. **统计分析**: 趋势预测、异常检测、周期性分析
5. **报告模板**: 自动生成标准化分析报告

### 自定义扩展点
1. 在`plot_time_trend_chart`函数中添加新的图表类型
2. 在`generate_daily_statistics`函数中添加新的统计维度
3. 在`parse_tapd_time`函数中支持新的时间格式
4. 通过配置文件自定义颜色方案和样式

---

**版本**: 1.0  
**更新日期**: 2025-08-29  
**维护者**: TAPD平台MCP开发团队
