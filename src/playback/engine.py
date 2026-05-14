"""
Playback Engine - Core State Machine for Product Loop Playback
播放引擎 — QTimer 状态机核心 (v4.0)

职责:
- 管理产品循环播放（顺序/随机）
- 整合 ObsController + SegmentPlayer + OrderMatcher
- 通过 PyQt6 信号与 GUI 通信
- QTimer 每 100ms tick 驱动状态机

架构:
┌─────────────────────────────────────────────────────┐
│                  PlaybackEngine                      │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ ObsController │  │SegmentPlayer │  │OrderMatcher│ │
│  │ (场景切换)     │  │ (分段时间追踪)│  │ (评论匹配) │ │
│  └───────────────┘  └──────────────┘  └───────────┘ │
│                          │                          │
│                    QTimer(100ms)                     │
│                          │                          │
│                    PyQt6 signals                     │
└─────────────────────────────────────────────────────┘
"""

import logging
import random
from typing import Dict, Any, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .obs_controller import ObsController
from .segment_player import SegmentPlayer
from .order_matcher import OrderMatcher
from ..core.enums import PlaybackState, LiveStatus
from ..data.services import ProductStateService

logger = logging.getLogger(__name__)


class PlaybackEngine(QObject):
    """
    播放引擎 — QTimer 驱动的状态机

    使用示例:
        engine = PlaybackEngine(config)
        engine.initialize_products(products_list)

        # 连接 GUI 信号
        engine.state_changed.connect(ui.on_state_change)
        engine.product_switched.connect(ui.on_product_switch)

        engine.start()
    """

    # === PyQt6 信号定义 ===

    # 播放状态变化
    state_changed = pyqtSignal(str, str)          # (old_state, new_state)

    # 产品切换
    product_switched = pyqtSignal(int, str)       # (product_id, product_name)

    # 分段进度
    segment_changed = pyqtSignal(int, int)         # (current_index, total)
    progress_updated = pyqtSignal(float)           # (0.0~1.0)

    # 点播事件
    order_received = pyqtSignal(str, str)          # (username, comment)
    order_matched = pyqtSignal(int, str, float)    # (product_id, name, confidence)
    order_rejected = pyqtSignal(str)               # (reason)

    # 日志
    log_message = pyqtSignal(str)

    def __init__(self, config: Dict[str, Any]):
        super().__init__()

        self.config = config
        playback_cfg = config.get('playback', {})

        # 播放配置
        self._loop_mode = playback_cfg.get('loop_mode', 'sequential')
        self._transition_delay = playback_cfg.get('transition_delay', 2)
        self._enable_order = playback_cfg.get('enable_comment_order', True)
        self._tick_ms = playback_cfg.get('tick_interval_ms', 100)

        # 子模块
        self._obs = ObsController(config)
        self._segment_player = SegmentPlayer(config)
        self._order_matcher = OrderMatcher(config)

        # 产品数据
        self._products: List[Dict[str, Any]] = []
        self._current_index: int = -1
        self._play_order: List[int] = []  # 播放顺序（随机模式下 shuffle 后的索引列表）

        # 状态
        self._state = PlaybackState.IDLE
        self._transition_timer: float = 0.0  # 切换等待计时（秒）

        # QTimer 驱动
        self._tick_timer = QTimer()
        self._tick_timer.setInterval(self._tick_ms)
        self._tick_timer.timeout.connect(self._on_tick)

        # 产品状态服务
        self._product_service = ProductStateService()

    # ========== 公共 API ==========

    def initialize_products(self, products: List[Dict[str, Any]]):
        """
        初始化产品列表

        Args:
            products: 产品数据列表 [{id, name, product_alias, script_segments, ...}]
        """
        self._products = products
        self._build_play_order()
        self._obs.register_all_from_products(products)
        self._log(f"已加载 {len(products)} 个产品")

    def start(self):
        """启动播放引擎"""
        if not self._products:
            self._log("无产品数据，无法启动", level='error')
            self._transition_to(PlaybackState.ERROR)
            return

        self._transition_to(PlaybackState.LOADING)
        self._current_index = 0
        self._build_play_order()

        try:
            # 连接 OBS
            if self._obs.is_available():
                self._obs.connect()

            # 加载第一个产品
            self._load_current_product()
            self._transition_to(PlaybackState.PLAYING)
            self._tick_timer.start()
            self._log("播放引擎已启动")

        except Exception as e:
            self._log(f"启动失败: {e}", level='error')
            self._transition_to(PlaybackState.ERROR)

    def stop(self):
        """停止播放引擎"""
        self._tick_timer.stop()
        self._segment_player.reset()
        self._transition_to(PlaybackState.STOPPED)
        self._log("播放引擎已停止")

    def pause(self):
        """暂停播放"""
        if self._state == PlaybackState.PLAYING:
            self._segment_player.pause()
            self._transition_to(PlaybackState.PAUSED)

    def resume(self):
        """恢复播放"""
        if self._state == PlaybackState.PAUSED:
            self._segment_player.resume()
            self._transition_to(PlaybackState.PLAYING)

    def next_product(self):
        """手动跳转到下一个产品"""
        self._advance_to_next()

    def switch_to_product(self, product_id: int):
        """
        切换到指定产品（评论点播触发）

        Args:
            product_id: 目标产品 ID
        """
        # 查找产品索引
        for i, p in enumerate(self._products):
            if p.get('id') == product_id:
                self._transition_to(PlaybackState.SWITCHING)
                self._current_index = i
                self._load_current_product()
                self._transition_to(PlaybackState.PLAYING)
                self.product_switched.emit(product_id, p.get('name', ''))
                return

        self._log(f"未找到产品: id={product_id}", level='warning')

    def handle_comment(self, username: str, content: str,
                       public_qa: List[Dict] = None):
        """
        处理用户评论 — 尝试点播匹配

        Args:
            username: 用户名
            content: 评论内容
            public_qa: 公共 Q&A 列表（可选）
        """
        self.order_received.emit(username, content)

        if not self._enable_order:
            self.order_rejected.emit("点播功能未启用")
            return

        result = self._order_matcher.match(content, self._products, public_qa)

        if result:
            self.order_matched.emit(
                result['product_id'],
                result['product_name'],
                result['confidence']
            )
            self._log(f"点播匹配: {username} → {result['product_name']} "
                      f"(confidence={result['confidence']:.2f})")

            # 如果不是当前产品，执行切换
            current = self._get_current_product()
            if not current or current.get('id') != result['product_id']:
                self.switch_to_product(result['product_id'])
        else:
            self.order_rejected.emit("未匹配到产品")

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态摘要"""
        current = self._get_current_product()
        return {
            'state': self._state.value,
            'loop_mode': self._loop_mode,
            'current_product': current.get('name', '') if current else '',
            'current_index': self._current_index,
            'total_products': len(self._products),
            'progress': self._segment_player.get_progress(),
            'elapsed': self._segment_player.get_elapsed(),
            'segment': self._segment_player.get_current_segment_index(),
            'total_segments': self._segment_player.get_segment_count(),
        }

    # ========== 内部方法 ==========

    def _on_tick(self):
        """QTimer 回调 — 状态机主循环"""
        if self._state not in (PlaybackState.PLAYING, PlaybackState.SWITCHING):
            return

        # 推进分段播放器
        new_seg = self._segment_player.tick(self._tick_ms)
        if new_seg is not None:
            self.segment_changed.emit(
                new_seg,
                self._segment_player.get_segment_count()
            )

        # 更新进度
        self.progress_updated.emit(self._segment_player.get_progress())

        # 检查是否播放完毕
        if self._segment_player.is_finished():
            self._advance_to_next()

    def _advance_to_next(self):
        """推进到下一个产品"""
        self._transition_to(PlaybackState.SWITCHING)

        # 下一个索引
        if self._loop_mode == 'random':
            self._current_index = (self._current_index + 1) % len(self._play_order)
        else:
            self._current_index = (self._current_index + 1) % len(self._products)

        if self._current_index >= len(self._products):
            self._current_index = 0
            if self._loop_mode == 'random':
                self._build_play_order()

        self._load_current_product()
        self._transition_to(PlaybackState.PLAYING)

    def _load_current_product(self):
        """加载当前产品到 SegmentPlayer + OBS"""
        product = self._get_current_product()
        if not product:
            return

        pid = product.get('id')
        pname = product.get('name', '')

        # 加载分段数据
        self._segment_player.load_product(product)
        self._segment_player.play()

        # 切换 OBS 场景
        if self._obs.is_available():
            self._obs.switch_to_product(pid)

        self.product_switched.emit(pid, pname)
        self._log(f"当前产品: {pname} (index={self._current_index})")

    def _get_current_product(self) -> Optional[Dict[str, Any]]:
        """获取当前产品"""
        if not self._products:
            return None

        idx = self._current_index
        if self._loop_mode == 'random' and self._play_order:
            idx = self._play_order[min(idx, len(self._play_order) - 1)]
        else:
            idx = min(idx, len(self._products) - 1)

        return self._products[idx] if idx >= 0 else None

    def _build_play_order(self):
        """构建播放顺序（随机模式）"""
        if self._loop_mode == 'random' and self._products:
            self._play_order = list(range(len(self._products)))
            random.shuffle(self._play_order)
            self._current_index = 0

    def _transition_to(self, new_state: PlaybackState):
        """状态转换"""
        old = self._state
        self._state = new_state
        self.state_changed.emit(old.value, new_state.value)
        logger.debug(f"PlaybackEngine: {old.value} → {new_state.value}")

    def _log(self, message: str, level: str = 'info'):
        """发送日志"""
        getattr(logger, level)(message)
        self.log_message.emit(message)

    # ========== 属性访问 ==========

    @property
    def state(self) -> PlaybackState:
        return self._state

    @property
    def obs_controller(self) -> ObsController:
        return self._obs

    @property
    def segment_player(self) -> SegmentPlayer:
        return self._segment_player

    @property
    def order_matcher(self) -> OrderMatcher:
        return self._order_matcher
