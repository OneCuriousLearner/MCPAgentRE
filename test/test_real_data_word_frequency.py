"""
使用实际TAPD数据测试优化后的词频分析器
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_tools.word_frequency_analyzer import TAPDWordFrequencyAnalyzer


def test_real_tapd_data():
    """使用实际TAPD数据测试词频分析器"""
    
    # 使用实际数据测试
    analyzer = TAPDWordFrequencyAnalyzer()
    result = analyzer.analyze_word_frequency(min_frequency=2, use_extended_fields=True)

    print('=== 实际TAPD数据词频分析结果 ===')
    print(f'状态: {result["status"]}')

    if result['status'] == 'success':
        stats = result['statistics']
        print(f'数据项总数: {stats["total_items"]} (需求: {stats["stories_count"]}, 缺陷: {stats["bugs_count"]})')
        print(f'总词汇数: {stats["total_words"]}')
        print(f'唯一词汇数: {stats["unique_words"]}')
        print(f'高频词汇数 (≥2次): {stats["high_frequency_words"]}')
        
        print('\n=== 前20个高频词汇 ===')
        top_words = result['word_frequency']['top_20_words']
        for i, (word, freq) in enumerate(top_words.items(), 1):
            print(f'{i:2d}. {word}: {freq}次')
        
        print('\n=== 关键词分类 ===')
        categories = result['search_suggestions']['category_keywords']
        for category, words in categories.items():
            print(f'{category}: {len(words)}个词汇')
            if words:
                print(f'  示例: {" ".join(words[:5])}')
        
        print('\n=== 搜索建议关键词 ===')
        recommended = result['search_suggestions']['recommended_keywords']
        print(f'推荐关键词: {", ".join(recommended[:10])}')
        
        # 检查保留的重要词汇
        important_keywords = [
            '问题', '解决', '修复', 'bug', 'Bug', 'BUG', '缺陷', '错误', '异常', '故障',
            '需求', '功能', '特性', '模块', '系统', '平台', '服务', '接口', 'api', 'API',
            '用户', '客户', '管理员', '开发', '测试', '运维', '产品', '业务', '流程', '步骤'
        ]
        
        found_keywords = result['word_frequency']['high_frequency_words']
        preserved_count = sum(1 for keyword in important_keywords if keyword in found_keywords)
        
        print(f'\n=== 关键词保留验证 ===')
        print(f'预期保留的重要词汇: {len(important_keywords)}个')
        print(f'实际发现的重要词汇: {preserved_count}个')
        print(f'保留率: {preserved_count/len(important_keywords)*100:.1f}%')
        
        preserved_words = [(keyword, found_keywords[keyword]) for keyword in important_keywords if keyword in found_keywords]
        preserved_words.sort(key=lambda x: x[1], reverse=True)
        
        print('\n实际保留的重要词汇:')
        for keyword, freq in preserved_words:
            print(f'  {keyword}: {freq}次')
    
    else:
        print(f'分析失败: {result["message"]}')


if __name__ == "__main__":
    test_real_tapd_data()
