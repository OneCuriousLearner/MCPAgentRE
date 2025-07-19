"""
历史需求知识库 - 极简版本

只做一件事：增强TAPD数据，让现有的search_data()工具返回更有用的信息
不添加新的MCP工具，只在现有数据基础上增加关联信息
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.common_utils import get_config, get_file_manager


def enhance_tapd_data_with_knowledge(tapd_file: str = "local_data/msg_from_fetcher.json",
                                    testcase_file: Optional[str] = None) -> Dict[str, Any]:
    """
    增强TAPD数据，添加测试用例模板和关联信息
    不创建新的数据库，而是直接增强现有的TAPD数据文件
    """
    try:
        config = get_config()
        file_manager = get_file_manager()
        
        # 加载原始TAPD数据
        tapd_data = file_manager.load_tapd_data(tapd_file)
        stories = tapd_data.get('stories', [])
        
        # 处理测试用例数据
        test_case_templates = {}
        if testcase_file and Path(testcase_file).exists():
            test_case_templates = _extract_test_case_templates(testcase_file)
        
        # 增强需求数据
        enhanced_stories = []
        for story in stories:
            # 保持原有数据不变，只添加知识库信息
            enhanced_story = story.copy()
            
            # 添加增强信息
            enhanced_story['kb_info'] = {
                "feature_type": _extract_feature_type(story),
                "test_case_suggestions": _suggest_test_cases(story, test_case_templates),
                "similar_keywords": _extract_keywords(story)
            }
            
            enhanced_stories.append(enhanced_story)
        
        # 保存增强后的数据
        enhanced_data = {
            **tapd_data,
            'stories': enhanced_stories,
            'knowledge_base_meta': {
                "enhanced_at": datetime.now().isoformat(),
                "test_templates_count": len(test_case_templates),
                "enhanced_requirements": len(enhanced_stories)
            }
        }
        
        # 保存到原文件，备份原文件
        backup_file = Path(tapd_file).with_suffix('.backup.json')
        if Path(tapd_file).exists():
            import shutil
            shutil.copy2(tapd_file, backup_file)
        
        file_manager.save_json_data(enhanced_data, tapd_file)
        
        return {
            "status": "success",
            "message": f"TAPD数据增强完成，备份保存为 {backup_file.name}",
            "enhanced_requirements": len(enhanced_stories),
            "test_templates": len(test_case_templates),
            "backup_file": str(backup_file)
        }
        
    except Exception as e:
        return {"status": "error", "message": f"数据增强失败: {str(e)}"}


def _extract_test_case_templates(testcase_file: str) -> Dict[str, Any]:
    """提取测试用例模板"""
    try:
        df = pd.read_excel(testcase_file)
        
        templates = {}
        for _, row in df.iterrows():
            title = str(row.get('用例标题', '')).strip()
            if not title:
                continue
                
            # 提取模板类型
            template_type = _categorize_test_case(title)
            
            if template_type not in templates:
                templates[template_type] = {
                    "examples": [],
                    "common_steps": [],
                    "priorities": []
                }
            
            # 收集示例
            templates[template_type]["examples"].append({
                "title": title,
                "steps": str(row.get('步骤描述', '')).strip(),
                "expected": str(row.get('预期结果', '')).strip(),
                "priority": str(row.get('等级', '')).strip()
            })
        
        return templates
        
    except Exception as e:
        print(f"提取测试用例模板失败: {e}")
        return {}


def _categorize_test_case(title: str) -> str:
    """对测试用例进行简单分类"""
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['登录', '注册', '密码']):
        return "用户认证"
    elif any(word in title_lower for word in ['搜索', '查询', '过滤']):
        return "搜索功能"
    elif any(word in title_lower for word in ['上传', '下载', '文件']):
        return "文件操作"
    elif any(word in title_lower for word in ['支付', '订单', '购买']):
        return "交易流程"
    elif any(word in title_lower for word in ['权限', '角色', '授权']):
        return "权限管理"
    else:
        return "通用功能"


def _extract_feature_type(story: Dict) -> str:
    """从需求中提取功能类型"""
    name = story.get('name', '').lower()
    description = story.get('description', '').lower()
    
    # 简单的关键词映射
    type_keywords = {
        '登录': '用户认证',
        '搜索': '搜索功能',
        '上传': '文件操作',
        '支付': '交易流程',
        '权限': '权限管理'
    }
    
    for keyword, feature_type in type_keywords.items():
        if keyword in name or keyword in description:
            return feature_type
    
    return "通用功能"


def _suggest_test_cases(story: Dict, templates: Dict) -> List[str]:
    """为需求推荐测试用例"""
    feature_type = _extract_feature_type(story)
    
    suggestions = []
    if feature_type in templates:
        # 取前3个最相关的测试用例标题
        examples = templates[feature_type]["examples"][:3]
        suggestions = [example["title"] for example in examples]
    
    return suggestions


def _extract_keywords(story: Dict) -> List[str]:
    """提取关键词"""
    import jieba
    
    content = f"{story.get('name', '')} {story.get('description', '')}"
    words = jieba.cut(content)
    
    # 过滤有意义的词汇
    meaningful_words = [word for word in words 
                       if len(word) > 1 and word not in ['功能', '需求', '系统', '支持', '用户']]
    
    return list(set(meaningful_words))[:8]  # 最多8个关键词


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='历史需求知识库 - 增强TAPD数据')
    parser.add_argument('-t', '--tapd-file', default='local_data/msg_from_fetcher.json', 
                       help='TAPD数据文件路径')
    parser.add_argument('-c', '--testcase-file', 
                       help='测试用例Excel文件路径')
    
    args = parser.parse_args()
    
    print("增强TAPD数据，添加知识库信息...")
    print(f"TAPD文件: {args.tapd_file}")
    print(f"测试用例文件: {args.testcase_file}")
    
    result = enhance_tapd_data_with_knowledge(args.tapd_file, args.testcase_file)
    
    if result['status'] == 'success':
        print(f"\n✅ {result['message']}")
        print(f"增强需求数: {result['enhanced_requirements']}")
        print(f"测试模板数: {result['test_templates']}")
        print(f"备份文件: {result['backup_file']}")
    else:
        print(f"\n❌ {result['message']}")