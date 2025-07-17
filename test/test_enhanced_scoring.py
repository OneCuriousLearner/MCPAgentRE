"""
增强评分功能测试脚本
演示新的灵活打分规则和多套评分标准
"""
import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.enhanced_scoring_config import (
    get_enhanced_config_manager, 
    ScoringStrategy,
    ScoreThresholds,
    ScoringRange
)
from mcp_tools.enhanced_testcase_scorer import get_enhanced_quality_scorer


async def test_enhanced_scoring():
    """测试增强评分功能"""
    print("=" * 70)
    print("增强评分功能测试")
    print("=" * 70)
    
    # 1. 创建配置管理器
    config_manager = await get_enhanced_config_manager()
    
    # 2. 创建多套评分标准
    print("\n1. 创建多套评分标准:")
    
    # 创建严格模式配置
    strict_profile = await config_manager.create_profile(
        name="strict_mode",
        description="严格的评分标准，适用于高质量要求的项目",
        strategy=ScoringStrategy.STRICT
    )
    
    # 创建宽松模式配置
    lenient_profile = await config_manager.create_profile(
        name="lenient_mode",
        description="宽松的评分标准，适用于快速迭代的项目",
        strategy=ScoringStrategy.LENIENT
    )
    
    print(f"[OK] 创建严格模式配置: {strict_profile.name}")
    print(f"[OK] 创建宽松模式配置: {lenient_profile.name}")
    
    # 3. 自定义阈值设置
    print("\n2. 自定义评分阈值:")
    
    # 为严格模式设置更高的阈值
    strict_profile.thresholds = ScoreThresholds(
        excellent_min=9.5,
        good_min=8.0,
        fair_min=6.0,
        poor_max=5.9
    )
    
    # 为宽松模式设置更低的阈值
    lenient_profile.thresholds = ScoreThresholds(
        excellent_min=8.0,
        good_min=6.0,
        fair_min=4.0,
        poor_max=3.9
    )
    
    # 保存配置
    await config_manager.save_profile(strict_profile)
    await config_manager.save_profile(lenient_profile)
    
    print(f"[OK] 严格模式阈值: 优秀≥9.5, 良好≥8.0, 及格≥6.0")
    print(f"[OK] 宽松模式阈值: 优秀≥8.0, 良好≥6.0, 及格≥4.0")
    
    # 4. 自定义评分范围
    print("\n3. 自定义评分范围:")
    
    # 为严格模式的标题维度设置更严格的评分范围
    strict_title_ranges = [
        ScoringRange(10, 15, 10, "标题简洁精确"),
        ScoringRange(16, 25, 8, "标题长度适中"),
        ScoringRange(26, 35, 6, "标题稍长"),
        ScoringRange(36, 50, 4, "标题过长"),
        ScoringRange(0, 9, 2, "标题过短")
    ]
    
    strict_profile.dimensions["title"].scoring_ranges = strict_title_ranges
    strict_profile.dimensions["title"].custom_params.update({
        "max_length": 35,  # 更严格的长度限制
        "min_length": 10
    })
    
    await config_manager.save_profile(strict_profile)
    print("[OK] 严格模式标题评分范围已更新")
    
    # 5. 调整维度权重
    print("\n4. 调整维度权重:")
    
    # 为严格模式增加测试步骤的权重
    strict_profile.dimensions["steps"].weight = 0.35
    strict_profile.dimensions["expected_result"].weight = 0.3
    strict_profile.dimensions["title"].weight = 0.15
    strict_profile.dimensions["precondition"].weight = 0.1
    strict_profile.dimensions["priority"].weight = 0.1
    
    await config_manager.save_profile(strict_profile)
    print("[OK] 严格模式权重分配: 测试步骤35%, 预期结果30%, 标题15%, 前置条件10%, 优先级10%")
    
    # 6. 准备测试用例
    print("\n5. 准备测试用例:")
    
    test_cases = [
        {
            "id": "TC001",
            "title": "用户登录功能验证",
            "precondition": "用户已注册且账号状态正常",
            "steps": "1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮\n4. 验证页面跳转",
            "expected_result": "用户成功登录，跳转到首页，显示用户信息",
            "priority": "P1"
        },
        {
            "id": "TC002",
            "title": "登录测试",
            "precondition": "",
            "steps": "输入用户名密码，点击登录",
            "expected_result": "登录成功",
            "priority": "高"
        },
        {
            "id": "TC003",
            "title": "用户在购物车页面添加商品时系统应正确计算总价格并更新显示",
            "precondition": "1. 用户已登录\n2. 购物车中已有商品\n3. 商品库存充足\n4. 价格数据准确",
            "steps": "1. 用户访问购物车页面\n2. 点击添加商品按钮\n3. 选择商品规格\n4. 输入商品数量\n5. 确认添加\n6. 系统计算总价\n7. 更新页面显示\n8. 验证计算结果\n9. 检查库存变化\n10. 保存购物车状态",
            "expected_result": "系统正确计算包含新添加商品的总价格，页面实时更新显示总价、商品数量和优惠信息，同时更新库存状态",
            "priority": "P2"
        }
    ]
    
    # 7. 使用不同配置档案进行评分对比
    print("\n6. 多配置档案评分对比:")
    
    profiles = ["default", "strict_mode", "lenient_mode"]
    
    for i, testcase in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1}: {testcase['title'][:30]}... ---")
        
        for profile_name in profiles:
            try:
                scorer = await get_enhanced_quality_scorer(profile_name)
                result = await scorer.score_single_testcase(testcase, profile_name)
                
                print(f"{profile_name:12s}: {result['total_score']:5.2f}/10 ({result['score_level_cn']})")
                
            except Exception as e:
                print(f"{profile_name:12s}: 评分失败 - {str(e)}")
    
    # 8. 批量评分统计对比
    print("\n7. 批量评分统计对比:")
    
    for profile_name in profiles:
        try:
            scorer = await get_enhanced_quality_scorer(profile_name)
            batch_result = await scorer.score_batch_testcases(test_cases, 5, profile_name)
            
            print(f"\n{profile_name} 统计:")
            print(f"  平均分: {batch_result['average_score']:.2f}")
            print(f"  分布: {batch_result['score_distribution']}")
            print(f"  策略: {batch_result['strategy']}")
            
        except Exception as e:
            print(f"{profile_name} 统计失败: {str(e)}")
    
    # 9. 展示配置档案列表
    print("\n8. 当前配置档案列表:")
    profiles_list = await config_manager.list_profiles()
    for profile in profiles_list:
        print(f"  - {profile['name']}: {profile['description']} ({profile['strategy']})")
    
    # 10. 验证配置
    print("\n9. 配置验证:")
    for profile_name in ["strict_mode", "lenient_mode"]:
        try:
            profile = await config_manager.load_profile(profile_name)
            validation = profile.validate()
            
            print(f"\n{profile_name} 验证结果:")
            print(f"  有效性: {'[OK]' if validation['valid'] else '[ERROR]'}")
            print(f"  总权重: {validation['total_weight']:.3f}")
            print(f"  启用维度: {validation['enabled_dimensions']}")
            
            if validation['warnings']:
                print(f"  警告: {validation['warnings']}")
            if validation['errors']:
                print(f"  错误: {validation['errors']}")
                
        except Exception as e:
            print(f"{profile_name} 验证失败: {str(e)}")
    
    print("\n" + "=" * 70)
    print("增强评分功能测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_enhanced_scoring())