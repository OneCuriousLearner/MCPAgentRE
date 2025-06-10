from typing import Any
import json
import asyncio
from mcp.server.fastmcp import FastMCP
from tapd_data_fetcher import get_story_msg, get_bug_msg

# 初始化MCP服务器
mcp = FastMCP("tapd")

@mcp.tool()
async def get_tapd_stories() -> str:
    """获取TAPD平台指定项目的需求数据（支持分页）

    Returns:
        str: 格式化后的需求数据JSON字符串
    """
    try:
        stories = await get_story_msg()
        return json.dumps(stories, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取需求数据失败：{str(e)}"

@mcp.tool()
async def get_tapd_bugs() -> str:
    """获取TAPD平台指定项目的缺陷数据（支持分页）

    Returns:
        str: 格式化后的缺陷数据JSON字符串
    """
    try:
        bugs = await get_bug_msg()
        return json.dumps(bugs, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取缺陷数据失败：{str(e)}"

if __name__ == "__main__":

    import asyncio
    
    print('===== 开始获取需求数据 =====')
    stories = asyncio.run(get_tapd_stories())
    print('===== 开始获取缺陷数据 =====')
    bugs = asyncio.run(get_tapd_bugs())

    # 打印需求数据结果
    print('===== 需求数据获取结果 =====')
    print(stories)
    # 打印缺陷数据结果
    print('===== 缺陷数据获取结果 =====')
    print(bugs)

    # 启动MCP服务器（使用标准输入输出传输）
    mcp.run(transport='stdio')