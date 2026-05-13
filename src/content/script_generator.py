"""
Script Generator Handler - LLM 文案生成 (支持远程 API)
负责根据房源/产品信息生成直播讲解文案
"""

import logging
from typing import Dict, Any, Optional
import re
import json
from ..core.base import Base
from ..core.exceptions import ScriptGenerationError

logger = logging.getLogger(__name__)


class ScriptGeneratorHandler(Base):
    """
    脚本生成处理节点
    
    功能:
    - 接收房源/产品信息
    - 调用 LLM (远程 API / 本地模型) 生成直播讲解文案
    - 格式化输出，控制时长 (30-60 秒)
    
    支持的 LLM 服务:
    - DeepSeek (远程 API, 推荐)
    - 其他兼容 OpenAI API的服务
    - 本地 GGUF 模型 (可选)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        
        # LLM 配置
        self._mode = config.get('llm', {}).get('mode', 'remote')  # remote / local
        self._system_prompt = config.get('llm', {}).get(
            'system_prompt', 
            "你是一位专业的二手房车销售专家，擅长用生动的语言介绍房产和房车产品。你的任务是生成适合数字人直播的讲解文案。"
        )
        
        # 远程 API 配置
        self._remote_config = config.get('llm', {}).get('remote', {})
        self._provider = self._remote_config.get('provider', 'deepseek')
        self._api_key = self._remote_config.get('api_key', '')
        self._base_url = self._remote_config.get('base_url', 'https://api.deepseek.com/v1')
        self._model = self._remote_config.get('model', 'deepseek-chat')
        
        # 本地模型配置
        self._local_config = config.get('llm', {}).get('local', {})
        self._local_model = self._local_config.get('model', 'qwen/Qwen-7B-Chat-GGUF')
        self._quantization = self._local_config.get('quantization', 'q4_0')
        
        # 输出模板 (v3.0: 支持占位符)
        output_template = config.get('llm', {}).get('output_template', '')
        if output_template:
            self._output_template = output_template
        else:
            self._output_template = """【开场】(5-10 秒)
{opening}

【核心卖点】(20-30 秒)
{highlights}

【互动引导】(5-10 秒)
{call_to_action}"""
        
        # v3.0: 动态模板配置 (支持占位符填充)
        self._prompt_config = config.get('llm', {}).get('prompt_config', {})
        self._role = self._prompt_config.get('role', '二手房车销售专家')
        self._product_type = self._prompt_config.get('product_type', '房产和房车产品')
        self._selling_points = self._prompt_config.get('selling_points', [])
        
        # 动态系统提示词模板 (v3.0)
        system_prompt_template = config.get('llm', {}).get('system_prompt_template', None)
        if system_prompt_template:
            self._system_prompt_template = system_prompt_template
    
    def handle(self, property_info: str) -> str:
        """
        处理文案生成
        
        Args:
            property_info: 房源/产品信息
            
        Returns:
            str: 生成的直播讲解文案
        """
        try:
            if self._mode == 'remote':
                script = self._generate_with_remote_api(property_info)
            else:
                script = self._generate_with_local_model(property_info)
            
            return script
            
        except Exception as e:
            logger.error(f"LLM 文案生成失败：{e}")
            # 降级返回示例文案
            return self._generate_fallback_script(property_info)
    
    def _generate_with_remote_api(self, property_info: str) -> str:
        """使用远程 API 生成文案 (v3.0: 支持动态模板)"""
        import requests
        
        if not self._api_key:
            raise ScriptGenerationError(
                f"{self._provider} API Key 未配置，请在系统设置中填写"
            )
        
        # v3.0: 使用动态模板生成 system_prompt
        if hasattr(self, '_system_prompt_template'):
            try:
                selling_points_str = '\n'.join([f'- {sp}' for sp in self._selling_points])
                dynamic_system_prompt = self._system_prompt_template.format(
                    role=self._role,
                    product_type=self._product_type,
                    property_info=property_info,
                    selling_points=selling_points_str
                )
            except KeyError as e:
                logger.warning(f"模板占位符缺失：{e}，使用默认 system_prompt")
                dynamic_system_prompt = self._system_prompt
        else:
            # 降级：构建传统提示词
            dynamic_system_prompt = f"""你是一位专业的{self._role}专家，擅长用生动的语言介绍{self._product_type}产品。你的任务是生成适合数字人直播的讲解文案。

【产品信息】
{property_info}

【核心卖点】
{' '.join(self._selling_points) if self._selling_points else '面积、价格、地段、配套'}

【要求】
1. 突出产品卖点 (面积、价格、地段、配套)
2. 时长控制在 30-60 秒 (约 150-250 字)
3. 口语化表达，避免专业术语
4. 开头要有吸引力，结尾引导互动"""
        
        # 构建完整的用户提示词
        user_prompt = f"""根据以上产品信息和卖点，生成一段适合数字人直播的讲解文案：

【输出格式】请按以下结构组织文案：
{{opening}} - 开场白 (5-10 秒)
{{highlights}} - 核心卖点 (20-30 秒)  
{{call_to_action}} - 互动引导 (5-10 秒)"""
        
        # DeepSeek API 请求格式
        messages = [
            {"role": "system", "content": dynamic_system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = requests.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}"
                },
                json={
                    "model": self._model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            if response.status_code != 200:
                error_msg = f"API 请求失败：{response.status_code} {response.text}"
                logger.error(error_msg)
                raise ScriptGenerationError(error_msg)
            
            result = response.json()
            generated_text = result['choices'][0]['message']['content']
            
            # 清理输出，移除 Markdown 标记等
            cleaned_script = self._clean_generated_text(generated_text)
            
            logger.info(f"远程 API 生成文案成功：{len(cleaned_script)}字")
            return cleaned_script
            
        except requests.exceptions.RequestException as e:
            raise ScriptGenerationError(f"网络请求失败：{str(e)}")
    
    def _generate_with_local_model(self, property_info: str) -> str:
        """使用本地模型生成文案 (预留接口)"""
        # TODO: 集成 llama.cpp / transformers
        
        # 当前降级方案：返回示例文案，提示用户配置远程 API
        fallback_script = f"""【开场】(5-10 秒)

大家好！今天给大家带来一套超值的二手房车，性价比超高！

【核心卖点】(20-30 秒)

这套房源位于{property_info.split(',')[0] if ',' in property_info else '核心地段'}，面积{property_info.split(',')[-2] if len(property_info.split(',')) > 1 else '89 平'}，价格只要{property_info.split(',')[-1].split('万')[0] if '万' in property_info else '500'}万！

主要亮点包括：
- 户型方正，采光充足
- 周边配套完善，交通便利  
- 精装修可直接入住
- 性价比高，投资自住两相宜

【互动引导】(5-10 秒)

感兴趣的朋友可以在评论区留言，我会详细介绍！点赞关注不迷路~"""
        
        logger.warning(f"本地模式未实现，返回降级文案：{len(fallback_script)}字")
        return fallback_script
    
    def _clean_generated_text(self, text: str) -> str:
        """清理生成的文本，移除 Markdown 标记等"""
        # 移除 ```text ... ``` 或 ```markdown ... ``` 包裹
        text = re.sub(r'```(?:text|markdown)?\n?', '', text)
        text = re.sub(r'```\n?', '', text)
        
        # 移除多余的换行符
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _generate_fallback_script(self, property_info: str) -> str:
        """生成降级文案 (当 LLM 不可用时使用)"""
        # 解析基本信息
        info = property_info.strip()
        
        script = f"""【开场】(5-10 秒)

大家好！今天给大家带来一套超值的二手房车，性价比超高！

【核心卖点】(20-30 秒)

这套房源位于{info.split(',')[0] if ',' in info else '核心地段'}，面积{info.split(',')[-2] if len(info.split(',')) > 1 else '89 平'}，价格只要{info.split(',')[-1].split('万')[0] if '万' in info else '500'}万！

主要亮点包括：
- 户型方正，采光充足
- 周边配套完善，交通便利  
- 精装修可直接入住
- 性价比高，投资自住两相宜

【互动引导】(5-10 秒)

感兴趣的朋友可以在评论区留言，我会详细介绍！点赞关注不迷路~"""
        
        logger.warning(f"使用降级文案：{len(script)}字")
        return script
    
    def parse_script(self, script: str) -> Dict[str, str]:
        """
        解析生成的文案结构
        
        Returns:
            dict: {'opening': ..., 'highlights': ..., 'call_to_action': ...}
        """
        result = {
            'opening': '',
            'highlights': '',
            'call_to_action': ''
        }
        
        # 简单解析模板结构
        opening_match = re.search(r'【开场】.*?(?=【核心卖点】)', script, re.DOTALL)
        highlights_match = re.search(r'【核心卖点】.*?(?=【互动引导】)', script, re.DOTALL)
        cta_match = re.search(r'【互动引导】(.*)$', script, re.DOTALL)
        
        if opening_match:
            result['opening'] = self._clean_section(opening_match.group())
        if highlights_match:
            result['highlights'] = self._clean_section(highlights_match.group())
        if cta_match:
            result['call_to_action'] = cta_match.group(1).strip()
        
        return result
    
    def _clean_section(self, text: str) -> str:
        """清理段落文本，去除时间标注"""
        # 移除 (XX-XX 秒) 这类标注
        cleaned = re.sub(r'\([^)]*\)', '', text)
        # 移除标题行
        cleaned = re.sub(r'【[^】]*】', '', cleaned).strip()
        return cleaned
    
    def estimate_duration(self, script: str) -> int:
        """
        估算文案朗读时长 (秒)
        
        按中文平均语速 250 字/分钟计算
        """
        # 只统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', script))
        return int(chinese_chars / 250 * 60)
