#!/usr/bin/env python3
"""
历史需求知识库命令行演示工具

使用方法：
    python demo_knowledge_base.py --help
    python demo_knowledge_base.py build
    python demo_knowledge_base.py search "图片合并"
    python demo_knowledge_base.py recommend "用户头像上传功能"
    python demo_knowledge_base.py stats
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.requirement_knowledge_base import RequirementKnowledgeBase


class KnowledgeBaseDemo:
    """历史需求知识库演示类"""
    
    def __init__(self):
        self.kb = RequirementKnowledgeBase()
        
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
        
    def print_separator(self):
        """打印分隔线"""
        print("-" * 60)
        
    async def build_knowledge_base(self, data_file: Optional[str] = None):
        """构建知识库"""
        self.print_header("🏗️ 构建历史需求知识库")
        
        if data_file is None:
            data_file = "local_data/msg_from_fetcher.json"
            
        # 检查数据文件是否存在
        if not Path(data_file).exists():
            print(f"❌ 数据文件不存在: {data_file}")
            print("💡 建议先运行: uv run tapd_data_fetcher.py 获取数据")
            print("💡 或者运行: uv run mcp_tools/fake_tapd_gen.py 生成测试数据")
            return False
            
        print(f"📂 使用数据文件: {data_file}")
        
        try:
            # 从TAPD数据构建知识库
            from mcp_tools.requirement_knowledge_base import build_knowledge_base_from_tapd_data
            result = await build_knowledge_base_from_tapd_data(data_file)
            
            if result.get("success"):
                print("✅ 知识库构建成功!")
                print(f"📊 处理了 {result.get('total_items', 0)} 个数据项")
                print(f"🎯 生成了 {result.get('requirements_count', 0)} 个需求")
                print(f"📋 创建了 {result.get('templates_count', 0)} 个测试用例模板")
                return True
            else:
                print(f"❌ 构建失败: {result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"❌ 构建过程中出现异常: {str(e)}")
            return False
            
    async def search_requirements(self, query: str, top_k: int = 5):
        """搜索相似需求"""
        self.print_header(f"🔍 搜索相似需求: '{query}'")
        
        try:
            results = self.kb.search_similar_requirements(query, top_k=top_k)
            
            if not results:
                print("❌ 没有找到相关需求")
                print("💡 建议:")
                print("   - 检查知识库是否已构建")
                print("   - 尝试更通用的关键词")
                print("   - 确保知识库中有相关数据")
                return
                
            print(f"📋 找到 {len(results)} 个相关需求:")
            
            for i, result in enumerate(results, 1):
                req = result['requirement']
                score = result['match_score']
                
                print(f"\n{i}. 【{req['title']}】")
                print(f"   💫 相似度: {score:.2f}")
                print(f"   🏷️ 功能类型: {req['feature_type']}")
                print(f"   📝 描述: {req['description'][:100]}...")
                print(f"   🔗 需求ID: {req['req_id']}")
                
                # 显示关键词
                if req.get('technical_keywords'):
                    keywords = ', '.join(req['technical_keywords'][:5])
                    print(f"   🔧 关键词: {keywords}")
                    
        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
            
    async def recommend_test_cases(self, requirement_title: str, description: str = "", feature_type: str = ""):
        """推荐测试用例"""
        self.print_header(f"🎯 为需求推荐测试用例: '{requirement_title}'")
        
        # 构建需求数据
        requirement_data = {
            "title": requirement_title,
            "description": description or f"关于{requirement_title}的功能需求",
            "feature_type": feature_type or "功能需求",
            "business_scenario": [requirement_title],
            "technical_keywords": requirement_title.split()
        }
        
        try:
            recommendations = await self.kb.recommend_test_cases_for_requirement(
                requirement_data=requirement_data,
                use_ai=False  # 使用本地推荐，不调用AI
            )
            
            if not recommendations:
                print("❌ 没有找到相关的测试用例推荐")
                print("💡 建议:")
                print("   - 检查知识库是否已构建")
                print("   - 尝试更具体的需求描述")
                return
                
            print(f"📋 找到 {len(recommendations)} 个测试用例推荐:")
            
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. 【来源: {rec['source']}】")
                print(f"   💫 匹配度: {rec['match_score']:.2f}")
                print(f"   📝 推荐理由: {rec['reason']}")
                
                if 'template' in rec and isinstance(rec['template'], dict):
                    template = rec['template']
                    print(f"   🎬 测试场景: {template.get('scenario', 'N/A')}")
                    print(f"   🔧 测试类型: {template.get('test_type', 'N/A')}")
                    
                    if template.get('steps_template'):
                        print("   📋 测试步骤:")
                        for j, step in enumerate(template['steps_template'][:3], 1):
                            print(f"      {j}. {step}")
                            
        except Exception as e:
            print(f"❌ 推荐失败: {str(e)}")
            
    async def show_stats(self):
        """显示知识库统计信息"""
        self.print_header("📊 知识库统计信息")
        
        try:
            stats = self.kb.get_knowledge_base_stats()
            
            if 'error' in stats:
                print(f"❌ 获取统计信息失败: {stats['error']}")
                return
                
            print(f"📚 总需求数量: {stats.get('total_requirements', 0)}")
            print(f"🏷️ 功能类型数: {len(stats.get('feature_types', []))}")
            print(f"📋 测试模板数: {stats.get('template_count', 0)}")
            print(f"🔄 演化特性数: {stats.get('evolution_features', 0)}")
            print(f"📅 最后更新: {stats.get('last_updated', 'N/A')}")
            
            # 显示功能类型分布
            if stats.get('requirements_by_type'):
                print("\n🎯 需求类型分布:")
                for type_name, count in stats['requirements_by_type'].items():
                    print(f"   • {type_name}: {count} 个")
                    
            # 显示功能类型列表
            if stats.get('feature_types'):
                print(f"\n🏷️ 功能类型列表:")
                for i, feature_type in enumerate(stats['feature_types'][:10], 1):
                    print(f"   {i}. {feature_type}")
                if len(stats['feature_types']) > 10:
                    print(f"   ... 还有 {len(stats['feature_types']) - 10} 个")
                    
        except Exception as e:
            print(f"❌ 获取统计信息失败: {str(e)}")
            
    async def add_requirement(self, req_id: str, title: str, description: str, feature_type: str):
        """添加新需求"""
        self.print_header(f"➕ 添加新需求: {title}")
        
        requirement_data = {
            "req_id": req_id,
            "title": title,
            "description": description,
            "feature_type": feature_type,
            "complexity": "中等",
            "business_scenario": [feature_type],
            "technical_keywords": title.split(),
            "test_case_templates": []
        }
        
        try:
            success = self.kb.add_requirement_to_knowledge_base(requirement_data)
            
            if success:
                print("✅ 需求添加成功!")
                print(f"🆔 需求ID: {req_id}")
                print(f"📝 标题: {title}")
                print(f"🏷️ 类型: {feature_type}")
            else:
                print("❌ 需求添加失败")
                
        except Exception as e:
            print(f"❌ 添加需求失败: {str(e)}")
            
    async def interactive_demo(self):
        """交互式演示"""
        self.print_header("🎮 交互式演示模式")
        
        print("欢迎使用历史需求知识库！")
        print("您可以尝试以下操作:")
        print("1. 搜索需求")
        print("2. 推荐测试用例")
        print("3. 查看统计信息")
        print("4. 添加新需求")
        print("0. 退出")
        
        while True:
            try:
                choice = input("\n请选择操作 (0-4): ").strip()
                
                if choice == '0':
                    print("👋 再见！")
                    break
                elif choice == '1':
                    query = input("请输入搜索关键词: ").strip()
                    if query:
                        await self.search_requirements(query)
                elif choice == '2':
                    title = input("请输入需求标题: ").strip()
                    if title:
                        await self.recommend_test_cases(title)
                elif choice == '3':
                    await self.show_stats()
                elif choice == '4':
                    req_id = input("请输入需求ID: ").strip()
                    title = input("请输入需求标题: ").strip()
                    description = input("请输入需求描述: ").strip()
                    feature_type = input("请输入功能类型: ").strip()
                    if req_id and title and description and feature_type:
                        await self.add_requirement(req_id, title, description, feature_type)
                else:
                    print("❌ 无效选择，请重试")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 操作失败: {str(e)}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="历史需求知识库命令行演示工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
    python demo_knowledge_base.py build
    python demo_knowledge_base.py search "图片合并"
    python demo_knowledge_base.py recommend "用户头像上传功能"
    python demo_knowledge_base.py stats
    python demo_knowledge_base.py add REQ_TEST_001 "测试功能" "这是一个测试功能" "测试"
    python demo_knowledge_base.py interactive
        """
    )
    
    parser.add_argument('action', choices=['build', 'search', 'recommend', 'stats', 'add', 'interactive'],
                       help='要执行的操作')
    parser.add_argument('args', nargs='*', help='操作参数')
    parser.add_argument('--data-file', '-f', help='数据文件路径')
    parser.add_argument('--top-k', '-k', type=int, default=5, help='搜索结果数量')
    
    args = parser.parse_args()
    
    demo = KnowledgeBaseDemo()
    
    try:
        if args.action == 'build':
            await demo.build_knowledge_base(args.data_file)
            
        elif args.action == 'search':
            if not args.args:
                print("❌ 请提供搜索关键词")
                return
            await demo.search_requirements(args.args[0], args.top_k)
            
        elif args.action == 'recommend':
            if not args.args:
                print("❌ 请提供需求标题")
                return
            title = args.args[0]
            description = args.args[1] if len(args.args) > 1 else ""
            feature_type = args.args[2] if len(args.args) > 2 else ""
            await demo.recommend_test_cases(title, description, feature_type)
            
        elif args.action == 'stats':
            await demo.show_stats()
            
        elif args.action == 'add':
            if len(args.args) < 4:
                print("❌ 请提供: 需求ID 标题 描述 功能类型")
                return
            await demo.add_requirement(args.args[0], args.args[1], args.args[2], args.args[3])
            
        elif args.action == 'interactive':
            await demo.interactive_demo()
            
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())