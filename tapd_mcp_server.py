from typing import Any
import json
import asyncio
from mcp.server.fastmcp import FastMCP
from tapd_data_fetcher import get_story_msg, get_bug_msg    # 从tapd_data_fetcher模块导入获取需求和缺陷数据的函数
from mcp_tools.example_tool import example_function    # 从mcp_tools.example_tool模块导入示例工具函数
from mcp_tools.simple_vectorizer import simple_vectorize_data, simple_search_data, simple_get_db_info    # 导入简化向量化工具

# 初始化MCP服务器
mcp = FastMCP("tapd")

@mcp.tool()
async def example_tool(param1: str, param2: int) -> dict:
    """
    示例工具函数（用于演示MCP工具注册方式）
    
    功能描述:
        - 展示如何创建和注册新的MCP工具
        - 演示参数传递和返回值处理
        
    参数:
        param1 (str): 示例字符串参数，将被转换为大写
        param2 (int): 示例整型参数，将被乘以2
        
    返回:
        dict: 包含处理结果的字典，格式为:
            {
                "processed_str": 处理后的字符串,
                "processed_num": 处理后的数字,
                "combined": 组合后的结果
            }
    """
    return await example_function(param1, param2)

@mcp.tool()
async def get_tapd_stories() -> str:
    """获取TAPD平台指定项目的需求数据（支持分页）
    
    功能描述:
        - 从TAPD API获取指定项目的所有需求数据
        - 支持分页获取大量数据
        - 自动处理API认证和错误
        
    返回数据格式:
        - 每个需求包含ID、标题、状态、优先级、创建/修改时间等字段
        - 数据已按JSON格式序列化，确保AI客户端可直接解析
        
    Returns:
        str: 格式化后的需求数据JSON字符串，包含中文内容
    """
    try:
        stories = await get_story_msg()
        return json.dumps(stories, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取需求数据失败：{str(e)}"

@mcp.tool()
async def get_tapd_bugs() -> str:
    """获取TAPD平台指定项目的缺陷数据（支持分页）
    
    功能描述:
        - 从TAPD API获取指定项目的所有缺陷数据
        - 支持按状态、优先级等条件过滤
        - 自动处理API认证和错误
        
    返回数据格式:
        - 每个缺陷包含ID、标题、严重程度、状态、解决方案等字段
        - 数据已按JSON格式序列化，确保AI客户端可直接解析
        
    Returns:
        str: 格式化后的缺陷数据JSON字符串，包含中文内容
    """
    try:
        bugs = await get_bug_msg()
        return json.dumps(bugs, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取缺陷数据失败：{str(e)}"

@mcp.tool()
async def vectorize_data(chunk_size: int = 10) -> str:
    """向量化TAPD数据以支持大批量数据处理
    
    功能描述:
        - 将获取到的的TAPD数据进行向量化
        - 解决大批量数据处理时tokens超限问题
        - 数据分片处理，提高检索效率
        - 使用SentenceTransformers和FAISS构建向量数据库
        
    参数:
        chunk_size (int): 分片大小，每个分片包含的条目数，默认10条
        
    返回:
        str: 向量化处理结果的JSON字符串
        
    使用场景:
        - 初次设置或数据更新时调用
        - 为后续的智能搜索和相似度匹配做准备
    """
    try:
        result = await simple_vectorize_data(chunk_size=chunk_size)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"向量化失败：{str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def search_data(query: str, top_k: int = 5) -> str:
    """在向量化的TAPD数据中进行智能搜索
    
    功能描述:
        - 基于语义相似度搜索相关的需求和缺陷
        - 支持自然语言查询，无需精确匹配关键词
        - 返回最相关的数据条目，避免处理全量数据
        - 有效解决大批量数据分析的token限制问题
        
    参数:
        query (str): 搜索查询，支持中文自然语言描述
        top_k (int): 返回最相似的K个结果，默认5个
        
    返回:
        str: 搜索结果的JSON字符串，包含相关度分数和数据详情
        
    使用示例:
        - "查找订单相关的需求"
        - "用户评价功能的缺陷"
        - "高优先级的开发任务"
    """
    try:
        result = await simple_search_data(query, top_k)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error", 
            "message": f"搜索失败：{str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool() 
async def get_vector_info() -> str:
    """获取向量数据库状态和统计信息
    
    功能描述:
        - 检查向量数据库是否已建立
        - 获取数据库统计信息（条目数、分片数等）
        - 帮助了解当前数据处理能力
        
    返回:
        str: 数据库信息的JSON字符串
        
    统计信息包括:
        - 总分片数和条目数
        - 需求和缺陷的分片分布
        - 向量维度和存储路径
    """
    try:
        result = await simple_get_db_info()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取信息失败：{str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

if __name__ == "__main__":

    # import asyncio
    
    # print('===== 开始获取需求数据 =====')
    # stories = asyncio.run(get_tapd_stories())
    # print('===== 开始获取缺陷数据 =====')
    # bugs = asyncio.run(get_tapd_bugs())

    # # 打印需求数据结果
    # print('===== 需求数据获取结果 =====')
    # print(stories)
    # # 打印缺陷数据结果
    # print('===== 缺陷数据获取结果 =====')
    # print(bugs)

    # 启动MCP服务器（使用标准输入输出传输）
    mcp.run(transport='stdio')