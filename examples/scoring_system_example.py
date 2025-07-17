"""
测试用例质量评分系统使用示例
演示如何使用配置管理和评分功能
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.scoring_config_manager import get_config_manager
from mcp_tools.testcase_quality_scorer import get_quality_scorer


async def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 获取评分器
    scorer = await get_quality_scorer()
    
    # 示例测试用例
    testcase = {
        "id": "TC_LOGIN_001",
        "title": "用户登录功能验证",
        "precondition": "用户已注册账号",
        "steps": "1. 打开登录页面\n2. 输入正确的用户名和密码\n3. 点击登录按钮",
        "expected_result": "登录成功，跳转到用户首页，显示欢迎信息",
        "priority": "P1"
    }
    
    # 进行评分
    result = await scorer.score_single_testcase(testcase)
    
    print(f"测试用例: {testcase['title']}")
    print(f"总分: {result['total_score']}")
    print(f"等级: {result['score_level']}")
    print("详细评分:")
    for item, score_info in result['detailed_scores'].items():
        print(f"  {item}: {score_info['score']} 分 - {score_info['reason']}")
    
    if result['improvement_suggestions']:
        print("改进建议:")
        for suggestion in result['improvement_suggestions']:
            print(f"  - {suggestion}")


async def example_config_management():
    """配置管理示例"""
    print("\n=== 配置管理示例 ===")
    
    # 获取配置管理器
    config_manager = await get_config_manager()
    
    # 查看当前配置
    print("1. 当前配置:")
    config = await config_manager.load_config()
    summary = await config_manager.get_config_summary()
    print(f"   标题最大长度: {summary['rules_summary']['title']['max_length']}")
    print(f"   标题权重: {summary['rules_summary']['title']['weight']}")
    
    # 自定义标题规则
    print("\n2. 自定义标题规则:")
    custom_title_rule = {
        "max_length": 60,
        "min_length": 10,
        "weight": 0.3
    }
    
    await config_manager.update_rule("title", custom_title_rule)
    print(f"   已更新标题最大长度为: {custom_title_rule['max_length']}")
    print(f"   已更新标题权重为: {custom_title_rule['weight']}")
    
    # 验证配置
    print("\n3. 验证配置:")
    current_config = await config_manager.load_config()
    config_dict = config_manager._config_to_dict(current_config)
    validation_result = await config_manager.validate_config(config_dict)
    print(f"   配置有效性: {validation_result['valid']}")
    if validation_result['warnings']:
        print(f"   警告: {validation_result['warnings']}")
    
    # 重置为默认配置
    print("\n4. 重置为默认配置:")
    await config_manager.reset_to_default()
    reset_config = await config_manager.load_config()
    print(f"   重置后标题最大长度: {reset_config.title_rule.max_length}")


async def example_batch_scoring():
    """批量评分示例"""
    print("\n=== 批量评分示例 ===")
    
    # 获取评分器
    scorer = await get_quality_scorer()
    
    # 示例测试用例批量数据
    test_cases = [
        {
            "id": "TC_001",
            "title": "用户注册功能测试",
            "precondition": "系统正常运行",
            "steps": "1. 打开注册页面\n2. 填写用户信息\n3. 点击注册按钮",
            "expected_result": "注册成功，发送确认邮件",
            "priority": "P1"
        },
        {
            "id": "TC_002",
            "title": "密码找回",
            "precondition": "",
            "steps": "点击找回密码",
            "expected_result": "正常",
            "priority": "High"
        },
        {
            "id": "TC_003",
            "title": "用户个人信息修改功能完整性验证测试",
            "precondition": "1. 用户已登录\n2. 用户有修改权限\n3. 数据库连接正常",
            "steps": "1. 进入个人信息页面\n2. 修改各项信息\n3. 保存修改\n4. 验证修改结果",
            "expected_result": "信息修改成功，页面显示最新信息，数据库记录更新",
            "priority": "P2"
        }
    ]
    
    # 批量评分
    batch_result = await scorer.score_batch_testcases(test_cases, batch_size=2)
    
    print(f"批量评分结果:")
    print(f"  总数: {batch_result['total_count']}")
    print(f"  成功数: {batch_result['success_count']}")
    print(f"  平均分: {batch_result['average_score']}")
    print(f"  分数分布: {batch_result['score_distribution']}")
    
    # 显示评分详情
    print("\n各用例评分详情:")
    for result in batch_result['results']:
        if 'error' not in result:
            print(f"  {result['testcase_id']}: {result['total_score']} 分 ({result['score_level']})")
            if result['improvement_suggestions']:
                print(f"    主要建议: {result['improvement_suggestions'][0]}")


async def example_quality_analysis():
    """质量分析示例"""
    print("\n=== 质量分析示例 ===")
    
    # 模拟不同质量水平的测试用例
    quality_samples = [
        {
            "level": "优秀",
            "testcase": {
                "id": "TC_EXCELLENT",
                "title": "用户登录安全验证",
                "precondition": "用户已注册有效账号",
                "steps": "1. 打开登录页面\n2. 输入正确用户名和密码\n3. 点击登录按钮\n4. 验证登录状态",
                "expected_result": "登录成功，跳转到首页，session建立，用户状态为已登录",
                "priority": "P1"
            }
        },
        {
            "level": "需要改进",
            "testcase": {
                "id": "TC_POOR",
                "title": "测试",
                "precondition": "",
                "steps": "操作",
                "expected_result": "正常",
                "priority": ""
            }
        }
    ]
    
    scorer = await get_quality_scorer()
    
    for sample in quality_samples:
        print(f"\n{sample['level']}示例:")
        result = await scorer.score_single_testcase(sample['testcase'])
        print(f"  总分: {result['total_score']}")
        print(f"  等级: {result['score_level']}")
        
        # 分析具体问题
        low_scores = []
        for item, score_info in result['detailed_scores'].items():
            if score_info['score'] < 7:
                low_scores.append(f"{item}({score_info['score']}分)")
        
        if low_scores:
            print(f"  低分项: {', '.join(low_scores)}")
        
        if result['improvement_suggestions']:
            print(f"  改进建议: {len(result['improvement_suggestions'])} 条")


async def main():
    """主函数"""
    print("测试用例质量评分系统使用示例")
    print("=" * 50)
    
    try:
        await example_basic_usage()
        await example_config_management()
        await example_batch_scoring()
        await example_quality_analysis()
        
        print("\n示例演示完成！")
        
    except Exception as e:
        print(f"\n示例运行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())