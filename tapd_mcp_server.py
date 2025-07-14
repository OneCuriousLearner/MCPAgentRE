from typing import Any, Optional
import json
import asyncio
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from tapd_data_fetcher import get_story_msg, get_bug_msg    # 从tapd_data_fetcher模块导入获取需求和缺陷数据的函数
from mcp_tools.example_tool import example_function    # 从mcp_tools.example_tool模块导入示例工具函数
from mcp_tools.simple_vectorizer import simple_vectorize_data, simple_search_data as _simple_search_data, simple_get_db_info    # 导入简化向量化工具
from mcp_tools.data_vectorizer import vectorize_tapd_data, search_tapd_data, get_vector_db_info    # 导入完整向量化工具
from mcp_tools.fake_tapd_gen import generate as fake_generate    # 导入TAPD数据生成器
from mcp_tools.context_optimizer import build_overview    # 导入上下文优化器

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
async def get_tapd_data() -> str:
    """从TAPD API获取需求和缺陷数据并保存到本地文件
    
    功能描述:
        - 从TAPD API获取完整的需求和缺陷数据
        - 将数据保存到本地文件 local_data/msg_from_fetcher.json
        - 返回获取到的需求和缺陷数量统计
        - 为后续的本地数据分析提供数据基础
        
    数据保存格式:
        {
            "stories": [...],  // 需求数据数组
            "bugs": [...]      // 缺陷数据数组
        }
        
    返回:
        str: 包含数据获取结果和统计信息的JSON字符串
        
    使用场景:
        - 初次设置时获取最新数据
        - 定期更新本地数据缓存
        - 为离线分析准备数据
    """
    try:
        print('===== 开始获取需求数据 =====')
        stories_data = await get_story_msg()
        
        print('===== 开始获取缺陷数据 =====')
        bugs_data = await get_bug_msg()
        
        # 准备要保存的数据
        data_to_save = {
            'stories': stories_data,
            'bugs': bugs_data
        }
        
        # 确保目录存在并保存数据
        os.makedirs('local_data', exist_ok=True)
        with open(os.path.join('local_data', 'msg_from_fetcher.json'), 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        
        # 返回统计结果
        result = {
            "status": "success",
            "message": "数据已成功保存至local_data/msg_from_fetcher.json文件",
            "statistics": {
                "stories_count": len(stories_data),
                "bugs_count": len(bugs_data),
                "total_count": len(stories_data) + len(bugs_data)
            },
            "file_path": "local_data/msg_from_fetcher.json"
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取和保存TAPD数据失败：{str(e)}",
            "suggestion": "请检查API密钥配置和网络连接"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_tapd_stories() -> str:
    """获取TAPD平台指定项目的需求数据（支持分页）
    
    功能描述:
        - 从TAPD API获取指定项目的所有需求数据
        - 支持分页获取大量数据
        - 自动处理API认证和错误
        - 数据不保存至本地，建议仅在数据量较小时使用
        
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
        - 数据不保存至本地，建议仅在数据量较小时使用
        
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
            - 推荐值：10-20（平衡精度与效率）
            - 较小值：搜索更精准，但分片更多
            - 较大值：减少分片数量，但可能降低搜索精度
        
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

@mcp.tool()
async def simple_search_data(query: str, top_k: int = 5) -> str:
    """在向量化的TAPD数据中进行智能搜索
    
    功能描述:
        - 简化的TAPD向量化工具，优化性能，减少重复加载
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
        result = await _simple_search_data(query, top_k)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error", 
            "message": f"搜索失败：{str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def advanced_vectorize_data(data_file_path: Optional[str] = None, chunk_size: int = 10) -> str:
    """高级向量化TAPD数据（完整版）
    
    功能描述:
        - 完整版TAPD数据向量化工具，提供详细的配置和管理功能
        - 面向对象设计，支持灵活的参数配置和详细的元数据管理
        - 提取更丰富的字段信息，包括工作量、进度、回归次数等
        - 自动保存详细的配置文件和统计信息
        - 适用于生产环境和需要详细数据追溯的场景
        
    参数:
        data_file_path (str): 数据文件路径，默认为 local_data/msg_from_fetcher.json
        chunk_size (int): 分片大小，每个分片包含的条目数，默认10条
            - 推荐值：10-20（平衡精度与效率）
            - 较小值：搜索更精准，但分片更多
            - 较大值：减少分片数量，但可能降低搜索精度
        
    返回:
        str: 向量化处理结果的JSON字符串，包含详细统计信息
        
    与简化版的区别:
        - 提供更详细的元数据管理和配置保存
        - 支持更丰富的字段提取和处理
        - 更适合生产环境和复杂场景使用
    """
    try:
        result = await vectorize_tapd_data(data_file_path, chunk_size)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"高级向量化失败：{str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def advanced_search_data(query: str, top_k: int = 5) -> str:
    """在向量化的TAPD数据中进行高级智能搜索（完整版）
    
    功能描述:
        - 完整版TAPD向量化搜索工具，提供更详细的搜索结果
        - 基于语义相似度搜索相关的需求和缺陷
        - 支持自然语言查询，返回详细的元数据信息
        - 包含更丰富的条目信息和相关性分析
        - 适用于需要详细分析和数据追溯的场景
        
    参数:
        query (str): 搜索查询，支持中文自然语言描述
        top_k (int): 返回最相似的K个结果，默认5个
        
    返回:
        str: 搜索结果的JSON字符串，包含详细的相关度分数和完整数据详情
        
    与简化版的区别:
        - 返回更详细的元数据信息
        - 包含完整的原始数据条目
        - 提供更丰富的分析维度
        
    使用示例:
        - "查找订单相关的需求"
        - "用户评价功能的缺陷"
        - "高优先级的开发任务"
    """
    try:
        result = await search_tapd_data(query, top_k)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error", 
            "message": f"高级搜索失败：{str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool() 
async def advanced_get_vector_info() -> str:
    """获取高级向量数据库状态和详细统计信息（完整版）
    
    功能描述:
        - 完整版向量数据库信息查询工具
        - 获取详细的数据库配置和统计信息
        - 包含模型信息、创建时间等详细元数据
        - 提供完整的数据库健康状态检查
        - 适用于生产环境监控和详细分析
        
    返回:
        str: 详细数据库信息的JSON字符串
        
    与简化版的区别:
        - 提供更详细的配置信息
        - 包含模型版本和创建时间
        - 支持更全面的状态检查
        
    统计信息包括:
        - 总分片数和条目数
        - 需求和缺陷的分片分布
        - 向量维度和存储路径
        - 模型名称和创建时间
        - 详细的配置参数
    """
    try:
        result = await get_vector_db_info()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取高级向量信息失败：{str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def generate_fake_tapd_data(
    n_story_A: int = 300, 
    n_story_B: int = 200,
    n_bug_A: int = 400, 
    n_bug_B: int = 300,
    output_path: str = "local_data/fake_tapd.json"
) -> str:
    """生成模拟的TAPD需求和缺陷数据
    
    功能描述:
        - 使用Faker库生成中文模拟数据，用于测试和开发
        - 创建两种类型的需求：算法策略类和功能决策类需求
        - 创建两种类型的缺陷：简单缺陷和包含详细复现步骤的缺陷
        - 自动添加优先级、状态、创建时间、负责人、标签等公共字段
        - 生成的数据格式与真实TAPD数据保持一致
        
    参数:
        n_story_A (int): 算法策略类需求数量，默认300条
        n_story_B (int): 功能决策类需求数量，默认200条
        n_bug_A (int): 简单缺陷数量，默认400条
        n_bug_B (int): 详细缺陷数量，默认300条
        output_path (str): 输出文件路径，默认为 local_data/fake_tapd.json
        
    返回:
        str: 生成结果的JSON字符串，包含生成的数据统计信息
        
    使用场景:
        - 开发和测试阶段生成测试数据
        - 验证向量化和搜索功能
        - 演示和培训场景
    """
    try:
        import os
        # 确保目标目录存在
        dir_path = os.path.dirname(output_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 调用生成函数
        fake_generate(n_story_A, n_story_B, n_bug_A, n_bug_B, output_path)
        
        total_items = n_story_A + n_story_B + n_bug_A + n_bug_B
        result = {
            "status": "success", 
            "message": f"Successfully generated {total_items} TAPD items",
            "details": {
                "story_type_A": n_story_A,
                "story_type_B": n_story_B, 
                "bug_type_A": n_bug_A,
                "bug_type_B": n_bug_B,
                "total": total_items,
                "output_file": output_path
            }
        }
        # 使用ASCII安全模式返回结果，避免编码问题
        return json.dumps(result, ensure_ascii=True, indent=2)
    except UnicodeEncodeError as e:
        error_result = {
            "status": "error",
            "message": f"Encoding error during data generation: {str(e)}",
            "suggestion": "Try using ASCII-safe file paths and avoid special characters"
        }
        return json.dumps(error_result, ensure_ascii=True, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Failed to generate fake data: {str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=True, indent=2)

@mcp.tool()
async def generate_tapd_overview(
    since: str = "2025-01-01",
    until: str = datetime.now().strftime("%Y-%m-%d"),
    max_total_tokens: int = 6000,
    model: str = "deepseek-reasoner",
    endpoint: str = "https://api.deepseek.com/v1",
    use_local_data: bool = True
) -> str:
    """生成TAPD数据的智能概览和摘要
    
    功能描述:
        - 使用上下文优化器处理大型TAPD数据集
        - 基于token数量自动分块数据，避免token超限问题
        - 集成在线LLM API（DeepSeek/Qwen/OpenAI兼容）进行智能摘要
        - 递归摘要生成，将多个数据块的摘要合并为总体概览
        - 支持时间范围过滤，获取指定期间的数据摘要
        
    参数:
        since (str): 开始时间，格式为 YYYY-MM-DD，默认 "2025-01-01"
        until (str): 结束时间，格式为 YYYY-MM-DD，默认为当前系统日期
        max_total_tokens (int): 最大token数量，默认6000
        model (str): LLM模型名称，默认 "deepseek-reasoner"
        endpoint (str): API端点URL，默认DeepSeek API
        use_local_data (bool): 是否使用本地数据，默认True（使用本地文件），False时从TAPD API获取最新数据
        
    返回:
        str: 概览结果的JSON字符串，包含数据统计和智能摘要
        
    注意事项:
        - 需要配置环境变量 DS_KEY（DeepSeek API密钥）
        - 首次使用时需要确保网络连接正常，用于调用在线LLM
        - 处理大量数据时可能需要较长时间
        
    使用场景:
        - 生成项目质量分析报告
        - 快速了解项目整体情况
        - 为管理层提供数据概览
    """
    try:
        # 导入必要的函数
        from tapd_data_fetcher import get_story_msg, get_bug_msg, get_local_story_msg, get_local_bug_msg
        
        # 根据参数选择数据源
        if use_local_data:
            print("使用本地数据文件进行分析...")
            get_story_func = get_local_story_msg
            get_bug_func = get_local_bug_msg
        else:
            print("从TAPD API获取最新数据进行分析...")
            get_story_func = get_story_msg
            get_bug_func = get_bug_msg
        
        # 包装获取函数以适配context_optimizer的接口
        async def fetch_story(**params):
            # 这里需要适配分页参数，暂时返回所有数据
            stories = await get_story_func()
            # 简单的分页模拟
            page = params.get('page', 1)
            limit = params.get('limit', 200)
            start = (page - 1) * limit
            end = start + limit
            return stories[start:end] if len(stories) > start else []
            
        async def fetch_bug(**params):
            # 这里需要适配分页参数，暂时返回所有数据
            bugs = await get_bug_func()
            # 简单的分页模拟
            page = params.get('page', 1)
            limit = params.get('limit', 200)
            start = (page - 1) * limit
            end = start + limit
            return bugs[start:end] if len(bugs) > start else []
        
        # 调用上下文优化器
        overview = await build_overview(
            fetch_story=fetch_story,
            fetch_bug=fetch_bug,
            since=since,
            until=until,
            max_total_tokens=max_total_tokens,
            model=model,
            endpoint=endpoint
        )
        
        # 检查摘要是否包含错误信息
        summary_text = overview.get("summary_text", "")
        if "无法生成智能摘要" in summary_text or "API配置错误" in summary_text:
            # 如果摘要包含错误信息，返回错误状态
            error_result = {
                "status": "error",
                "message": "智能摘要生成失败",
                "details": summary_text,
                "suggestion": "请设置环境变量 DS_KEY 为您的DeepSeek API密钥",
                "time_range": f"{since} 至 {until}",
                "total_stories": overview.get("total_stories", 0),
                "total_bugs": overview.get("total_bugs", 0),
                "chunks": overview.get("chunks", 0)
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)
        
        result = {
            "status": "success",
            "time_range": f"{since} 至 {until}",
            **overview
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"生成概览失败：{str(e)}",
            "suggestion": "请检查API密钥配置和网络连接"
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