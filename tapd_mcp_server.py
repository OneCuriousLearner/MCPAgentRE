from typing import Any, Optional
import json
import asyncio
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from tapd_data_fetcher import get_story_msg, get_bug_msg    # 从tapd_data_fetcher模块导入获取需求和缺陷数据的函数
from mcp_tools.example_tool import example_function    # 从mcp_tools.example_tool模块导入示例工具函数
from mcp_tools.data_vectorizer import vectorize_tapd_data, search_tapd_data, get_vector_db_info    # 导入优化后的向量化工具
from mcp_tools.fake_tapd_gen import generate as fake_generate    # 导入TAPD数据生成器
from mcp_tools.context_optimizer import build_overview    # 导入上下文优化器
from mcp_tools.docx_summarizer import summarize_docx as _summarize_docx
from mcp_tools.word_frequency_analyzer import analyze_tapd_word_frequency    # 导入词频分析器
from mcp_tools.data_preprocessor import preprocess_description_field, preview_description_cleaning    # 导入数据预处理工具

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
async def vectorize_data(data_file_path: Optional[str] = None, chunk_size: int = 10) -> str:
    """向量化TAPD数据以支持大批量数据处理
    
    功能描述:
        - 将获取到的的TAPD数据进行向量化
        - 解决大批量数据处理时tokens超限问题
        - 数据分片处理，提高检索效率
        - 使用SentenceTransformers和FAISS构建向量数据库
        
    参数:
        data_file_path (str): 数据文件路径，默认为 local_data/msg_from_fetcher.json
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
        result = await vectorize_tapd_data(data_file_path, chunk_size)
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
        result = await get_vector_db_info()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取信息失败：{str(e)}"
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
        result = await search_tapd_data(query, top_k)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error", 
            "message": f"搜索失败：{str(e)}"
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
    model: str = "deepseek-chat",
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
        model (str): LLM模型名称，默认 "deepseek-chat"（若需要更高质量，可使用 "deepseek-reasoner"，但响应时间可能较长）
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
        from tapd_data_fetcher import (
            get_story_msg, get_bug_msg, 
            get_local_story_msg_filtered, get_local_bug_msg_filtered,
            get_story_msg_filtered, get_bug_msg_filtered
        )
        
        # 根据参数选择数据源并直接获取筛选后的数据
        if use_local_data:
            print(f"[本地数据] 使用本地数据文件进行分析，时间范围：{since} 到 {until}")
            stories_data = await get_local_story_msg_filtered(since, until)
            bugs_data = await get_local_bug_msg_filtered(since, until)
        else:
            print(f"[API数据] 从TAPD API获取最新数据进行分析，时间范围：{since} 到 {until}")
            stories_data = await get_story_msg_filtered(since, until)
            bugs_data = await get_bug_msg_filtered(since, until)
        
        print(f"[数据加载] 数据加载完成：{len(stories_data)} 条需求，{len(bugs_data)} 条缺陷")
        
        # 包装获取函数以适配context_optimizer的接口
        async def fetch_story(**params):
            # 直接返回已筛选的数据，无需分页处理
            return stories_data
            
        async def fetch_bug(**params):
            # 直接返回已筛选的数据，无需分页处理
            return bugs_data
        
        print(f"[AI分析] 开始调用AI生成智能概览分析（模型：{model}）...")
        print("[处理中] 正在处理数据并生成质量分析报告，预计需要10-20秒...")
        
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
        
        print("[分析完成] AI分析完成，正在整理输出结果...")
        
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

@mcp.tool()
async def summarize_docx(docx_path: str, max_paragraphs: int = 5) -> str:
    """
    读取 docx 文档，返回所有段落内容和摘要的 JSON 数据
    
    参数：
        docx_path (str): .docx 文件路径
        max_paragraphs (int): 摘要最多包含的段落数，默认5
    返回：
        str: JSON 字符串，包含所有段落和摘要
    """
    # 兼容 async 调用
    import asyncio
    loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
    return await loop.run_in_executor(None, _summarize_docx, docx_path, max_paragraphs)

@mcp.tool()
async def analyze_word_frequency(
    min_frequency: int = 3,
    use_extended_fields: bool = True,
    data_file_path: str = "local_data/msg_from_fetcher.json"
) -> str:
    """
    分析TAPD数据的词频分布，生成关键词词云统计
    
    功能描述:
        - 从TAPD数据中提取关键词并统计词频
        - 支持中文分词和停用词过滤
        - 为搜索功能提供准确的关键词建议
        - 生成词频分布统计和分类关键词
        
    参数:
        min_frequency (int): 最小词频阈值，默认3
            - 只返回出现次数 >= min_frequency 的词汇
            - 推荐值: 3-10（根据数据量调整）
        use_extended_fields (bool): 是否使用扩展字段，默认True
            - True: 分析 name, description, test_focus, label, acceptance, comment, status, priority, iteration_id
            - False: 仅分析 name, description, test_focus, label
        data_file_path (str): 数据文件路径，默认为 local_data/msg_from_fetcher.json
            - 支持自定义数据源路径
            
    返回:
        str: 词频分析结果的JSON字符串，包含:
            - 高频词统计
            - 频次分布
            - 搜索关键词建议
            - 分类关键词推荐
            
    使用场景:
        - 为 search_data 提供精准搜索关键词
        - 生成项目词云可视化数据
        - 了解项目重点关注领域和常见问题
        - 优化搜索查询的准确性
        
    注意事项:
        - 首次使用前请确保已调用 get_tapd_data 获取数据
        - 中文分词基于jieba库，适合中文项目分析
        - 自动过滤常见停用词，专注于有意义的关键词
    """
    try:
        result = await analyze_tapd_word_frequency(
            min_frequency=min_frequency,
            use_extended_fields=use_extended_fields,
            data_file_path=data_file_path
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"词频分析失败：{str(e)}",
            "suggestion": "请检查数据文件是否存在，建议先调用 get_tapd_data 工具获取数据"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def preprocess_tapd_description(
    data_file_path: str = "local_data/msg_from_fetcher.json",
    output_file_path: str = "local_data/preprocessed_data.json",
    use_api: bool = True,
    process_documents: bool = False,
    process_images: bool = False
) -> str:
    """
    预处理TAPD数据的description字段，清理HTML样式并使用AI优化内容
    
    功能描述:
        - 清理description字段中的HTML样式信息（margin、padding、color等无用属性）
        - 保留有意义的文字内容、超链接和图片地址
        - 使用DeepSeek API对内容进行准确复述，压缩冗余信息
        - 提取腾讯文档链接和图片路径信息
        - 为未来的文档内容提取和OCR识别预留接口
        
    参数:
        data_file_path (str): 输入数据文件路径，默认"local_data/msg_from_fetcher.json"
        output_file_path (str): 输出文件路径，默认"local_data/preprocessed_data.json"
        use_api (bool): 是否使用DeepSeek API进行内容复述，默认True
        process_documents (bool): 是否处理腾讯文档链接（预留功能），默认False
        process_images (bool): 是否处理图片内容（预留功能），默认False
        
    返回:
        str: 处理结果的JSON字符串，包含统计信息
        
    处理效果:
        - 原始HTML长度通常可压缩60-80%
        - 保留所有关键业务信息和技术细节
        - 提升后续向量化和搜索的准确性
        - 减少token消耗，提高AI处理效率
        
    使用场景:
        - 获取TAPD数据后的第一步预处理
        - 为词频分析和向量化准备清洁数据
        - 优化AI分析和报告生成的输入质量
        
    注意事项:
        - 需要设置DS_KEY环境变量（DeepSeek API密钥）
        - 建议先使用preview_description_cleaning预览效果
        - 处理大量数据时可能需要较长时间
    """
    try:
        result = await preprocess_description_field(
            data_file_path=data_file_path,
            output_file_path=output_file_path,
            use_api=use_api,
            process_documents=process_documents,
            process_images=process_images
        )
        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"数据预处理失败：{str(e)}",
            "suggestion": "请检查数据文件是否存在，API密钥是否正确配置"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
def preview_tapd_description_cleaning(
    data_file_path: str = "local_data/msg_from_fetcher.json",
    item_count: int = 3
) -> str:
    """
    预览TAPD数据description字段清理效果，不实际修改数据
    
    功能描述:
        - 展示HTML样式清理前后的对比效果
        - 统计压缩比例和提取的链接、图片信息
        - 帮助用户了解预处理效果和决定参数设置
        - 不调用API，仅展示样式清理效果
        
    参数:
        data_file_path (str): 数据文件路径，默认"local_data/msg_from_fetcher.json"
        item_count (int): 预览的条目数量，默认3条
        
    返回:
        str: 预览结果的JSON字符串
        
    预览信息包括:
        - 原始内容和清理后内容的长度对比
        - 内容预览（前200字符）
        - 提取的文档链接和图片路径列表
        - 每个条目的基本信息（ID、标题等）
        
    使用场景:
        - 在正式预处理前评估效果
        - 调试和优化清理规则
        - 了解数据质量和复杂度
        
    注意事项:
        - 此工具不会修改原始数据
        - 不需要API密钥，可安全使用
        - 建议在大批量处理前先预览
    """
    try:
        result = preview_description_cleaning(
            data_file_path=data_file_path,
            item_count=item_count
        )
        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"预览失败：{str(e)}",
            "suggestion": "请检查数据文件是否存在"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

if __name__ == "__main__":

    # 启动MCP服务器（使用标准输入输出传输）
    mcp.run(transport='stdio')