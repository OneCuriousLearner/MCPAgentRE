"""
测试用例质量评分系统测试脚本
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
    
    # 测试配置摘要
    print("\n2. 获取配置摘要...")
    summary = await config_manager.get_config_summary()
    print(f"   摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
    
    # 测试更新规则
    print("\n3. 更新标题规则...")
    new_title_rule = {
        "max_length": 50,
        "min_length": 8,
        "weight": 0.25
    }
    await config_manager.update_rule("title", new_title_rule)
    updated_config = await config_manager.load_config()
    print(f"   更新后的标题最大长度: {updated_config.title_rule.max_length}")
    print(f"   更新后的标题权重: {updated_config.title_rule.weight}")
    
    # 测试配置验证
    print("\n4. 测试配置验证...")
    test_config = {
        "version": "1.0",
        "title_rule": {"max_length": 60, "weight": 0.3},
        "precondition_rule": {"max_count": 3, "weight": 0.1},
        "steps_rule": {"min_steps": 1, "weight": 0.3},
        "expected_result_rule": {"weight": 0.2},
        "priority_rule": {"weight": 0.1}
    }
    
    validation_result = await config_manager.validate_config(test_config)
    print(f"   验证结果: {json.dumps(validation_result, ensure_ascii=False, indent=2)}")
    
    # 测试重置配置
    print("\n5. 重置为默认配置...")
    await config_manager.reset_to_default()
    reset_config = await config_manager.load_config()
    print(f"   重置后的标题最大长度: {reset_config.title_rule.max_length}")
    
    # 清理测试文件
    if os.path.exists("test/test_config.json"):
        os.remove("test/test_config.json")
    
    print("✓ 配置管理器测试完成")


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
            "title": "这是一个非常长的测试用例标题，可能会超过推荐的长度限制，需要检查是否会被正确评分",
            "precondition": "",
            "steps": "点击按钮",
            "expected_result": "正常",
            "priority": "High"
        },
        {
            "id": "TC003",
            "title": "用户信息查询验证测试",
            "precondition": "1. 用户已登录系统\n2. 用户有查询权限",
            "steps": "1. 进入用户管理页面\n2. 选择查询条件\n3. 点击查询按钮\n4. 验证查询结果",
            "expected_result": "系统返回符合条件的用户信息列表，包含用户ID、姓名、状态等字段，数据准确无误",
            "priority": "P2"
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
        print(f"   步骤分数: {result['detailed_scores']['steps']['score']}")
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
    
    print("✓ 质量评分器测试完成")


async def test_edge_cases():
    """测试边界情况和异常处理"""
    print("\n=== 测试边界情况 ===")
    
    scorer = TestCaseQualityScorer()
    await scorer.initialize()
    
    # 测试空数据
    print("1. 测试空数据...")
    empty_case = {
        "id": "TC_EMPTY",
        "title": "",
        "precondition": "",
        "steps": "",
        "expected_result": "",
        "priority": ""
    }
    
    result = await scorer.score_single_testcase(empty_case)
    print(f"   空数据总分: {result['total_score']}")
    print(f"   改进建议数: {len(result['improvement_suggestions'])}")
    
    # 测试极长数据
    print("\n2. 测试极长数据...")
    long_case = {
        "id": "TC_LONG",
        "title": "这是一个极其详细和冗长的测试用例标题，包含了大量的描述性文字，目的是测试系统对于过长标题的处理能力和评分逻辑",
        "precondition": "前置条件1：用户已经完成了系统注册\n前置条件2：用户已经通过了身份验证\n前置条件3：系统处于正常运行状态",
        "steps": "1. 执行第一步操作\n2. 执行第二步操作\n3. 执行第三步操作\n4. 执行第四步操作\n5. 执行第五步操作\n6. 执行第六步操作\n7. 执行第七步操作\n8. 执行第八步操作\n9. 执行第九步操作\n10. 执行第十步操作",
        "expected_result": "系统应该能够正确处理所有的输入数据，并返回准确的结果信息，同时保证数据的完整性和一致性，确保用户体验良好",
        "priority": "P0"
    }
    
    result = await scorer.score_single_testcase(long_case)
    print(f"   长数据总分: {result['total_score']}")
    print(f"   标题评分: {result['detailed_scores']['title']['score']}")
    print(f"   前置条件评分: {result['detailed_scores']['precondition']['score']}")
    
    # 测试异常数据
    print("\n3. 测试异常数据...")
    try:
        invalid_case = {
            "id": "TC_INVALID",
            "title": None,
            "precondition": 123,
            "steps": [],
            "expected_result": {"invalid": "data"},
            "priority": "INVALID"
        }
        
        result = await scorer.score_single_testcase(invalid_case)
        print(f"   异常数据处理成功，总分: {result['total_score']}")
    except Exception as e:
        print(f"   异常数据处理失败: {str(e)}")
    
    print("✓ 边界情况测试完成")


async def test_performance():
    """测试性能表现"""
    print("\n=== 测试性能表现 ===")
    
    scorer = TestCaseQualityScorer()
    await scorer.initialize()
    
    # 生成大量测试数据
    print("1. 生成测试数据...")
    test_cases = []
    for i in range(50):
        test_cases.append({
            "id": f"TC_{i:03d}",
            "title": f"测试用例标题{i}",
            "precondition": f"前置条件{i}",
            "steps": f"1. 步骤1\n2. 步骤2\n3. 步骤3",
            "expected_result": f"预期结果{i}",
            "priority": "P1"
        })
    
    # 测试批量处理性能
    print("2. 测试批量处理性能...")
    import time
    start_time = time.time()
    
    batch_result = await scorer.score_batch_testcases(test_cases, batch_size=10)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"   处理了 {batch_result['total_count']} 个测试用例")
    print(f"   总耗时: {processing_time:.2f} 秒")
    print(f"   平均耗时: {processing_time/batch_result['total_count']:.3f} 秒/用例")
    print(f"   成功率: {batch_result['success_count']/batch_result['total_count']*100:.1f}%")
    
    print("✓ 性能测试完成")


async def main():
    """主测试函数"""
    print("开始测试用例质量评分系统...")
    
    try:
        await test_config_manager()
        await test_quality_scorer()
        await test_edge_cases()
        await test_performance()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())