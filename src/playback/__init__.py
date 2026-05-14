"""
Playback Engine Package (v4.0)
播放引擎模块 — 视频循环播放 + 评论点播切换

模块:
- engine.py: PlaybackEngine (QTimer 状态机核心)
- obs_controller.py: ObsController (OBS 场景切换)
- segment_player.py: SegmentPlayer (分段播放器)
- order_matcher.py: OrderMatcher (评论点播匹配器)
"""

from .obs_controller import ObsController
from .segment_player import SegmentPlayer
from .order_matcher import OrderMatcher
from .engine import PlaybackEngine

__all__ = ['PlaybackEngine', 'ObsController', 'SegmentPlayer', 'OrderMatcher']
