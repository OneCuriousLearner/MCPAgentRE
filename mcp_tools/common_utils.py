"""
MCP工具公共工具模块

提供所有MCP工具共用的基础功能和配置管理
"""

import os
import json
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List
from sentence_transformers import SentenceTransformer


class MCPToolsConfig:
    """MCP工具配置管理器"""
    
    def __init__(self):
        self.project_root = self._get_project_root()
        self.local_data_path = self.project_root / "local_data"
        self.models_path = self.project_root / "models"
        self.vector_data_path = self.local_data_path / "vector_data"
        
        # 确保目录存在
        self.local_data_path.mkdir(exist_ok=True)
        self.models_path.mkdir(exist_ok=True)
        self.vector_data_path.mkdir(exist_ok=True)
    
    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        current_file = Path(__file__).absolute()
        return current_file.parent.parent
    
    def get_data_file_path(self, relative_path: str = "msg_from_fetcher.json") -> str:
        """
        获取数据文件的绝对路径
        
        参数:
            relative_path: 相对路径，如果以 'local_data/' 开头，则直接使用；
                          否则假设是相对于 local_data 目录的路径
        """
        if relative_path.startswith('local_data/'):
            # 相对于项目根目录的路径
            return str(self.project_root / relative_path)
        else:
            # 相对于 local_data 目录的路径
            return str(self.local_data_path / relative_path)
    
    def get_vector_db_path(self, name: str = "data_vector") -> str:
        """获取向量数据库路径"""
        return str(self.vector_data_path / name)
    
    def get_model_cache_path(self) -> str:
        """获取模型缓存路径"""
        return str(self.models_path)


class APIManager:
    """API调用管理器 - 统一的LLM API调用功能"""
    
    def __init__(self):
        self.endpoint = os.getenv("DS_EP", "https://api.deepseek.com/v1")
        self.model = os.getenv("DS_MODEL", "deepseek-chat")  # 默认使用deepseek-chat
        self.api_key = os.getenv("DS_KEY")
        self._headers_cache: Optional[Dict[str, str]] = None
    
    def get_headers(self) -> Dict[str, str]:
        """构建API请求头，检查API密钥是否已设置"""
        if self._headers_cache is None:
            if not self.api_key:
                raise RuntimeError("No API key provided – set DS_KEY environment variable!")
            self._headers_cache = {"Authorization": f"Bearer {self.api_key}"}
        return self._headers_cache
    
    async def call_llm(self, prompt: str, session: aiohttp.ClientSession, 
                      model: Optional[str] = None, endpoint: Optional[str] = None, 
                      max_tokens: int = 60) -> str:
        """调用在线LLM API，支持DeepSeek‑Reasoner的reasoning_content字段"""
        try:
            headers = self.get_headers()  # 检查API密钥
        except RuntimeError as e:
            # 抛出更具体的错误信息
            raise RuntimeError(f"API配置错误: {str(e)}\n请设置环境变量 DS_KEY 为您的DeepSeek API密钥") from e
        
        use_model = model or self.model
        use_endpoint = endpoint or self.endpoint
        
        payload = {
            "model": use_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        
        try:
            async with session.post(f"{use_endpoint}/chat/completions", json=payload, headers=headers, timeout=240) as resp:
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
            
            # 仅在使用deepseek-reasoner模型时才获取思考过程
            if use_model == "deepseek-reasoner":
                # DeepSeek-Reasoner 把推理和最终回答分开
                content = msg.get("content", "").strip()
                reasoning_content = msg.get("reasoning_content", "").strip()
                
                # 默认只返回最终回答content，不追加思考过程
                text = content
                
                # 如果最终回答为空，则使用思考内容作为备选
                if not text and reasoning_content:
                    text = reasoning_content
            else:
                # 对于其他模型（如deepseek-chat），直接获取content
                text = msg.get("content", "").strip()
            
            # 对于摘要生成等长文本任务，保留完整内容
            # 只有在max_tokens较小时（<100）才进行截断处理
            if max_tokens < 100:
                # 简单处理，截取到第一个句号或换行符
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


class ModelManager:
    """模型管理器 - 统一的模型加载和缓存管理"""
    
    _shared_model: Optional[SentenceTransformer] = None
    _model_name_cache: Optional[str] = None
    
    def __init__(self, config: MCPToolsConfig):
        self.config = config
    
    def get_project_model_path(self, model_name: str = "paraphrase-MiniLM-L6-v2") -> Optional[str]:
        """
        获取项目本地模型路径
        
        参数:
            model_name: 模型名称，默认为 "paraphrase-MiniLM-L6-v2"
            
        返回:
            str: 本地模型路径，如果不存在则返回None
        """
        # 构建模型目录路径
        model_dir = self.config.models_path / f"models--sentence-transformers--{model_name}"
        
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
    
    def get_model(self, model_name: str = "paraphrase-MiniLM-L6-v2") -> SentenceTransformer:
        """
        获取模型实例，使用缓存避免重复加载
        
        参数:
            model_name: 模型名称
            
        返回:
            SentenceTransformer: 模型实例
        """
        if (ModelManager._shared_model is None or 
            ModelManager._model_name_cache != model_name):
            
            print(f"正在加载向量化模型: {model_name}")
            
            # 尝试使用项目本地模型
            local_model_path = self.get_project_model_path(model_name)
            
            if local_model_path:
                print(f"使用本地模型: {local_model_path}")
                ModelManager._shared_model = SentenceTransformer(local_model_path)
                print("本地模型加载完成")
            else:
                print(f"本地模型不存在，将下载到：{self.config.models_path / model_name}")
                print("注意：首次运行需要VPN访问HuggingFace下载模型...")
                
                # 设置缓存目录到项目本地
                cache_dir = str(self.config.models_path)
                os.environ['TRANSFORMERS_CACHE'] = cache_dir
                os.environ['HF_HOME'] = cache_dir
                
                ModelManager._shared_model = SentenceTransformer(
                    model_name, 
                    cache_folder=cache_dir
                )
                print(f"模型已下载并保存到：{self.config.models_path / model_name}")
            
            ModelManager._model_name_cache = model_name
            print("模型加载完成")
        
        return ModelManager._shared_model
    
    @classmethod
    def clear_cache(cls):
        """清除模型缓存"""
        cls._shared_model = None
        cls._model_name_cache = None


class TextProcessor:
    """文本处理工具"""
    
    @staticmethod
    def extract_text_from_item(item: Dict[str, Any], item_type: str) -> str:
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
            if 'severity' in item:
                texts.append(f"严重程度: {item['severity']}")
            if 'resolution' in item:
                texts.append(f"解决方案: {item['resolution']}")
            if 'test_focus' in item:
                texts.append(f"测试重点: {item['test_focus']}")
                
        # 添加描述信息（通常是最重要的）
        if 'description' in item and item['description']:
            # 截取描述的前500字符，避免太长
            desc = str(item['description'])[:500]
            texts.append(f"描述: {desc}")
        
        return " | ".join(texts)


class FileManager:
    """文件管理工具"""
    
    def __init__(self, config: MCPToolsConfig):
        self.config = config
    
    def load_tapd_data(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载TAPD数据
        
        参数:
            file_path: 数据文件路径，如果为None则使用默认路径
            
        返回:
            Dict: TAPD数据字典
        """
        if file_path is None:
            # 使用默认路径
            file_path = self.config.get_data_file_path()
        elif not os.path.isabs(file_path):
            # 相对路径处理：直接使用 get_data_file_path 来统一处理
            file_path = self.config.get_data_file_path(file_path)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """
        加载JSON数据
        
        参数:
            file_path: 数据文件路径
            
        返回:
            Dict: JSON数据
        """
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载JSON文件失败: {file_path}, 错误: {str(e)}")
            return {}

    def save_json_data(self, data: Dict[str, Any], file_path: str):
        """
        保存JSON数据
        
        参数:
            data: 要保存的数据
            file_path: 保存路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局实例管理
_global_config: Optional[MCPToolsConfig] = None
_global_model_manager: Optional[ModelManager] = None
_global_file_manager: Optional[FileManager] = None
_global_api_manager: Optional[APIManager] = None


def get_config() -> MCPToolsConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = MCPToolsConfig()
    return _global_config


def get_model_manager() -> ModelManager:
    """获取全局模型管理器实例"""
    global _global_model_manager
    if _global_model_manager is None:
        _global_model_manager = ModelManager(get_config())
    return _global_model_manager


def get_file_manager() -> FileManager:
    """获取全局文件管理器实例"""
    global _global_file_manager
    if _global_file_manager is None:
        _global_file_manager = FileManager(get_config())
    return _global_file_manager


def get_api_manager() -> APIManager:
    """获取全局API管理器实例"""
    global _global_api_manager
    if _global_api_manager is None:
        _global_api_manager = APIManager()
    return _global_api_manager
