"""
Order Matcher - Comment-to-Product Matching Engine
评论点播匹配器 (v4.0)

职责:
- 接收用户评论 → 匹配对应产品
- 四级匹配策略：别名匹配 → 私有Q&A → 公共Q&A → 无匹配
- 冷却机制防止频繁切换

设计模式：策略模式（多种匹配策略组合）
"""

import logging
import time
from typing import Dict, Any, List, Optional

from ..core.base import Base

logger = logging.getLogger(__name__)


class OrderMatcher(Base):
    """
    评论点播匹配器

    匹配优先级（从高到低）:
    1. 产品别名直接匹配（product_alias 关键词）
    2. 私有 Q&A 匹配（产品的 qa_pairs）
    3. 公共 Q&A 匹配（PublicQA.linked_product_id）
    4. 返回 None（无匹配）

    使用示例:
        matcher = OrderMatcher(config)
        result = matcher.match("看看1号房车", products, qa_service)
        if result:
            engine.switch_to_product(result['product_id'])
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__()

        playback_cfg = config.get('playback', {})
        self._min_confidence = playback_cfg.get('order_match_min_confidence', 0.6)
        self._cooldown_seconds = playback_cfg.get('order_cooldown_seconds', 10)

        self._last_match_time: float = 0.0
        self._last_matched_product_id: Optional[int] = None

    def match(self, comment: str, products: List[Dict[str, Any]],
              public_qa_list: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        匹配评论到产品

        Args:
            comment: 用户评论文本
            products: 产品列表 [{id, name, product_alias, qa_pairs, ...}]
            public_qa_list: 公共 Q&A 列表 [{id, question, answer, keywords, linked_product_id, ...}]

        Returns:
            dict or None:
                {
                    'product_id': int,
                    'product_name': str,
                    'confidence': float (0.0~1.0),
                    'source': 'alias'|'private_qa'|'public_qa',
                    'reply_text': str (可选，自动回复话术)
                }
        """
        if not comment or not products:
            return None

        # 冷却检查
        if self._is_in_cooldown():
            logger.debug(f"点播冷却中，跳过匹配")
            return None

        # 1. 别名直接匹配（最高优先级）
        result = self._match_by_alias(comment, products)
        if result:
            return result

        # 2. 私有 Q&A 匹配
        result = self._match_by_private_qa(comment, products)
        if result:
            return result

        # 3. 公共 Q&A 匹配
        if public_qa_list:
            result = self._match_by_public_qa(comment, products, public_qa_list)
            if result:
                return result

        return None

    def _match_by_alias(self, comment: str,
                        products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """别名关键词匹配"""
        for product in products:
            aliases_str = product.get('product_alias', '') or ''
            if not aliases_str:
                continue

            aliases = [a.strip() for a in aliases_str.split(',') if a.strip()]
            for alias in aliases:
                if alias in comment:
                    self._record_match(product['id'])
                    product_name = product.get('name', '')
                    return {
                        'product_id': product['id'],
                        'product_name': product_name,
                        'confidence': 1.0,
                        'source': 'alias',
                        'reply_text': f"好的，马上带你看{product_name}！"
                    }

        return None

    def _match_by_private_qa(self, comment: str,
                             products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """私有 Q&A 匹配"""
        for product in products:
            qa_pairs = product.get('qa_pairs', []) or []
            for qa in qa_pairs:
                confidence = self._calculate_match_score(comment, qa)
                if confidence >= self._min_confidence:
                    self._record_match(product['id'])
                    return {
                        'product_id': product['id'],
                        'product_name': product.get('name', ''),
                        'confidence': confidence,
                        'source': 'private_qa',
                        'reply_text': qa.get('answer', '')[:50]
                    }

        return None

    def _match_by_public_qa(self, comment: str,
                            products: List[Dict[str, Any]],
                            public_qa_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """公共 Q&A 匹配 — 通过 linked_product_id 关联产品"""
        # 构建 product_id → product 的查找表
        product_map = {p['id']: p for p in products}

        for qa in public_qa_list:
            linked_id = qa.get('linked_product_id')
            if not linked_id or linked_id not in product_map:
                continue

            confidence = self._calculate_match_score(comment, qa)
            if confidence >= self._min_confidence:
                product = product_map[linked_id]
                self._record_match(linked_id)
                return {
                    'product_id': linked_id,
                    'product_name': product.get('name', ''),
                    'confidence': confidence,
                    'source': 'public_qa',
                    'reply_text': qa.get('answer', '')[:50]
                }

        return None

    def _calculate_match_score(self, comment: str, qa: Dict[str, Any]) -> float:
        """
        计算评论与 Q&A 的匹配分数 (0.0 ~ 1.0)

        策略:
        - 关键字匹配权重 0.7
        - 字符重合度权重 0.3
        """
        question = qa.get('question', '')
        keywords = qa.get('keywords', []) or []

        score = 0.0

        # 1. 关键字匹配（权重 0.7）
        if keywords:
            matched = sum(1 for kw in keywords if kw in comment)
            score += (matched / max(len(keywords), 1)) * 0.7

        # 2. 字符重合度（权重 0.3）
        if question:
            common = set(comment) & set(question)
            score += (len(common) / max(len(set(question)), 1)) * 0.3

        return min(score, 1.0)

    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却期"""
        if self._cooldown_seconds <= 0:
            return False
        return (time.time() - self._last_match_time) < self._cooldown_seconds

    def _record_match(self, product_id: int):
        """记录匹配时间和产品"""
        self._last_match_time = time.time()
        self._last_matched_product_id = product_id

    def reset_cooldown(self):
        """重置冷却（用于手动操作）"""
        self._last_match_time = 0.0
        self._last_matched_product_id = None

    def get_last_match(self) -> Optional[Dict[str, Any]]:
        """获取上次匹配信息"""
        if self._last_matched_product_id is None:
            return None
        return {
            'product_id': self._last_matched_product_id,
            'elapsed': time.time() - self._last_match_time
        }
