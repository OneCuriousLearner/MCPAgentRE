# 测试用例质量评分系统使用指南

## 系统概述

测试用例质量评分系统是一个基于规则的自动化评分工具，能够对测试用例的质量进行客观评估，并提供改进建议。

## 核心功能

### 1. 配置管理
- **获取配置**: `get_scoring_config()`
- **更新规则**: `configure_scoring_rules(rule_name, rule_config)`
- **验证配置**: `validate_scoring_config(config_json)`
- **重置配置**: `reset_scoring_config()`

### 2. 质量评分
- **单个评分**: `score_testcase_quality(testcase_data)`
- **批量评分**: `score_testcases_batch(testcases_data, batch_size)`

## 评分规则

### 标题评分 (权重: 0.2)
- **长度检查**: 推荐5-40字符
- **内容检查**: 包含操作动词
- **评分范围**: 0-10分

### 前置条件评分 (权重: 0.15)
- **数量检查**: 推荐0-2项
- **清晰度检查**: 避免模糊描述
- **评分范围**: 0-10分

### 测试步骤评分 (权重: 0.25)
- **步骤数量**: 推荐2-5步
- **编号要求**: 使用数字编号
- **具体性检查**: 避免模糊操作
- **评分范围**: 0-10分

### 预期结果评分 (权重: 0.25)
- **长度检查**: 推荐5-200字符
- **具体性检查**: 避免"正常"、"成功"等模糊词汇
- **验证点检查**: 包含具体验证内容
- **评分范围**: 0-10分

### 优先级评分 (权重: 0.15)
- **标准格式**: P0、P1、P2、P3
- **必需性检查**: 不能为空
- **评分范围**: 0-10分

## 使用示例

### 基本评分
```python
from mcp_tools.testcase_quality_scorer import get_quality_scorer

scorer = await get_quality_scorer()
testcase = {
    "id": "TC001",
    "title": "用户登录功能测试",
    "precondition": "用户已注册",
    "steps": "1. 打开登录页面\\n2. 输入用户名和密码\\n3. 点击登录按钮",
    "expected_result": "登录成功，跳转到首页",
    "priority": "P1"
}

result = await scorer.score_single_testcase(testcase)
print(f"总分: {result['total_score']}")
print(f"等级: {result['score_level']}")
```

### 配置管理
```python
from mcp_tools.scoring_config_manager import get_config_manager

config_manager = await get_config_manager()

# 自定义标题规则
custom_rule = {
    "max_length": 50,
    "min_length": 10,
    "weight": 0.3
}
await config_manager.update_rule("title", custom_rule)
```

### 批量评分
```python
test_cases = [testcase1, testcase2, testcase3]
batch_result = await scorer.score_batch_testcases(test_cases, batch_size=10)

print(f"平均分: {batch_result['average_score']}")
print(f"分数分布: {batch_result['score_distribution']}")
```

## MCP工具调用

### 通过MCP服务器调用

1. **获取评分配置**
```bash
# 调用MCP工具
get_scoring_config()
```

2. **配置评分规则**
```bash
# 更新标题规则
configure_scoring_rules("title", '{"max_length": 50, "weight": 0.3}')
```

3. **评分测试用例**
```bash
# 单个用例评分
score_testcase_quality('{"id": "TC001", "title": "登录测试", ...}')

# 批量评分
score_testcases_batch('[{"id": "TC001", ...}, {"id": "TC002", ...}]')
```

## 评分等级

- **优秀** (9.0-10.0分): 用例质量很高，基本无需改进
- **良好** (7.0-8.9分): 用例质量较好，有少量改进空间
- **及格** (5.0-6.9分): 用例基本可用，需要一定改进
- **需要改进** (0.0-4.9分): 用例质量较差，需要大量改进

## 改进建议类型

1. **标题建议**: 长度优化、动词使用
2. **前置条件建议**: 数量控制、描述清晰
3. **步骤建议**: 编号使用、具体描述
4. **预期结果建议**: 避免模糊词汇、增加验证点
5. **优先级建议**: 使用标准格式

## 最佳实践

1. **定期校准**: 根据团队标准调整评分规则
2. **批量处理**: 使用适当的batch_size避免资源过载
3. **持续改进**: 根据评分结果和建议优化测试用例
4. **配置备份**: 定期备份自定义配置
5. **团队协作**: 确保团队成员理解评分标准

## 常见问题

**Q: 如何调整评分权重？**
A: 使用 `configure_scoring_rules()` 修改各项规则的weight参数，确保总权重接近1.0。

**Q: 评分结果不准确怎么办？**
A: 可以调整对应规则的阈值和评分范围，或者添加更多评分维度。

**Q: 如何处理中文用例？**
A: 系统已优化中文处理，使用jieba分词和中文停用词过滤。

**Q: 支持自定义评分规则吗？**
A: 当前支持调整现有规则参数，未来可扩展添加新的评分维度。