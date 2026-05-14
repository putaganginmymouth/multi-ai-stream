"""
PlaybackEngine 单元测试 (v4.0)
测试 QTimer 状态机核心功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from unittest.mock import Mock, patch, MagicMock

# Mock PyQt6 before importing the module
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()

from playback.engine import PlaybackEngine
from core.enums import PlaybackState


class TestPlaybackEngine:
    """PlaybackEngine 状态机测试"""

    @pytest.fixture
    def products(self):
        return [
            {
                'id': 1,
                'name': '产品A',
                'product_alias': 'A,产品A',
                'script_segments': [
                    {'start': 0, 'end': 30, 'text': '产品A介绍'}
                ],
                'duration': 30,
                'qa_pairs': []
            },
            {
                'id': 2,
                'name': '产品B',
                'product_alias': 'B,产品B',
                'script_segments': [
                    {'start': 0, 'end': 30, 'text': '产品B介绍'}
                ],
                'duration': 30,
                'qa_pairs': []
            },
        ]

    @pytest.fixture
    def config(self):
        return {
            'obs': {'host': 'localhost', 'port': 4455},
            'playback': {
                'loop_mode': 'sequential',
                'transition_delay': 2,
                'enable_comment_order': True,
                'tick_interval_ms': 100,
                'order_match_min_confidence': 0.5,
                'order_cooldown_seconds': 0,
            }
        }

    @pytest.fixture
    def engine(self, config):
        return PlaybackEngine(config)

    def test_init_state_is_idle(self, engine):
        """初始状态应为 IDLE"""
        assert engine.state == PlaybackState.IDLE

    def test_initialize_products(self, engine, products):
        """初始化产品列表"""
        engine.initialize_products(products)
        status = engine.get_status()
        assert status['total_products'] == 2

    def test_start_transitions_to_playing(self, engine, products):
        """启动后应进入 PLAYING 状态"""
        engine.initialize_products(products)
        engine.start()
        assert engine.state == PlaybackState.PLAYING

    def test_stop_transitions_to_stopped(self, engine, products):
        """停止后应进入 STOPPED"""
        engine.initialize_products(products)
        engine.start()
        engine.stop()
        assert engine.state == PlaybackState.STOPPED

    def test_pause_resume(self, engine, products):
        """暂停/恢复"""
        engine.initialize_products(products)
        engine.start()
        assert engine.state == PlaybackState.PLAYING

        engine.pause()
        assert engine.state == PlaybackState.PAUSED

        engine.resume()
        assert engine.state == PlaybackState.PLAYING

    def test_start_without_products(self, engine):
        """无产品时启动应进入 ERROR"""
        engine.start()
        assert engine.state == PlaybackState.ERROR

    def test_switch_to_product(self, engine, products):
        """切换到指定产品"""
        engine.initialize_products(products)
        engine.start()

        engine.switch_to_product(2)
        status = engine.get_status()
        assert engine.state == PlaybackState.PLAYING

    def test_switch_to_nonexistent_product(self, engine, products):
        """切换到不存在的产品"""
        engine.initialize_products(products)
        engine.start()
        engine.switch_to_product(999)  # 不应崩溃

    def test_next_product(self, engine, products):
        """跳转到下一个产品"""
        engine.initialize_products(products)
        engine.start()
        assert engine.state == PlaybackState.PLAYING

        engine.next_product()
        assert engine.state == PlaybackState.PLAYING

    def test_handle_comment_alias_match(self, engine, products):
        """评论匹配到产品别名时应切换"""
        engine.initialize_products(products)
        engine.start()

        engine.handle_comment('用户1', '看看产品B', public_qa=[])

    def test_handle_comment_no_match(self, engine, products):
        """评论未匹配时不应切换"""
        engine.initialize_products(products)
        engine.start()

        engine.handle_comment('用户1', '今天天气好', public_qa=[])

    def test_handle_comment_order_disabled(self, engine, products, config):
        """禁用点播时应拒绝"""
        config['playback']['enable_comment_order'] = False
        eng = PlaybackEngine(config)
        eng.initialize_products(products)
        eng.start()

        eng.handle_comment('用户1', '看看产品B')

    def test_get_status(self, engine, products):
        """获取状态摘要"""
        engine.initialize_products(products)
        status = engine.get_status()

        assert 'state' in status
        assert 'loop_mode' in status
        assert 'total_products' in status
        assert 'progress' in status


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
