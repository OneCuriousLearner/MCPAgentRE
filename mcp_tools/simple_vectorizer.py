"""
简化的TAPD向量化工具
优化性能，减少重复加载
"""

import json
import os
import pickle
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path

# 全局模型缓存
_GLOBAL_MODEL_CACHE = None
_GLOBAL_INDEX_CACHE = None
_GLOBAL_METADATA_CACHE = None

def get_project_model_path(model_name: str = "paraphrase-MiniLM-L6-v2") -> Optional[str]:
    """
    获取项目本地模型路径
    
    参数:
        model_name: 模型名称，默认为 "paraphrase-MiniLM-L6-v2"
        
    返回:
        str: 本地模型路径，如果不存在则返回None
    """
    # 获取项目根目录
    current_file = Path(__file__).absolute()
    project_root = current_file.parent.parent
    
    # 构建模型目录路径
    model_dir = project_root / "models" / f"models--sentence-transformers--{model_name}"
    
    if not model_dir.exists():
        print(f"本地模型目录不存在: {model_dir}")
        return None
    
    # 查找快照目录
    snapshots_dir = model_dir / "snapshots"
    if not snapshots_dir.exists():
        print(f"快照目录不存在: {snapshots_dir}")
        return None
    
    # 获取所有快照目录
    snapshot_dirs = list(snapshots_dir.glob("*"))
    if not snapshot_dirs:
        print(f"未找到模型快照: {snapshots_dir}")
        return None
    
    # 选择最新的快照（按修改时间排序）
    latest_snapshot = max(snapshot_dirs, key=lambda d: d.stat().st_mtime)
    print(f"找到本地模型: {latest_snapshot}")
    return str(latest_snapshot)

def get_or_create_model():
    """获取或创建全局模型实例"""
    global _GLOBAL_MODEL_CACHE
    if _GLOBAL_MODEL_CACHE is None:
        print("正在初始化向量化模型...")
        
        # 尝试使用本地模型
        local_model_path = get_project_model_path()
        
        from sentence_transformers import SentenceTransformer
        
        if local_model_path:
            print(f"使用本地模型: {local_model_path}")
            _GLOBAL_MODEL_CACHE = SentenceTransformer(local_model_path)
            print("本地模型加载完成")
        else:
            # 获取项目根目录
            current_file = Path(__file__).absolute()
            project_root = current_file.parent.parent
            models_dir = project_root / "models"
            
            print(f"本地模型不存在，将下载到：{models_dir / 'paraphrase-MiniLM-L6-v2'}")
            print("注意：首次运行需要VPN访问HuggingFace下载模型...")
            
            # 设置缓存目录到项目本地
            os.environ['TRANSFORMERS_CACHE'] = str(models_dir)
            os.environ['HF_HOME'] = str(models_dir)
            
            _GLOBAL_MODEL_CACHE = SentenceTransformer("paraphrase-MiniLM-L6-v2", cache_folder=str(models_dir))
            print(f"模型已下载并保存到：{models_dir / 'paraphrase-MiniLM-L6-v2'}")
        
        print("模型初始化完成")
    return _GLOBAL_MODEL_CACHE

def load_vector_database(vector_db_path: str = "local_data/vector_data/data_vector"):
    """加载向量数据库"""
    global _GLOBAL_INDEX_CACHE, _GLOBAL_METADATA_CACHE
    
    if _GLOBAL_INDEX_CACHE is not None and _GLOBAL_METADATA_CACHE is not None:
        return _GLOBAL_INDEX_CACHE, _GLOBAL_METADATA_CACHE
    
    try:
        import faiss
        
        # 加载索引
        index_path = f"{vector_db_path}.index"
        if not os.path.exists(index_path):
            return None, None
            
        _GLOBAL_INDEX_CACHE = faiss.read_index(index_path)
        
        # 加载元数据
        metadata_path = f"{vector_db_path}.metadata.pkl"
        if not os.path.exists(metadata_path):
            return None, None
            
        with open(metadata_path, 'rb') as f:
            _GLOBAL_METADATA_CACHE = pickle.load(f)
            
        print(f"已加载向量数据库 - 分片数: {len(_GLOBAL_METADATA_CACHE)}, 向量维度: {_GLOBAL_INDEX_CACHE.d}")
        return _GLOBAL_INDEX_CACHE, _GLOBAL_METADATA_CACHE
        
    except Exception as e:
        print(f"加载向量数据库失败: {str(e)}")
        return None, None

async def simple_vectorize_data(chunk_size: int = 10) -> dict:
    """简化的向量化函数"""
    try:
        data_file_path = "local_data/msg_from_fetcher.json"
        
        if not os.path.exists(data_file_path):
            return {
                "status": "error",
                "message": f"数据文件不存在: {data_file_path}"
            }
        
        # 加载模型
        model = get_or_create_model()
        
        # 读取数据
        with open(data_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stories = data.get('stories', [])
        bugs = data.get('bugs', [])
        
        print(f"发现 {len(stories)} 个需求, {len(bugs)} 个缺陷")
        
        # 简化的文本提取
        def extract_text(item, item_type):
            texts = []
            if 'name' in item:
                texts.append(f"标题: {item['name']}")
            elif 'title' in item:
                texts.append(f"标题: {item['title']}")
            if 'status' in item:
                texts.append(f"状态: {item['status']}")
            if 'priority' in item:
                texts.append(f"优先级: {item['priority']}")
            texts.append(f"类型: {item_type}")
            return " | ".join(texts)
        
        # 处理分片
        all_chunks = []
        all_texts = []
        
        # 处理需求
        for i in range(0, len(stories), chunk_size):
            chunk_items = stories[i:i+chunk_size]
            texts = [extract_text(item, "story") for item in chunk_items]
            chunk_text = "\n".join(texts)
            
            all_chunks.append({
                'type': 'story',
                'items': chunk_items,
                'count': len(chunk_items)
            })
            all_texts.append(chunk_text)
        
        # 处理缺陷
        for i in range(0, len(bugs), chunk_size):
            chunk_items = bugs[i:i+chunk_size]
            texts = [extract_text(item, "bug") for item in chunk_items]
            chunk_text = "\n".join(texts)
            
            all_chunks.append({
                'type': 'bug', 
                'items': chunk_items,
                'count': len(chunk_items)
            })
            all_texts.append(chunk_text)
        
        if not all_texts:
            return {
                "status": "error",
                "message": "没有找到可处理的数据"
            }
        
        # 向量化
        print(f"正在向量化 {len(all_texts)} 个文本分片...")
        vectors = model.encode(all_texts, show_progress_bar=True)
        
        # 创建索引
        import faiss
        dimension = vectors.shape[1]
        index = faiss.IndexFlatIP(dimension)
        
        # 标准化并添加向量
        vectors_norm = vectors.astype(np.float32)
        faiss.normalize_L2(vectors_norm)
        index.add(vectors_norm)
        
        # 保存
        vector_db_path = "local_data/vector_data/data_vector"
        os.makedirs(os.path.dirname(vector_db_path), exist_ok=True)
        
        faiss.write_index(index, f"{vector_db_path}.index")
        
        with open(f"{vector_db_path}.metadata.pkl", 'wb') as f:
            pickle.dump(all_chunks, f)
        
        # 更新全局缓存
        global _GLOBAL_INDEX_CACHE, _GLOBAL_METADATA_CACHE
        _GLOBAL_INDEX_CACHE = index
        _GLOBAL_METADATA_CACHE = all_chunks
        
        print(f"向量化完成! 共处理 {len(all_chunks)} 个分片")
        
        return {
            "status": "success",
            "message": "TAPD数据向量化完成",
            "stats": {
                "total_chunks": len(all_chunks),
                "vector_dimension": dimension,
                "total_items": sum(chunk['count'] for chunk in all_chunks)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"向量化失败: {str(e)}"
        }

async def simple_search_data(query: str, top_k: int = 5) -> dict:
    """简化的搜索函数"""
    try:
        print(f"开始搜索: '{query}', top_k={top_k}")
        
        # 加载模型和数据库
        print("正在加载模型...")
        model = get_or_create_model()
        print("模型加载完成")
        
        print("正在加载向量数据库...")
        index, metadata = load_vector_database()
        print(f"向量数据库加载完成，分片数: {len(metadata) if metadata else 0}")
        
        if index is None or metadata is None:
            return {
                "status": "error",
                "message": "向量数据库未找到，请先运行向量化"
            }
        
        # 查询向量化
        print("正在向量化查询文本...")
        query_vector = model.encode([query])
        query_norm = query_vector.astype(np.float32)
        print("查询向量化完成")
        
        import faiss
        faiss.normalize_L2(query_norm)
        print("查询向量归一化完成")
        
        # 搜索
        search_k = min(top_k, len(metadata))
        print(f"开始向量搜索，搜索范围: {search_k}/{len(metadata)}")
        scores, indices = index.search(query_norm, search_k)
        print(f"向量搜索完成，返回 {len(indices[0])} 个结果")
        
        # 格式化结果
        print("正在格式化搜索结果...")
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(metadata) and idx >= 0:  # 添加边界检查
                chunk = metadata[idx]
                # 兼容两种元数据格式
                chunk_type = chunk.get('type') or chunk.get('item_type', 'unknown')
                item_count = chunk.get('count') or chunk.get('item_count', 0)
                items = chunk.get('items') or chunk.get('original_items', [])
                
                # 限制每个结果中的items数量，避免过大的响应
                limited_items = items[:3] if isinstance(items, list) else []
                
                results.append({
                    'relevance_score': float(score),
                    'chunk_type': chunk_type,
                    'item_count': item_count,
                    'items': limited_items
                })
                print(f"处理结果 {i+1}: type={chunk_type}, score={score:.4f}, items={len(limited_items)}")
            else:
                print(f"警告: 无效索引 {idx}, 跳过")
        
        print(f"搜索完成，返回 {len(results)} 个有效结果")
        return {
            "status": "success",
            "message": f"找到 {len(results)} 个相关结果",
            "query": query,
            "results": results
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"搜索过程发生错误: {str(e)}")
        print(f"错误详情: {error_detail}")
        return {
            "status": "error",
            "message": f"搜索失败: {str(e)}",
            "error_detail": error_detail
        }

async def simple_get_db_info() -> dict:
    """获取数据库信息"""
    try:
        index, metadata = load_vector_database()
        
        if index is None or metadata is None:
            return {
                "status": "not_found",
                "message": "向量数据库不存在，请先运行向量化"
            }
        
        story_chunks = sum(1 for chunk in metadata if chunk.get('type') == 'story' or chunk.get('item_type') == 'story')
        bug_chunks = sum(1 for chunk in metadata if chunk.get('type') == 'bug' or chunk.get('item_type') == 'bug')
        
        return {
            "status": "ready",
            "message": "向量数据库已就绪",
            "stats": {
                "total_chunks": len(metadata),
                "vector_dimension": index.d,
                "total_items": sum(chunk.get('count', 0) or chunk.get('item_count', 0) for chunk in metadata),
                "story_chunks": story_chunks,
                "bug_chunks": bug_chunks
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取信息失败: {str(e)}"
        }
