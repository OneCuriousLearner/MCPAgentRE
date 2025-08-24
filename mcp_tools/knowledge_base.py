"""
历史需求知识库 - 知识查询版本

该脚本用于管理和查询历史需求知识库，为 TAPD 数据分析提供知识库支持功能。

主要功能：
- 从 TAPD JSON 数据中提取需求信息，仅读取不修改原始文件
- 可选加载测试用例模板 Excel 文件，并分析标题、步骤、预期等信息
- 根据简单的关键词映射，对需求进行功能类型分类（如用户认证、搜索功能等）
- 针对不同功能类型，推荐对应的测试用例标题（最多3条）
- 使用 jieba 分词，从需求标题和描述中提取关键信息词，输出最多8个关键词
- 将知识库信息保存到独立的配置文件中，与原始数据分离存储

数据存储逻辑：
- 知识库数据存储在 config/knowledge_base_config.json 中
- 采用与 test_case_require_list_knowledge_base.py 相同的文件管理方式
- 原始 TAPD 数据文件保持不变，仅作为数据源读取

使用示例：
    python mcp_tools/knowledge_base.py -t local_data/msg_from_fetcher.json -c test_cases.xlsx

函数说明：
- enhance_tapd_data_with_knowledge：知识库查询和分析函数
- _extract_test_case_templates：提取并组织测试用例模板
- _categorize_test_case：对测试用例标题进行分类
- _extract_feature_type：基于关键词映射提取需求功能类型
- _suggest_test_cases：为需求推荐测试用例
- _extract_keywords：从文本中提取关键词
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import re

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.common_utils import get_config, get_file_manager


class HistoryRequirementKnowledgeBase:
    """历史需求知识库管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.file_manager = get_file_manager()
        # 配置文件路径至根目录的config文件夹
        config_dir = Path(self.config.project_root) / "config"
        # 确保config目录存在
        config_dir.mkdir(exist_ok=True)
        self.config_file = config_dir / "knowledge_base_config.json"
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """加载知识库配置"""
        try:
            if self.config_file.exists():
                data = self.file_manager.load_json_data(str(self.config_file))
                return data
            return {
                'requirements_analysis': [],
                'test_case_templates': {},
                'feature_types': {},
                'keywords_mapping': {},
                'total_count': 0,
                'last_updated': None
            }
        except Exception as e:
            print(f"❌ 加载知识库配置失败: {e}")
            return {
                'requirements_analysis': [],
                'test_case_templates': {},
                'feature_types': {},
                'keywords_mapping': {},
                'total_count': 0,
                'last_updated': None
            }
    
    def _save_knowledge_base(self):
        """保存知识库配置"""
        try:
            self.knowledge_base['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.file_manager.save_json_data(self.knowledge_base, str(self.config_file))
            print(f"✅ 知识库配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存知识库配置失败: {e}")

    def _extract_text_from_html(self, html_text: str) -> str:
        """从HTML文本中提取纯文本内容"""
        if not html_text:
            return ""
        
        # 简单的HTML标签清理
        text = re.sub(r'<[^>]+>', '', html_text)
        # 处理HTML实体
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # 清理多余空白
        text = ' '.join(text.split())
        return text.strip()


def enhance_tapd_data_with_knowledge(tapd_file: str = "local_data/msg_from_fetcher.json",
                                    testcase_file: Optional[str] = None) -> Dict[str, Any]:
    """
    分析TAPD数据并生成知识库信息
    仅读取原始数据，不修改原始文件，知识库信息保存到独立配置文件
    """
    try:
        # 初始化知识库管理器
        kb_manager = HistoryRequirementKnowledgeBase()
        
        # 加载原始TAPD数据（仅读取）
        tapd_data = kb_manager.file_manager.load_tapd_data(tapd_file)
        stories = tapd_data.get('stories', [])
        
        if not stories:
            return {
                "status": "error",
                "message": "未找到需求数据，请先调用 get_tapd_data 工具获取数据"
            }
        
        # 处理测试用例数据
        test_case_templates = {}
        if testcase_file and Path(testcase_file).exists():
            test_case_templates = _extract_test_case_templates(testcase_file)
        
        # 分析需求数据并生成知识库信息
        analyzed_requirements = []
        feature_types = {}
        keywords_mapping = {}
        
        for story in stories:
            # 提取基本信息
            story_id = story.get('id', '')
            title = story.get('name', '')
            description = kb_manager._extract_text_from_html(story.get('description', ''))
            
            # 分析功能类型
            feature_type = _extract_feature_type(story)
            if feature_type not in feature_types:
                feature_types[feature_type] = 0
            feature_types[feature_type] += 1
            
            # 生成测试用例建议
            test_case_suggestions = _suggest_test_cases(story, test_case_templates)
            
            # 提取关键词
            keywords = _extract_keywords(story)
            for keyword in keywords:
                if keyword not in keywords_mapping:
                    keywords_mapping[keyword] = []
                keywords_mapping[keyword].append({
                    'story_id': story_id,
                    'title': title[:50] + '...' if len(title) > 50 else title
                })
            
            # 构建分析结果
            requirement_analysis = {
                'requirement_id': story_id,
                'title': title,
                'description_preview': description[:200] + '...' if len(description) > 200 else description,
                'status': story.get('status', ''),
                'priority': story.get('priority', ''),
                'creator': story.get('creator', ''),
                'feature_type': feature_type,
                'test_case_suggestions': test_case_suggestions,
                'keywords': keywords,
                'created': story.get('created', ''),
                'modified': story.get('modified', ''),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            analyzed_requirements.append(requirement_analysis)
        
        # 更新知识库
        kb_manager.knowledge_base.update({
            'requirements_analysis': analyzed_requirements,
            'test_case_templates': test_case_templates,
            'feature_types': feature_types,
            'keywords_mapping': keywords_mapping,
            'total_count': len(analyzed_requirements)
        })
        
        # 保存知识库配置
        kb_manager._save_knowledge_base()
        
        return {
            "status": "success",
            "message": f"知识库分析完成，已保存到 {kb_manager.config_file.name}",
            "analyzed_requirements": len(analyzed_requirements),
            "test_templates": len(test_case_templates),
            "feature_types_count": len(feature_types),
            "unique_keywords": len(keywords_mapping),
            "config_file": str(kb_manager.config_file)
        }
        
    except Exception as e:
        return {"status": "error", "message": f"知识库分析失败: {str(e)}"}


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
    
    parser = argparse.ArgumentParser(description='历史需求知识库 - 分析TAPD数据并构建知识库')
    parser.add_argument('-t', '--tapd-file', default='local_data/msg_from_fetcher.json', 
                       help='TAPD数据文件路径')
    parser.add_argument('-c', '--testcase-file', 
                       help='测试用例Excel文件路径')
    
    args = parser.parse_args()
    
    print("分析TAPD数据，构建历史需求知识库...")
    print(f"TAPD文件: {args.tapd_file}")
    print(f"测试用例文件: {args.testcase_file}")
    
    result = enhance_tapd_data_with_knowledge(args.tapd_file, args.testcase_file)
    
    if result['status'] == 'success':
        print(f"\n✅ {result['message']}")
        print(f"分析需求数: {result['analyzed_requirements']}")
        print(f"测试模板数: {result['test_templates']}")
        print(f"功能类型数: {result['feature_types_count']}")
        print(f"关键词数: {result['unique_keywords']}")
        print(f"配置文件: {result['config_file']}")
    else:
        print(f"\n❌ {result['message']}")