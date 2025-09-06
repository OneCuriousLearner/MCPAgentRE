"""
Vectorization worker process

Purpose:
- Run TAPD vectorization in an isolated subprocess so any library prints/logs
  cannot pollute the MCP server's stdio channel.
- Outputs a single JSON line to stdout on completion.

Usage:
  python -m mcp_tools.vec_worker --file local_data/msg_from_fetcher.json --chunk 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys


async def _run(data_file_path: str, chunk_size: int, preserve_existing: bool) -> int:
    # Import here to avoid importing heavy libs when not needed.
    try:
        from .data_vectorizer import vectorize_tapd_data  # type: ignore
    except Exception:
        # Fallback for direct execution context
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from mcp_tools.data_vectorizer import vectorize_tapd_data  # type: ignore

    try:
        res = await vectorize_tapd_data(data_file_path, chunk_size, remove_existing=(not preserve_existing))
        # Ensure dict
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except Exception:
                res = {"status": "error", "message": "Invalid payload from vectorize_tapd_data"}

        # Print a single JSON blob to stdout
        print(json.dumps(res, ensure_ascii=False))
        return 0
    except Exception as e:
        err = {"status": "error", "message": f"Worker exception: {e}"}
        print(json.dumps(err, ensure_ascii=False))
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="TAPD Vectorization Worker")
    parser.add_argument("--file", dest="data_file_path", default="local_data/msg_from_fetcher.json")
    parser.add_argument("--chunk", dest="chunk_size", type=int, default=10)
    parser.add_argument("--preserve-existing", action="store_true", help="保留已有向量库文件（默认会删除后重建）")
    args = parser.parse_args()

    try:
        return asyncio.run(_run(args.data_file_path, args.chunk_size, getattr(args, "preserve_existing", False)))
    except RuntimeError:
        # Fallback for environments with an active event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run(args.data_file_path, args.chunk_size, getattr(args, "preserve_existing", False)))


if __name__ == "__main__":
    sys.exit(main())
