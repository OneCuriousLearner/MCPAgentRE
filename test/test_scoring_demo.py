"""
测试用例质量评分功能演示脚本
"""
import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.testcase_quality_scorer import get_quality_scorer
from mcp_tools.scoring_config_manager import get_config_manager


async def demo_scoring():
    """演示评分功能"""
    print("=" * 60)
    print("测试用例质量评分功能演示")
    print("=" * 60)
    
    # 1. 获取当前配置
    print("\n1. 当前评分配置:")
    config_manager = await get_config_manager()
    config = await config_manager.load_config()
    summary = await config_manager.get_config_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # 2. 准备测试用例
    test_cases = [
        {
            "id": "TC001",
            "title": "用户登录功能验证",
            "precondition": "用户已注册且账号状态正常",
            "steps": "1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮",
            "expected_result": "用户成功登录，跳转到首页",
            "priority": "P1"
        },
        {
            "id": "TC002", 
            "title": "测试",
            "precondition": "",
            "steps": "点击按钮",
            "expected_result": "成功",
            "priority": "高"
        },
        {
            "id": "TC003",
            "title": "用户注册时输入非法邮箱格式应显示错误提示信息",
            "precondition": "1. 用户未登录\n2. 进入注册页面\n3. 数据库连接正常\n4. 邮箱验证服务可用",
            "steps": "1. 用户访问注册页面\n2. 输入用户名\n3. 输入非法格式的邮箱地址(如：test@)\n4. 输入密码\n5. 输入确认密码\n6. 点击注册按钮\n7. 观察页面反应\n8. 检查错误提示信息\n9. 验证表单状态\n10. 确认数据库未创建新用户",
            "expected_result": "页面在邮箱输入框下方显示红色错误提示信息'请输入有效的邮箱地址'，注册按钮保持不可点击状态，表单不提交，数据库中不会创建新的用户记录",
            "priority": "P2"
        }
    ]
    
    # 3. 单个评分演示
    print("\n2. 单个测试用例评分演示:")
    scorer = await get_quality_scorer()
    
    for i, testcase in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1} ---")
        print(f"标题: {testcase['title']}")
        
        result = await scorer.score_single_testcase(testcase)
        print(f"总分: {result['total_score']}/10 ({result['score_level']})")
        print("分项评分:")
        
        for dimension, score_info in result['detailed_scores'].items():
            print(f"  {dimension}: {score_info['score']}/10 - {score_info['reason']}")
        
        if result['improvement_suggestions']:
            print("改进建议:")
            for suggestion in result['improvement_suggestions'][:5]:  # 只显示前5个
                print(f"  - {suggestion}")
        
        print("-" * 50)
    
    # 4. 批量评分演示
    print("\n3. 批量评分统计:")
    batch_result = await scorer.score_batch_testcases(test_cases, batch_size=2)
    
    print(f"总计处理: {batch_result['total_count']} 个测试用例")
    print(f"成功评分: {batch_result['success_count']} 个")
    print(f"平均分: {batch_result['average_score']}/10")
    print("分数分布:")
    for level, count in batch_result['score_distribution'].items():
        print(f"  {level}: {count} 个")
    
    print("\n=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_scoring())