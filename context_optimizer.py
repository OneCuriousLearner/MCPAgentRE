from __future__ import annotations

import asyncio, json, os, sys
from typing import List, Dict, AsyncIterable, Callable, Awaitable

import aiohttp
import tiktoken

# ---------------------------------------------------------------------------
# token helper – use cl100k_base tokenizer (open‑sourced; no GPT key required)
# ---------------------------------------------------------------------------
ENC = tiktoken.get_encoding("cl100k_base")

def tokens(text: str) -> int:
    """Return approximate token count for a UTF‑8 string."""
    return len(ENC.encode(text))

# ---------------------------------------------------------------------------
# 1. Paginated item fetcher
# ---------------------------------------------------------------------------
async def iter_items(fetch_fn: Callable[..., Awaitable[List[Dict]]], *, page_size: int = 200, **params) -> AsyncIterable[Dict]:
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

def chunkify(items: List[Dict], max_tokens: int = 1000) -> List[List[Dict]]:
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
    global _HEADERS_CACHE
    if _HEADERS_CACHE is None:
        if not API_KEY:
            raise RuntimeError("No API key provided – set DS_KEY (or compatible)!")
        _HEADERS_CACHE = {"Authorization": f"Bearer {API_KEY}"}
    return _HEADERS_CACHE


async def call_llm(prompt: str, session: aiohttp.ClientSession, *, model: str, endpoint: str, max_tokens: int = 60) -> str:
    """Single completion call. 兼容 DeepSeek‑Reasoner 的 `reasoning_content` 字段。"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    async with session.post(f"{endpoint}/chat/completions", json=payload, headers=build_headers(), timeout=60) as resp:
        js = await resp.json()

    msg = js["choices"][0]["message"]
    # DeepSeek‑Reasoner 把推理和最终回答分开；如果 content 为空则回退到 reasoning_content。
    text = (msg.get("content") or msg.get("reasoning_content") or "").strip()
    for sep in ('。', '\n'):
        if sep in text:
            text = text.split(sep, 1)[0] + '。'
            break
    if not text:
        raise RuntimeError("LLM 返回空字符串，可能是 URL / KEY / model 配置问题。响应片段: " + str(js)[:400])
    return text


async def summarize_chunk(chunk: List[Dict], session: aiohttp.ClientSession, *, model: str, endpoint: str) -> str:
    titles = "\n".join(it.get("title", "") for it in chunk[:50])
    prompt = f"请用一句中文概括以下缺陷/需求的主要主题：\n{titles}\n### 答案："
    return await call_llm(prompt, session, model=model, endpoint=endpoint, max_tokens=500)


async def recursive_summary(sentences: List[str], session: aiohttp.ClientSession, *, model: str, endpoint: str) -> str:
    if len(sentences) == 1:
        return sentences[0]
    merged_prompt = "请将下列多句摘要再压缩成一句中文：\n" + "\n".join(sentences) + "\n### 答案："
    return await call_llm(merged_prompt, session, model=model, endpoint=endpoint, max_tokens=500)

# ---------------------------------------------------------------------------
# 4. build_overview
# ---------------------------------------------------------------------------

async def build_overview(
    fetch_story: Callable[..., Awaitable[List[Dict]]],
    fetch_bug:   Callable[..., Awaitable[List[Dict]]],
    since: str,
    until: str,
    *,
    max_total_tokens: int = 6000,
    model: str = API_MODEL_DEFAULT,
    endpoint: str = API_ENDPOINT_DEFAULT,
) -> Dict:
    stories, bugs = [], []
    async for s in iter_items(fetch_story, created_after=since, created_before=until):
        stories.append(s)
    async for b in iter_items(fetch_bug, created_after=since, created_before=until):
        bugs.append(b)

    async with aiohttp.ClientSession() as session:
        chunks = chunkify(stories + bugs, 1000)
        summaries = [await summarize_chunk(ck, session, model=model, endpoint=endpoint) for ck in chunks]
        summary_text = await recursive_summary(summaries, session, model=model, endpoint=endpoint)

    if tokens(summary_text) > max_total_tokens:
        summary_text = summary_text[:max_total_tokens]
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
    ap.add_argument("-f", "--file", default="fake_tapd.json", help="path to local TAPD json for smoke test")
    ap.add_argument("--model", default=API_MODEL_DEFAULT, help="LLM model name – e.g. deepseek-reasoner / qwen:chat")
    ap.add_argument("--endpoint", default=API_ENDPOINT_DEFAULT, help="Chat completion endpoint URL")
    ap.add_argument("--offline", action="store_true", help="return dummy summary (no LLM call)")
    ap.add_argument("--debug", action="store_true", help="print counters")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.file).read_text())
    half = len(data) // 2
    stories, bugs = data[:half], data[half:]

    async def fetch_story(*, page: int = 1, limit: int = 200, **_):
        start, end = (page - 1) * limit, page * limit
        return stories[start:end]

    async def fetch_bug(*, page: int = 1, limit: int = 200, **_):
        start, end = (page - 1) * limit, page * limit
        return bugs[start:end]

    if args.offline:
        async def summarize_chunk(chunk, session, **kw):
            return "dummy summary"
        globals()["summarize_chunk"] = summarize_chunk

    async def _main():
        ov = await build_overview(fetch_story, fetch_bug, "2025-01-01", "2025-12-31", model=args.model, endpoint=args.endpoint)
        if args.debug:
            print(f"> stories={len(stories)} bugs={len(bugs)} chunks={ov['chunks']}", file=sys.stderr)
        print(json.dumps(ov, ensure_ascii=False, indent=2))

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(_main())
