"""
简化的测试用例质量评分系统测试脚本
验证配置管理和评分功能的正确性
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.scoring_config_manager import ScoringConfigManager, ScoringConfig
from mcp_tools.testcase_quality_scorer import TestCaseQualityScorer


async def test_config_manager():
    """测试配置管理器功能"""
    print("=== 测试配置管理器 ===")
    
    config_manager = ScoringConfigManager("test/test_config.json")
    
    # 测试加载默认配置
    print("1. 加载默认配置...")
    config = await config_manager.load_config()
    print(f"   版本: {config.version}")
    print(f"   标题权重: {config.title_rule.weight}")
    print(f"   标题最大长度: {config.title_rule.max_length}")
    
    # 测试更新规则
    print("\n2. 更新标题规则...")
    new_title_rule = {
        "max_length": 50,
        "min_length": 8,
        "weight": 0.25
    }
    await config_manager.update_rule("title", new_title_rule)
    updated_config = await config_manager.load_config()
    print(f"   更新后的标题最大长度: {updated_config.title_rule.max_length}")
    print(f"   更新后的标题权重: {updated_config.title_rule.weight}")
    
    # 测试重置配置
    print("\n3. 重置为默认配置...")
    await config_manager.reset_to_default()
    reset_config = await config_manager.load_config()
    print(f"   重置后的标题最大长度: {reset_config.title_rule.max_length}")
    
    # 清理测试文件
    if os.path.exists("test/test_config.json"):
        os.remove("test/test_config.json")
    
    print("配置管理器测试完成")


async def test_quality_scorer():
    """测试质量评分器功能"""
    print("\n=== 测试质量评分器 ===")
    
    scorer = TestCaseQualityScorer()
    await scorer.initialize()
    
    # 测试用例数据
    test_cases = [
        {
            "id": "TC001",
            "title": "登录功能测试",
            "precondition": "用户已注册",
            "steps": "1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮",
            "expected_result": "登录成功，跳转到首页",
            "priority": "P1"
        },
        {
            "id": "TC002",
            "title": "这是一个非常长的测试用例标题，可能会超过推荐的长度限制",
            "precondition": "",
            "steps": "点击按钮",
            "expected_result": "正常",
            "priority": "High"
        }
    ]
    
    # 测试单个用例评分
    print("1. 测试单个用例评分...")
    for i, testcase in enumerate(test_cases):
        print(f"\n   测试用例 {i+1}: {testcase['title'][:20]}...")
        result = await scorer.score_single_testcase(testcase)
        print(f"   总分: {result['total_score']}")
        print(f"   等级: {result['score_level']}")
        print(f"   标题分数: {result['detailed_scores']['title']['score']}")
        print(f"   改进建议数: {len(result['improvement_suggestions'])}")
        
        if result['improvement_suggestions']:
            print(f"   主要建议: {result['improvement_suggestions'][0]}")
    
    # 测试批量评分
    print("\n2. 测试批量评分...")
    batch_result = await scorer.score_batch_testcases(test_cases, batch_size=2)
    print(f"   总数: {batch_result['total_count']}")
    print(f"   成功数: {batch_result['success_count']}")
    print(f"   平均分: {batch_result['average_score']}")
    print(f"   分数分布: {batch_result['score_distribution']}")
    
    print("质量评分器测试完成")


async def main():
    """主测试函数"""
    print("开始测试用例质量评分系统...")
    
    try:
        await test_config_manager()
        await test_quality_scorer()
        
        print("\n所有测试完成！")
        
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())