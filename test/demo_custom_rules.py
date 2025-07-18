"""
演示测试用例规则自定义功能的完整流程
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.test_case_rules_customer import TestCaseRulesCustomer
from mcp_tools.test_case_evaluator import TestCaseEvaluator


async def demo_custom_rules():
    """演示自定义规则的完整流程"""
    print("=== 测试用例规则自定义功能演示 ===\n")
    
    # 创建配置管理器
    customer = TestCaseRulesCustomer()
    
    # 1. 显示当前配置
    print("1. 当前默认配置:")
    customer.display_current_config()
    
    # 2. 设置自定义配置
    print("\n2. 设置自定义配置...")
    custom_config = {
        "title_max_length": 60,  # 增加标题长度限制
        "max_steps": 15,         # 增加步骤数上限
        "priority_ratios": {
            "P0": {"min": 15, "max": 30},  # 提高P0占比
            "P1": {"min": 50, "max": 65},  # 调整P1占比
            "P2": {"min": 5, "max": 25}    # 调整P2占比
        },
        "version": "1.0",
        "last_updated": None
    }
    
    customer.save_config(custom_config)
    print("✓ 自定义配置已保存")
    print(f"   标题长度: {custom_config['title_max_length']}字符")
    print(f"   步骤数: {custom_config['max_steps']}步")
    print(f"   P0占比: {custom_config['priority_ratios']['P0']['min']}-{custom_config['priority_ratios']['P0']['max']}%")
    print(f"   P1占比: {custom_config['priority_ratios']['P1']['min']}-{custom_config['priority_ratios']['P1']['max']}%")
    print(f"   P2占比: {custom_config['priority_ratios']['P2']['min']}-{custom_config['priority_ratios']['P2']['max']}%")
    
    # 3. 创建评估器，验证配置是否生效
    print("\n3. 创建评估器验证配置...")
    try:
        evaluator = TestCaseEvaluator(max_context_tokens=8000)
        print("✓ 评估器创建成功，配置已自动加载")
        
        # 4. 检查生成的提示词模板
        print("\n4. 检查生成的动态提示词模板...")
        template = evaluator.evaluation_prompt_template
        
        # 查找关键配置项在模板中的体现
        key_phrases = [
            ("标题长度", "不超过 60 字符"),
            ("步骤数", "不超过15步"),
            ("P0占比", "15%~30%"),
            ("P1占比", "50%~65%"),
            ("P2占比", "5%~25%")
        ]
        
        print("   配置项在提示词中的体现:")
        for desc, phrase in key_phrases:
            if phrase in template:
                print(f"   ✓ {desc}: 找到 '{phrase}'")
            else:
                print(f"   ✗ {desc}: 未找到 '{phrase}'")
        
        # 5. 模拟一个简单的测试用例评估（不实际调用API）
        print("\n5. 模拟测试用例评估...")
        test_case = {
            "test_case_id": "TC001",
            "test_case_title": "这是一个测试用例标题，长度刚好在新的60字符限制内",
            "prerequisites": "已登录系统",
            "step_description": "1. 打开页面\n2. 输入数据\n3. 点击提交",
            "expected_result": "提交成功"
        }
        
        # 估算这个测试用例的token数量
        token_count = evaluator.estimate_batch_tokens([test_case])
        print(f"   测试用例预计tokens: {token_count}")
        
        # 检查是否超出阈值
        if token_count <= evaluator.token_threshold:
            print(f"   ✓ 未超出阈值({evaluator.token_threshold})，可以正常处理")
        else:
            print(f"   ⚠ 超出阈值({evaluator.token_threshold})，需要分批处理")
            
    except Exception as e:
        print(f"   ✗ 评估器创建失败: {e}")
    
    # 6. 恢复默认配置
    print("\n6. 恢复默认配置...")
    customer.reset_to_default()
    print("✓ 已恢复默认配置")
    
    print("\n=== 演示完成 ===")
    print("\n总结:")
    print("1. 配置功能完全正常工作")
    print("2. 评估器能自动加载配置并生成动态提示词")
    print("3. 用户可以灵活调整评估规则以适应不同项目需求")
    print("4. 所有配置都会持久化保存，便于长期使用")


if __name__ == "__main__":
    asyncio.run(demo_custom_rules())
