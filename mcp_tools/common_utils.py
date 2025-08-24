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
import asyncio

# SiliconFlow 默认模型（可通过环境变量 SF_MODEL 覆盖）
# 若要查看可用的模型，请前往 https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions
SF_DEFAULT_MODEL = os.getenv("SF_MODEL", "moonshotai/Kimi-K2-Instruct")


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
        self.deepseek_endpoint = os.getenv("DS_EP", "https://api.deepseek.com/v1")
        self.deepseek_model = os.getenv("DS_MODEL", "deepseek-chat")
        self.deepseek_api_key = os.getenv("DS_KEY")
        
        # 硅基流动配置
        self.sf_endpoint = "https://api.siliconflow.cn/v1"
        self.sf_api_key = os.getenv("SF_KEY")
        
        self._deepseek_headers_cache: Optional[Dict[str, str]] = None
        self._sf_headers_cache: Optional[Dict[str, str]] = None
    
    def get_headers(self, endpoint: Optional[str] = None) -> Dict[str, str]:
        """构建API请求头，根据endpoint选择对应的API密钥"""
        # 判断是否为硅基流动端点
        if endpoint and "siliconflow" in endpoint:
            if self._sf_headers_cache is None:
                if not self.sf_api_key:
                    raise RuntimeError("No SiliconFlow API key provided – set SF_KEY environment variable!")
                self._sf_headers_cache = {
                    "Authorization": f"Bearer {self.sf_api_key}",
                    "Content-Type": "application/json"
                }
            return self._sf_headers_cache
        else:
            # 默认使用DeepSeek配置（包括endpoint为None的情况）
            if self._deepseek_headers_cache is None:
                if not self.deepseek_api_key:
                    raise RuntimeError("No DeepSeek API key provided – set DS_KEY environment variable!")
                self._deepseek_headers_cache = {"Authorization": f"Bearer {self.deepseek_api_key}"}
            return self._deepseek_headers_cache
    
    async def call_llm(self, prompt: str, 
                      session: aiohttp.ClientSession, 
                      model: Optional[str] = None, 
                      endpoint: Optional[str] = None, 
                      max_tokens: int = 60) -> str:
        """
        调用在线LLM API，支持DeepSeek和SiliconFlow两种API
        
        该函数自动根据endpoint参数检测API类型，并适配相应的请求格式和错误处理。
        
        参数:
            prompt (str): 用户输入的提示词/问题，作为对话内容发送给模型
            session (aiohttp.ClientSession): 异步HTTP会话对象，用于发送API请求
            model (Optional[str]): 指定要使用的模型名称，默认值根据API类型自动选择
                DeepSeek API模型选项:
                    - "deepseek-chat" (默认): 通用对话模型，指向DeepSeek-V3-0324
                    - "deepseek-reasoner": 推理模型，指向DeepSeek-R1-0528，支持reasoning_content字段
                SiliconFlow API模型选项:
                    - "moonshotai/Kimi-K2-Instruct" (默认，可通过环境变量 SF_MODEL 或常量 SF_DEFAULT_MODEL 覆盖): 月之暗面Kimi模型
                    - "Qwen/QwQ-32B": 通义千问推理模型  
                    - "deepseek-ai/DeepSeek-V3": DeepSeek V3模型
                    - "THUDM/GLM-4-9B-0414": 智谱GLM模型
                    - 其他支持的模型请参考SiliconFlow API文档
            endpoint (Optional[str]): API端点URL，用于确定使用哪种API
                - None (默认): 使用DeepSeek API (https://api.deepseek.com/v1)
                - "https://api.deepseek.com/v1": 显式指定DeepSeek API
                - "https://api.siliconflow.cn/v1": 使用SiliconFlow API
                - 系统通过检测endpoint中是否包含"siliconflow"来自动选择API类型
            max_tokens (int): 生成响应的最大token数量，默认60
                - DeepSeek API: 根据模型限制调整
                - SiliconFlow API: 范围1-16384，默认512
                - 建议值: 摘要任务100-500，对话任务60-200，长文本生成500-2000
        
        返回:
            str: 模型生成的文本响应
                - 对于deepseek-reasoner模型: 优先返回content字段，content为空时返回reasoning_content
                - 对于其他模型: 直接返回content字段内容
                - 当max_tokens<100时会进行截断处理（截取到第一个句号或换行符）
        
        抛出异常:
            RuntimeError: API调用相关错误，包括:
                配置错误:
                    - "SiliconFlow API配置错误": SF_KEY环境变量未设置
                    - "DeepSeek API配置错误": DS_KEY环境变量未设置
                
                网络错误:
                    - "API请求超时": 网络超时或连接问题
                    - "API网络请求失败": 其他网络相关错误
                    - "API返回空字符串": 模型返回空响应
                    - "API响应格式错误": JSON解析失败或字段缺失
        
        使用示例:
            # 使用默认DeepSeek API
            result = await api_manager.call_llm(
                prompt="你好，请介绍一下自己",
                session=session,
                max_tokens=100
            )
            
            # 使用DeepSeek推理模型
            result = await api_manager.call_llm(
                prompt="解释量子计算的基本原理",
                session=session,
                model="deepseek-reasoner",
                endpoint="https://api.deepseek.com/v1",
                max_tokens=500
            )
            
            # 使用SiliconFlow的Kimi模型
            result = await api_manager.call_llm(
                prompt="分析这段代码的优化建议",
                session=session,
                model="moonshotai/Kimi-K2-Instruct",
                endpoint="https://api.siliconflow.cn/v1",
                max_tokens=300
            )
        
        环境变量要求:
            - DS_KEY: DeepSeek API密钥，从 https://platform.deepseek.com/api_keys 获取
            - SF_KEY: SiliconFlow API密钥，从 https://siliconflow.cn/ 获取
            - SF_MODEL: 覆盖 SiliconFlow 默认模型 (可选，默认: moonshotai/Kimi-K2-Instruct)
            - DS_EP: DeepSeek API端点 (可选，默认: https://api.deepseek.com/v1)
            - DS_MODEL: DeepSeek默认模型 (可选，默认: deepseek-chat)
        
        注意事项:
            - temperature固定为0.2，适合大多数任务场景
            - DeepSeek API建议根据使用场景设置temperature: 代码生成0.0，数据分析1.0，通用对话1.3
            - SiliconFlow API默认包含额外参数: top_p=0.7, frequency_penalty=0.5
            - 请求超时时间设置为300秒
            - 系统自动处理不同API的请求格式差异
        """
        # 确定使用的端点和模型
        use_endpoint = endpoint or self.deepseek_endpoint
        
        # 判断是否为硅基流动API
        is_siliconflow = "siliconflow" in use_endpoint
        is_deepseek = "deepseek" in use_endpoint
        
        use_model = None
        payload = {}
        headers = {}
        text = ""

        if is_siliconflow:
            # 硅基流动API配置
            use_model = model or SF_DEFAULT_MODEL
            try:
                headers = self.get_headers(use_endpoint)
            except RuntimeError as e:
                raise RuntimeError(f"SiliconFlow API配置错误: {str(e)}\n请设置环境变量 SF_KEY 为您的SiliconFlow API密钥") from e
            
            payload = {
                "model": use_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "top_p": 0.7,
                "frequency_penalty": 0.5,
                "n": 1,
                "response_format": {"type": "text"}
            }
        elif is_deepseek:
            # DeepSeek API配置
            use_model = model or self.deepseek_model
            try:
                headers = self.get_headers(use_endpoint)
            except RuntimeError as e:
                raise RuntimeError(f"DeepSeek API配置错误: {str(e)}\n请设置环境变量 DS_KEY 为您的DeepSeek API密钥") from e
            
            payload = {
                "model": use_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.2,
            }
        
        try:
            async with session.post(f"{use_endpoint}/chat/completions", json=payload, headers=headers, timeout=300) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    
                    # 根据API类型提供不同的错误信息
                    if is_siliconflow:
                        # SiliconFlow API错误处理（根据官方文档）
                        if resp.status == 400:
                            raise RuntimeError(f"SiliconFlow API请求参数错误: {error_text}")
                        elif resp.status == 401:
                            raise RuntimeError("SiliconFlow API认证失败: Invalid token，请检查SF_KEY环境变量是否正确设置")
                        elif resp.status == 404:
                            raise RuntimeError(f"SiliconFlow API页面未找到: 可能是模型不存在或API路径错误 - {use_model}")
                        elif resp.status == 429:
                            raise RuntimeError("SiliconFlow API请求速率达到上限: TPM limit reached，请合理规划请求速率或联系 contact@siliconflow.cn")
                        elif resp.status == 503:
                            raise RuntimeError("SiliconFlow API服务过载: 模型服务过载，请稍后重试")
                        elif resp.status == 504:
                            raise RuntimeError("SiliconFlow API网关超时: 请求超时，请稍后重试")
                        else:
                            raise RuntimeError(f"SiliconFlow API调用失败 (状态码: {resp.status}): {error_text}")
                    elif is_deepseek:
                        # DeepSeek API错误处理（根据官方文档）
                        if resp.status == 400:
                            raise RuntimeError(f"DeepSeek API格式错误: 请求体格式错误。{error_text}")
                        elif resp.status == 401:
                            raise RuntimeError("DeepSeek API认证失败: API key错误，请检查DS_KEY环境变量是否正确设置")
                        elif resp.status == 402:
                            raise RuntimeError("DeepSeek API余额不足: 账号余额不足，请前往 https://platform.deepseek.com/top_up 充值")
                        elif resp.status == 422:
                            raise RuntimeError(f"DeepSeek API参数错误: 请求体参数错误。{error_text}")
                        elif resp.status == 429:
                            raise RuntimeError("DeepSeek API请求速率达到上限: 请求速率（TPM或RPM）达到上限，请合理规划请求速率")
                        elif resp.status == 500:
                            raise RuntimeError("DeepSeek API服务器故障: 服务器内部故障，请等待后重试")
                        elif resp.status == 503:
                            raise RuntimeError("DeepSeek API服务器繁忙: 服务器负载过高，请稍后重试")
                        else:
                            raise RuntimeError(f"DeepSeek API调用失败 (状态码: {resp.status}): {error_text}")
                
                js = await resp.json()
        except asyncio.TimeoutError:
            api_name = "SiliconFlow" if is_siliconflow else "DeepSeek"
            raise RuntimeError(f"{api_name} API请求超时，请检查网络连接或稍后重试")
        except Exception as e:
            if "API配置错误" in str(e) or "API认证失败" in str(e) or "API调用失败" in str(e):
                raise  # 重新抛出已知的API错误
            api_name = "SiliconFlow" if is_siliconflow else "DeepSeek"
            raise RuntimeError(f"{api_name} API网络请求失败: {str(e)}")

        try:
            msg = js["choices"][0]["message"]
            
            if is_siliconflow:
                # SiliconFlow API响应处理
                text = msg.get("content", "").strip()
                # SiliconFlow可能有reasoning_content字段（某些推理模型）
                reasoning_content = msg.get("reasoning_content", "").strip()
                if not text and reasoning_content:
                    text = reasoning_content
            elif is_deepseek:
                # DeepSeek API响应处理
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
                api_name = "SiliconFlow" if is_siliconflow else "DeepSeek"
                raise RuntimeError(f"{api_name} API返回空字符串，可能是模型或配置问题。响应片段: " + str(js)[:400])
            return text
        except KeyError as e:
            api_name = "SiliconFlow" if is_siliconflow else "DeepSeek"
            raise RuntimeError(f"{api_name} API响应格式错误，缺少字段: {str(e)}。响应内容: {str(js)[:400]}")
        except Exception as e:
            api_name = "SiliconFlow" if is_siliconflow else "DeepSeek"
            raise RuntimeError(f"解析{api_name} API响应失败: {str(e)}。响应内容: {str(js)[:400]}")


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
