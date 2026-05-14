"""
SegmentPlayer 单元测试 (v4.0)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from playback.segment_player import SegmentPlayer


class TestSegmentPlayer:
    """SegmentPlayer 核心功能测试"""

    @pytest.fixture
    def sample_segments(self):
        return [
            {"start": 0, "end": 15, "text": "开场白", "visual": "wide"},
            {"start": 15, "end": 30, "text": "核心卖点", "visual": "closeup"},
            {"start": 30, "end": 45, "text": "互动引导", "visual": "wide"},
        ]

    @pytest.fixture
    def product_data(self, sample_segments):
        return {
            'id': 1,
            'name': '测试产品',
            'duration': 45,
            'script_segments': sample_segments
        }

    @pytest.fixture
    def config(self):
        return {'playback': {'default_duration': 60}}

    @pytest.fixture
    def player(self, config):
        return SegmentPlayer(config)

    def test_init_state(self, player):
        """初始状态应为未播放"""
        assert player.is_playing() is False
        assert player.get_progress() == 0.0
        assert player.get_segment_count() == 0

    def test_load_product(self, player, product_data):
        """加载产品后应有正确的分段数"""
        player.load_product(product_data)
        assert player.get_segment_count() == 3
        assert player.get_total_duration() == 45.0

    def test_load_product_without_segments(self, player, product_data):
        """无分段时使用默认时长"""
        product_data['script_segments'] = []
        product_data['duration'] = 0
        player.load_product(product_data)
        assert player.get_segment_count() == 0
        assert player.get_total_duration() == 60.0

    def test_play_and_pause(self, player, product_data):
        """播放和暂停"""
        player.load_product(product_data)
        assert player.is_playing() is False

        player.play()
        assert player.is_playing() is True

        player.pause()
        assert player.is_playing() is False

        player.resume()
        assert player.is_playing() is True

    def test_tick_advances_progress(self, player, product_data):
        """tick 后进度应推进"""
        player.load_product(product_data)
        player.play()

        result = player.tick(1000)  # 1 秒
        assert player.get_elapsed() > 0.9

    def test_segment_transition(self, player, product_data):
        """进入新分段时 tick 应返回新索引"""
        player.load_product(product_data)
        player.play()

        # 在分段 0 内
        result = player.tick(5000)
        assert player.get_current_segment_index() == 0

        # 跨入分段 1 (15s)
        player.skip_to(16.0)
        result = player.tick(100)
        assert player.get_current_segment_index() == 1

    def test_is_finished(self, player, product_data):
        """播放完毕后 is_finished 应返回 True"""
        player.load_product(product_data)
        player.play()

        player.tick(46000)  # 超过总时长
        assert player.is_finished() is True
        assert player.get_progress() == 1.0

    def test_reset(self, player, product_data):
        """reset 后应回到初始状态"""
        player.load_product(product_data)
        player.play()
        player.tick(10000)
        assert player.get_elapsed() > 0

        player.reset()
        assert player.get_elapsed() == 0.0
        assert player.get_current_segment_index() == -1
        assert player.is_playing() is False

    def test_skip_to(self, player, product_data):
        """跳转到指定时间"""
        player.load_product(product_data)
        player.play()

        player.skip_to(25.0)
        assert 24.0 < player.get_elapsed() < 26.0

    def test_no_segments_tick(self, player, product_data):
        """无分段时 tick 不抛异常"""
        product_data['script_segments'] = []
        player.load_product(product_data)
        player.play()

        result = player.tick(1000)  # 不应抛异常
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
