"""
测试优化后的词频分析器
验证保留的有价值词汇是否能正确参与词频统计
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_tools.word_frequency_analyzer import TAPDWordFrequencyAnalyzer


def test_preserved_keywords():
    """测试保留的关键词是否能正确参与分析"""
    
    # 创建测试数据
    test_data = {
        "stories": [
            {
                "name": "用户登录功能需求",
                "description": "开发用户登录系统，支持多种认证方式，需要解决安全问题",
                "test_focus": "测试登录流程的完整性",
                "label": "功能开发"
            },
            {
                "name": "API接口优化",
                "description": "对现有API接口进行性能优化，修复已知缺陷",
                "test_focus": "测试接口响应时间",
                "label": "性能优化"
            }
        ],
        "bugs": [
            {
                "name": "系统异常Bug修复",
                "description": "修复系统在特定条件下出现的异常错误",
                "test_focus": "验证异常场景不再出现",
                "label": "bug修复"
            },
            {
                "name": "业务流程问题",
                "description": "用户反馈业务流程中存在逻辑错误，需要产品和开发协作解决",
                "test_focus": "测试业务流程完整性",
                "label": "流程优化"
            }
        ]
    }
    
    # 保存测试数据
    test_data_path = project_root / "local_data" / "test_word_frequency.json"
    test_data_path.parent.mkdir(exist_ok=True)
    
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # 初始化分析器
    analyzer = TAPDWordFrequencyAnalyzer(str(test_data_path))
    
    # 执行词频分析
    result = analyzer.analyze_word_frequency(min_frequency=1, use_extended_fields=True)
    
    print("=== 词频分析结果 ===")
    print(f"状态: {result['status']}")
    
    if result['status'] == 'success':
        # 检查保留的关键词
        preserved_keywords = [
            '问题', '解决', '修复', 'bug', 'Bug', 'BUG', '缺陷', '错误', '异常', '故障',
            '需求', '功能', '特性', '模块', '系统', '平台', '服务', '接口', 'api', 'API',
            '用户', '客户', '管理员', '开发', '测试', '运维', '产品', '业务', '流程', '步骤'
        ]
        
        found_keywords = result['word_frequency']['high_frequency_words']
        
        print(f"\n总词汇数: {result['statistics']['total_words']}")
        print(f"唯一词汇数: {result['statistics']['unique_words']}")
        print(f"高频词汇数: {result['statistics']['high_frequency_words']}")
        
        print(f"\n=== 发现的高频词汇 ===")
        for word, freq in found_keywords.items():
            print(f"{word}: {freq}")
        
        print(f"\n=== 保留的关键词检查 ===")
        preserved_found = []
        for keyword in preserved_keywords:
            if keyword in found_keywords:
                preserved_found.append((keyword, found_keywords[keyword]))
                print(f"✓ {keyword}: {found_keywords[keyword]}")
        
        print(f"\n=== 关键词分类 ===")
        categories = result['search_suggestions']['category_keywords']
        for category, words in categories.items():
            print(f"{category}: {', '.join(words)}")
        
        print(f"\n=== 搜索建议关键词 ===")
        recommended = result['search_suggestions']['recommended_keywords']
        print(f"推荐关键词: {', '.join(recommended[:10])}")
        
        # 验证重要关键词是否被保留
        important_keywords_found = len(preserved_found)
        print(f"\n=== 验证结果 ===")
        print(f"应保留的关键词数量: {len(preserved_keywords)}")
        print(f"实际发现的关键词数量: {important_keywords_found}")
        print(f"保留率: {important_keywords_found/len(preserved_keywords)*100:.1f}%")
        
        if important_keywords_found > 0:
            print("✓ 词频分析器成功保留了有价值的关键词")
        else:
            print("✗ 需要进一步优化停用词列表")
    
    else:
        print(f"分析失败: {result['message']}")
    
    # 清理测试文件
    if test_data_path.exists():
        test_data_path.unlink()


if __name__ == "__main__":
    test_preserved_keywords()
