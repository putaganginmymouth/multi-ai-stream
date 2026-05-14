"""
Streaming Lip-Sync Pipeline - Real-time Digital Human Broadcast
流式数字人口播管线 (v4.0)

核心设计:
- 双缓冲架构：播放当前段 + 异步预生成下一段
- LLM 文案 → TTS 音频 → LivePortrait 口型视频帧
- 全程流式，无需预生成文件
- 支持评论点播中断

工作模式:
1. LLM 生成初始文案 → TTS → LivePortrait 开始播放
2. 播放同时，LLM 异步生成下一段文案（双缓冲）
3. 当前段播完 → swap 到下一段（无缝切换）
4. 评论点播 → 中断当前段，LLM 即时生成新产品内容
"""

import logging
import threading
from typing import Dict, Any, Optional, Iterator, List, Callable
from pathlib import Path

from ..core.base import Base
from ..core.enums import PipelineBufferState
from ..core.exceptions import ContentError

logger = logging.getLogger(__name__)


class StreamBuffer:
    """
    双缓冲容器

    维护当前播放段和预生成的下一段。
    线程安全：使用 Lock 保护读写操作。
    """

    def __init__(self):
        self._current: Optional[Dict[str, Any]] = None
        self._next: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._state = PipelineBufferState.EMPTY

    def put_current(self, segment: Dict[str, Any]):
        """设置当前播放段"""
        with self._lock:
            self._current = segment
            self._state = PipelineBufferState.PLAYING

    def put_next(self, segment: Dict[str, Any]):
        """设置预生成的下一段"""
        with self._lock:
            self._next = segment
            if self._state == PipelineBufferState.PLAYING:
                self._state = PipelineBufferState.READY

    def swap(self) -> Optional[Dict[str, Any]]:
        """
        切换到下一段

        Returns:
            被替换掉的旧当前段（可用于清理），无下一段时返回 None
        """
        with self._lock:
            if self._next is None:
                return None

            old = self._current
            self._current = self._next
            self._next = None
            self._state = PipelineBufferState.PLAYING if self._current else PipelineBufferState.EMPTY
            return old

    def get_current(self) -> Optional[Dict[str, Any]]:
        """获取当前播放段"""
        with self._lock:
            return self._current

    def has_next(self) -> bool:
        """是否有预生成的下一段"""
        with self._lock:
            return self._next is not None

    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self._current = None
            self._next = None
            self._state = PipelineBufferState.EMPTY

    @property
    def state(self) -> PipelineBufferState:
        return self._state


class StreamingLipSyncPipeline(Base):
    """
    流式数字人口播管线

    使用示例:
        pipeline = StreamingLipSyncPipeline(
            config=config,
            script_generator=script_gen_handler,
            tts_handler=tts_handler,
            avatar_engine=liveportrait_engine
        )
        pipeline.start(product_info="豪华房车，5.9米，88万")
        for frame in pipeline.stream_frames():
            # 将 frame 发送给 OBS
            pass

    架构:
    ┌───────────────────────────────────────────────┐
    │          StreamingLipSyncPipeline              │
    │                                               │
    │  StreamBuffer (双缓冲)                          │
    │  ┌──────────┐    ┌──────────┐                 │
    │  │ current  │ ←→ │   next   │                 │
    │  │ (播放中)  │    │ (预生成) │                 │
    │  └──────────┘    └──────────┘                 │
    │       │                ▲                       │
    │       ▼                │                       │
    │  LivePortrait    LLM+TTS 异步线程              │
    └───────────────────────────────────────────────┘
    """

    def __init__(self, config: Dict[str, Any],
                 script_generator, tts_handler, avatar_engine):
        super().__init__()

        self.config = config
        self.script_generator = script_generator      # ScriptGeneratorHandler
        self.tts_handler = tts_handler                # TTSHandler
        self.avatar_engine = avatar_engine            # LivePortraitEngine or BaseAvatar

        self.buffer = StreamBuffer()

        # 输出配置
        output_cfg = config.get('output', {})
        self._output_dir = Path(output_cfg.get('video_dir', './output/videos'))
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # 数字人形象路径
        self._avatar_image = config.get('avatar', {}).get('avatar_image', '')

        # 播放控制
        self._is_running = False
        self._prefetch_thread: Optional[threading.Thread] = None

        # 回调
        self._on_segment_start: Optional[Callable] = None
        self._on_segment_end: Optional[Callable] = None
        self._on_error: Optional[Callable] = None

    def set_callbacks(self, on_segment_start=None, on_segment_end=None, on_error=None):
        """设置回调函数"""
        self._on_segment_start = on_segment_start
        self._on_segment_end = on_segment_end
        self._on_error = on_error

    def start(self, product_info: str):
        """
        启动流式管线

        Args:
            product_info: 产品信息文本，作为 LLM 生成文案的上下文
        """
        self._is_running = True
        self.buffer.clear()

        try:
            # 生成初始段（文案 → TTS 音频）
            initial_script = self.script_generator.handle(product_info)
            initial_audio = self.tts_handler.handle(initial_script)

            self.buffer.put_current({
                'script': initial_script,
                'audio_path': str(initial_audio),
                'product_info': product_info
            })

            logger.info(f"流式管线已启动: {product_info[:50]}...")

            # 通知回调
            if self._on_segment_start:
                self._on_segment_start(product_info)

            # 启动异步预生成下一段
            self._prefetch_next(product_info)

        except Exception as e:
            logger.error(f"启动流式管线失败: {e}")
            if self._on_error:
                self._on_error(str(e))
            raise ContentError(f"流式管线启动失败: {e}")

    def stream_frames(self, fps: int = 30) -> Iterator:
        """
        流式生成视频帧

        每次调用返回一帧画面（numpy array），可直接送入 OBS Virtual Camera。
        当前段播完时自动 swap 到下一段。

        Yields:
            np.ndarray: RGB 视频帧
        """
        if not self._is_running:
            return

        current = self.buffer.get_current()
        if not current:
            logger.warning("缓冲区为空，无法生成帧")
            return

        # 使用 LivePortrait 逐帧生成
        frame_iter = self.avatar_engine.generate_stream(
            audio_path=current['audio_path'],
            image_path=self._avatar_image or current.get('avatar_image', ''),
            fps=fps
        )

        for frame in frame_iter:
            if not self._is_running:
                break
            yield frame

        # 当前段播完，尝试切换
        if self._on_segment_end:
            self._on_segment_end(current.get('product_info', ''))

        self._maybe_swap()

    def _maybe_swap(self):
        """如果下一段就绪，执行切换"""
        if self.buffer.has_next():
            old = self.buffer.swap()
            if old and old.get('audio_path'):
                self._cleanup_audio(old['audio_path'])

            new_current = self.buffer.get_current()
            if new_current and self._on_segment_start:
                self._on_segment_start(new_current.get('product_info', ''))

            logger.info("缓冲段切换完成")
            return True
        return False

    def handle_order(self, product_info: str):
        """
        处理评论点播 — 中断当前播放，切换到新产品

        Args:
            product_info: 新产品的描述信息
        """
        logger.info(f"点播切换: {product_info[:50]}...")

        # 停止预生成
        self._is_running = False

        # 清空缓冲区
        current = self.buffer.get_current()
        if current and current.get('audio_path'):
            self._cleanup_audio(current['audio_path'])
        self.buffer.clear()

        # 重新启动（新产品）
        self._is_running = True
        self.start(product_info)

    def stop(self):
        """停止管线"""
        self._is_running = False
        self.buffer.clear()

        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=3)

        logger.info("流式管线已停止")

    def _prefetch_next(self, context: str):
        """异步预生成下一段文案 + TTS"""

        def _run():
            if not self._is_running:
                return

            try:
                next_script = self.script_generator.handle(
                    f"继续介绍产品，上段讲了：{context[:200]}...请从新的角度继续介绍。"
                )
                next_audio = self.tts_handler.handle(next_script)

                if self._is_running:  # 可能在生成过程中被停止
                    self.buffer.put_next({
                        'script': next_script,
                        'audio_path': str(next_audio)
                    })
                    logger.debug(f"预生成完成: {len(next_script)} 字符")

            except Exception as e:
                logger.error(f"预生成失败: {e}")
                if self._on_error:
                    self._on_error(f"预生成失败: {e}")

        self._prefetch_thread = threading.Thread(
            target=_run, daemon=True, name='pipeline-prefetch'
        )
        self._prefetch_thread.start()

    def _cleanup_audio(self, audio_path: str):
        """清理临时音频文件"""
        try:
            path = Path(audio_path)
            if path.exists() and path.parent == self._output_dir:
                path.unlink(missing_ok=True)
        except Exception:
            pass  # 清理失败不影响主流程

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_buffer_state(self) -> PipelineBufferState:
        return self.buffer.state
