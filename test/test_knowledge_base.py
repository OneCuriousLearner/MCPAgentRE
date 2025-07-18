"""
测试历史需求知识库功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.knowledge_base import enhance_tapd_data_with_knowledge
from mcp_tools.common_utils import get_config, get_file_manager


def test_knowledge_base():
    """测试知识库功能"""
    print("测试历史需求知识库功能")
    
    config = get_config()
    file_manager = get_file_manager()
    
    # 检查TAPD数据文件是否存在
    tapd_file = config.local_data_path / "msg_from_fetcher.json"
    if not tapd_file.exists():
        print(f"ERROR: TAPD数据文件不存在: {tapd_file}")
        print("请先运行 uv run tapd_data_fetcher.py 获取数据")
        return
    
    # 检查测试用例文件
    testcase_file = config.local_data_path / "TestCase_20250717141033-32202633.xlsx"
    if not testcase_file.exists():
        print(f"WARNING: 测试用例文件不存在: {testcase_file}")
        testcase_file = None
    else:
        print(f"SUCCESS: 找到测试用例文件: {testcase_file}")
    
    # 测试数据增强
    print("\n开始测试数据增强功能...")
    result = enhance_tapd_data_with_knowledge(
        tapd_file=str(tapd_file),
        testcase_file=str(testcase_file) if testcase_file else None
    )
    
    print(f"数据增强结果: {result}")
    
    # 验证增强后的数据
    if result.get("status") == "success":
        print("\n验证增强后的数据...")
        enhanced_data = file_manager.load_tapd_data(str(tapd_file))
        
        if 'knowledge_base_meta' in enhanced_data:
            meta = enhanced_data['knowledge_base_meta']
            print(f"知识库元数据: {meta}")
        
        # 检查第一个需求的增强信息
        stories = enhanced_data.get('stories', [])
        if stories and 'kb_info' in stories[0]:
            kb_info = stories[0]['kb_info']
            print(f"第一个需求的知识库信息: {kb_info}")
        
        print("\n知识库功能测试完成！")
        print("现在可以使用 search_data() 工具搜索需求，结果将包含测试用例建议")
    else:
        print(f"ERROR: 数据增强失败: {result}")


if __name__ == "__main__":
    test_knowledge_base()