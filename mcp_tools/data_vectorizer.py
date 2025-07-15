"""
TAPD数据向量化工具

该模块实现将TAPD表单数据向量化，以解决大批量数据处理时tokens超限的问题。
使用SentenceTransformers进行文本向量化，FAISS进行向量存储和检索。
"""

import json
import os
import pickle
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss


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


class TAPDDataVectorizer:
    """TAPD数据向量化处理器"""
    
    # 类级别的模型缓存
    _shared_model = None
    _model_name_cache = None
    
    def __init__(self, model_name: str = "paraphrase-MiniLM-L6-v2", vector_db_path: Optional[str] = None):
        """
        初始化向量化器
        
        参数:
            model_name: 使用的预训练模型名称，默认使用轻量级的paraphrase-MiniLM-L6-v2
            vector_db_path: 向量数据库存储路径
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.vector_db_path = vector_db_path or "local_data/vector_data/data_vector"
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        
    @classmethod
    def _get_shared_model(cls, model_name: str) -> SentenceTransformer:
        """获取共享模型实例，避免重复加载"""
        if cls._shared_model is None or cls._model_name_cache != model_name:
            print(f"正在加载向量化模型: {model_name}")
            
            # 尝试使用项目本地模型
            local_model_path = get_project_model_path(model_name)
            
            if local_model_path:
                print(f"使用本地模型: {local_model_path}")
                cls._shared_model = SentenceTransformer(local_model_path)
                print("本地模型加载完成")
            else:
                # 获取项目根目录
                current_file = Path(__file__).absolute()
                project_root = current_file.parent.parent
                models_dir = project_root / "models"
                
                print(f"本地模型不存在，将下载到：{models_dir / model_name}")
                print("注意：首次运行需要VPN访问HuggingFace下载模型...")
                
                # 设置缓存目录到项目本地
                os.environ['TRANSFORMERS_CACHE'] = str(models_dir)
                os.environ['HF_HOME'] = str(models_dir)
                
                cls._shared_model = SentenceTransformer(model_name, cache_folder=str(models_dir))
                print(f"模型已下载并保存到：{models_dir / model_name}")
            
            cls._model_name_cache = model_name
            print("模型加载完成")
        return cls._shared_model
        
    def _ensure_model_loaded(self):
        """确保模型已加载"""
        if self.model is None:
            self.model = self._get_shared_model(self.model_name)
    
    def _extract_text_from_item(self, item: Dict[str, Any], item_type: str) -> str:
        """
        从TAPD数据项中提取关键文本信息
        
        参数:
            item: TAPD数据项（需求或缺陷）
            item_type: 数据类型 ("story" 或 "bug")
            
        返回:
            str: 提取的关键文本信息
        """
        texts = []
        
        # 通用字段
        if 'name' in item:
            texts.append(f"标题: {item['name']}")
        elif 'title' in item:
            texts.append(f"标题: {item['title']}")
            
        if 'status' in item:
            texts.append(f"状态: {item['status']}")
            
        if 'priority' in item:
            texts.append(f"优先级: {item['priority']}")
        
        # 需求特有字段
        if item_type == "story":
            if 'effort' in item:
                texts.append(f"工作量: {item['effort']}")
            if 'progress' in item:
                texts.append(f"进度: {item['progress']}%")
            if 'label' in item:
                texts.append(f"标签: {item['label']}")
                
        # 缺陷特有字段  
        elif item_type == "bug":
            if 'reporter' in item:
                texts.append(f"报告人: {item['reporter']}")
            if 'regression_number' in item:
                texts.append(f"回归次数: {item['regression_number']}")
        
        # 时间信息
        if 'created' in item:
            texts.append(f"创建时间: {item['created']}")
        if 'modified' in item:
            texts.append(f"修改时间: {item['modified']}")
            
        # 将数据类型信息也加入
        texts.append(f"类型: {item_type}")
        texts.append(f"ID: {item.get('id', 'unknown')}")
        
        return " | ".join(texts)
    
    def _chunk_data(self, items: List[Dict[str, Any]], item_type: str, chunk_size: int = 10) -> List[Dict[str, Any]]:
        """
        将数据分片以避免单个文本过长
        
        参数:
            items: 数据项列表
            item_type: 数据类型
            chunk_size: 每个分片的大小
            
        返回:
            List[Dict]: 分片后的数据，每个包含text和metadata
        """
        chunks = []
        
        for i in range(0, len(items), chunk_size):
            chunk_items = items[i:i+chunk_size]
            
            # 提取每个item的文本
            item_texts = []
            item_ids = []
            for item in chunk_items:
                text = self._extract_text_from_item(item, item_type)
                item_texts.append(text)
                item_ids.append(item.get('id', f'{item_type}_{i}'))
            
            # 合并成一个分片
            chunk_text = "\n\n".join(item_texts)
            
            chunk_metadata = {
                'chunk_id': f"{item_type}_chunk_{i//chunk_size}",
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
    
    def process_tapd_data(self, data_file_path: str, chunk_size: int = 10) -> bool:
        """
        处理TAPD数据文件，进行向量化
        
        参数:
            data_file_path: TAPD数据文件路径
            chunk_size: 分片大小，每个分片包含的条目数
            
        返回:
            bool: 处理是否成功
        """
        try:
            # 确保模型已加载
            self._ensure_model_loaded()
            
            # 读取数据
            print(f"正在读取数据文件: {data_file_path}")
            with open(data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取需求和缺陷数据
            stories = data.get('stories', [])
            bugs = data.get('bugs', [])
            
            print(f"发现 {len(stories)} 个需求, {len(bugs)} 个缺陷")
            
            # 分片处理数据
            all_chunks = []
            
            if stories:
                story_chunks = self._chunk_data(stories, "story", chunk_size)
                all_chunks.extend(story_chunks)
                print(f"需求数据分为 {len(story_chunks)} 个分片")
            
            if bugs:
                bug_chunks = self._chunk_data(bugs, "bug", chunk_size)
                all_chunks.extend(bug_chunks)
                print(f"缺陷数据分为 {len(bug_chunks)} 个分片")
            
            if not all_chunks:
                print("警告: 没有找到可处理的数据")
                return False
            
            # 向量化文本
            print(f"正在向量化 {len(all_chunks)} 个文本分片...")
            texts = [chunk['text'] for chunk in all_chunks]
            if self.model is not None:
                vectors = self.model.encode(texts, show_progress_bar=True)
            else:
                raise ValueError("模型未正确加载")
            
            # 创建FAISS索引
            print("正在创建向量索引...")
            dimension = int(vectors.shape[1])
            self.index = faiss.IndexFlatIP(dimension)
            
            # 标准化向量以便使用余弦相似度
            vectors_float32 = vectors.astype(np.float32)
            faiss.normalize_L2(vectors_float32)
            self.index.add(vectors_float32)
            
            # 保存元数据
            self.metadata = [chunk['metadata'] for chunk in all_chunks]
            
            # 保存到文件
            self._save_vector_db()
            
            print(f"向量化完成! 共处理 {len(all_chunks)} 个分片，向量维度: {dimension}")
            return True
            
        except Exception as e:
            print(f"处理数据时发生错误: {str(e)}")
            return False
    
    def _save_vector_db(self):
        """保存向量数据库到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
            
            # 保存FAISS索引
            index_path = f"{self.vector_db_path}.index"
            faiss.write_index(self.index, index_path)
            
            # 保存元数据
            metadata_path = f"{self.vector_db_path}.metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
                
            # 保存配置信息
            config_path = f"{self.vector_db_path}.config.json"
            config = {
                'model_name': self.model_name,
                'chunk_count': len(self.metadata),
                'vector_dimension': self.index.d if self.index else 0,
                'created_at': str(np.datetime64('now'))
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"向量数据库已保存到: {self.vector_db_path}")
            
        except Exception as e:
            print(f"保存向量数据库时发生错误: {str(e)}")
    
    def load_vector_db(self) -> bool:
        """从文件加载向量数据库"""
        try:
            # 加载FAISS索引
            index_path = f"{self.vector_db_path}.index"
            if not os.path.exists(index_path):
                print(f"向量索引文件不存在: {index_path}")
                return False
                
            self.index = faiss.read_index(index_path)
            
            # 加载元数据
            metadata_path = f"{self.vector_db_path}.metadata.pkl"
            if not os.path.exists(metadata_path):
                print(f"元数据文件不存在: {metadata_path}")
                return False
                
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            # 加载配置
            config_path = f"{self.vector_db_path}.config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"已加载向量数据库 - 模型: {config.get('model_name')}, "
                          f"分片数: {config.get('chunk_count')}, "
                          f"向量维度: {config.get('vector_dimension')}")
            
            return True
            
        except Exception as e:
            print(f"加载向量数据库时发生错误: {str(e)}")
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
            
            # 确保模型已加载
            self._ensure_model_loaded()
            
            # 向量化查询
            if self.model is not None:
                query_vector = self.model.encode([query])
                faiss.normalize_L2(query_vector)
            else:
                raise ValueError("模型未正确加载")
            
            # 搜索
            if self.index is not None:
                query_float32 = query_vector.astype(np.float32)
                scores, indices = self.index.search(query_float32, top_k)
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
            print(f"搜索时发生错误: {str(e)}")
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
            print(f"获取统计信息时发生错误: {str(e)}")
            return {}


# 以下是供MCP工具调用的函数

async def vectorize_tapd_data(data_file_path: Optional[str] = None, chunk_size: int = 10) -> dict:
    """
    向量化TAPD数据的主函数
    
    参数:
        data_file_path: 数据文件路径，默认为 local_data/msg_from_fetcher.json
        chunk_size: 分片大小，每个分片包含的条目数
        
    返回:
        处理结果字典
    """
    if data_file_path is None:
        data_file_path = "local_data/msg_from_fetcher.json"
    
    # 使用绝对路径
    if not os.path.isabs(data_file_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_file_path = os.path.join(base_dir, data_file_path)
    
    vectorizer = TAPDDataVectorizer()
    
    if not os.path.exists(data_file_path):
        return {
            "status": "error",
            "message": f"数据文件不存在: {data_file_path}"
        }
    
    success = vectorizer.process_tapd_data(data_file_path, chunk_size)
    
    if success:
        stats = vectorizer.get_database_stats()
        return {
            "status": "success",
            "message": "TAPD数据向量化完成",
            "stats": stats,
            "vector_db_path": vectorizer.vector_db_path
        }
    else:
        return {
            "status": "error",
            "message": "TAPD数据向量化失败"
        }


async def search_tapd_data(query: str, top_k: int = 5) -> dict:
    """
    在向量化的TAPD数据中搜索相关内容
    
    参数:
        query: 搜索查询
        top_k: 返回最相似的K个结果
        
    返回:
        搜索结果字典
    """
    vectorizer = TAPDDataVectorizer()
    
    results = vectorizer.search_similar(query, top_k)
    
    if results:
        # 格式化返回结果
        formatted_results = []
        for result in results:
            metadata = result['metadata']
            formatted_result = {
                'relevance_score': result['score'],
                'chunk_info': {
                    'chunk_id': metadata.get('chunk_id'),
                    'item_type': metadata.get('item_type'),
                    'item_count': metadata.get('item_count'),
                    'item_ids': metadata.get('item_ids', [])
                },
                'items': result['items'][:3]  # 只返回前3个条目以节省空间
            }
            formatted_results.append(formatted_result)
        
        return {
            "status": "success",
            "message": f"找到 {len(results)} 个相关结果",
            "query": query,
            "results": formatted_results
        }
    else:
        return {
            "status": "error",
            "message": "搜索失败或未找到相关结果"
        }


async def get_vector_db_info() -> dict:
    """
    获取向量数据库信息
    
    返回:
        数据库信息字典
    """
    vectorizer = TAPDDataVectorizer()
    
    # 检查数据库是否存在
    index_path = f"{vectorizer.vector_db_path}.index"
    if not os.path.exists(index_path):
        return {
            "status": "not_found",
            "message": "向量数据库不存在，请先运行向量化操作"
        }
    
    stats = vectorizer.get_database_stats()
    
    if stats:
        return {
            "status": "ready",
            "message": "向量数据库已就绪",
            "stats": stats,
            "database_path": vectorizer.vector_db_path
        }
    else:
        return {
            "status": "error",
            "message": "无法获取数据库信息"
        }
