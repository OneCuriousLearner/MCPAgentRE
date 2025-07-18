"""
历史需求知识库功能测试脚本（简化版）

测试知识库的核心功能：
1. 知识库构建和初始化
2. 需求添加和搜索
3. 测试用例推荐
4. 覆盖度分析
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.requirement_knowledge_base import RequirementKnowledgeBase, build_knowledge_base_from_tapd_data


async def test_knowledge_base_creation():
    """测试知识库创建和初始化"""
    print("\n=== 测试1: 知识库创建和初始化 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        print("知识库实例创建成功")
        
        # 获取统计信息
        stats = kb.get_knowledge_base_stats()
        print(f"知识库统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        return True
    except Exception as e:
        print(f"知识库创建失败: {str(e)}")
        return False


async def test_add_requirement():
    """测试添加需求到知识库"""
    print("\n=== 测试2: 添加需求到知识库 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        # 添加测试需求
        test_requirement = {
            "req_id": "REQ_LOGIN_001",
            "title": "用户登录功能",
            "description": "支持手机号、邮箱登录，包含密码强度验证和多因子认证",
            "feature_type": "认证授权",
            "complexity": "中等",
            "business_scenario": ["用户管理", "安全验证"],
            "technical_keywords": ["登录", "验证", "Token", "Session", "MFA"],
            "test_case_templates": [
                {
                    "scenario": "正常登录流程",
                    "test_type": "功能测试",
                    "title_template": "验证正常登录功能",
                    "steps_template": ["打开登录页面", "输入有效凭证", "点击登录", "验证跳转"],
                    "expected_template": "成功登录并跳转到主页",
                    "priority": "P0"
                }
            ]
        }
        
        success = kb.add_requirement_to_knowledge_base(test_requirement)
        if success:
            print(f"成功添加需求: {test_requirement['req_id']} - {test_requirement['title']}")
            return True
        else:
            print(f"添加需求失败: {test_requirement['req_id']}")
            return False
        
    except Exception as e:
        print(f"添加需求测试失败: {str(e)}")
        return False


async def test_search_similar_requirements():
    """测试搜索相似需求功能"""
    print("\n=== 测试3: 搜索相似需求 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        # 测试搜索查询
        query = "用户登录"
        print(f"搜索查询: '{query}'")
        
        similar_reqs = kb.search_similar_requirements(query=query, top_k=3)
        
        if similar_reqs:
            print(f"找到 {len(similar_reqs)} 个相似需求:")
            for i, req in enumerate(similar_reqs, 1):
                req_data = req['requirement']
                print(f"{i}. {req_data['title']} (相似度: {req['match_score']:.2f})")
            return True
        else:
            print("未找到相似需求")
            return False
        
    except Exception as e:
        print(f"搜索相似需求测试失败: {str(e)}")
        return False


async def test_recommend_test_cases():
    """测试测试用例推荐功能"""
    print("\n=== 测试4: 测试用例推荐 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        # 测试需求
        test_requirement = {
            "req_id": "REQ_NEW_001",
            "title": "密码重置功能",
            "description": "用户忘记密码时可以通过邮箱或手机号重置密码",
            "feature_type": "认证授权",
            "business_scenario": ["用户管理", "安全验证"],
            "technical_keywords": ["密码", "重置", "邮箱", "手机", "验证码"]
        }
        
        print(f"为需求推荐测试用例:")
        print(f"需求: {test_requirement['title']}")
        print(f"描述: {test_requirement['description']}")
        
        # 获取推荐（不使用AI，避免API依赖）
        recommendations = await kb.recommend_test_cases_for_requirement(
            requirement_data=test_requirement,
            use_ai=False
        )
        
        if recommendations:
            print(f"获得 {len(recommendations)} 个推荐:")
            for i, rec in enumerate(recommendations, 1):
                print(f"推荐 {i}: 来源={rec['source']}, 匹配度={rec['match_score']:.2f}")
            return True
        else:
            print("暂无推荐结果")
            return False
        
    except Exception as e:
        print(f"测试用例推荐测试失败: {str(e)}")
        return False


async def test_knowledge_base_stats():
    """测试知识库统计信息"""
    print("\n=== 测试5: 知识库统计信息 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        stats = kb.get_knowledge_base_stats()
        
        if 'error' not in stats:
            print("知识库统计信息:")
            print(f"总需求数量: {stats['total_requirements']}")
            print(f"功能类型: {stats['feature_types']}")
            print(f"最后更新: {stats['last_updated']}")
            return True
        else:
            print(f"获取统计信息失败: {stats['error']}")
            return False
        
    except Exception as e:
        print(f"知识库统计测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("开始历史需求知识库功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行所有测试
    test_functions = [
        ("知识库创建", test_knowledge_base_creation),
        ("添加需求", test_add_requirement),
        ("搜索相似需求", test_search_similar_requirements),
        ("测试用例推荐", test_recommend_test_cases),
        ("统计信息", test_knowledge_base_stats)
    ]
    
    for test_name, test_func in test_functions:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"{test_name}测试出现异常: {str(e)}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n测试完成: {passed} 个通过, {failed} 个失败")
    
    if failed == 0:
        print("所有测试通过！历史需求知识库功能正常。")
    else:
        print("部分测试失败，请检查相关功能。")


if __name__ == "__main__":
    asyncio.run(main())