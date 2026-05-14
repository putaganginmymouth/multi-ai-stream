"""
Segment Player - Script Segment-based Timed Playback
基于 script_segments 数据的分段同步播放器 (v4.0)

职责:
- 根据 ProductAsset.script_segments 驱动播放
- 在正确的时间点触发分段切换信号
- 支持时间进度追踪和完成检测

segment 数据格式:
{
    "start": 0,        # 起始秒
    "end": 15,         # 结束秒
    "text": "...",     # 此段口播文案
    "visual": "wide"   # 可选：画面提示 (wide/closeup/transition)
}
"""

import logging
from typing import Dict, Any, List, Optional

from ..core.base import Base

logger = logging.getLogger(__name__)


class SegmentPlayer(Base):
    """
    分段播放器

    使用示例:
        player = SegmentPlayer(config)
        player.load_product(product_data)  # product_data 包含 script_segments
        player.play()

        while not player.is_finished():
            new_idx = player.tick(100)  # 100ms 增量
            if new_idx is not None:
                print(f"进入分段 {new_idx}: {player.get_current_segment()}")
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__()

        self.config = config

        # 当前产品信息
        self._current_product_id: Optional[int] = None
        self._segments: List[Dict[str, Any]] = []
        self._total_duration: float = 0.0

        # 播放状态
        self._elapsed: float = 0.0
        self._current_segment_idx: int = -1
        self._is_playing: bool = False

        # 默认时长（当视频未提供时长信息时）
        self._default_duration = config.get('playback', {}).get('default_duration', 60)

    def load_product(self, product_data: Dict[str, Any]):
        """
        加载产品及其分段数据

        Args:
            product_data: 产品数据字典，需包含 script_segments 字段
        """
        self._current_product_id = product_data.get('id')
        self._segments = product_data.get('script_segments', []) or []

        # 计算总时长
        video_duration = product_data.get('duration', 0) or 0
        if video_duration > 0:
            self._total_duration = float(video_duration)
        elif self._segments:
            # 从最后一段的 end 推算
            self._total_duration = max(
                seg.get('end', 0) for seg in self._segments
            )
        else:
            self._total_duration = float(self._default_duration)

        self._elapsed = 0.0
        self._current_segment_idx = -1
        self._is_playing = False

        logger.debug(
            f"加载产品 segments: product_id={self._current_product_id}, "
            f"segments={len(self._segments)}, duration={self._total_duration:.1f}s"
        )

    def play(self):
        """开始播放"""
        self._is_playing = True
        self._elapsed = 0.0
        self._current_segment_idx = -1
        logger.debug(f"SegmentPlayer 开始播放: product_id={self._current_product_id}")

    def pause(self):
        """暂停播放"""
        self._is_playing = False

    def resume(self):
        """恢复播放"""
        self._is_playing = True

    def tick(self, delta_ms: int) -> Optional[int]:
        """
        每次 tick 调用，推进播放进度

        Args:
            delta_ms: 距上次 tick 的毫秒数

        Returns:
            Optional[int]: 新进入的分段索引，无变化时返回 None
        """
        if not self._is_playing or not self._segments:
            return None

        self._elapsed += delta_ms / 1000.0

        new_idx = self._get_segment_at(self._elapsed)
        if new_idx != self._current_segment_idx:
            self._current_segment_idx = new_idx
            return new_idx

        return None

    def skip_to(self, seconds: float):
        """跳转到指定秒数"""
        self._elapsed = max(0.0, min(seconds, self._total_duration))
        self._current_segment_idx = self._get_segment_at(self._elapsed)

    def get_current_segment(self) -> Optional[Dict[str, Any]]:
        """获取当前分段信息"""
        if 0 <= self._current_segment_idx < len(self._segments):
            return self._segments[self._current_segment_idx]
        return None

    def get_progress(self) -> float:
        """
        获取播放进度

        Returns:
            float: 0.0 ~ 1.0
        """
        if self._total_duration <= 0:
            return 0.0
        return min(self._elapsed / self._total_duration, 1.0)

    def get_elapsed(self) -> float:
        """获取已播放秒数"""
        return self._elapsed

    def get_total_duration(self) -> float:
        """获取总时长"""
        return self._total_duration

    def is_finished(self) -> bool:
        """是否播放完毕"""
        return self._elapsed >= self._total_duration

    def is_playing(self) -> bool:
        return self._is_playing

    def get_segment_count(self) -> int:
        """获取分段总数"""
        return len(self._segments)

    def get_current_segment_index(self) -> int:
        """获取当前分段索引"""
        return self._current_segment_idx

    def reset(self):
        """重置播放器"""
        self._elapsed = 0.0
        self._current_segment_idx = -1
        self._is_playing = False

    def _get_segment_at(self, elapsed: float) -> int:
        """根据已播放时间查找对应分段索引"""
        for i, seg in enumerate(self._segments):
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            if start <= elapsed <= end:
                return i
        return self._current_segment_idx
