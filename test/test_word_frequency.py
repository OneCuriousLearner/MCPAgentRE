"""
词频分析工具测试脚本
"""

import sys
import os
import asyncio
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.word_frequency_analyzer import analyze_tapd_word_frequency


async def test_word_frequency_analyzer():
    """测试词频分析工具"""
    
    print("=== TAPD词频分析工具测试 ===\n")
    
    # 检查数据文件是否存在
    data_file = "local_data/msg_from_fetcher.json"
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        print("💡 请先运行 get_tapd_data 工具获取TAPD数据")
        return
    
    try:
        # 测试基础功能
        print("🔍 测试基础词频分析...")
        result = await analyze_tapd_word_frequency(
            min_frequency=3,
            use_extended_fields=True
        )
        
        if result.get("status") == "success":
            print("✅ 基础词频分析成功!")
            
            # 显示统计信息
            stats = result.get("statistics", {})
            print(f"📊 数据统计:")
            print(f"   - 总词数: {stats.get('total_words', 0)}")
            print(f"   - 唯一词数: {stats.get('unique_words', 0)}")
            print(f"   - 高频词数: {stats.get('high_frequency_words', 0)}")
            print(f"   - 需求数量: {stats.get('stories_count', 0)}")
            print(f"   - 缺陷数量: {stats.get('bugs_count', 0)}")
            
            # 显示前10个高频词
            word_freq = result.get("word_frequency", {})
            top_words = word_freq.get("top_20_words", {})
            if top_words:
                print(f"\n🎯 前10个高频关键词:")
                for i, (word, freq) in enumerate(list(top_words.items())[:10], 1):
                    print(f"   {i:2d}. {word}: {freq}次")
            
            # 显示搜索建议
            suggestions = result.get("search_suggestions", {})
            keywords = suggestions.get("recommended_keywords", [])
            if keywords:
                print(f"\n💡 推荐搜索关键词:")
                print(f"   {', '.join(keywords[:10])}")
            
            # 显示分类关键词
            categories = suggestions.get("category_keywords", {})
            if categories:
                print(f"\n📂 分类关键词:")
                for category, words in categories.items():
                    if words:
                        print(f"   {category}: {', '.join(words[:5])}")
            
        else:
            print(f"❌ 基础词频分析失败: {result.get('message', 'Unknown error')}")
            return
        
        # 测试不同参数
        print(f"\n🔍 测试高阈值词频分析...")
        result_high = await analyze_tapd_word_frequency(
            min_frequency=10,
            use_extended_fields=False
        )
        
        if result_high.get("status") == "success":
            print("✅ 高阈值词频分析成功!")
            stats_high = result_high.get("statistics", {})
            print(f"📊 高阈值统计 (仅核心字段):")
            print(f"   - 高频词数: {stats_high.get('high_frequency_words', 0)}")
        else:
            print(f"❌ 高阈值词频分析失败: {result_high.get('message', 'Unknown error')}")
        
        print(f"\n🎉 词频分析工具测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_word_frequency_analyzer())
