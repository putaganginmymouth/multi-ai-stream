"""
Reply Generator Handler - 评论回复生成器 (LLM 优先 + Q&A 降级)
负责根据用户评论生成智能回复，支持四级降级策略
"""

import re
import time
from typing import Optional, Dict, Any, List
import threading
import logging
import requests

logger = logging.getLogger(__name__)


class ReplyGeneratorHandler:
    """实时评论 LLM 生成回复 + Q&A 降级系统"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        
        # LLM 配置
        self.system_prompt = config.get('expert_role', {}).get(
            'definition', 
            """你是一位专业的房车产品专家，拥有 10 年以上 RV 行业经验。你的特点是：
- 清晰专业：用简洁语言解释技术参数
- 具体详实：提供真实数据和场景化描述
- 耐心周到：主动解答用户可能关心的所有问题
- 热情亲和：像朋友一样推荐产品，避免过度营销感

回答风格要求:
1. 每条回复不超过 80 字 (20 秒语音)
2. 先肯定用户关注点，再补充关键信息
3. 必要时提供对比建议或购买指导
4. 结尾引导互动："感兴趣可以留言了解更多" """
        )
        
        # 降级配置
        self.llm_timeout = int(config.get('llm_timeout_seconds', 10))
        self.qa_min_confidence = float(config.get('qa_match_min_confidence', 0.6))
        
        # Q&A 匹配算法参数
        self.keyword_weight = 1.0
        self.semantic_weight = 0.5
        
        # 服务实例
        from ..data.services import get_product_state_service, get_public_qa_service
        self.state_service = get_product_state_service()
        self.public_qa_service = get_public_qa_service()
    
    def generate_reply(self, user_comment: str) -> Dict[str, Any]:
        """
        生成回复 (主流程：LLM → 公共 Q&A → 私有 Q&A → 默认回复)
        
        Args:
            user_comment: 用户评论文本
            
        Returns:
            dict: {
                'reply': str,           # 生成的回复文案
                'source': 'llm'/'qa'/'fallback',  # 来源：LLM/Q&A/默认
                'confidence': float,    # 置信度 (Q&A 模式)
                'error': Optional[str], # 错误信息
                'matched_qa_id': Optional[int],  # 匹配的 Q&A ID(如有)
                'is_public': bool      # 是否来自公共 Q&A
            }
        """
        
        # Step 1: 获取当前产品上下文 + 所有可用 Q&A
        product_context = self.state_service.get_current_product()
        public_qa_list = self.public_qa_service.get_all_public_qa(enabled_only=True)
        
        if not product_context:
            return {
                'reply': '请先选择正在介绍的产品',
                'source': 'system',
                'confidence': 0.0,
                'error': None,
                'matched_qa_id': None,
                'is_public': False
            }
        
        # Step 2: 尝试 LLM 生成 (带超时)
        llm_reply = self._try_llm_generate(user_comment, product_context['detail'])
        
        if llm_reply and len(llm_reply.get('reply', '')) > 0:
            return {
                'reply': llm_reply['reply'],
                'source': 'llm',
                'confidence': 1.0,
                'error': None,
                'matched_qa_id': None,
                'is_public': False
            }
        
        # Step 3: LLM 失败，降级到 Q&A 匹配 (公共优先，然后私有)
        all_qa_pairs = public_qa_list + product_context.get('qa_pairs', [])
        
        return self._match_qa_reply(user_comment, all_qa_pairs)
    
    def _try_llm_generate(self, comment: str, product_detail: str) -> Optional[Dict]:
        """尝试 LLM 生成，失败返回 None"""
        
        result_container = {'reply': None, 'error': None}
        
        def llm_thread():
            try:
                reply_text = self._call_llm_api(comment, product_detail)
                
                # 时长校验 (确保≤85 字，约 20 秒语音)
                if len(reply_text) > 85:
                    reply_text = reply_text[:80] + "..."
                
                result_container['reply'] = reply_text.strip()
            except Exception as e:
                result_container['error'] = str(e)
        
        thread = threading.Thread(target=llm_thread, daemon=True)
        thread.start()
        thread.join(timeout=self.llm_timeout)
        
        if thread.is_alive():
            logger.warning(f"LLM 响应超时 ({self.llm_timeout}s)")
            return None
        
        if result_container['reply']:
            return {'reply': result_container['reply'], 'error': None}
        
        logger.error(f"LLM 生成失败：{result_container['error']}")
        return None
    
    def _call_llm_api(self, comment: str, product_detail: str) -> str:
        """调用 LLM API (DeepSeek)"""
        
        prompt = f"""{self.system_prompt}

【当前产品介绍】
{product_detail}

【用户评论】
{comment}

请基于产品详细信息，用专业、耐心、周到的风格回复用户。
注意：回复长度控制在 50-80 字 (约 20 秒语音)。"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 从配置获取 API Key
        remote_config = self.config.get('remote', {})
        api_key = remote_config.get('api_key')
        
        if not api_key:
            raise Exception("LLM API Key 未配置")
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": remote_config.get('model', 'deepseek-chat'),
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 200
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"API 请求失败：{response.status_code} {response.text}")
        
        return response.json()['choices'][0]['message']['content']
    
    def _match_qa_reply(self, comment: str, qa_pairs: List[Dict]) -> Dict[str, Any]:
        """Q&A 关键字匹配 (公共优先，然后私有)"""
        
        best_match = None
        max_confidence = 0.0
        matched_qa_id = None
        
        for i, qa in enumerate(qa_pairs):
            confidence = self._calculate_match_score(comment, qa)
            
            if confidence > max_confidence and confidence >= self.qa_min_confidence:
                max_confidence = confidence
                
                # 记录 QA ID(用于追踪是公共还是私有)
                matched_qa_id = qa.get('id', f'private_{i}')
                
                best_match = qa
        
        if best_match:
            return {
                'reply': best_match['answer'],
                'source': 'qa',
                'confidence': max_confidence,
                'error': None,
                'matched_qa_id': matched_qa_id,
                'is_public': 'id' in best_match  # True=公共 Q&A, False=私有 Q&A
            }
        else:
            return {
                'reply': '感谢您的关注！这个问题比较具体，我让专家稍后详细解答~',
                'source': 'fallback',
                'confidence': 0.0,
                'error': None,
                'matched_qa_id': None,
                'is_public': False
            }
    
    def _calculate_match_score(self, comment: str, qa_pair: Dict) -> float:
        """计算评论与 Q&A 的匹配分数 (0-1)"""
        
        question = qa_pair.get('question', '')
        keywords = qa_pair.get('keywords', []) or []
        
        score = 0.0
        
        # 1. 关键字匹配 (权重高，1.0)
        if keywords:
            matched_keywords = [kw for kw in keywords if kw in comment]
            keyword_score = len(matched_keywords) / max(len(keywords), 1)
            score += keyword_score * self.keyword_weight
        
        # 2. 问题文本相似度 (字符重合度，权重 0.5)
        if question:
            common_chars = set(comment) & set(question)
            semantic_score = len(common_chars) / max(len(set(question)), 1)
            score += semantic_score * self.semantic_weight
        
        return min(score, 1.0)
