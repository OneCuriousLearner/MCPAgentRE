#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用 Token 计算器

用法：直接运行本文件。用户可修改顶部的 need_count_token 多行字符串作为输入，程序会输出对应的 token 数。
建议使用：uv run test\test_token_counter.py
"""

import os
import sys

# 将项目根目录加入 sys.path，便于导入公共工具
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.common_utils import get_token_counter

# ---------------- 用户可编辑区：修改下方多行字符串来测试 ----------------
need_count_token = """
这里是示例文本。
You can replace this block with any text you want to count tokens for.
中文与 English 混排、数字123 和标点符号也会影响 token 估算。
"""
# ----------------------------------------------------------------------


def main():
    tc = get_token_counter()  # 自动优先使用 DeepSeek tokenizer，失败则回退到估算模式
    text = need_count_token or ""
    tokens = tc.count_tokens(text)

    # 终端输出
    print("=== Token 统计结果 ===")
    print(f"字符数: {len(text)}")
    print(f"Token 数: {tokens}")


if __name__ == "__main__":
    print(
r'''
 ______   ______     __  __     ______     __   __    
/\__  _\ /\  __ \   /\ \/ /    /\  ___\   /\ "-.\ \   
\/_/\ \/ \ \ \/\ \  \ \  _"-.  \ \  __\   \ \ \-.  \  
   \ \_\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_\\"\_\ 
    \/_/   \/_____/   \/_/\/_/   \/_____/   \/_/ \/_/ 
 ______     ______     __  __     __   __     ______   ______     ______    
/\  ___\   /\  __ \   /\ \/\ \   /\ "-.\ \   /\__  _\ /\  ___\   /\  == \   
\ \ \____  \ \ \/\ \  \ \ \_\ \  \ \ \-.  \  \/_/\ \/ \ \  __\   \ \  __<   
 \ \_____\  \ \_____\  \ \_____\  \ \_\\"\_\    \ \_\  \ \_____\  \ \_\ \_\ 
  \/_____/   \/_____/   \/_____/   \/_/ \/_/     \/_/   \/_____/   \/_/ /_/ 
''')
    main()
