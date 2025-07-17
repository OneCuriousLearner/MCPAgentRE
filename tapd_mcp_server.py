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
from mcp_tools.scoring_config_manager import get_config_manager    # 导入配置管理器
from mcp_tools.testcase_quality_scorer import get_quality_scorer    # 导入质量评分器

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

@mcp.tool()
async def get_scoring_config() -> str:
    """
    获取当前的测试用例质量评分配置
    
    功能描述:
        - 返回当前评分规则配置的详细信息
        - 包括各项评分权重、阈值和评分范围
        - 用于了解当前的评分标准
        
    返回:
        str: 配置信息的JSON字符串
        
    配置信息包括:
        - 标题长度限制和权重
        - 前置条件数量限制和权重
        - 测试步骤要求和权重
        - 预期结果要求和权重
        - 优先级设置和权重
        - 创建和更新时间
        
    使用场景:
        - 查看当前评分标准
        - 配置调整前的参考
        - 评分结果分析和解释
    """
    try:
        config_manager = await get_config_manager()
        config = await config_manager.load_config()
        
        result = {
            "status": "success",
            "config": config_manager._config_to_dict(config),
            "summary": await config_manager.get_config_summary()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取配置失败：{str(e)}",
            "suggestion": "请检查配置文件是否正确"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def configure_scoring_rules(
    rule_name: str,
    rule_config: str,
    validate_only: bool = False
) -> str:
    """
    配置测试用例质量评分规则
    
    功能描述:
        - 支持自定义各项评分规则的参数
        - 可以单独配置标题、前置条件、测试步骤、预期结果、优先级规则
        - 提供配置验证功能
        - 支持权重调整和阈值设置
        
    参数:
        rule_name (str): 规则名称，可选值：
            - "title": 标题评分规则
            - "precondition": 前置条件评分规则
            - "steps": 测试步骤评分规则
            - "expected_result": 预期结果评分规则
            - "priority": 优先级评分规则
        rule_config (str): 规则配置的JSON字符串
        validate_only (bool): 是否仅验证配置，不保存，默认False
        
    返回:
        str: 配置结果的JSON字符串
        
    配置示例:
        标题规则: {"max_length": 50, "min_length": 5, "weight": 0.25}
        前置条件: {"max_count": 3, "weight": 0.1}
        测试步骤: {"min_steps": 2, "max_steps": 8, "weight": 0.3}
        
    使用场景:
        - 根据团队标准调整评分规则
        - 适配不同项目的质量要求
        - 优化评分算法的准确性
    """
    try:
        # 解析规则配置
        try:
            config_data = json.loads(rule_config)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"JSON格式错误：{str(e)}",
                "suggestion": "请检查JSON格式是否正确"
            }, ensure_ascii=False, indent=2)
        
        config_manager = await get_config_manager()
        
        # 验证配置
        if rule_name in ["title", "precondition", "steps", "expected_result", "priority"]:
            # 构建完整配置进行验证
            current_config = await config_manager.load_config()
            test_config = config_manager._config_to_dict(current_config)
            test_config[f"{rule_name}_rule"] = config_data
            
            validation_result = await config_manager.validate_config(test_config)
            
            if not validation_result["valid"]:
                return json.dumps({
                    "status": "error",
                    "message": "配置验证失败",
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"]
                }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": f"不支持的规则类型：{rule_name}",
                "suggestion": "支持的规则类型：title, precondition, steps, expected_result, priority"
            }, ensure_ascii=False, indent=2)
        
        # 如果仅验证，返回验证结果
        if validate_only:
            return json.dumps({
                "status": "success",
                "message": "配置验证通过",
                "rule_name": rule_name,
                "config": config_data,
                "validation": validation_result
            }, ensure_ascii=False, indent=2)
        
        # 更新配置
        await config_manager.update_rule(rule_name, config_data)
        
        result = {
            "status": "success",
            "message": f"成功更新{rule_name}规则",
            "rule_name": rule_name,
            "new_config": config_data,
            "validation": validation_result,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"配置更新失败：{str(e)}",
            "suggestion": "请检查配置参数是否正确"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def reset_scoring_config() -> str:
    """
    重置评分配置为默认值
    
    功能描述:
        - 将所有评分规则重置为系统默认值
        - 清除所有自定义配置
        - 恢复标准的评分权重和阈值
        
    返回:
        str: 重置结果的JSON字符串
        
    默认配置包括:
        - 标题：最大40字符，权重0.2
        - 前置条件：最大2项，权重0.15
        - 测试步骤：1-10步，权重0.25
        - 预期结果：5-200字符，权重0.25
        - 优先级：P0-P3，权重0.15
        
    使用场景:
        - 配置出现问题时恢复默认
        - 重新开始配置调整
        - 标准化评分规则
    """
    try:
        config_manager = await get_config_manager()
        await config_manager.reset_to_default()
        
        # 获取重置后的配置
        new_config = await config_manager.load_config()
        
        result = {
            "status": "success",
            "message": "评分配置已重置为默认值",
            "config": config_manager._config_to_dict(new_config),
            "reset_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"重置配置失败：{str(e)}",
            "suggestion": "请检查配置文件权限"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def validate_scoring_config(config_json: str) -> str:
    """
    验证评分配置的有效性
    
    功能描述:
        - 验证配置JSON格式和数据有效性
        - 检查权重总和是否合理
        - 检查数值范围是否正确
        - 提供配置优化建议
        
    参数:
        config_json (str): 完整的评分配置JSON字符串
        
    返回:
        str: 验证结果的JSON字符串
        
    验证项目:
        - JSON格式正确性
        - 权重总和接近1.0
        - 数值范围合理性
        - 必需字段完整性
        
    使用场景:
        - 配置更新前的预检查
        - 配置文件导入验证
        - 配置质量评估
    """
    try:
        # 解析JSON
        try:
            config_data = json.loads(config_json)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"JSON格式错误：{str(e)}",
                "suggestion": "请检查JSON格式是否正确"
            }, ensure_ascii=False, indent=2)
        
        config_manager = await get_config_manager()
        validation_result = await config_manager.validate_config(config_data)
        
        result = {
            "status": "success" if validation_result["valid"] else "error",
            "message": "配置验证完成",
            "validation_result": validation_result,
            "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"验证失败：{str(e)}",
            "suggestion": "请检查配置格式"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def score_testcase_quality(
    testcase_data: str,
    return_details: bool = True
) -> str:
    """
    对单个测试用例进行质量评分
    
    功能描述:
        - 基于当前配置规则对测试用例进行质量评分
        - 分析标题、前置条件、测试步骤、预期结果、优先级
        - 提供详细的分项评分和改进建议
        - 支持批量评分处理
        
    参数:
        testcase_data (str): 测试用例数据的JSON字符串
        return_details (bool): 是否返回详细评分信息，默认True
        
    返回:
        str: 评分结果的JSON字符串
        
    测试用例数据格式:
        {
            "id": "用例ID",
            "title": "测试用例标题",
            "precondition": "前置条件",
            "steps": "测试步骤",
            "expected_result": "预期结果",
            "priority": "优先级"
        }
        
    返回结果包括:
        - 总分和等级
        - 分项详细评分
        - 改进建议列表
        - 评分时间
        
    使用场景:
        - 测试用例质量检查
        - 用例编写指导
        - 质量标准验证
    """
    try:
        # 解析测试用例数据
        try:
            testcase = json.loads(testcase_data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"测试用例数据格式错误：{str(e)}",
                "suggestion": "请检查JSON格式是否正确"
            }, ensure_ascii=False, indent=2)
        
        # 获取评分器并进行评分
        scorer = await get_quality_scorer()
        score_result = await scorer.score_single_testcase(testcase)
        
        # 根据参数决定返回详细信息还是简化信息
        if return_details:
            result = {
                "status": "success",
                "score_result": score_result
            }
        else:
            result = {
                "status": "success",
                "testcase_id": score_result["testcase_id"],
                "total_score": score_result["total_score"],
                "score_level": score_result["score_level"],
                "improvement_count": len(score_result["improvement_suggestions"])
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"评分失败：{str(e)}",
            "suggestion": "请检查测试用例数据格式"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def score_testcases_batch(
    testcases_data: str,
    batch_size: int = 10,
    return_summary_only: bool = False
) -> str:
    """
    批量评分测试用例
    
    功能描述:
        - 对多个测试用例进行批量质量评分
        - 支持分批处理，避免内存过载
        - 提供统计汇总和分布分析
        - 生成批量改进建议
        
    参数:
        testcases_data (str): 测试用例数组的JSON字符串
        batch_size (int): 每批处理的用例数量，默认10
        return_summary_only (bool): 是否仅返回汇总信息，默认False
        
    返回:
        str: 批量评分结果的JSON字符串
        
    输入数据格式:
        [
            {
                "id": "用例ID",
                "title": "测试用例标题",
                "precondition": "前置条件",
                "steps": "测试步骤",
                "expected_result": "预期结果",
                "priority": "优先级"
            },
            ...
        ]
        
    返回结果包括:
        - 处理统计信息
        - 平均分和分数分布
        - 详细评分结果（可选）
        - 批量改进建议汇总
        
    使用场景:
        - 大批量测试用例质量检查
        - 团队用例质量评估
        - 质量改进计划制定
    """
    try:
        # 解析测试用例数组
        try:
            testcases = json.loads(testcases_data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"测试用例数据格式错误：{str(e)}",
                "suggestion": "请检查JSON格式是否正确"
            }, ensure_ascii=False, indent=2)
        
        if not isinstance(testcases, list):
            return json.dumps({
                "status": "error",
                "message": "测试用例数据必须是数组格式",
                "suggestion": "请提供测试用例数组"
            }, ensure_ascii=False, indent=2)
        
        if len(testcases) == 0:
            return json.dumps({
                "status": "error",
                "message": "测试用例数组为空",
                "suggestion": "请提供至少一个测试用例"
            }, ensure_ascii=False, indent=2)
        
        # 获取评分器并进行批量评分
        scorer = await get_quality_scorer()
        batch_result = await scorer.score_batch_testcases(testcases, batch_size)
        
        # 根据参数决定返回详细信息还是汇总信息
        if return_summary_only:
            result = {
                "status": "success",
                "summary": {
                    "total_count": batch_result["total_count"],
                    "success_count": batch_result["success_count"],
                    "error_count": batch_result["error_count"],
                    "average_score": batch_result["average_score"],
                    "score_distribution": batch_result["score_distribution"],
                    "processed_at": batch_result["processed_at"]
                }
            }
        else:
            result = {
                "status": "success",
                "batch_result": batch_result
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"批量评分失败：{str(e)}",
            "suggestion": "请检查测试用例数据格式和系统资源"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

if __name__ == "__main__":

    # 启动MCP服务器（使用标准输入输出传输）
    mcp.run(transport='stdio')