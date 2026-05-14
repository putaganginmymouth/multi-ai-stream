"""
OrderMatcher 单元测试 (v4.0)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from playback.order_matcher import OrderMatcher


class TestOrderMatcher:
    """OrderMatcher 核心功能测试"""

    @pytest.fixture
    def products(self):
        return [
            {
                'id': 1,
                'name': '1号房车-豪华版',
                'product_alias': '1号,一号,1号房车,豪华版',
                'qa_pairs': [
                    {'question': '价格多少', 'answer': '88万', 'keywords': ['价格', '多少钱']},
                ]
            },
            {
                'id': 2,
                'name': '2号房车-经济版',
                'product_alias': '2号,二号,2号房车,经济版',
                'qa_pairs': [
                    {'question': '尺寸多大', 'answer': '5.9米', 'keywords': ['尺寸', '多大', '大小']},
                ]
            },
        ]

    @pytest.fixture
    def public_qa(self):
        return [
            {
                'id': 101,
                'question': '保修多久',
                'answer': '三年保修',
                'keywords': ['保修', '售后'],
                'linked_product_id': 1,
            }
        ]

    @pytest.fixture
    def config(self):
        return {
            'playback': {
                'order_match_min_confidence': 0.5,
                'order_cooldown_seconds': 0,  # 测试时无冷却
            }
        }

    @pytest.fixture
    def matcher(self, config):
        return OrderMatcher(config)

    def test_alias_match_exact(self, matcher, products):
        """评论包含别名时应精确匹配"""
        result = matcher.match('看看1号房车', products)
        assert result is not None
        assert result['product_id'] == 1
        assert result['source'] == 'alias'
        assert result['confidence'] == 1.0

    def test_alias_match_partial(self, matcher, products):
        """别名部分匹配"""
        result = matcher.match('一号在哪里', products)
        assert result is not None
        assert result['product_id'] == 1

    def test_alias_match_second_product(self, matcher, products):
        """匹配第二个产品"""
        result = matcher.match('看看2号房车', products)
        assert result is not None
        assert result['product_id'] == 2
        assert result['source'] == 'alias'

    def test_no_match(self, matcher, products):
        """无关评论应返回 None"""
        result = matcher.match('今天天气真好', products)
        assert result is None

    def test_qa_match_by_keywords(self, matcher, products):
        """通过 Q&A 关键词匹配"""
        result = matcher.match('这个多少钱', products)
        assert result is not None
        assert result['product_id'] == 1
        assert result['source'] == 'private_qa'

    def test_public_qa_match(self, matcher, products, public_qa):
        """通过公共 Q&A linked_product_id 匹配"""
        result = matcher.match('保修多久啊', products, public_qa)
        assert result is not None
        assert result['product_id'] == 1
        assert result['source'] == 'public_qa'

    def test_empty_comment(self, matcher, products):
        """空评论应返回 None"""
        assert matcher.match('', products) is None
        assert matcher.match(None, products) is None

    def test_empty_products(self, matcher):
        """无产品时应返回 None"""
        assert matcher.match('1号房车', []) is None

    def test_cooldown(self, products):
        """冷却期内应跳过匹配"""
        import time
        config = {'playback': {'order_match_min_confidence': 0.5, 'order_cooldown_seconds': 999}}
        matcher = OrderMatcher(config)

        result1 = matcher.match('1号房车', products)
        assert result1 is not None

        # 冷却期内第二次匹配应返回 None
        result2 = matcher.match('2号房车', products)
        assert result2 is None

        # 重置后应可匹配
        matcher.reset_cooldown()
        result3 = matcher.match('2号房车', products)
        assert result3 is not None

    def test_get_last_match(self, matcher, products):
        """获取上次匹配信息"""
        matcher.match('1号房车', products)
        last = matcher.get_last_match()
        assert last is not None
        assert last['product_id'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
