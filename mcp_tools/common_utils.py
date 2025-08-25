"""
MCP工具公共工具模块

提供所有MCP工具共用的基础功能和配置管理
"""

import os
import json
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Tuple
import asyncio
import re
import uuid
import pandas as pd

# SiliconFlow 默认模型（可通过环境变量 SF_MODEL 覆盖）
# 若要查看可用的模型，请前往 https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions
SF_DEFAULT_MODEL = os.getenv("SF_MODEL", "deepseek-ai/DeepSeek-V3.1")


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
        use_endpoint = endpoint or self.sf_endpoint
        
        # 判断是否为硅基流动API
        is_siliconflow = "siliconflow" in use_endpoint
        is_deepseek = "deepseek" in use_endpoint
        
        # 确定使用的模型
        if is_siliconflow:
            use_model = model or SF_DEFAULT_MODEL
        elif is_deepseek:
            use_model = model or self.deepseek_model
        else:
            use_model = model or self.deepseek_model
            
        payload = {}
        headers = {}
        text = ""

        print(f"API调用参数: endpoint={use_endpoint}, model={use_model}, max_tokens={max_tokens}")

        if is_siliconflow:
            # 硅基流动API配置
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
    
    _shared_model: Optional[Any] = None
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
    
    def get_model(self, model_name: str = "paraphrase-MiniLM-L6-v2") -> Any:
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
                # 延迟导入，避免在模块导入阶段引入重依赖
                from sentence_transformers import SentenceTransformer
                ModelManager._shared_model = SentenceTransformer(local_model_path)
                print("本地模型加载完成")
            else:
                print(f"本地模型不存在，将下载到：{self.config.models_path / model_name}")
                print("注意：首次运行需要VPN访问HuggingFace下载模型...")
                
                # 设置缓存目录到项目本地
                cache_dir = str(self.config.models_path)
                os.environ['TRANSFORMERS_CACHE'] = cache_dir
                os.environ['HF_HOME'] = cache_dir
                
                from sentence_transformers import SentenceTransformer
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
    
    def read_excel_with_mapping(
        self,
        excel_file_path: str,
        column_mapping: Dict[str, str],
        na_to_empty: bool = True
    ) -> List[Dict[str, Any]]:
        """
        读取Excel并按列映射输出为list[dict]，自动处理NaN与去两端空白。

        参数:
            excel_file_path: Excel文件路径
            column_mapping: {Excel列名: 输出键名}
            na_to_empty: 是否将NaN/None转换为空字符串

        返回:
            List[Dict[str, Any]]: 行字典列表
        """
        try:
            df = pd.read_excel(excel_file_path)
        except Exception as e:
            raise RuntimeError(f"读取Excel失败: {excel_file_path} — {e}")

        results: List[Dict[str, Any]] = []
        # 使用DataFrame的get以容错缺少列的情况
        for _, row in df.iterrows():
            item: Dict[str, Any] = {}
            for xls_col, out_key in column_mapping.items():
                val = row.get(xls_col, "")
                if na_to_empty and (pd.isna(val) or val is None):
                    val = ""
                # 统一为字符串并去除两端空白
                if isinstance(val, str):
                    item[out_key] = val.strip()
                else:
                    # 对数字等非字符串，保持原值；若需要字符串，调用方可自行转换
                    item[out_key] = val
            results.append(item)
        return results
    
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


# 新增：可靠传输与ACK管理器
class TransmissionManager:
    """管理分块数据的标识、ACK校验、重试与报告输出"""

    def __init__(self, file_manager: FileManager):
        self.fm = file_manager
        # 复用本地数据目录
        self.retry_log_path = self.fm.config.get_data_file_path("retry_log.json")
        self.report_path = self.fm.config.get_data_file_path("transmission_report.json")
        self.retry_logs: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {
            "total_chunks": 0,
            "ack_success_chunks": 0,
            "ack_failed_chunks": 0,
            "total_retries": 0,
        }

    def assign_ids(self, chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为分块内的每个条目分配稳定的data_id（若无则生成），并返回精简视图用于ACK。"""
        minified: List[Dict[str, Any]] = []
        for it in chunk:
            data_id = it.get("_data_id")
            if not data_id:
                data_id = str(uuid.uuid4())
                it["_data_id"] = data_id
            title = it.get("name") or it.get("title") or ""
            minified.append({"id": data_id, "title": str(title)[:80]})
        return minified

    def build_ack_prompt(self, items: List[Dict[str, Any]], mode: str = "ack_only") -> str:
        ids = [x["id"] for x in items]
        example = {"status": "ok", "received_count": len(ids), "data_ids": ids}
        if mode == "ack_and_analyze":
            example["analysis_text"] = "这里输出对这些条目的分析摘要（300-500字）"
        items_text = "\n".join(f"- {it['id']}: {it['title']}" for it in items)
        return (
            "请先对以下数据执行接收确认（ACK）：列出你成功接收到的id，并统计数量。"\
            "严格仅输出JSON，字段包括：status('ok'|'partial'|'error'), received_count(整数), data_ids(字符串数组)"
            + (", analysis_text(字符串,300-500字) — 当模式为ack_and_analyze时必须包含" if mode == "ack_and_analyze" else "")
            + f"\nJSON输出示例：\n{json.dumps(example, ensure_ascii=False)}\n"
            + "以下是数据项（仅包含简要信息）：\n" + items_text + "\n"
            + f"仅输出JSON。当前模式: {mode}"
        )

    def extract_first_json(self, text: str) -> Optional[Dict[str, Any]]:
        """尽力从模型文本中提取首个有效JSON对象。"""
        # 优先代码块
        try:
            if "```" in text:
                parts = text.split("```")
                for i in range(1, len(parts), 2):
                    blk = parts[i]
                    if blk.lstrip().startswith("json"):
                        blk = blk.split("\n", 1)[1] if "\n" in blk else ""
                    try:
                        return json.loads(blk.strip())
                    except Exception:
                        continue
            # 直接整体解析
            return json.loads(text)
        except Exception:
            pass
        # 正则回退
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

    def verify_ack(self, sent_ids: List[str], ack: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(ack, dict):
            return {"ok": False, "missing": list(sent_ids), "extra": [], "received_count": 0}
        recv_ids = [str(x) for x in ack.get("data_ids", [])]
        sent_set, recv_set = set(sent_ids), set(recv_ids)
        missing = list(sent_set - recv_set)
        extra = list(recv_set - sent_set)
        ok = (ack.get("status") in ("ok", "success")) and (len(missing) == 0)
        rc = ack.get("received_count", len(recv_ids))
        return {"ok": ok, "missing": missing, "extra": extra, "received_count": rc}

    def log_retry(self, chunk_index: int, attempt: int, reason: str, details: Dict[str, Any]):
        entry = {"chunk_index": chunk_index, "attempt": attempt, "reason": reason, "details": details}
        self.retry_logs.append(entry)
        try:
            existing = self.fm.load_json_data(self.retry_log_path) or {}
            arr = existing.get("retries", [])
            arr.append(entry)
            existing["retries"] = arr
            self.fm.save_json_data(existing, self.retry_log_path)
        except Exception as e:
            print(f"[Transmission] 写入重试日志失败: {e}")

    def update_stats(self, success: bool, retries: int = 0):
        self.stats["total_chunks"] += 1
        if success:
            self.stats["ack_success_chunks"] += 1
        else:
            self.stats["ack_failed_chunks"] += 1
        self.stats["total_retries"] += retries

    def finalize_report(self) -> Dict[str, Any]:
        report = {
            "stats": self.stats,
            "retry_log_path": self.retry_log_path,
            "generated_at": __import__("datetime").datetime.now().isoformat(),
        }
        try:
            self.fm.save_json_data(report, self.report_path)
        except Exception as e:
            print(f"[Transmission] 写入传输报告失败: {e}")
        report["report_path"] = self.report_path
        return report


class TokenCounter:
    """Token计数器 - 支持transformers tokenizer和改进的预估模式"""
    
    def __init__(self, config: Optional[MCPToolsConfig] = None):
        self.config = config or get_config()
        self.tokenizer = None
        self._try_load_tokenizer()
    
    def _try_load_tokenizer(self):
        """尝试加载DeepSeek tokenizer"""
        try:
            # 尝试使用transformers库加载tokenizer
            import transformers
            
            tokenizer_path = self.config.models_path / "deepseek_v3_tokenizer" / "deepseek_v3_tokenizer"
            
            if tokenizer_path.exists():
                self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                    str(tokenizer_path), 
                    trust_remote_code=True
                )
                print("已加载DeepSeek tokenizer（transformers），将使用精确token计数")
                return
            else:
                print(f"DeepSeek tokenizer路径不存在: {tokenizer_path}")
                
        except ImportError as e:
            print(f"transformers库未安装: {e}")
        except Exception as e:
            print(f"加载DeepSeek tokenizer失败: {e}")
        
        print("将使用改进的预估模式进行token计数")
        self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        参数:
            text: 要计算的文本
            
        返回:
            token数量
        """
        if self.tokenizer:
            try:
                tokens = self.tokenizer.encode(text)
                return len(tokens)
            except Exception as e:
                print(f"使用tokenizer计数失败: {e}，转为预估模式")
        
        # 改进的预估模式：基于测试结果优化参数
        # 测试结果显示：
        # - 样本文本平均比率: 0.98 (预估vs实际)
        # - 真实用例平均比率: 0.91 (预估vs实际)
        # - 预估模式总体偏低约10%，需要调整系数
        import re
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        digits = len(re.findall(r'[0-9]', text))
        punctuation = len(re.findall(r'[^\w\s]', text))
        spaces = len(re.findall(r'\s', text))
        other_chars = len(text) - chinese_chars - english_chars - digits - punctuation - spaces
        
        # 基于测试结果调整的系数
        estimated_tokens = int(
            chinese_chars * 0.7 +      # 中文字符（从0.6调整到0.7）
            english_chars * 0.35 +     # 英文字符（从0.3调整到0.35）
            digits * 0.3 +             # 数字
            punctuation * 0.4 +        # 标点符号
            spaces * 0.1 +             # 空格
            other_chars * 0.4          # 其他字符
        )
        
        # 添加10%的修正系数，因为测试显示预估偏低
        estimated_tokens = int(estimated_tokens * 1.1)
        
        return estimated_tokens



class BatchingUtils:    # 无状态、仅提供静态方法，不提供全局实例函数
    """通用分批工具：按token预算对列表进行贪心切分。"""

    @staticmethod
    def split_by_token_budget(
        items: List[Any],
        estimate_tokens_fn: Callable[[List[Any]], int],
        token_threshold: int,
        start_index: int = 0
    ) -> Tuple[List[Any], int, int]:
        """
        基于token预算，将items从start_index开始贪心装入一批，尽量不超过阈值；
        若首个元素本身即超过阈值，也会收纳该元素以保证前进。

        返回: (当前批次列表, 下一批起始索引, 当前批次估算token数)
        """
        if not items or start_index >= len(items):
            return [], start_index, 0

        batch: List[Any] = []
        last_tokens = 0

        for i in range(start_index, len(items)):
            candidate = batch + [items[i]]
            try:
                cand_tokens = estimate_tokens_fn(candidate)
            except Exception as e:
                raise RuntimeError(f"估算tokens失败: {e}")

            if cand_tokens > token_threshold and batch:
                # 超阈值且已有内容，停止累加
                break

            batch.append(items[i])
            last_tokens = cand_tokens

        next_index = start_index + len(batch)
        return batch, next_index, last_tokens

class TokenBudgetUtils:  # 无状态：统一的回复token预算计算工具
    """
    统一的回复 token 预算计算：确保在总上下文窗口内满足 请求(prompt)+回复(response)+安全余量(safety)。

    典型用法：
        max_out = TokenBudgetUtils.compute_response_tokens(prompt_text, total_budget=6000, desired_response_cap=800)

    约定：
    - total_budget: 模型总上下文预算（prompt+response+safety），如 4k/8k/16k。
    - desired_response_cap: 业务侧希望的最大回复上限；最终返回不会超过它。
    - safety_tokens: 预留的安全余量；不传则按 total_budget 的 5%（且不小于128，不大于512）取值。
    - min_out: 在可行范围内，尽量给到的最小回复上限，避免 0 或过小导致 API 拒绝。
    """

    @staticmethod
    def compute_response_tokens(
        prompt_text: str,
        *,
        total_budget: int = 6000,
        desired_response_cap: int = 800,
        safety_tokens: Optional[int] = None,
        min_out: int = 64,
    ) -> int:
        # 计数请求侧 tokens
        try:
            tc = get_token_counter()
            prompt_tokens = tc.count_tokens(prompt_text or "")
        except Exception:
            # 最保守退化：4字符≈1token
            prompt_tokens = max(0, len(prompt_text or "") // 4)

        # 安全余量：默认 total 的 5%，夹在 [128,512]
        if safety_tokens is None:
            safety = max(128, min(512, int(total_budget * 0.05)))
        else:
            safety = max(0, int(safety_tokens))

        # 可用于回复的预算
        available = total_budget - prompt_tokens - safety

        # 基于可用预算与业务上限取最小，同时保证不低于 min_out
        if available <= 0:
            # prompt 已超预算，退化到很小的回复上限，尽量不为0
            return max(16, min(min_out, desired_response_cap))

        # 正常路径
        max_resp = min(desired_response_cap, available)
        if max_resp < min_out:
            # 预算不够时，仍提供一个小的可用窗口，避免为0
            return max(16, max_resp)
        return int(max_resp)



class MarkdownUtils:    # 无状态、仅提供静态方法，不提供全局实例函数
    """Markdown表格解析通用工具（纯解析，不做业务映射）。"""

    @staticmethod
    def parse_markdown_tables(md_text: str) -> List[Dict[str, Any]]:
        """
        解析Markdown中的所有表格，返回标准化结构：
        [{"headers": [...], "rows": [[...],[...], ...]}]

        - 自动跳过对齐分隔行（---, :---:, ---: 等）
        - 支持以竖线开头或不以竖线开头的表格行
        - 保留单元格原始文本（去除两端空白）
        """
        lines = md_text.splitlines()
        tables: List[Dict[str, Any]] = []

        i = 0
        n = len(lines)

        def split_row(line: str) -> List[str]:
            parts = [p.strip() for p in line.split('|')]
            # 移除首尾由于前导/尾随竖线产生的空单元
            if parts and parts[0] == '':
                parts = parts[1:]
            if parts and parts[-1] == '':
                parts = parts[:-1]
            return parts

        def is_sep_row(line: str) -> bool:
            # 典型分隔行：| --- | :---: | ---: |
            core = line.strip().strip('|').strip()
            if not core:
                return False
            cells = [c.strip() for c in core.split('|')]
            if not cells:
                return False
            return all(re.fullmatch(r":?-{3,}:?", c.replace(' ', '')) is not None for c in cells)

        while i < n:
            line = lines[i].rstrip()

            # 找到表头候选行：包含至少一个'|'并且下一行是对齐分隔行
            if '|' in line and (i + 1) < n and '|' in lines[i + 1] and is_sep_row(lines[i + 1]):
                headers = split_row(line)
                i += 2  # 跳过分隔行
                rows: List[List[str]] = []
                # 读取后续数据行
                while i < n:
                    data_line = lines[i].rstrip()
                    if '|' in data_line:
                        # 到下一个表或无效结构时停止
                        if (i + 1) < n and '|' in lines[i + 1] and is_sep_row(lines[i + 1]):
                            break
                        rows.append(split_row(data_line))
                        i += 1
                    else:
                        break

                tables.append({"headers": headers, "rows": rows})
                continue  # 已经前进到正确位置

            i += 1

        return tables


# 全局实例管理
_global_config: Optional[MCPToolsConfig] = None
_global_model_manager: Optional[ModelManager] = None
_global_file_manager: Optional[FileManager] = None
_global_api_manager: Optional[APIManager] = None
_global_transmission_manager: Optional[TransmissionManager] = None
_global_token_counter: Optional[TokenCounter] = None

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


def get_transmission_manager() -> TransmissionManager:
    """获取全局传输管理器实例"""
    global _global_transmission_manager
    if _global_transmission_manager is None:
        _global_transmission_manager = TransmissionManager(get_file_manager())
    return _global_transmission_manager


def get_token_counter() -> TokenCounter:
    """获取全局Token计数器实例"""
    global _global_token_counter
    if _global_token_counter is None:
        _global_token_counter = TokenCounter(get_config())
    return _global_token_counter
