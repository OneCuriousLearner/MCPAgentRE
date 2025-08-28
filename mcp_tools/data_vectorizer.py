"""
TAPD数据向量化工具

该模块实现将TAPD表单数据向量化，以解决大批量数据处理时tokens超限的问题。
使用SentenceTransformers进行文本向量化，FAISS进行向量存储和检索。

优化版本特性：
- 统一的配置管理
- 优化的模型缓存机制
- 标准化的元数据格式
- 改进的错误处理
"""

import json
import os
import pickle
import sys
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from contextlib import redirect_stdout

# 兼容作为脚本直接运行与作为包导入两种场景
try:
    from .common_utils import (
        get_config,
        get_model_manager,
        get_file_manager,
        TextProcessor,
    )
except ImportError:
    # 直接运行脚本（uv run mcp_tools\data_vectorizer.py）时，退回到绝对导入
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_tools.common_utils import (  # type: ignore
        get_config,
        get_model_manager,
        get_file_manager,
        TextProcessor,
    )


class TAPDDataVectorizer:
    """TAPD数据向量化处理器 - 优化版"""
    
    def __init__(self, model_name: str = "paraphrase-MiniLM-L6-v2", vector_db_path: Optional[str] = None):
        """
        初始化向量化器
        
        参数:
            model_name: 使用的预训练模型名称，默认使用轻量级的paraphrase-MiniLM-L6-v2
            vector_db_path: 向量数据库存储路径
        """
        self.config = get_config()
        self.model_manager = get_model_manager()
        self.file_manager = get_file_manager()
        self.text_processor = TextProcessor()
        
        self.model_name = model_name
        self.vector_db_path = vector_db_path or self.config.get_vector_db_path()
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        self._last_error: Optional[str] = None

    # Lightweight logging (timestamped; flush immediately to Inspector notifications)
    def _log(self, msg: str) -> None:
        print(f"[Vectorizer {datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)

    # --- FAISS 兼容性封装：适配不同Python封装签名 ---
    def _faiss_add(self, x: np.ndarray) -> None:
        """兼容不同 add 接口：优先使用 add(x)，失败时回退 add(n, x)"""
        try:
            self.index.add(x)  # type: ignore[arg-type]
        except TypeError:
            n = int(x.shape[0])
            self.index.add(n, x)  # type: ignore[misc]

    def _faiss_search(self, x: np.ndarray, k: int):
        """兼容不同 search 接口：优先使用 search(x, k)，失败时回退 search(n, x, k, distances, labels)"""
        try:
            return self.index.search(x, k)  # type: ignore[call-arg]
        except TypeError:
            n = int(x.shape[0])
            distances = np.empty((n, k), dtype=np.float32)
            labels = np.empty((n, k), dtype=np.int64)
            self.index.search(n, x, k, distances, labels)  # type: ignore[misc]
            return distances, labels
        
    def _get_model(self):
        """获取模型实例"""
        return self.model_manager.get_model(self.model_name)
    
    async def _get_model_async(self):
        """异步获取模型实例"""
        return await self.model_manager.get_model_async(self.model_name)

    def _encode_texts_with_progress(self, model, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """分批进行编码，输出进度日志，避免长时间无输出。"""
        n = len(texts)
        if n == 0:
            return np.zeros((0, 384), dtype=np.float32)  # 维度将被实际模型覆盖，这里仅占位
        vecs: List[np.ndarray] = []
        start = time.perf_counter()
        for i in range(0, n, batch_size):
            batch = texts[i:i+batch_size]
            t0 = time.perf_counter()
            v = model.encode(batch, show_progress_bar=False)
            dt = time.perf_counter() - t0
            self._log(f"Encoding progress {min(i+len(batch), n)}/{n}, batch elapsed {dt:.2f}s")
            vecs.append(v)
        total_dt = time.perf_counter() - start
        self._log(f"Encoding completed, total {total_dt:.2f}s")
        return np.vstack(vecs)
    
    def _chunk_data(self, items: List[Dict[str, Any]], item_type: str, chunk_size: int) -> List[Dict[str, Any]]:
        """
        将数据分片处理
        
        参数:
            items: 数据项列表
            item_type: 数据类型 ("story" 或 "bug")
            chunk_size: 分片大小
            
        返回:
            List[Dict]: 分片后的数据，每个分片包含文本和元数据
        """
        chunks = []
        
        for i in range(0, len(items), chunk_size):
            chunk_items = items[i:i+chunk_size]
            
            # 提取文本
            chunk_texts = []
            item_ids = []
            
            for item in chunk_items:
                text = self.text_processor.extract_text_from_item(item, item_type)
                chunk_texts.append(text)
                
                # 获取ID（兼容不同的ID字段）
                item_id = item.get('id') or item.get('story_id') or item.get('bug_id') or str(i)
                item_ids.append(item_id)
            
            # 合并文本
            chunk_text = " | ".join(chunk_texts)
            
            # 生成唯一chunk_id
            chunk_id = f"{item_type}_{i//chunk_size}_{hash(chunk_text) % 10000}"
            
            # 元数据
            chunk_metadata = {
                'chunk_id': chunk_id,
                'item_type': item_type,
                'item_ids': item_ids,
                'item_count': len(chunk_items),
                'chunk_index': i//chunk_size,
                'original_items': chunk_items  # 保存原始数据
            }
            
            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })
            
        return chunks
    
    def process_tapd_data(self, data_file_path: Optional[str] = None, chunk_size: int = 10) -> bool:
        """
        处理TAPD数据文件，进行向量化
        
        参数:
            data_file_path: TAPD数据文件路径
            chunk_size: 分片大小，每个分片包含的条目数
            
        返回:
            bool: 处理是否成功
        """
        try:
            # Read data (resolve path from project root; default to local_data/msg_from_fetcher.json)
            project_root = self.config._get_project_root()  # 项目根目录
            effective_path = data_file_path if (data_file_path and str(data_file_path).strip()) else os.path.join("local_data", "msg_from_fetcher.json")

            # 相对路径按“项目根目录”为基准进行解析
            if not os.path.isabs(effective_path):
                effective_path = os.path.join(project_root, effective_path.lstrip("\\/"))

            if not os.path.exists(effective_path):
                # Raise with a clear hint for MCP error propagation
                raise FileNotFoundError(f"Data file not found: {effective_path}")
            self._log(f"Start vectorization, data file: {effective_path}")
            if chunk_size <= 0:
                self._log(f"Warning: invalid chunk_size {chunk_size}, fallback to 10")
                chunk_size = 10
            # Read JSON by absolute path; avoid any special local_data-relative logic
            t0 = time.perf_counter()
            data = self.file_manager.load_json_data(effective_path)
            self._log(f"Data file loaded in {(time.perf_counter()-t0):.2f}s")
            
            # 提取需求和缺陷数据
            stories = data.get('stories', [])
            bugs = data.get('bugs', [])
            
            self._log(f"Found {len(stories)} stories, {len(bugs)} bugs")
            
            # 分片处理数据
            all_chunks = []
            
            if stories:
                story_chunks = self._chunk_data(stories, "story", chunk_size)
                all_chunks.extend(story_chunks)
                self._log(f"Stories split into {len(story_chunks)} chunks")
            
            if bugs:
                bug_chunks = self._chunk_data(bugs, "bug", chunk_size)
                all_chunks.extend(bug_chunks)
                self._log(f"Bugs split into {len(bug_chunks)} chunks")
            
            if not all_chunks:
                self._log("Warning: no data to process")
                self._last_error = "No stories or bugs in data"
                return False
            
            # 向量化文本
            self._log(f"Vectorizing {len(all_chunks)} text chunks...")
            texts = [chunk['text'] for chunk in all_chunks]
            
            t0 = time.perf_counter()
            self._log("Loading model...")
            # 直接获取模型，依赖日志降噪配置避免第三方库写入 stdout
            model = self._get_model()
            self._log(f"Model ready in {(time.perf_counter()-t0):.2f}s")
            # 分批编码，输出进度
            vectors = self._encode_texts_with_progress(model, texts, batch_size=max(16, min(128, len(texts))))
            
            # 创建FAISS索引
            self._log("Building vector index...")
            dimension = int(vectors.shape[1])
            self.index = faiss.IndexFlatIP(dimension)
            
            # 标准化向量以便使用余弦相似度
            t0 = time.perf_counter()
            vectors_float32 = vectors.astype(np.float32)
            faiss.normalize_L2(vectors_float32)
            # 兼容不同签名
            self._faiss_add(vectors_float32)
            self._log(f"Index built in {(time.perf_counter()-t0):.2f}s")
            
            # 保存元数据
            self.metadata = [chunk['metadata'] for chunk in all_chunks]
            
            # 保存到文件
            t0 = time.perf_counter()
            self._save_vector_db()
            self._log(f"Vector DB saved in {(time.perf_counter()-t0):.2f}s")
            
            self._log(f"Vectorization done! processed {len(all_chunks)} chunks, dim: {dimension}")
            return True
            
        except Exception as e:
            self._log(f"Error during processing: {str(e)}")
            # 记录错误并让调用方感知失败原因
            self._last_error = str(e)
            return False
    
    def _save_vector_db(self):
        """保存向量数据库到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
            
            # 保存FAISS索引
            index_path = f"{self.vector_db_path}.index"
            faiss.write_index(self.index, index_path)
            
            # 保存元数据 (向量数据和元数据仍需要特殊处理，因为FileManager没有支持pickle和faiss格式)
            metadata_path = f"{self.vector_db_path}.metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
                
            # 保存配置信息 - 使用统一的FileManager
            config_path = f"{self.vector_db_path}.config.json"
            config = {
                'model_name': self.model_name,
                'chunk_count': len(self.metadata),
                'vector_dimension': self.index.d if self.index else 0,
                'created_at': str(np.datetime64('now'))
            }
            self.file_manager.save_json_data(config, config_path)
            
            self._log(f"Vector DB saved to: {self.vector_db_path}")
            
        except Exception as e:
            self._log(f"Error saving vector DB: {str(e)}")
    
    def load_vector_db(self) -> bool:
        """从文件加载向量数据库"""
        try:
            # 加载FAISS索引
            index_path = f"{self.vector_db_path}.index"
            if not os.path.exists(index_path):
                self._log(f"Vector index file not found: {index_path}")
                return False
                
            self.index = faiss.read_index(index_path)
            
            # 加载元数据
            metadata_path = f"{self.vector_db_path}.metadata.pkl"
            if not os.path.exists(metadata_path):
                self._log(f"Metadata file not found: {metadata_path}")
                return False
                
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            # 加载配置 - 使用统一的FileManager
            config_path = f"{self.vector_db_path}.config.json"
            if os.path.exists(config_path):
                try:
                    config = self.file_manager.load_json_data(config_path)
                    self._log(f"Vector DB loaded - model: {config.get('model_name')}, chunks: {config.get('chunk_count')}, dim: {config.get('vector_dimension')}")
                except Exception as e:
                    self._log(f"Failed to read config: {str(e)}")
            
            return True
            
        except Exception as e:
            self._log(f"Error loading vector DB: {str(e)}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索与查询最相似的数据片段
        
        参数:
            query: 查询文本
            top_k: 返回最相似的K个结果
            
        返回:
            List[Dict]: 相似结果列表，包含分数和元数据
        """
        try:
            if self.index is None:
                if not self.load_vector_db():
                    return []
            
            # 向量化查询（保持与Faiss接口的数据类型一致）
            model = self._get_model()
            query_vector = model.encode([query]).astype(np.float32)
            faiss.normalize_L2(query_vector)
            
            # 搜索
            if self.index is not None:
                query_float32 = query_vector.astype(np.float32)
                # 兼容不同签名
                scores, indices = self._faiss_search(query_float32, top_k)
            else:
                raise ValueError("索引未正确加载")
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.metadata):
                    result = {
                        'score': float(score),
                        'metadata': self.metadata[idx],
                        'items': self.metadata[idx].get('original_items', [])
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            self._log(f"Error during search: {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            if self.index is None:
                if not self.load_vector_db():
                    return {}
            
            stats = {
                'total_chunks': len(self.metadata),
                'vector_dimension': self.index.d if self.index is not None else 0,
                'total_items': sum(meta.get('item_count', 0) for meta in self.metadata),
                'story_chunks': sum(1 for meta in self.metadata if meta.get('item_type') == 'story'),
                'bug_chunks': sum(1 for meta in self.metadata if meta.get('item_type') == 'bug'),
            }
            
            return stats
            
        except Exception as e:
            self._log(f"Error getting stats: {str(e)}")
            return {}

    async def process_tapd_data_async(self, data_file_path: Optional[str] = None, chunk_size: int = 10) -> bool:
        """
        异步处理TAPD数据文件，进行向量化
        
        参数:
            data_file_path: TAPD数据文件路径
            chunk_size: 分片大小，每个分片包含的条目数
            
        返回:
            bool: 处理是否成功
        """
        try:
            # Read data (resolve path from project root; default to local_data/msg_from_fetcher.json)
            project_root = self.config._get_project_root()  # 项目根目录
            effective_path = data_file_path if (data_file_path and str(data_file_path).strip()) else os.path.join("local_data", "msg_from_fetcher.json")

            # 相对路径按"项目根目录"为基准进行解析
            if not os.path.isabs(effective_path):
                effective_path = os.path.join(project_root, effective_path.lstrip("\\/"))

            if not os.path.exists(effective_path):
                # Raise with a clear hint for MCP error propagation
                raise FileNotFoundError(f"Data file not found: {effective_path}")
            self._log(f"Start async vectorization, data file: {effective_path}")
            if chunk_size <= 0:
                self._log(f"Warning: invalid chunk_size {chunk_size}, fallback to 10")
                chunk_size = 10
            # Read JSON by absolute path; avoid any special local_data-relative logic
            t0 = time.perf_counter()
            data = self.file_manager.load_json_data(effective_path)
            self._log(f"Data file loaded in {(time.perf_counter()-t0):.2f}s")
            
            # 提取需求和缺陷数据
            stories = data.get('stories', [])
            bugs = data.get('bugs', [])
            
            self._log(f"Found {len(stories)} stories, {len(bugs)} bugs")
            
            # 分片处理数据
            all_chunks = []
            
            if stories:
                story_chunks = self._chunk_data(stories, "story", chunk_size)
                all_chunks.extend(story_chunks)
                self._log(f"Stories split into {len(story_chunks)} chunks")
            
            if bugs:
                bug_chunks = self._chunk_data(bugs, "bug", chunk_size)
                all_chunks.extend(bug_chunks)
                self._log(f"Bugs split into {len(bug_chunks)} chunks")
            
            if not all_chunks:
                self._log("Warning: no data to process")
                self._last_error = "No stories or bugs in data"
                return False
            
            # 向量化文本
            self._log(f"Vectorizing {len(all_chunks)} text chunks...")
            texts = [chunk['text'] for chunk in all_chunks]
            
            t0 = time.perf_counter()
            self._log("Loading model asynchronously...")
            # 异步获取模型，避免阻塞事件循环
            model = await self._get_model_async()
            self._log(f"Model ready in {(time.perf_counter()-t0):.2f}s")
            # 分批编码，输出进度 - 需要在线程池中执行，因为编码是CPU密集型任务
            vectors = await asyncio.to_thread(
                self._encode_texts_with_progress, 
                model, 
                texts, 
                max(16, min(128, len(texts)))
            )
            
            # 创建FAISS索引 - 也需要在线程池中执行
            self._log("Building vector index...")
            dimension = int(vectors.shape[1])
            self.index = faiss.IndexFlatIP(dimension)
            
            # 标准化向量以便使用余弦相似度
            t0 = time.perf_counter()
            vectors_float32 = vectors.astype(np.float32)
            faiss.normalize_L2(vectors_float32)
            # 兼容不同签名
            self._faiss_add(vectors_float32)
            self._log(f"Index built in {(time.perf_counter()-t0):.2f}s")
            
            # 保存元数据
            self.metadata = [chunk['metadata'] for chunk in all_chunks]
            
            # 保存到文件 - 在线程池中执行I/O操作
            t0 = time.perf_counter()
            await asyncio.to_thread(self._save_vector_db)
            self._log(f"Vector DB saved in {(time.perf_counter()-t0):.2f}s")
            
            self._log(f"Async vectorization done! processed {len(all_chunks)} chunks, dim: {dimension}")
            return True
            
        except Exception as e:
            self._log(f"Error during async processing: {str(e)}")
            # 记录错误并让调用方感知失败原因
            self._last_error = str(e)
            return False


# 以下是供MCP工具调用的函数

async def vectorize_tapd_data(data_file_path: Optional[str] = None, chunk_size: int = 10) -> dict:
    """
    Main function to vectorize TAPD data
    
    参数:
        data_file_path: 数据文件路径，默认为 local_data/msg_from_fetcher.json
        chunk_size: 分片大小，每个分片包含的条目数
        
    返回:
    Result dict
    """
    vectorizer = get_global_vectorizer()
    
    try:
        overall_t0 = time.perf_counter()
        
        # 优先使用异步版本，避免阻塞事件循环
        try:
            success = await vectorizer.process_tapd_data_async(data_file_path, chunk_size)
        except AttributeError:
            # 如果异步版本不存在，回退到线程池版本
            success = await asyncio.to_thread(vectorizer.process_tapd_data, data_file_path, chunk_size)
        
        if success:
            stats = vectorizer.get_database_stats()
            return {
                "status": "success",
                "message": "Vectorization completed",
                "stats": stats,
                "vector_db_path": vectorizer.vector_db_path,
                "data_file_path": data_file_path or "local_data/msg_from_fetcher.json",
                "elapsed_seconds": round(time.perf_counter() - overall_t0, 2)
            }
        else:
            # 优先返回内部记录的错误信息
            detail = getattr(vectorizer, "_last_error", "Unknown error")
            return {
                "status": "error",
                "message": "Vectorization failed",
                "details": str(detail),
                "data_file_path": data_file_path or "local_data/msg_from_fetcher.json",
                "elapsed_seconds": round(time.perf_counter() - overall_t0, 2)
            }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "message": f"Data file not found: {str(e)}",
            "data_file_path": data_file_path or "local_data/msg_from_fetcher.json"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during vectorization: {str(e)}",
            "data_file_path": data_file_path or "local_data/msg_from_fetcher.json"
        }


async def search_tapd_data(query: str, top_k: int = 5) -> dict:
    """
    Search related content in vectorized TAPD data
    
    参数:
        query: 搜索查询
        top_k: 返回最相似的K个结果
        
    返回:
    Result dict
    """
    vectorizer = get_global_vectorizer()

    try:
        # 轻量防御：空查询直接返回
        if not query or not str(query).strip():
            return {
                "status": "error",
                "message": "Query is empty"
            }

        # 限制每批返回的条目数（items per batch），避免过大带来IO与序列化开销
        items_per_batch = max(1, min(int(top_k), 50))

        # 固定返回相似度最高的前两批（即前2个分片/组）
        group_count = 2
        top_chunks = vectorizer.search_similar(query, group_count)

        if top_chunks:
            formatted_results = []
            for rank, chunk in enumerate(top_chunks, start=1):
                metadata = chunk['metadata']
                # 从该分片的原始条目中取前 items_per_batch 条
                # 目前按原顺序截取，如需更精准可在未来加入条目级向量或关键词打分
                items = (chunk.get('items') or [])[:items_per_batch]

                formatted_results.append({
                    'batch_rank': rank,
                    'relevance_score': float(chunk['score']),
                    'chunk_info': {
                        'chunk_id': metadata.get('chunk_id'),
                        'item_type': metadata.get('item_type'),
                        'item_count': metadata.get('item_count'),
                        'item_ids': metadata.get('item_ids', [])
                    },
                    'items': items
                })

            return {
                "status": "success",
                "message": f"Returned top {len(formatted_results)} batches, {items_per_batch} items per batch",
                "query": query,
                "batches": len(formatted_results),
                "items_per_batch": items_per_batch,
                "results": formatted_results
            }
        else:
            return {
                "status": "error",
                "message": "Search failed or no results found"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during search: {str(e)}"
        }


async def get_vector_db_info() -> dict:
    """
    Get vector database info
    
    返回:
    Database info dict
    """
    vectorizer = get_global_vectorizer()
    
    try:
        # 检查数据库是否存在
        index_path = f"{vectorizer.vector_db_path}.index"
        if not os.path.exists(index_path):
            return {
                "status": "not_found",
                "message": "Vector DB not found; run vectorization first"
            }
        
        stats = vectorizer.get_database_stats()
        
        if stats:
            return {
                "status": "ready",
                "message": "Vector DB is ready",
                "stats": stats,
                "database_path": vectorizer.vector_db_path
            }
        else:
            return {
                "status": "error",
                "message": "Unable to get database info"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get vector DB info: {str(e)}"
        }


# --- 模块级单例，避免每次MCP调用重复加载模型/索引 ---
_GLOBAL_VECTORIZER: Optional[TAPDDataVectorizer] = None

def get_global_vectorizer() -> TAPDDataVectorizer:
    global _GLOBAL_VECTORIZER
    if _GLOBAL_VECTORIZER is None:
        _GLOBAL_VECTORIZER = TAPDDataVectorizer()
        # 不在导入时预加载索引，避免 MCP 启动时的潜在问题
        # _GLOBAL_VECTORIZER.load_vector_db()
    return _GLOBAL_VECTORIZER


# 轻量级 CLI，便于直接通过命令行进行快速测试/使用
if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="TAPD 数据向量化工具 (CLI)")
    subparsers = parser.add_subparsers(dest="command")

    # info 子命令：查看向量库状态
    subparsers.add_parser("info", help="查看向量数据库状态与统计信息")

    # vectorize 子命令：执行向量化
    p_vec = subparsers.add_parser("vectorize", help="执行TAPD数据向量化")
    p_vec.add_argument("--file", "-f", dest="data_file_path", default="local_data/msg_from_fetcher.json", help="数据文件路径，默认使用 local_data/msg_from_fetcher.json（相对路径按项目根目录解析）")
    p_vec.add_argument("--chunk", "-c", dest="chunk_size", type=int, default=10, help="分片大小，默认10")

    # search 子命令：语义搜索
    p_search = subparsers.add_parser("search", help="在向量库中进行语义搜索")
    p_search.add_argument("--query", "-q", required=True, help="自然语言查询")
    p_search.add_argument("--topk", "-k", type=int, default=5, help="返回TopK，默认5")

    args = parser.parse_args()

    async def _main():
        if args.command == "vectorize":
            res = await vectorize_tapd_data(data_file_path=args.data_file_path, chunk_size=args.chunk_size)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif args.command == "search":
            res = await search_tapd_data(query=args.query, top_k=args.topk)
            print(json.dumps(res, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            # 默认展示 info
            res = await get_vector_db_info()
            print(json.dumps(res, ensure_ascii=False, indent=2), file=sys.stderr)

    try:
        asyncio.run(_main())
    except RuntimeError:
        # 某些环境已存在事件循环（如在交互式环境），采用新循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_main())