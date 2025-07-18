"""
使用Excel测试用例文件测试历史需求知识库功能

本脚本将：
1. 读取Excel测试用例文件
2. 从测试用例中提取需求信息
3. 构建知识库
4. 测试搜索和推荐功能
"""

import asyncio
import json
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.requirement_knowledge_base import RequirementKnowledgeBase
from mcp_tools.test_case_evaluator import TestCaseProcessor


async def load_excel_test_cases(excel_path: str):
    """加载Excel测试用例文件"""
    print(f"=== 加载Excel文件: {excel_path} ===")
    
    try:
        # 使用pandas读取Excel文件
        df = pd.read_excel(excel_path)
        print(f"成功读取Excel文件，包含 {len(df)} 行数据")
        
        # 显示列名
        print(f"Excel列名: {list(df.columns)}")
        
        # 显示前几行数据的概览
        print("\n前3行数据概览:")
        for i, row in df.head(3).iterrows():
            print(f"第{i+1}行:")
            for col in df.columns:
                value = str(row[col])[:100] if pd.notna(row[col]) else ""
                print(f"  {col}: {value}")
        
        return df
        
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return None


async def extract_requirements_from_test_cases(df):
    """从测试用例中提取需求信息"""
    print("\n=== 从测试用例提取需求信息 ===")
    
    requirements = []
    
    # 根据测试用例的目录和标题推断需求
    if '用例目录' in df.columns:
        # 按用例目录分组
        for category in df['用例目录'].dropna().unique():
            category_cases = df[df['用例目录'] == category]
            
            # 生成需求信息
            requirement = {
                "req_id": f"REQ_{category.replace(' ', '_').replace('/', '_')}_001",
                "title": f"{category}相关功能",
                "description": f"基于测试用例分析，{category}相关的功能需求",
                "feature_type": category,
                "complexity": "中等",
                "business_scenario": [category],
                "technical_keywords": [],
                "test_case_templates": []
            }
            
            # 从测试用例中提取关键词
            keywords = set()
            templates = []
            
            for _, case in category_cases.iterrows():
                # 提取关键词
                if '用例标题' in case and pd.notna(case['用例标题']):
                    title_words = str(case['用例标题']).split()
                    keywords.update([word for word in title_words if len(word) > 1])
                
                # 创建测试用例模板
                if '用例标题' in case and pd.notna(case['用例标题']):
                    template = {
                        "scenario": str(case['用例标题'])[:50],
                        "test_type": "功能测试",
                        "title_template": str(case['用例标题']),
                        "priority": case.get('等级', 'P1') if '等级' in case else 'P1'
                    }
                    
                    if '步骤描述' in case and pd.notna(case['步骤描述']):
                        template["steps_template"] = str(case['步骤描述']).split('\n')[:5]
                    
                    if '预期结果' in case and pd.notna(case['预期结果']):
                        template["expected_template"] = str(case['预期结果'])[:200]
                    
                    templates.append(template)
            
            requirement["technical_keywords"] = list(keywords)[:10]
            requirement["test_case_templates"] = templates[:5]  # 最多5个模板
            
            requirements.append(requirement)
            print(f"提取需求: {requirement['title']} (包含{len(templates)}个测试用例模板)")
    
    print(f"总计提取 {len(requirements)} 个需求")
    return requirements


async def test_knowledge_base_with_excel():
    """使用Excel数据测试知识库功能"""
    print("\n=== 使用Excel数据测试知识库 ===")
    
    # 初始化知识库
    kb = RequirementKnowledgeBase()
    
    # Excel文件路径
    excel_path = "local_data/TestCase_20250717141033-32202633.xlsx"
    
    # 1. 加载Excel数据
    df = await load_excel_test_cases(excel_path)
    if df is None:
        return False
    
    # 2. 提取需求信息
    requirements = await extract_requirements_from_test_cases(df)
    if not requirements:
        print("未能从Excel中提取需求信息")
        return False
    
    # 3. 添加需求到知识库
    print(f"\n=== 添加 {len(requirements)} 个需求到知识库 ===")
    success_count = 0
    for req in requirements:
        if kb.add_requirement_to_knowledge_base(req):
            success_count += 1
            print(f"✓ 添加需求: {req['title']}")
        else:
            print(f"✗ 添加失败: {req['title']}")
    
    print(f"成功添加 {success_count}/{len(requirements)} 个需求")
    
    # 4. 测试搜索功能
    print(f"\n=== 测试搜索功能 ===")
    test_queries = ["登录", "用户", "验证", "功能", "测试"]
    
    for query in test_queries:
        results = kb.search_similar_requirements(query, top_k=3)
        print(f"搜索 '{query}': 找到 {len(results)} 个相关需求")
        for i, result in enumerate(results, 1):
            req_data = result['requirement']
            print(f"  {i}. {req_data['title']} (相似度: {result['match_score']:.2f})")
    
    # 5. 测试推荐功能
    print(f"\n=== 测试推荐功能 ===")
    test_requirement = {
        "title": "新用户注册功能",
        "description": "用户可以通过邮箱或手机号注册新账户",
        "feature_type": "用户管理",
        "business_scenario": ["用户注册", "账户管理"],
        "technical_keywords": ["注册", "用户", "账户", "邮箱", "手机"]
    }
    
    recommendations = await kb.recommend_test_cases_for_requirement(
        requirement_data=test_requirement,
        use_ai=False
    )
    
    print(f"为 '{test_requirement['title']}' 获得 {len(recommendations)} 个推荐")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. 来源: {rec['source']}, 匹配度: {rec['match_score']:.2f}")
        if 'template' in rec and isinstance(rec['template'], dict):
            template = rec['template']
            print(f"     场景: {template.get('scenario', 'N/A')}")
    
    # 6. 显示知识库统计
    print(f"\n=== 知识库统计信息 ===")
    stats = kb.get_knowledge_base_stats()
    if 'error' not in stats:
        print(f"总需求数: {stats['total_requirements']}")
        print(f"功能类型: {stats['feature_types']}")
        print(f"按类型分布:")
        for type_name, count in stats.get('requirements_by_type', {}).items():
            print(f"  - {type_name}: {count} 个")
    
    return True


async def main():
    """主函数"""
    print("使用Excel测试用例文件测试历史需求知识库功能")
    print("=" * 60)
    
    try:
        result = await test_knowledge_base_with_excel()
        
        if result:
            print("\n" + "=" * 60)
            print("测试完成！知识库功能与Excel数据集成成功")
            print("\n现在您可以：")
            print("1. 通过AI客户端使用这些需求数据")
            print("2. 继续添加更多需求到知识库")
            print("3. 使用搜索和推荐功能辅助测试用例编写")
        else:
            print("\n测试过程中出现问题，请检查Excel文件格式")
            
    except Exception as e:
        print(f"\n测试过程中出现异常: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())