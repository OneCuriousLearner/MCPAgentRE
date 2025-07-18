#!/usr/bin/env python3
"""
历史需求知识库快速演示脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.requirement_knowledge_base import RequirementKnowledgeBase
import pandas as pd


async def demo_with_excel_data():
    """使用Excel数据演示知识库功能"""
    print("=" * 60)
    print("  历史需求知识库快速演示")
    print("=" * 60)
    
    # 初始化知识库
    kb = RequirementKnowledgeBase()
    
    # 检查Excel文件
    excel_file = "local_data/TestCase_20250717141033-32202633.xlsx"
    if not Path(excel_file).exists():
        print(f"错误: Excel文件不存在: {excel_file}")
        return
        
    print(f"使用Excel文件: {excel_file}")
    
    # 直接读取Excel并构建几个示例需求
    try:
        df = pd.read_excel(excel_file)
        print(f"Excel文件包含 {len(df)} 个测试用例")
        
        # 从前几个测试用例创建需求
        sample_requirements = [
            {
                "req_id": "REQ_IMAGE_001",
                "title": "图片合并功能",
                "description": "支持多种格式图片的合并处理，包括JPG、PNG、JPEG等格式",
                "feature_type": "图片处理",
                "complexity": "中等",
                "business_scenario": ["图片编辑", "多媒体处理"],
                "technical_keywords": ["图片", "合并", "处理", "格式转换"],
                "test_case_templates": []
            },
            {
                "req_id": "REQ_USER_001", 
                "title": "用户权限管理",
                "description": "管理不同用户的访问权限，包括查看、编辑、删除等权限控制",
                "feature_type": "用户管理",
                "complexity": "高",
                "business_scenario": ["权限控制", "用户管理"],
                "technical_keywords": ["用户", "权限", "管理", "访问控制"],
                "test_case_templates": []
            },
            {
                "req_id": "REQ_VIDEO_001",
                "title": "视频处理功能", 
                "description": "支持视频的播放、编辑、压缩等处理功能",
                "feature_type": "视频处理",
                "complexity": "高",
                "business_scenario": ["视频播放", "多媒体处理"],
                "technical_keywords": ["视频", "播放", "编辑", "压缩"],
                "test_case_templates": []
            },
            {
                "req_id": "REQ_WECHAT_001",
                "title": "微信元素集成",
                "description": "集成微信相关功能，支持微信登录、分享等",
                "feature_type": "第三方集成",
                "complexity": "中等", 
                "business_scenario": ["微信集成", "社交功能"],
                "technical_keywords": ["微信", "集成", "登录", "分享"],
                "test_case_templates": []
            }
        ]
        
        # 添加需求到知识库
        print("\n添加示例需求到知识库...")
        for req in sample_requirements:
            success = kb.add_requirement_to_knowledge_base(req)
            if success:
                print(f"成功添加: {req['title']}")
            else:
                print(f"添加失败: {req['title']}")
                
        # 显示统计信息
        print("\n" + "="*60)
        print("  知识库统计信息")
        print("="*60)
        
        stats = kb.get_knowledge_base_stats()
        if 'error' not in stats:
            print(f"总需求数量: {stats.get('total_requirements', 0)}")
            print(f"功能类型数: {len(stats.get('feature_types', []))}")
            print(f"测试模板数: {stats.get('template_count', 0)}")
            
            if stats.get('feature_types'):
                print("\n功能类型列表:")
                for i, feature_type in enumerate(stats['feature_types'], 1):
                    print(f"   {i}. {feature_type}")
        
        # 演示搜索功能
        print("\n" + "="*60)
        print("  搜索功能演示")
        print("="*60)
        
        test_queries = ["图片", "用户", "视频", "微信"]
        for query in test_queries:
            print(f"\n搜索: '{query}'")
            results = kb.search_similar_requirements(query, top_k=3)
            
            if results:
                print(f"找到 {len(results)} 个相关需求:")
                for i, result in enumerate(results, 1):
                    req = result['requirement']
                    score = result['match_score']
                    print(f"   {i}. {req['title']} (相似度: {score:.2f})")
            else:
                print("   未找到相关需求")
        
        # 演示推荐功能
        print("\n" + "="*60)
        print("  推荐功能演示")
        print("="*60)
        
        test_requirements = [
            "图片滤镜功能",
            "用户登录验证",
            "视频播放器"
        ]
        
        for req_title in test_requirements:
            print(f"\n为需求 '{req_title}' 推荐测试用例:")
            
            requirement_data = {
                "title": req_title,
                "description": f"关于{req_title}的功能需求",
                "feature_type": "功能需求",
                "business_scenario": [req_title],
                "technical_keywords": req_title.split()
            }
            
            recommendations = await kb.recommend_test_cases_for_requirement(
                requirement_data=requirement_data,
                use_ai=False
            )
            
            if recommendations:
                print(f"   找到 {len(recommendations)} 个推荐:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. 来源: {rec['source']} (匹配度: {rec['match_score']:.2f})")
            else:
                print("   暂无推荐")
                
        print("\n" + "="*60)
        print("  演示完成！")
        print("="*60)
        print("您现在可以使用以下命令继续探索:")
        print("  uv run demo_kb_simple.py search \"关键词\"")
        print("  uv run demo_kb_simple.py recommend \"需求标题\"")
        print("  uv run demo_kb_simple.py stats")
        print("  uv run demo_kb_simple.py add REQ_NEW_001 \"新需求\" \"描述\" \"类型\"")
        
    except Exception as e:
        print(f"错误: {str(e)}")


if __name__ == "__main__":
    asyncio.run(demo_with_excel_data())