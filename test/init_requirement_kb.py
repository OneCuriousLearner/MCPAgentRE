"""
初始化需求单知识库配置文件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.test_case_require_list_knowledge_base import RequirementKnowledgeBase

def main():
    """初始化需求单知识库配置文件"""
    print("=== 初始化需求单知识库配置文件 ===")
    
    # 创建需求单知识库管理器（这会自动创建配置文件）
    kb = RequirementKnowledgeBase()
    
    # 检查是否成功创建
    config_file = kb.config_file
    print(f"配置文件路径：{config_file}")
    
    # 保存一个空配置（如果不存在）
    kb._save_requirements()
    
    if config_file.exists():
        print(f"配置文件已创建：{config_file}")
        print(f"当前包含 {len(kb.requirements)} 个需求单")
    else:
        print(f"配置文件创建失败：{config_file}")
    
    print("=== 初始化完成 ===")

if __name__ == "__main__":
    main()
