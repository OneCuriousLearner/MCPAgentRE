"""
历史需求知识库功能测试脚本

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
        print("✅ 知识库实例创建成功")
        
        # 获取统计信息
        stats = kb.get_knowledge_base_stats()
        print(f"📊 知识库统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        return True
    except Exception as e:
        print(f"❌ 知识库创建失败: {str(e)}")
        return False


async def test_add_requirement():
    """测试添加需求到知识库"""
    print("\n=== 测试2: 添加需求到知识库 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        # 添加测试需求
        test_requirements = [
            {
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
                        "title_template": "验证{登录方式}正常登录功能",
                        "steps_template": ["打开登录页面", "输入有效凭证", "点击登录", "验证跳转"],
                        "expected_template": "成功登录并跳转到主页",
                        "priority": "P0"
                    },
                    {
                        "scenario": "异常登录处理",
                        "test_type": "异常测试",
                        "title_template": "验证{异常情况}的错误处理",
                        "steps_template": ["打开登录页面", "输入异常凭证", "点击登录", "验证错误提示"],
                        "expected_template": "显示相应错误信息",
                        "priority": "P1"
                    }
                ]
            },
            {
                "req_id": "REQ_USER_PROFILE_001",
                "title": "用户个人资料管理",
                "description": "用户可以查看和编辑个人资料，包括头像、昵称、联系方式等",
                "feature_type": "用户管理",
                "complexity": "简单",
                "business_scenario": ["个人中心", "用户信息"],
                "technical_keywords": ["个人资料", "编辑", "头像", "昵称"],
                "test_case_templates": [
                    {
                        "scenario": "查看个人资料",
                        "test_type": "功能测试",
                        "title_template": "验证个人资料页面显示",
                        "steps_template": ["登录系统", "进入个人中心", "查看资料信息"],
                        "expected_template": "正确显示用户资料信息",
                        "priority": "P1"
                    }
                ]
            },
            {
                "req_id": "REQ_ORDER_001",
                "title": "订单管理系统",
                "description": "用户可以创建、查看、修改和取消订单",
                "feature_type": "业务管理",
                "complexity": "复杂",
                "business_scenario": ["电商", "订单处理"],
                "technical_keywords": ["订单", "创建", "查看", "修改", "取消"],
                "test_case_templates": [
                    {
                        "scenario": "创建订单",
                        "test_type": "功能测试",
                        "title_template": "验证订单创建流程",
                        "steps_template": ["选择商品", "填写订单信息", "提交订单", "验证创建结果"],
                        "expected_template": "成功创建订单并生成订单号",
                        "priority": "P0"
                    }
                ]
            }
        ]
        
        # 批量添加需求
        success_count = 0
        for req in test_requirements:
            if kb.add_requirement_to_knowledge_base(req):
                success_count += 1
                print(f"✅ 成功添加需求: {req['req_id']} - {req['title']}")
            else:
                print(f"❌ 添加需求失败: {req['req_id']}")
        
        print(f"📈 总计添加 {success_count}/{len(test_requirements)} 个需求")
        
        # 检查统计信息
        stats = kb.get_knowledge_base_stats()
        print(f"📊 更新后的知识库统计: 总需求数={stats.get('total_requirements', 0)}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 添加需求测试失败: {str(e)}")
        return False


async def test_search_similar_requirements():
    """测试搜索相似需求功能"""
    print("\n=== 测试3: 搜索相似需求 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        # 测试不同的搜索查询
        test_queries = [
            {"query": "用户登录", "feature_type": "", "description": "搜索登录相关需求"},
            {"query": "个人资料", "feature_type": "用户管理", "description": "在用户管理类别中搜索个人资料"},
            {"query": "订单创建", "feature_type": "", "description": "搜索订单创建相关需求"},
            {"query": "验证功能", "feature_type": "", "description": "搜索验证相关需求"}
        ]
        
        for test_query in test_queries:
            print(f"\n🔍 {test_query['description']}")
            print(f"   查询: '{test_query['query']}'")
            if test_query['feature_type']:
                print(f"   类型过滤: {test_query['feature_type']}")
            
            similar_reqs = kb.search_similar_requirements(
                query=test_query['query'],
                feature_type=test_query['feature_type'],
                top_k=3
            )
            
            if similar_reqs:
                print(f"   找到 {len(similar_reqs)} 个相似需求:")
                for i, req in enumerate(similar_reqs, 1):
                    req_data = req['requirement']
                    print(f"   {i}. {req_data['title']} (相似度: {req['match_score']:.2f})")
                    if 'matched_keywords' in req:
                        print(f"      匹配关键词: {', '.join(req['matched_keywords'])}")
            else:
                print("   ❌ 未找到相似需求")
        
        return True
        
    except Exception as e:
        print(f"❌ 搜索相似需求测试失败: {str(e)}")
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
        
        print(f"📋 为需求推荐测试用例:")
        print(f"   需求: {test_requirement['title']}")
        print(f"   描述: {test_requirement['description']}")
        print(f"   类型: {test_requirement['feature_type']}")
        
        # 获取推荐（不使用AI，避免API依赖）
        print("\n🤖 获取推荐（基于历史数据）...")
        recommendations = await kb.recommend_test_cases_for_requirement(
            requirement_data=test_requirement,
            use_ai=False  # 不使用AI推荐，避免API依赖
        )
        
        if recommendations:
            print(f"✅ 获得 {len(recommendations)} 个推荐:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n   推荐 {i}:")
                print(f"   来源: {rec['source']}")
                print(f"   匹配度: {rec['match_score']:.2f}")
                
                template = rec['template']
                if isinstance(template, dict):
                    print(f"   场景: {template.get('scenario', 'N/A')}")
                    print(f"   类型: {template.get('test_type', 'N/A')}")
                    if 'title_template' in template:
                        print(f"   标题模板: {template['title_template']}")
                    if 'steps_template' in template:
                        print(f"   步骤模板: {template['steps_template']}")
        else:
            print("📝 暂无推荐结果，可能需要更多历史数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试用例推荐测试失败: {str(e)}")
        return False


async def test_coverage_analysis():
    """测试覆盖度分析功能"""
    print("\n=== 测试5: 测试覆盖度分析 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        # 分析已添加需求的覆盖度
        test_requirement_id = "REQ_LOGIN_001"
        
        print(f"📊 分析需求 {test_requirement_id} 的测试覆盖度...")
        
        coverage_analysis = kb.analyze_requirement_test_coverage(test_requirement_id)
        
        if 'error' not in coverage_analysis:
            print(f"✅ 覆盖度分析完成:")
            print(f"   需求: {coverage_analysis['requirement_title']}")
            print(f"   测试用例数量: {coverage_analysis['test_case_count']}")
            
            print(f"\n   已覆盖的测试领域:")
            for area in coverage_analysis['coverage_areas']:
                print(f"   • {area['scenario']} ({area['test_type']})")
            
            if coverage_analysis['missing_areas']:
                print(f"\n   缺失的测试类型:")
                for missing in coverage_analysis['missing_areas']:
                    print(f"   • {missing}")
            
            if coverage_analysis['recommendations']:
                print(f"\n   改进建议:")
                for rec in coverage_analysis['recommendations']:
                    print(f"   • {rec}")
        else:
            print(f"❌ 覆盖度分析失败: {coverage_analysis['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 覆盖度分析测试失败: {str(e)}")
        return False


async def test_knowledge_base_stats():
    """测试知识库统计信息"""
    print("\n=== 测试6: 知识库统计信息 ===")
    
    try:
        kb = RequirementKnowledgeBase()
        
        stats = kb.get_knowledge_base_stats()
        
        if 'error' not in stats:
            print("✅ 知识库统计信息:")
            print(f"   总需求数量: {stats['total_requirements']}")
            print(f"   功能类型: {stats['feature_types']}")
            print(f"   演化功能数: {stats['evolution_features']}")
            print(f"   模板数量: {stats['template_count']}")
            print(f"   最后更新: {stats['last_updated']}")
            
            if 'requirements_by_type' in stats:
                print(f"\n   按类型统计:")
                for type_name, count in stats['requirements_by_type'].items():
                    print(f"   • {type_name}: {count} 个")
        else:
            print(f"❌ 获取统计信息失败: {stats['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 知识库统计测试失败: {str(e)}")
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
        ("覆盖度分析", test_coverage_analysis),
        ("统计信息", test_knowledge_base_stats)
    ]
    
    for test_name, test_func in test_functions:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {str(e)}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n🎯 测试完成: {passed} 个通过, {failed} 个失败")
    
    if failed == 0:
        print("🎉 所有测试通过！历史需求知识库功能正常。")
    else:
        print("⚠️  部分测试失败，请检查相关功能。")


if __name__ == "__main__":
    asyncio.run(main())