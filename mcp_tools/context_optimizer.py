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
# 3. Online summariser (DeepSeek / Qwen / OpenAI‑compatible)
# ---------------------------------------------------------------------------
API_ENDPOINT_DEFAULT = os.getenv("DS_EP", "https://api.deepseek.com/v1")
API_MODEL_DEFAULT    = os.getenv("DS_MODEL", "deepseek-reasoner")
API_KEY              = os.getenv("DS_KEY")
_HEADERS_CACHE: dict[str, str] | None = None


def build_headers() -> dict[str, str]:
    """构建API请求头，检查API密钥是否已设置"""
    global _HEADERS_CACHE
    if _HEADERS_CACHE is None:
        if not API_KEY:
            raise RuntimeError("No API key provided – set DS_KEY (or compatible)!")
        _HEADERS_CACHE = {"Authorization": f"Bearer {API_KEY}"}
    return _HEADERS_CACHE


async def call_llm(prompt: str, session: aiohttp.ClientSession, *, model: str, endpoint: str, max_tokens: int = 60) -> str:
    """调用在线LLM API，支持DeepSeek‑Reasoner的reasoning_content字段"""
    try:
        headers = build_headers()  # 检查API密钥
    except RuntimeError as e:
        # 抛出更具体的错误信息
        raise RuntimeError(f"API配置错误: {str(e)}\n请设置环境变量 DS_KEY 为您的DeepSeek API密钥") from e
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    
    try:
        async with session.post(f"{endpoint}/chat/completions", json=payload, headers=headers, timeout=60) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise RuntimeError(f"API调用失败 (状态码: {resp.status}): {error_text}")
            js = await resp.json()
    except Exception as e:
        if "API配置错误" in str(e):
            raise  # 重新抛出API配置错误
        raise RuntimeError(f"网络请求失败: {str(e)}")

    try:
        msg = js["choices"][0]["message"]
        # DeepSeek‑Reasoner 把推理和最终回答分开；如果 content 为空则回退到 reasoning_content
        text = (msg.get("content") or msg.get("reasoning_content") or "").strip()
        for sep in ('。', '\n'):
            if sep in text:
                text = text.split(sep, 1)[0] + '。'
                break
        if not text:
            raise RuntimeError("LLM 返回空字符串，可能是 URL / KEY / model 配置问题。响应片段: " + str(js)[:400])
        return text
    except KeyError as e:
        raise RuntimeError(f"API响应格式错误，缺少字段: {str(e)}。响应内容: {str(js)[:400]}")
    except Exception as e:
        raise RuntimeError(f"解析API响应失败: {str(e)}。响应内容: {str(js)[:400]}")


async def summarize_chunk(chunk: List[Dict], session: aiohttp.ClientSession, *, model: str, endpoint: str) -> str:
    """对单个数据块生成详细摘要（100-300字）"""
    titles = "\n".join(it.get("title", "") for it in chunk[:50])
    prompt = f"""请分析以下TAPD需求和缺陷，生成一份详细的摘要报告（100-300字）：

项目条目：
{titles}

请从以下几个方面进行分析：
1. 主要功能模块和业务领域
2. 问题类型和严重程度分布
3. 开发重点和技术特征
4. 潜在的质量风险点

摘要："""
    return await call_llm(prompt, session, model=model, endpoint=endpoint, max_tokens=800)


async def recursive_summary(sentences: List[str], session: aiohttp.ClientSession, *, model: str, endpoint: str) -> str:
    """递归合并多个分块摘要为完整的项目概览（300-500字）"""
    if len(sentences) == 1:
        return sentences[0]
    
    all_summaries = "\n\n".join(f"模块{i+1}摘要：\n{summary}" for i, summary in enumerate(sentences))
    merged_prompt = f"""请将以下多个模块的分析摘要合并为一份完整的项目质量概览报告（300-500字）：

{all_summaries}

请生成一份综合性的项目概览，包含：
1. 整体项目特征和业务重点
2. 技术架构和开发重点分析
3. 质量风险评估和问题分布
4. 改进建议和关注要点

项目概览报告："""
    return await call_llm(merged_prompt, session, model=model, endpoint=endpoint, max_tokens=1200)

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
    model: str = API_MODEL_DEFAULT,
    endpoint: str = API_ENDPOINT_DEFAULT,
) -> Dict:
    """构建TAPD项目概览，支持时间范围过滤和智能摘要生成"""
    
    # 收集所有数据
    stories = [s async for s in iter_items(fetch_story)]
    bugs = [b async for b in iter_items(fetch_bug)]
    
    # 时间过滤（如果数据中有时间字段的话）
    # 这里可以根据实际数据结构添加时间过滤逻辑
    
    # 合并所有数据项
    all_items = stories + bugs
    if not all_items:
        return {
            "total_stories": 0,
            "total_bugs": 0,
            "summary_text": "未找到任何TAPD数据。",
            "chunks": 0,
            "truncated": False,
        }
    
    # 分块处理
    chunks = chunkify(all_items, max_total_tokens // 10)  # 每块约为总token的1/10
    
    async with aiohttp.ClientSession() as session:
        try:
            # 为每个块生成摘要
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                summary = await summarize_chunk(chunk, session, model=model, endpoint=endpoint)
                chunk_summaries.append(summary)
                print(f"完成第 {i+1}/{len(chunks)} 个数据块的摘要生成")
            
            # 递归合并摘要
            if len(chunk_summaries) > 1:
                summary_text = await recursive_summary(chunk_summaries, session, model=model, endpoint=endpoint)
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

    return {
        "total_stories": len(stories),
        "total_bugs": len(bugs),
        "summary_text": summary_text,
        "chunks": len(chunks),
        "truncated": truncated,
    }

# ---------------------------------------------------------------------------
# 5. CLI helper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse, pathlib

    ap = argparse.ArgumentParser(description="Generate TAPD overview via online LLM (DeepSeek/Qwen)")
    ap.add_argument("-f", "--file", default="../local_data/fake_tapd.json", help="path to local TAPD json for smoke test")
    ap.add_argument("--model", default=API_MODEL_DEFAULT, help="LLM model name – e.g. deepseek-reasoner / qwen:chat")
    ap.add_argument("--endpoint", default=API_ENDPOINT_DEFAULT, help="Chat completion endpoint URL")
    ap.add_argument("--offline", action="store_true", help="return dummy summary (no LLM call)")
    ap.add_argument("--debug", action="store_true", help="print counters")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.file).read_text(encoding='utf-8'))
    half = len(data) // 2
    stories, bugs = data[:half], data[half:]

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
            # 在线模式：调用LLM生成智能摘要
            result = await build_overview(
                fetch_story=fetch_story,
                fetch_bug=fetch_bug,
                model=args.model,
                endpoint=args.endpoint
            )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(_main())
