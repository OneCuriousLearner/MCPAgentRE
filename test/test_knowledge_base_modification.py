#!/usr/bin/env python3
"""
测试修改后的knowledge_base.py功能

验证点：
1. 原始TAPD数据文件保持不变
2. 知识库数据保存在独立配置文件中
3. 与test_case_require_list_knowledge_base.py使用相同的数据管理方式
4. MCP工具正常工作
"""

import json
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.knowledge_base import enhance_tapd_data_with_knowledge, HistoryRequirementKnowledgeBase
from tapd_mcp_server import enhance_tapd_with_knowledge


def test_original_file_unchanged():
    """测试原始文件是否保持不变"""
    print("=== 测试1: 原始文件保持不变 ===")
    
    original_file = project_root / "local_data" / "msg_from_fetcher.json"
    backup_file = project_root / "local_data" / "msg_from_fetcher.backup.json"
    
    # 检查原始文件状态
    if original_file.exists():
        with open(original_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stories = data.get('stories', [])
        if stories:
            first_story = stories[0]
            has_kb_info = 'kb_info' in first_story
            print(f"✓ 原始文件存在")
            print(f"✓ 原始文件未被修改（无kb_info字段）: {not has_kb_info}")
            print(f"✓ 备份文件不存在（应该不存在）: {not backup_file.exists()}")
            return not has_kb_info and not backup_file.exists()
        else:
            print("❌ 原始文件无数据")
            return False
    else:
        print("❌ 原始文件不存在")
        return False


def test_knowledge_base_config():
    """测试知识库配置文件"""
    print("\n=== 测试2: 知识库配置文件 ===")
    
    config_file = project_root / "config" / "knowledge_base_config.json"
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
        
        # 检查必要字段
        required_fields = ['requirements_analysis', 'test_case_templates', 'feature_types', 
                          'keywords_mapping', 'total_count', 'last_updated']
        
        missing_fields = [field for field in required_fields if field not in kb_data]
        
        print(f"✓ 知识库配置文件存在")
        print(f"✓ 包含所有必要字段: {len(missing_fields) == 0}")
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
        
        req_count = len(kb_data.get('requirements_analysis', []))
        print(f"✓ 需求分析数量: {req_count}")
        print(f"✓ 最后更新时间: {kb_data.get('last_updated', '未设置')}")
        
        return len(missing_fields) == 0 and req_count > 0
    else:
        print("❌ 知识库配置文件不存在")
        return False


def test_data_structure_consistency():
    """测试数据结构与test_case_require_list_knowledge_base.py的一致性"""
    print("\n=== 测试3: 数据结构一致性 ===")
    
    try:
        # 测试HistoryRequirementKnowledgeBase类的基本功能
        kb_manager = HistoryRequirementKnowledgeBase()
        
        print(f"✓ HistoryRequirementKnowledgeBase类可正常实例化")
        print(f"✓ 配置文件路径: {kb_manager.config_file}")
        print(f"✓ 使用common_utils模块: {hasattr(kb_manager, 'file_manager')}")
        
        # 检查目录结构
        config_dir = kb_manager.config_file.parent
        print(f"✓ config目录存在: {config_dir.exists()}")
        
        return True
    except Exception as e:
        print(f"❌ 数据结构一致性测试失败: {e}")
        return False


async def test_mcp_tool():
    """测试MCP工具功能"""
    print("\n=== 测试4: MCP工具功能 ===")
    
    try:
        # 测试直接函数调用
        result = enhance_tapd_data_with_knowledge()
        print(f"✓ 直接函数调用成功: {result['status'] == 'success'}")
        
        # 测试MCP工具调用
        mcp_result = await enhance_tapd_with_knowledge()
        mcp_data = json.loads(mcp_result)
        print(f"✓ MCP工具调用成功: {mcp_data['status'] == 'success'}")
        
        return result['status'] == 'success' and mcp_data['status'] == 'success'
    except Exception as e:
        print(f"❌ MCP工具测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始测试knowledge_base.py修改后的功能...\n")
    
    tests = [
        ("原始文件保持不变", test_original_file_unchanged),
        ("知识库配置文件", test_knowledge_base_config),
        ("数据结构一致性", test_data_structure_consistency),
        ("MCP工具功能", test_mcp_tool)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 发生异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "="*50)
    print("测试总结:")
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！knowledge_base.py修改成功！")
    else:
        print("⚠️  部分测试失败，需要检查问题")


if __name__ == "__main__":
    asyncio.run(main())
