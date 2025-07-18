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
from mcp_tools.enhanced_scoring_config import get_enhanced_config_manager    # 导入增强配置管理器
from mcp_tools.enhanced_testcase_scorer import get_enhanced_quality_scorer    # 导入增强评分器
from mcp_tools.requirement_knowledge_base import (
    RequirementKnowledgeBase, build_knowledge_base_from_tapd_data
)    # 导入历史需求知识库

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

# ===============================
# 增强评分功能接口
# ===============================

@mcp.tool()
async def create_scoring_profile(
    profile_name: str,
    description: str = "",
    strategy: str = "standard",
    base_profile: str = ""
) -> str:
    """
    创建新的评分配置档案
    
    功能描述:
        - 创建自定义的评分配置档案
        - 支持基于现有档案创建
        - 提供多种评分策略选择
        - 支持档案描述和元数据管理
        
    参数:
        profile_name (str): 新档案名称
        description (str): 档案描述，默认为空
        strategy (str): 评分策略，可选值：strict(严格)、standard(标准)、lenient(宽松)
        base_profile (str): 基础档案名称，如果提供则基于该档案创建
        
    返回:
        str: 创建结果的JSON字符串
        
    评分策略说明:
        - strict: 严格模式，评分标准较高
        - standard: 标准模式，平衡的评分标准
        - lenient: 宽松模式，评分标准较低
        
    使用场景:
        - 为不同项目创建专用评分标准
        - 适应不同团队的质量要求
        - 建立分层的评分体系
    """
    try:
        from mcp_tools.enhanced_scoring_config import ScoringStrategy
        
        # 验证策略参数
        strategy_map = {
            "strict": ScoringStrategy.STRICT,
            "standard": ScoringStrategy.STANDARD,
            "lenient": ScoringStrategy.LENIENT
        }
        
        if strategy not in strategy_map:
            return json.dumps({
                "status": "error",
                "message": f"不支持的评分策略：{strategy}",
                "suggestion": "可选值：strict、standard、lenient"
            }, ensure_ascii=False, indent=2)
        
        config_manager = await get_enhanced_config_manager()
        
        # 创建配置档案
        profile = await config_manager.create_profile(
            name=profile_name,
            description=description,
            strategy=strategy_map[strategy],
            base_profile=base_profile if base_profile else None
        )
        
        result = {
            "status": "success",
            "message": f"成功创建评分配置档案：{profile_name}",
            "profile": {
                "name": profile.name,
                "description": profile.description,
                "strategy": profile.strategy.value,
                "created_at": profile.created_at,
                "total_weight": profile.get_total_weight(),
                "dimensions_count": len(profile.dimensions)
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"创建配置档案失败：{str(e)}",
            "suggestion": "请检查参数是否正确"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def list_scoring_profiles() -> str:
    """
    列出所有可用的评分配置档案
    
    功能描述:
        - 显示所有已创建的评分配置档案
        - 提供档案的基本信息和元数据
        - 支持档案选择和管理
        
    返回:
        str: 档案列表的JSON字符串
        
    返回信息包括:
        - 档案名称和描述
        - 评分策略
        - 创建时间和更新时间
        - 作者信息
        - 版本号
        
    使用场景:
        - 查看可用的评分标准
        - 选择合适的评分档案
        - 管理评分配置
    """
    try:
        config_manager = await get_enhanced_config_manager()
        profiles = await config_manager.list_profiles()
        
        result = {
            "status": "success",
            "message": f"找到 {len(profiles)} 个评分配置档案",
            "profiles": profiles
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取配置档案列表失败：{str(e)}",
            "suggestion": "请检查配置目录权限"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def get_scoring_profile_details(profile_name: str) -> str:
    """
    获取评分配置档案的详细信息
    
    功能描述:
        - 显示指定档案的完整配置信息
        - 包括所有评分维度的详细设置
        - 显示评分阈值和策略配置
        
    参数:
        profile_name (str): 档案名称
        
    返回:
        str: 档案详细信息的JSON字符串
        
    详细信息包括:
        - 档案基本信息
        - 评分阈值设置
        - 各维度权重和配置
        - 评分范围设置
        - 自定义参数
        
    使用场景:
        - 查看档案的具体配置
        - 了解评分标准的细节
        - 配置调整前的参考
    """
    try:
        config_manager = await get_enhanced_config_manager()
        profile = await config_manager.load_profile(profile_name)
        
        # 构建详细信息
        dimensions_info = {}
        for dim_name, dim_rule in profile.dimensions.items():
            dimensions_info[dim_name] = {
                "name": dim_rule.name,
                "weight": dim_rule.weight,
                "enabled": dim_rule.enabled,
                "min_score": dim_rule.min_score,
                "max_score": dim_rule.max_score,
                "scoring_ranges": [
                    {
                        "min_value": sr.min_value,
                        "max_value": sr.max_value,
                        "score": sr.score,
                        "description": sr.description,
                        "weight_multiplier": sr.weight_multiplier
                    } for sr in dim_rule.scoring_ranges
                ],
                "custom_params": dim_rule.custom_params
            }
        
        result = {
            "status": "success",
            "profile": {
                "name": profile.name,
                "description": profile.description,
                "strategy": profile.strategy.value,
                "version": profile.version,
                "author": profile.author,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "thresholds": {
                    "excellent_min": profile.thresholds.excellent_min,
                    "good_min": profile.thresholds.good_min,
                    "fair_min": profile.thresholds.fair_min,
                    "poor_max": profile.thresholds.poor_max
                },
                "dimensions": dimensions_info,
                "total_weight": profile.get_total_weight(),
                "validation": profile.validate()
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取配置档案详情失败：{str(e)}",
            "suggestion": "请检查档案名称是否正确"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def update_scoring_thresholds(
    profile_name: str,
    excellent_min: float = 9.0,
    good_min: float = 7.0,
    fair_min: float = 5.0,
    poor_max: float = 4.9
) -> str:
    """
    更新评分配置档案的阈值设置
    
    功能描述:
        - 自定义评分等级的阈值设置
        - 支持灵活的分数区间调整
        - 验证阈值设置的合理性
        
    参数:
        profile_name (str): 档案名称
        excellent_min (float): 优秀等级最低分，默认9.0
        good_min (float): 良好等级最低分，默认7.0
        fair_min (float): 及格等级最低分，默认5.0
        poor_max (float): 需要改进等级最高分，默认4.9
        
    返回:
        str: 更新结果的JSON字符串
        
    阈值要求:
        - 必须满足：poor_max < fair_min <= good_min <= excellent_min <= 10.0
        - 所有阈值必须在0-10分范围内
        
    使用场景:
        - 调整评分等级标准
        - 适应不同的质量要求
        - 优化评分体系
    """
    try:
        from mcp_tools.enhanced_scoring_config import ScoreThresholds
        
        config_manager = await get_enhanced_config_manager()
        profile = await config_manager.load_profile(profile_name)
        
        # 创建新的阈值配置
        new_thresholds = ScoreThresholds(
            excellent_min=excellent_min,
            good_min=good_min,
            fair_min=fair_min,
            poor_max=poor_max
        )
        
        # 更新档案
        profile.thresholds = new_thresholds
        profile.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        await config_manager.save_profile(profile)
        
        result = {
            "status": "success",
            "message": f"成功更新档案 {profile_name} 的阈值设置",
            "profile_name": profile_name,
            "new_thresholds": {
                "excellent_min": excellent_min,
                "good_min": good_min,
                "fair_min": fair_min,
                "poor_max": poor_max
            },
            "updated_at": profile.updated_at
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"更新阈值设置失败：{str(e)}",
            "suggestion": "请检查阈值设置是否合理"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def update_dimension_config(
    profile_name: str,
    dimension_name: str,
    weight: float,
    enabled: bool = True,
    min_score: float = 0.0,
    max_score: float = 10.0,
    custom_params: str = "{}"
) -> str:
    """
    更新评分维度的配置
    
    功能描述:
        - 调整评分维度的权重和参数
        - 支持启用/禁用特定维度
        - 自定义评分范围和参数
        
    参数:
        profile_name (str): 档案名称
        dimension_name (str): 维度名称(title/precondition/steps/expected_result/priority)
        weight (float): 权重值(0-1之间)
        enabled (bool): 是否启用，默认True
        min_score (float): 最小分数，默认0.0
        max_score (float): 最大分数，默认10.0
        custom_params (str): 自定义参数的JSON字符串
        
    返回:
        str: 更新结果的JSON字符串
        
    使用场景:
        - 调整各维度的重要性
        - 禁用不需要的评分维度
        - 自定义评分参数
    """
    try:
        config_manager = await get_enhanced_config_manager()
        profile = await config_manager.load_profile(profile_name)
        
        if dimension_name not in profile.dimensions:
            return json.dumps({
                "status": "error",
                "message": f"维度 {dimension_name} 不存在",
                "suggestion": f"可用维度：{list(profile.dimensions.keys())}"
            }, ensure_ascii=False, indent=2)
        
        # 解析自定义参数
        try:
            custom_params_dict = json.loads(custom_params)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"自定义参数JSON格式错误：{str(e)}",
                "suggestion": "请检查JSON格式是否正确"
            }, ensure_ascii=False, indent=2)
        
        # 更新维度配置
        dimension = profile.dimensions[dimension_name]
        dimension.weight = weight
        dimension.enabled = enabled
        dimension.min_score = min_score
        dimension.max_score = max_score
        
        # 更新自定义参数
        if custom_params_dict:
            dimension.custom_params.update(custom_params_dict)
        
        # 更新时间戳
        profile.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        await config_manager.save_profile(profile)
        
        result = {
            "status": "success",
            "message": f"成功更新维度 {dimension_name} 的配置",
            "profile_name": profile_name,
            "dimension_name": dimension_name,
            "new_config": {
                "weight": weight,
                "enabled": enabled,
                "min_score": min_score,
                "max_score": max_score,
                "custom_params": custom_params_dict
            },
            "total_weight": profile.get_total_weight(),
            "updated_at": profile.updated_at
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"更新维度配置失败：{str(e)}",
            "suggestion": "请检查参数是否正确"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def enhanced_score_testcase(
    testcase_data: str,
    profile_name: str = "default",
    return_details: bool = True
) -> str:
    """
    使用增强评分引擎对测试用例进行评分
    
    功能描述:
        - 使用指定的评分档案进行评分
        - 支持多种评分策略
        - 提供更详细的评分分析
        - 支持自定义评分阈值
        
    参数:
        testcase_data (str): 测试用例数据的JSON字符串
        profile_name (str): 使用的评分档案名称，默认为"default"
        return_details (bool): 是否返回详细评分信息，默认True
        
    返回:
        str: 评分结果的JSON字符串
        
    相比基础评分的优势:
        - 支持多套评分标准
        - 灵活的阈值设置
        - 多种评分策略
        - 更详细的评分分析
        
    使用场景:
        - 高级测试用例质量评估
        - 多标准评分对比
        - 精确的质量控制
    """
    try:
        scorer = await get_enhanced_quality_scorer(profile_name)
        
        # 解析测试用例数据
        try:
            testcase = json.loads(testcase_data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"测试用例数据格式错误：{str(e)}",
                "suggestion": "请检查JSON格式是否正确"
            }, ensure_ascii=False, indent=2)
        
        # 获取评分结果
        score_result = await scorer.score_single_testcase(testcase, profile_name)
        
        # 根据参数决定返回信息
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
                "score_level_cn": score_result["score_level_cn"],
                "profile_name": score_result["profile_name"],
                "improvement_count": len(score_result["improvement_suggestions"])
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"增强评分失败：{str(e)}",
            "suggestion": "请检查测试用例数据格式和档案名称"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def enhanced_score_testcases_batch(
    testcases_data: str,
    profile_name: str = "default",
    batch_size: int = 10,
    return_summary_only: bool = False
) -> str:
    """
    使用增强评分引擎批量评分测试用例
    
    功能描述:
        - 批量处理多个测试用例
        - 使用指定的评分档案
        - 提供详细的统计分析
        - 支持大批量数据处理
        
    参数:
        testcases_data (str): 测试用例数组的JSON字符串
        profile_name (str): 使用的评分档案名称，默认为"default"
        batch_size (int): 每批处理的用例数量，默认10
        return_summary_only (bool): 是否仅返回汇总信息，默认False
        
    返回:
        str: 批量评分结果的JSON字符串
        
    返回信息包括:
        - 基于档案阈值的分布统计
        - 评分策略信息
        - 详细的批量处理结果
        
    使用场景:
        - 大规模测试用例质量评估
        - 质量报告生成
        - 批量质量改进分析
    """
    try:
        scorer = await get_enhanced_quality_scorer(profile_name)
        
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
        
        # 批量评分
        batch_result = await scorer.score_batch_testcases(testcases, batch_size, profile_name)
        
        # 根据参数决定返回信息
        if return_summary_only:
            result = {
                "status": "success",
                "summary": {
                    "total_count": batch_result["total_count"],
                    "success_count": batch_result["success_count"],
                    "error_count": batch_result["error_count"],
                    "average_score": batch_result["average_score"],
                    "score_distribution": batch_result["score_distribution"],
                    "profile_name": batch_result["profile_name"],
                    "strategy": batch_result["strategy"],
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
            "message": f"批量增强评分失败：{str(e)}",
            "suggestion": "请检查测试用例数据格式和系统资源"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

# ===============================
# 历史需求知识库功能接口
# ===============================

@mcp.tool()
async def build_requirement_knowledge_base(data_file_path: str = "local_data/msg_from_fetcher.json") -> str:
    """
    从TAPD数据构建历史需求知识库
    
    功能描述:
        - 从现有TAPD数据构建历史需求知识库
        - 提取需求的关键信息用于后续搜索和推荐
        - 支持自定义数据源路径
        - 为新测试用例编写提供历史参考基础
        
    参数:
        data_file_path (str): TAPD数据文件路径，默认为"local_data/msg_from_fetcher.json"
        
    返回:
        str: 构建结果的JSON字符串
        
    构建内容包括:
        - 需求基本信息（ID、标题、描述）
        - 功能分类和业务场景
        - 技术关键词提取
        - 测试用例模板关联
        
    使用场景:
        - 首次建立知识库
        - 更新现有知识库数据
        - 为团队提供需求历史参考
        
    注意事项:
        - 建议先调用get_tapd_data获取最新数据
        - 构建过程可能需要一定时间
        - 会覆盖现有的知识库数据
    """
    try:
        result = await build_knowledge_base_from_tapd_data(data_file_path)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"构建知识库失败：{str(e)}",
            "suggestion": "请检查数据文件是否存在，建议先调用get_tapd_data获取数据"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def add_requirement_to_knowledge_base(
    req_id: str,
    title: str,
    description: str,
    feature_type: str,
    complexity: str = "中等",
    business_scenario: str = "[]",
    technical_keywords: str = "[]",
    test_case_templates: str = "[]"
) -> str:
    """
    添加新需求到历史知识库
    
    功能描述:
        - 将新的需求信息添加到历史知识库
        - 支持完整的需求信息录入
        - 自动提取关键词和分类信息
        - 为后续的搜索和推荐提供数据
        
    参数:
        req_id (str): 需求ID，必须唯一
        title (str): 需求标题
        description (str): 需求描述
        feature_type (str): 功能类型（如：认证授权、数据管理、用户界面等）
        complexity (str): 复杂度等级，默认"中等"
        business_scenario (str): 业务场景JSON数组字符串，默认"[]"
        technical_keywords (str): 技术关键词JSON数组字符串，默认"[]"
        test_case_templates (str): 测试用例模板JSON数组字符串，默认"[]"
        
    返回:
        str: 添加结果的JSON字符串
        
    数据格式示例:
        business_scenario: ["用户管理", "安全验证"]
        technical_keywords: ["登录", "验证", "Token"]
        test_case_templates: [{"scenario": "正常登录", "steps": [...]}]
        
    使用场景:
        - 录入新的需求信息
        - 更新现有需求数据
        - 建立需求与测试用例的关联
        
    注意事项:
        - req_id必须唯一，重复ID会更新现有记录
        - JSON数组参数需要正确格式化
        - 建议提供详细的描述和分类信息
    """
    try:
        # 解析JSON数组参数
        try:
            business_scenario_list = json.loads(business_scenario)
            technical_keywords_list = json.loads(technical_keywords)
            test_case_templates_list = json.loads(test_case_templates)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"JSON格式错误：{str(e)}",
                "suggestion": "请检查business_scenario、technical_keywords、test_case_templates的JSON格式"
            }, ensure_ascii=False, indent=2)
        
        # 构建需求数据
        requirement_data = {
            "req_id": req_id,
            "title": title,
            "description": description,
            "feature_type": feature_type,
            "complexity": complexity,
            "business_scenario": business_scenario_list,
            "technical_keywords": technical_keywords_list,
            "change_history": [],
            "related_requirements": [],
            "test_case_templates": test_case_templates_list
        }
        
        # 添加到知识库
        kb = RequirementKnowledgeBase()
        success = kb.add_requirement_to_knowledge_base(requirement_data)
        
        if success:
            result = {
                "status": "success",
                "message": f"成功添加需求 {req_id} 到知识库",
                "requirement_id": req_id,
                "requirement_title": title,
                "feature_type": feature_type
            }
        else:
            result = {
                "status": "error",
                "message": f"添加需求 {req_id} 失败",
                "suggestion": "请检查需求数据格式"
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"添加需求到知识库失败：{str(e)}",
            "suggestion": "请检查参数格式和数据有效性"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def search_similar_requirements(
    query: str,
    feature_type: str = "",
    top_k: int = 5
) -> str:
    """
    搜索相似的历史需求
    
    功能描述:
        - 基于查询内容搜索相似的历史需求
        - 支持自然语言查询和关键词搜索
        - 可按功能类型过滤搜索结果
        - 返回相似度排序的需求列表
        
    参数:
        query (str): 搜索查询，支持自然语言描述
        feature_type (str): 功能类型过滤，默认为空（不过滤）
        top_k (int): 返回结果数量，默认5个
        
    返回:
        str: 搜索结果的JSON字符串
        
    搜索结果包括:
        - 需求基本信息
        - 相似度分数
        - 匹配的关键词
        - 关联的测试用例模板
        
    使用场景:
        - 查找相似的历史需求
        - 为新需求寻找参考案例
        - 了解相关功能的实现历史
        
    查询示例:
        - "用户登录验证功能"
        - "数据导入导出"
        - "权限管理系统"
        
    注意事项:
        - 需要先建立知识库
        - 查询词越具体，匹配效果越好
        - 支持中文和英文查询
    """
    try:
        kb = RequirementKnowledgeBase()
        
        # 搜索相似需求
        similar_reqs = kb.search_similar_requirements(
            query=query,
            feature_type=feature_type if feature_type else None,
            top_k=top_k
        )
        
        result = {
            "status": "success",
            "query": query,
            "feature_type": feature_type,
            "result_count": len(similar_reqs),
            "similar_requirements": similar_reqs
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"搜索相似需求失败：{str(e)}",
            "suggestion": "请检查知识库是否已建立，建议先调用build_requirement_knowledge_base"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def get_requirement_evolution_path(feature_id: str) -> str:
    """
    获取需求功能的演化路径
    
    功能描述:
        - 查看特定功能的历史演化过程
        - 了解功能的变更记录和发展轨迹
        - 分析功能演化的模式和趋势
        - 为新功能设计提供参考
        
    参数:
        feature_id (str): 功能ID或功能名称
        
    返回:
        str: 演化路径信息的JSON字符串
        
    演化信息包括:
        - 各个版本的功能特性
        - 测试重点的变化
        - 迁移和兼容性考虑
        - 演化模式分析
        
    使用场景:
        - 了解功能的发展历史
        - 分析功能变更的影响
        - 制定功能升级策略
        - 预测未来的演化趋势
        
    注意事项:
        - 需要预先录入演化数据
        - 功能ID需要准确匹配
        - 演化路径需要手动维护
    """
    try:
        kb = RequirementKnowledgeBase()
        evolution_path = kb.get_requirement_evolution_path(feature_id)
        
        result = {
            "status": "success",
            "feature_id": feature_id,
            "evolution_path": evolution_path
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取演化路径失败：{str(e)}",
            "suggestion": "请检查功能ID是否正确"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def recommend_test_cases_for_requirement(
    req_id: str = "",
    title: str = "",
    description: str = "",
    feature_type: str = "",
    business_scenario: str = "[]",
    technical_keywords: str = "[]",
    use_ai: bool = True
) -> str:
    """
    为需求推荐测试用例
    
    功能描述:
        - 基于需求信息智能推荐测试用例
        - 结合历史需求经验和AI分析
        - 提供多种测试场景的用例模板
        - 支持正常、异常、边界等测试类型
        
    参数:
        req_id (str): 需求ID，可选
        title (str): 需求标题
        description (str): 需求描述
        feature_type (str): 功能类型
        business_scenario (str): 业务场景JSON数组字符串，默认"[]"
        technical_keywords (str): 技术关键词JSON数组字符串，默认"[]"
        use_ai (bool): 是否使用AI推荐，默认True
        
    返回:
        str: 推荐结果的JSON字符串
        
    推荐内容包括:
        - 基于相似需求的模板推荐
        - AI生成的测试场景建议
        - 测试用例标题和步骤模板
        - 优先级和测试类型建议
        
    推荐来源:
        - 相似历史需求的测试用例
        - AI智能分析和生成
        - 标准测试用例模板库
        
    使用场景:
        - 新需求的测试用例设计
        - 测试用例完整性检查
        - 测试场景遗漏分析
        
    注意事项:
        - 需要配置AI API密钥（使用AI推荐时）
        - 推荐结果需要人工审核和调整
        - 建议结合实际业务场景使用
    """
    try:
        # 解析JSON数组参数
        try:
            business_scenario_list = json.loads(business_scenario)
            technical_keywords_list = json.loads(technical_keywords)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"JSON格式错误：{str(e)}",
                "suggestion": "请检查business_scenario、technical_keywords的JSON格式"
            }, ensure_ascii=False, indent=2)
        
        # 构建需求数据
        requirement_data = {
            "req_id": req_id,
            "title": title,
            "description": description,
            "feature_type": feature_type,
            "business_scenario": business_scenario_list,
            "technical_keywords": technical_keywords_list
        }
        
        # 获取推荐
        kb = RequirementKnowledgeBase()
        recommendations = await kb.recommend_test_cases_for_requirement(
            requirement_data=requirement_data,
            use_ai=use_ai
        )
        
        result = {
            "status": "success",
            "requirement_info": {
                "req_id": req_id,
                "title": title,
                "feature_type": feature_type
            },
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "use_ai": use_ai
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"推荐测试用例失败：{str(e)}",
            "suggestion": "请检查需求信息和网络连接（AI推荐时）"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def analyze_requirement_test_coverage(requirement_id: str) -> str:
    """
    分析需求的测试覆盖度
    
    功能描述:
        - 分析指定需求的测试用例覆盖情况
        - 识别测试覆盖的空白领域
        - 提供测试完整性评估
        - 给出测试改进建议
        
    参数:
        requirement_id (str): 需求ID
        
    返回:
        str: 覆盖度分析结果的JSON字符串
        
    分析内容包括:
        - 现有测试用例数量统计
        - 测试类型覆盖情况
        - 缺失的测试领域
        - 覆盖度改进建议
        
    测试类型分析:
        - 功能测试覆盖度
        - 异常测试覆盖度
        - 边界测试覆盖度
        - 性能测试覆盖度
        - 安全测试覆盖度
        
    使用场景:
        - 测试用例完整性检查
        - 测试策略制定
        - 质量保证评估
        - 测试计划优化
        
    注意事项:
        - 需要先将需求添加到知识库
        - 分析结果基于已录入的测试用例模板
        - 建议结合实际测试执行情况
    """
    try:
        kb = RequirementKnowledgeBase()
        coverage_analysis = kb.analyze_requirement_test_coverage(requirement_id)
        
        result = {
            "status": "success",
            "coverage_analysis": coverage_analysis
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"分析测试覆盖度失败：{str(e)}",
            "suggestion": "请检查需求ID是否正确，确保需求已添加到知识库"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

@mcp.tool()
async def get_knowledge_base_stats() -> str:
    """
    获取历史需求知识库统计信息
    
    功能描述:
        - 查看知识库的整体统计信息
        - 了解需求数量和分类分布
        - 检查知识库的健康状态
        - 为知识库管理提供数据支持
        
    返回:
        str: 统计信息的JSON字符串
        
    统计信息包括:
        - 总需求数量
        - 功能类型分布
        - 演化功能数量
        - 测试用例模板数量
        - 最后更新时间
        
    分类统计:
        - 按功能类型的需求分布
        - 按复杂度的需求分布
        - 按时间的需求分布
        
    使用场景:
        - 知识库健康检查
        - 数据质量评估
        - 知识库使用情况分析
        - 管理决策支持
        
    注意事项:
        - 需要已建立知识库
        - 统计数据实时计算
        - 反映当前知识库状态
    """
    try:
        kb = RequirementKnowledgeBase()
        stats = kb.get_knowledge_base_stats()
        
        result = {
            "status": "success",
            "knowledge_base_stats": stats
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取知识库统计信息失败：{str(e)}",
            "suggestion": "请检查知识库是否已建立"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

if __name__ == "__main__":

    # 启动MCP服务器（使用标准输入输出传输）
    mcp.run(transport='stdio')