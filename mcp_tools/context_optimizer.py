"""
TAPD 数据智能摘要优化工具

这个模块提供了基于在线LLM（如DeepSeek、Qwen等）的TAPD数据智能分析功能。
主要用于处理大型TAPD数据集，避免token超限问题，并生成高质量的项目概览摘要。

核心功能：
1. 数据分块处理：根据token限制自动将数据分割为合适的块
2. 在线LLM调用：支持DeepSeek/Qwen/OpenAI兼容的API
3. 递归摘要合并：将多个分块摘要合并为完整的项目概览
4. 错误处理和重试：完善的异常处理机制

使用场景：
- 生成项目质量分析报告
- 快速了解项目整体情况  
- 为管理层提供数据概览
"""

import json, os, aiohttp, asyncio
from typing import Dict, List, Callable, Awaitable, AsyncIterable
# 兼容导入：既支持作为包导入，也支持脚本直接运行
try:
    from .common_utils import get_api_manager, get_file_manager, TransmissionManager  # type: ignore
except Exception:
    import os, sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from mcp_tools.common_utils import get_api_manager, get_file_manager, TransmissionManager  # type: ignore

# ---------------------------------------------------------------------------
# 1. Pagination helpers
# ---------------------------------------------------------------------------

async def iter_items(fetch_fn: Callable[..., Awaitable[List[Dict]]], *, page_size: int = 200, **params) -> AsyncIterable[Dict]:
    """分页迭代器，逐页获取数据直到没有更多数据"""
    page = 1
    while True:
        res = await fetch_fn(page=page, limit=page_size, **params)
        if not res:
            break
        for itm in res:
            yield itm
        if len(res) < page_size:
            break
        page += 1

# ---------------------------------------------------------------------------
# 2. Chunkify
# ---------------------------------------------------------------------------

def tokens(text: str) -> int:
    """简单的token估算函数，大致按4个字符=1个token计算"""
    return len(text) // 4


def chunkify(items: List[Dict], max_tokens: int = 1000) -> List[List[Dict]]:
    """将数据项按token数量分块，避免单次请求token过多"""
    chunks, buf, cur = [], [], 0
    for it in items:
        t = tokens(it.get("title", ""))
        if cur + t > max_tokens and buf:
            chunks.append(buf)
            buf, cur = [], 0
        buf.append(it)
        cur += t
    if buf:
        chunks.append(buf)
    return chunks

# ---------------------------------------------------------------------------
# 3. Online summariser using unified API manager
# ---------------------------------------------------------------------------

async def call_llm(prompt: str, session: aiohttp.ClientSession, *, max_tokens: int = 60) -> str:
    """调用在线LLM API，使用统一的API管理器"""
    api_manager = get_api_manager()
    return await api_manager.call_llm(prompt, session, max_tokens=max_tokens)


async def summarize_chunk(
    chunk: List[Dict],
    session: aiohttp.ClientSession,
    *,
    tm: TransmissionManager,
    ack_mode: str = "ack_only",
    max_retries: int = 2,
    retry_backoff: float = 1.5,
    chunk_index: int = 0,
) -> str:
    """对单个数据块生成详细摘要（100-300字），接入ACK验证与重试机制"""
    # 第一步：为分块内条目分配稳定ID并请求ACK
    items_min = tm.assign_ids(chunk)
    sent_ids = [x["id"] for x in items_min]
    ack_prompt = tm.build_ack_prompt(items_min, mode=ack_mode)

    ack_ok = False
    ack_json = None
    for attempt in range(max_retries + 1):
        try:
            ack_resp = await call_llm(
                ack_prompt,
                session,
                max_tokens=800 if ack_mode == "ack_and_analyze" else 300,
            )
            ack_json = tm.extract_first_json(ack_resp)
            verify = tm.verify_ack(sent_ids, ack_json)
            if verify.get("ok"):
                tm.update_stats(True, retries=attempt)
                ack_ok = True
                # 如果在 ack_and_analyze 模式且模型已返回分析文本，直接使用
                if (
                    ack_mode == "ack_and_analyze"
                    and isinstance(ack_json, dict)
                    and ack_json.get("analysis_text")
                ):
                    return str(ack_json["analysis_text"])[:2000]
                break
            else:
                tm.log_retry(chunk_index, attempt + 1, "ack_validation_failed", {"verify": verify, "sample": (ack_resp or "")[:400]})
        except Exception as e:
            tm.log_retry(chunk_index, attempt + 1, "ack_call_failed", {"error": str(e)})
        # 失败则等待并重试
        if attempt < max_retries:
            await asyncio.sleep(retry_backoff)
        else:
            # 达到最大重试次数
            tm.update_stats(False, retries=attempt + 1)

    # 第二步：生成分析摘要（当ack_only 或者 ack失败但仍继续生成分析，确保功能可用）
    # 提取TAPD数据的关键信息，处理需求和缺陷的不同字段
    items_info = []
    for it in chunk[:50]:  # 限制处理数量以避免prompt过长
        # 处理标题字段（TAPD中是'name'不是'title'）
        title = it.get("name", "") or it.get("title", "")
        status = it.get("status", "")
        priority = it.get("priority", "")

        # 判断类型
        item_type = "需求" if "story" in str(it.get("workitem_type_id", "")) or "story" in str(it.get("id", "")) else "缺陷"

        # 构建条目描述
        item_desc = f"[{item_type}] {title}"
        if status:
            item_desc += f" (状态:{status})"
        if priority:
            item_desc += f" (优先级:{priority})"

        items_info.append(item_desc)

    items_text = "\n".join(items_info)

    prefix = "" if ack_ok else "[注意] ACK未完全通过，以下为在当前可用数据上的分析结果。\n\n"
    prompt = f"""{prefix}分析以下TAPD项目数据，生成详细的质量分析摘要（150-250字）：

{items_text}

请从以下维度分析：
1. 功能模块分布和业务特点
2. 需求与缺陷的优先级分布
3. 状态分布和进展情况
4. 潜在的质量风险

生成专业的项目质量分析摘要："""
    
    return await call_llm(prompt, session, max_tokens=600)


async def recursive_summary(sentences: List[str], session: aiohttp.ClientSession) -> str:
    """递归合并多个分块摘要为完整的项目概览（300-500字）"""
    if len(sentences) == 1:
        return sentences[0]

    all_summaries = "\n\n".join(f"模块{i+1}分析：\n{summary}" for i, summary in enumerate(sentences))
    merged_prompt = f"""将以下多个模块的分析结果合并为一份完整的TAPD项目质量概览报告（300-400字）：

{all_summaries}

请生成综合性的项目质量概览，包含：
1. 项目整体特征和主要业务模块
2. 需求与缺陷的总体分布特点
3. 质量状况评估和风险识别
4. 关键改进建议

TAPD项目质量概览："""
    return await call_llm(merged_prompt, session, max_tokens=800)

# ---------------------------------------------------------------------------
# 4. build_overview
# ---------------------------------------------------------------------------

async def build_overview(
    *,
    fetch_story: Callable[..., Awaitable[List[Dict]]],
    fetch_bug: Callable[..., Awaitable[List[Dict]]],
    since: str = "2025-01-01",
    until: str = "2025-12-31",
    max_total_tokens: int = 6000,
    # 新增可靠传输参数
    ack_mode: str = "ack_only",
    max_retries: int = 2,
    retry_backoff: float = 1.5,
    chunk_size: int = 0,
) -> Dict:
    """构建TAPD项目概览，支持时间范围过滤、智能摘要生成与ACK验证"""

    # 收集所有数据
    stories = [s async for s in iter_items(fetch_story)]
    bugs = [b async for b in iter_items(fetch_bug)]

    # 时间过滤：根据created或modified字段过滤
    def filter_by_time(items: List[Dict], since: str, until: str) -> List[Dict]:
        """根据时间范围过滤数据"""
        if not since and not until:
            return items

        filtered = []
        for item in items:
            # 获取时间字段（优先使用created，然后modified）
            time_str = item.get('created') or item.get('modified') or ''
            if not time_str:
                continue

            # 简单的时间比较（假设格式为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
            item_date = time_str.split(' ')[0]  # 只取日期部分

            # 检查是否在时间范围内
            if since and item_date < since:
                continue
            if until and item_date > until:
                continue

            filtered.append(item)
        return filtered

    # 应用时间过滤
    if since or until:
        stories = filter_by_time(stories, since, until)
        bugs = filter_by_time(bugs, since, until)

    # 合并所有数据项
    all_items = stories + bugs
    if not all_items:
        return {
            "total_stories": 0,
            "total_bugs": 0,
            "summary_text": "未找到任何TAPD数据。",
            "chunks": 0,
            "truncated": False,
            "transmission": {"stats": {"total_chunks": 0, "ack_success_chunks": 0, "ack_failed_chunks": 0, "total_retries": 0}}
        }

    # 分块处理：支持按项目数固定分块或按token估算
    if isinstance(chunk_size, int) and chunk_size > 0:
        chunks = [all_items[i:i+chunk_size] for i in range(0, len(all_items), chunk_size)]
    else:
        chunks = chunkify(all_items, max_total_tokens // 10)  # 每块约为总token的1/10
    print(f"[数据分块] 数据分块完成：共 {len(chunks)} 个数据块")

    # 初始化可靠传输管理器
    fm = get_file_manager()
    tm = TransmissionManager(fm)

    async with aiohttp.ClientSession() as session:
        try:
            # 为每个块生成摘要
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                print(f"[处理进度] 正在处理第 {i+1}/{len(chunks)} 个数据块（含ACK校验）...")
                summary = await summarize_chunk(
                    chunk,
                    session,
                    tm=tm,
                    ack_mode=ack_mode,
                    max_retries=max_retries,
                    retry_backoff=retry_backoff,
                    chunk_index=i,
                )
                chunk_summaries.append(summary)
                print(f"[完成] 完成第 {i+1}/{len(chunks)} 个数据块的摘要生成")

            # 递归合并摘要
            if len(chunk_summaries) > 1:
                print("[合并中] 正在合并多个数据块的摘要...")
                summary_text = await recursive_summary(chunk_summaries, session)
                print("[合并完成] 摘要合并完成")
            else:
                summary_text = chunk_summaries[0] if chunk_summaries else "无法生成摘要。"

        except Exception as e:
            # 如果LLM调用失败，返回基本统计信息
            error_msg = str(e)
            if "API配置错误" in error_msg:
                summary_text = f"无法生成智能摘要: {error_msg}"
            else:
                summary_text = f"摘要生成失败: {error_msg}。数据包含 {len(stories)} 个需求和 {len(bugs)} 个缺陷。"

    # 检查摘要长度
    if tokens(summary_text) > max_total_tokens:
        # 如果摘要太长，进行智能截断，保持完整性
        summary_text = summary_text[:max_total_tokens] + "...\n\n[摘要因长度限制被截断]"
        truncated = True
    else:
        truncated = False

    # 完成传输报告
    transmission_report = tm.finalize_report()

    return {
        "status": "success",
        "time_range": f"{since} 至 {until}",
        "total_stories": len(stories),
        "total_bugs": len(bugs),
        "summary_text": summary_text,
        "chunks": len(chunks),
        "truncated": truncated,
        "transmission": transmission_report,
    }

# ---------------------------------------------------------------------------
# 5. CLI helper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse, pathlib

    ap = argparse.ArgumentParser(description="Generate TAPD overview via online LLM (DeepSeek/Qwen)")
    ap.add_argument("-f", "--file", default="local_data/msg_from_fetcher.json", help="path to real TAPD data json file")
    ap.add_argument("--offline", action="store_true", help="return dummy summary (no LLM call)")
    ap.add_argument("--debug", action="store_true", help="print counters")
    args = ap.parse_args()

    # 处理文件路径：如果不是绝对路径，转换为相对于项目根目录的路径
    file_path = args.file
    if not pathlib.Path(file_path).is_absolute():
        base_dir = pathlib.Path(__file__).parent.parent
        file_path = str(base_dir / file_path)

    # 直接使用pathlib读取（原逻辑），但这里应该改为统一接口
    # 先临时保持原有逻辑，确保功能不受影响
    import json
    data = json.loads(pathlib.Path(file_path).read_text(encoding='utf-8'))
    
    # 适配数据格式：如果是TAPD格式（字典），提取stories和bugs；如果是列表格式，按原逻辑处理  
    if isinstance(data, dict) and ('stories' in data or 'bugs' in data):
        stories = data.get('stories', [])
        bugs = data.get('bugs', [])
    else:
        # 原来的列表格式逻辑
        if isinstance(data, list):
            half = len(data) // 2
            stories, bugs = data[:half], data[half:]
        else:
            stories, bugs = [], []

    async def fetch_story(*, page: int = 1, limit: int = 200, **_):
        start, end = (page - 1) * limit, page * limit
        return stories[start:end]

    async def fetch_bug(*, page: int = 1, limit: int = 200, **_):
        start, end = (page - 1) * limit, page * limit
        return bugs[start:end]

    async def _main():
        if args.offline:
            # 离线模式：返回基本统计信息
            result = {
                "total_stories": len(stories),
                "total_bugs": len(bugs),
                "summary_text": "离线模式：该项目包含多个电商相关功能模块，涉及用户管理、订单处理、支付系统等关键业务领域。",
                "chunks": (len(stories) + len(bugs)) // 100 + 1,
                "truncated": False,
            }
        else:
            # 在线模式：调用LLM生成智能摘要（使用默认ACK参数）
            result = await build_overview(
                fetch_story=fetch_story,
                fetch_bug=fetch_bug
            )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(_main())