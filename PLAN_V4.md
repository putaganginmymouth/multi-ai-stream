# Multi-AI-Stream v4.0 播放引擎实现规划

> **版本**: v4.0  
> **创建日期**: 2026-05-14  
> **状态**: 规划阶段  
> **基于**: v3.0 代码审查 + 架构分析  

---

## 🎯 目标

实现缺失的三大核心功能，补全 v3.0 中"数据模型已就绪但运行引擎缺失"的部分：

| 功能 | v3.0 状态 | v4.0 目标 |
|------|-----------|-----------|
| 视频循环播放（顺序/随机） | 仅有数据模型和配置 | 完整的 PlaybackEngine 运行引擎 |
| 视频素材+TTS 口播时间对齐 | 仅有 script_segments 字段 | 基于分段标注的同步播放 |
| 评论点播（观众发评论切产品） | 仅有 enable_comment_order 开关 | 关键词匹配→产品切换→画面响应 |

---

## 🏗️ 架构决策（已确认）

| 决策 | 选择 | 理由 |
|------|------|------|
| 运行时架构 | **QTimer 状态机** | 与 SchedulerService 一致，简单可靠，与 PyQt6 信号槽天然兼容 |
| 口播对齐策略 | **预计算分段对齐** | 复用已有 script_segments 数据模型，无需新增依赖 |
| 点播匹配策略 | **关键词 + Q&A 联动** | 复用 CommentAggregator→ReplyGeneratorHandler 链路 |
| OBS 集成方式 | **OBS 场景切换** | 与现有 DouyinPlatform OBS 控制一脉相承 |

---

## 📁 v4.0 新增/修改文件树

```
multi-ai-stream/
├── src/
│   ├── playback/                     # ⭐ 新增：播放引擎模块
│   │   ├── __init__.py
│   │   ├── engine.py                 # PlaybackEngine (QTimer 状态机核心)
│   │   ├── states.py                 # PlaybackState 枚举 + 状态转换表
│   │   ├── obs_controller.py         # OBS 场景/媒体源切换控制器
│   │   ├── segment_player.py         # 基于 script_segments 的分段播放器
│   │   └── order_matcher.py          # 评论点播匹配器 (对接 Q&A)
│   │
│   ├── core/
│   │   └── enums.py                  # ✏️ 修改：新增 PlaybackState 枚举
│   │
│   ├── data/
│   │   ├── models.py                 # ✏️ 修改：ProductAsset 加 product_alias 字段
│   │   │                             #         PublicQA 加 linked_product_id 字段
│   │   ├── repository.py            # ✏️ 修改：新增 find_by_alias 方法
│   │   └── services.py              # ✏️ 修改：ProductStateService 加 get_all_products
│   │
│   ├── comment/
│   │   └── responder.py             # ✏️ 修改：SmartResponder 集成 OrderMatcher
│   │
│   ├── gui/
│   │   └── main_window.py           # ✏️ 修改：集成 PlaybackEngine 面板
│   │
│   └── content/
│       └── reply_generator.py        # ✏️ 修改：回复中携带 product_id 信息
│
├── configs/
│   └── config.yaml                   # ✏️ 修改：新增 playback 配置段
│
└── tests/
    ├── test_playback_engine.py       # ⭐ 新增
    ├── test_order_matcher.py         # ⭐ 新增
    └── test_segment_player.py        # ⭐ 新增
```

---

## 📐 核心架构设计

### PlaybackEngine 状态机

```
                    ┌──────────────────────────────────┐
                    │         PlaybackEngine            │
                    │   (QObject + QTimer 100ms tick)   │
                    └──────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │ OrderMatcher  │       │ SegmentPlayer │       │ ObsController │
    │ (评论→产品匹配)│       │ (分段同步播放) │       │ (OBS场景切换)  │
    └───────────────┘       └───────────────┘       └───────────────┘
            │                         │                         │
            ▼                         ▼                         ▼
    CommentAggregator          ProductAsset              OBS WebSocket
    ReplyGeneratorHandler      script_segments           Scene/Source API
```

### 状态流转图

```
                    ┌──────────┐
                    │  IDLE    │◄────────────────────────────┐
                    └────┬─────┘                             │
                         │ start()                           │
                         ▼                                   │
                    ┌──────────┐                             │
              ┌────►│ LOADING  │                             │
              │     └────┬─────┘                             │
              │          │ 加载产品列表成功                     │
              │          ▼                                   │
              │     ┌──────────┐   评论点播匹配命中             │
              │     │ PLAYING  │──────┐                      │
              │     └────┬─────┘      │                      │
              │          │            ▼                      │
              │          │       ┌──────────┐                │
              │          │       │ SWITCHING│──► 切换OBS场景   │
              │          │       └────┬─────┘                │
              │          │            │ 场景切换完成            │
              │          │            ▼                      │
              │          │       ┌──────────┐                │
              │          │       │ ALIGNING │──► 等待分段对齐   │
              │          │       └────┬─────┘                │
              │          │            │ 对齐完成               │
              │          └────────────┘                      │
              │         当前产品播放完毕，循环到下一个             │
              │                                              │
              │     ┌──────────┐                             │
              └─────│  PAUSED  │                             │
                    └────┬─────┘                             │
                         │ resume()                          │
                         └───────────────────────────────────┘
```

### 信号定义

```python
class PlaybackEngine(QObject):
    # 播放状态变化
    state_changed = pyqtSignal(str, str)          # (old_state, new_state)
    
    # 产品切换
    product_switched = pyqtSignal(int, str)       # (product_id, product_name)
    
    # 分段进度
    segment_progress = pyqtSignal(int, int)        # (current_segment, total_segments)
    playback_tick = pyqtSignal(float)              # (elapsed_seconds)
    
    # 点播事件
    order_received = pyqtSignal(str, str)          # (username, comment)
    order_matched = pyqtSignal(int, str, float)    # (product_id, product_name, confidence)
    
    # 日志
    log_message = pyqtSignal(str)
```

---

## 🎭 Phase 0: 数字人口型同步（LivePortrait 实时驱动）

> **前置背景**：现有 `ContentPipeline._process_lip_sync()` 是 TODO，LivePortrait 引擎是桩代码。本 Phase 将其补全为真正的实时数字人口播引擎。

### 方案选型：LivePortrait 实时驱动

**用户已确认选 LivePortrait 实时方案。** 与 LLM 实时生成文案配合，形成完整的实时数字人直播闭环。

| 维度 | LivePortrait 实时 | Wav2Lip 预生成 |
|------|-------------------|-----------------|
| 帧率 | **30fps+** | ~1fps |
| 实时性 | ✅ 真正实时 | ❌ 需预生成，文案固化 |
| LLM 联动 | ✅ 文案可随时变化 | ❌ 生成后无法修改 |
| GPU 需求 | RTX 3060+ (8GB VRAM) | CPU 可用 |
| 模型大小 | ~2GB | ~500MB |

### 8GB VRAM 可行性

```
本地 GPU (8GB) 显存分配:
├── LivePortrait 模型     ~2.0 GB
├── PyTorch 运行时        ~0.5 GB  
├── 推理缓冲区            ~1.0 GB
└── 剩余                  ~4.5 GB ✅

远程 API (不占本地 GPU):
├── DeepSeek API  →  LLM 文案生成
└── Edge-TTS       →  语音合成
```

**关键设计：LLM 和 TTS 全部走远程 API，本地 GPU 只服务 LivePortrait。** 8GB VRAM 完全够用。

### 实时数据流

```
┌─────────────────────────────────────────────────────────┐
│                   LivePortrait 实时管线                    │
│                                                         │
│  DeepSeek API ──→ 文案流 ──→ Edge-TTS ──→ 音频流         │
│    (~1s 延迟)               (~0.5s 延迟)    │            │
│                                             ▼            │
│  数字人形象 ────────────────────→ LivePortraitEngine      │
│  (静态图片)                          │                   │
│                                      ▼ 30fps 视频帧       │
│                              OBS Virtual Camera          │
│                                      │                   │
│                                      ▼                   │
│                              RTMP → 各直播平台            │
└─────────────────────────────────────────────────────────┘
```

**流水线设计**：每轮讲解 30-60 秒，LLM 在当前轮播放时提前生成下一轮文案，实现无缝衔接。

### 架构设计：StreamingLipSyncPipeline

与 v3.0 的静态 ContentPipeline 不同，v4.0 需要的是**流式处理管线**：

```python
class StreamingLipSyncPipeline:
    """
    流式数字人口播管线
    
    流程:
    1. LLM 生成下一段文案（在当前段播放时异步预生成）
    2. TTS 合成为音频
    3. LivePortrait 实时生成口型视频帧
    4. 视频帧通过 OBS Virtual Camera 输出
    
    特点:
    - 双缓冲：播放当前段 + 预生成下一段
    - 支持打断：评论点播可中断当前播放
    """
```

### 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/avatar/live_portrait.py` | ✏️ 重写 | 补全实际 LivePortrait 推理代码 |
| `src/content/streaming_pipeline.py` | ⭐ 新增 | StreamingLipSyncPipeline 流式管线 |
| `src/content/pipeline.py` | ✏️ 修改 | _process_lip_sync() 对接新管线 |
| `src/core/enums.py` | ✏️ 修改 | 新增 PipelineBufferState 枚举 |
| `scripts/install_liveportrait.sh` | ✏️ 修改 | 完善安装脚本 |

### 分步任务

#### Task 0.1: 补全 LivePortraitEngine 实际推理

**文件**: `src/avatar/live_portrait.py` — 替换桩代码

```python
def _load(self):
    """加载 LivePortrait 模型到 GPU"""
    import torch
    from liveportrait.inference import InferenceManager
    
    # 自动检测设备
    self._device = self._detect_best_device()
    device = torch.device(self._device.value)
    
    # 初始化推理管理器
    self._lp_instance = InferenceManager(
        model_path=self._model_path,
        device=device,
        batch_size=self._batch_size
    )
    self._lp_instance.load_models()
    
    logger.info(f"LivePortrait 加载成功: device={self._device.value}")


def sync_lips(self, audio_chunk: np.ndarray, source_image: np.ndarray) -> np.ndarray:
    """
    实时口型同步 — 核心方法
    
    Args:
        audio_chunk: 音频数据 (numpy array, 采样率 16kHz)
        source_image: 数字人源图像 (H, W, C)
        
    Returns:
        np.ndarray: 口型同步后的图像帧
    """
    if not self._model_loaded:
        raise AvatarError("模型未加载", "MODEL_NOT_LOADED")
    
    result = self._lp_instance.realtime_infer(
        audio=audio_chunk,
        source=source_image,
        resize=self._resize
    )
    return result['frame']


def generate_stream(self, audio_path: str, image_path: str,
                    fps: int = 30) -> Iterator[np.ndarray]:
    """
    流式生成 — 逐帧 yield 视频画面
    
    用于对接 OBS Virtual Camera，每帧直接输出。
    """
    import cv2
    
    # 加载音频和图像
    audio = self._load_audio(audio_path)
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 计算音频分块
    chunk_size = int(audio.shape[0] / (audio.shape[0] / 16000 * fps))
    
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        frame = self.sync_lips(chunk, image_rgb)
        yield frame
```

> **注意**：实际的 LivePortrait Python API 可能与上述伪代码略有差异。需要参考 https://github.com/KwaiVGI/LivePortrait 的实际接口。

#### Task 0.2: StreamingLipSyncPipeline 流式管线

**文件**: `src/content/streaming_pipeline.py`（新增）

```python
"""流式数字人口播管线 — 双缓冲 + 实时生成"""

import logging
import threading
from typing import Dict, Any, Optional, Iterator
from collections import deque
from pathlib import Path

from ..core.base import Base
from ..core.enums import PipelineBufferState
from ..core.exceptions import ContentError

logger = logging.getLogger(__name__)


class StreamBuffer:
    """双缓冲：当前播放段 + 预生成下一段"""
    
    def __init__(self):
        self._current: Optional[Dict] = None    # 正在播放的段
        self._next: Optional[Dict] = None       # 预生成的下一段
        self._lock = threading.Lock()
        self._state = PipelineBufferState.EMPTY
    
    def put_current(self, segment: Dict):
        with self._lock:
            self._current = segment
            self._state = PipelineBufferState.PLAYING
    
    def put_next(self, segment: Dict):
        with self._lock:
            self._next = segment
            self._state = PipelineBufferState.READY
    
    def swap(self) -> Optional[Dict]:
        """切换到下一段"""
        with self._lock:
            old = self._current
            self._current = self._next
            self._next = None
            self._state = PipelineBufferState.PLAYING if self._current else PipelineBufferState.EMPTY
            return old
    
    def get_current(self) -> Optional[Dict]:
        return self._current
    
    def has_next(self) -> bool:
        return self._next is not None
    
    @property
    def state(self) -> PipelineBufferState:
        return self._state


class StreamingLipSyncPipeline(Base):
    """
    流式数字人口播管线
    
    工作模式:
    1. LLM 生成初始文案 → TTS → LivePortrait 开始播放
    2. 播放同时，LLM 异步生成下一段文案
    3. 当前段播完 → swap 到下一段（无缝切换）
    4. 评论点播 → 中断当前段，LLM 生成点播内容
    
    全程不需要预生成视频文件，全部实时。
    """
    
    def __init__(self, config: Dict[str, Any],
                 script_generator, tts_handler, avatar_engine):
        super().__init__()
        
        self.config = config
        self.script_generator = script_generator   # ScriptGeneratorHandler
        self.tts_handler = tts_handler              # TTSHandler
        self.avatar_engine = avatar_engine          # LivePortraitEngine
        
        self.buffer = StreamBuffer()
        self._output_dir = Path(config.get('output', {}).get('video_dir', './output'))
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
        # 预生成线程
        self._prefetch_thread: Optional[threading.Thread] = None
        self._is_running = False
    
    def start(self, initial_product_info: str):
        """启动流式管线"""
        self._is_running = True
        
        # 生成初始段
        initial_script = self.script_generator.handle(initial_product_info)
        initial_audio = self.tts_handler.handle(initial_script)
        
        self.buffer.put_current({
            'script': initial_script,
            'audio_path': str(initial_audio)
        })
        
        # 启动预生成线程
        self._prefetch_next(initial_product_info)
    
    def get_next_frame(self) -> Optional[Iterator]:
        """获取下一帧视频输出（供 OBS Virtual Camera 消费）"""
        current = self.buffer.get_current()
        if not current:
            return None
        
        # 检查是否需要切换
        if not self.buffer.has_next():
            # 预生成还没完成，继续播当前
            pass
        
        return self.avatar_engine.generate_stream(
            audio_path=current['audio_path'],
            image_path=self.config.get('avatar_image', '')
        )
    
    def handle_order(self, product_info: str):
        """处理点播 — 中断当前，切换到新产品"""
        self._is_running = False  # 停止当前
        self.start(product_info)   # 重新开始新产品
    
    def stop(self):
        """停止管线"""
        self._is_running = False
    
    def _prefetch_next(self, context: str):
        """异步预生成下一段文案+TTS"""
        def _run():
            if not self._is_running:
                return
            try:
                next_script = self.script_generator.handle(
                    f"继续介绍产品，上段讲了：{context[:100]}..."
                )
                next_audio = self.tts_handler.handle(next_script)
                self.buffer.put_next({
                    'script': next_script,
                    'audio_path': str(next_audio)
                })
            except Exception as e:
                logger.error(f"预生成失败: {e}")
        
        self._prefetch_thread = threading.Thread(target=_run, daemon=True)
        self._prefetch_thread.start()
```

#### Task 0.3: 新增 PipelineBufferState 枚举

**文件**: `src/core/enums.py`

```python
class PipelineBufferState(StrEnum):
    """流式管线缓冲区状态"""
    EMPTY = "empty"        # 缓冲区空
    LOADING = "loading"    # 正在加载/生成
    READY = "ready"        # 下一段就绪
    PLAYING = "playing"    # 播放中
```

#### Task 0.4: 对接 ContentPipeline

**文件**: `src/content/pipeline.py` — 修改 `_process_lip_sync()`

```python
def _process_lip_sync(self, audio_path: str, avatar_engine,
                      output_name: str) -> str:
    """处理口型同步阶段 (v4.0: 对接 LivePortrait 流式管线)"""
    if hasattr(avatar_engine, 'generate_stream'):
        from .streaming_pipeline import StreamingLipSyncPipeline
        
        streaming = StreamingLipSyncPipeline(
            config=self.config,
            script_generator=self.handlers[ScriptStage.SCRIPT_GENERATION],
            tts_handler=self.handlers[ScriptStage.TTS_SYNTHESIS],
            avatar_engine=avatar_engine
        )
        self._streaming = streaming
        return str(self._output_dir / f"{output_name}_live")
    
    logger.warning("avatar_engine 不支持流式生成，跳过口型同步")
    return str(self._output_dir / f"{output_name}_synced.mp4")
```

#### Task 0.5: 完善安装脚本

**文件**: `scripts/install_liveportrait.sh`

```bash
#!/bin/bash
# LivePortrait 模型安装脚本

MODEL_DIR="./assets/avatars/liveportrait"
mkdir -p "$MODEL_DIR"

echo "下载 LivePortrait 模型文件..."

# 从 HuggingFace 下载（约 2GB）
git clone https://huggingface.co/KwaiVGI/LivePortrait "$MODEL_DIR/hf_models"

# 安装 Python 依赖
pip install torch torchvision opencv-python numpy scipy

echo "✅ LivePortrait 安装完成"
```

---

## 📋 分阶段实施计划

### Phase 1: 基础设施（数据模型 + 枚举 + 配置）

#### Task 1.1: 扩展 PlaybackState 枚举

**文件**: `src/core/enums.py`

在现有枚举后追加：

```python
class PlaybackState(StrEnum):
    """播放引擎状态枚举"""
    IDLE = "idle"               # 未启动
    LOADING = "loading"         # 加载产品列表中
    PLAYING = "playing"         # 正常循环播放
    SWITCHING = "switching"     # 正在切换产品（评论点播触发）
    ALIGNING = "aligning"       # 正在对齐分段
    PAUSED = "paused"           # 暂停
    STOPPED = "stopped"         # 已停止
    ERROR = "error"             # 错误状态
```

#### Task 1.2: 扩展数据模型

**文件**: `src/data/models.py`

在 `ProductAsset` 类中添加：

```python
# 在 name 字段后添加
product_alias = Column(String(500), default='')   # 产品别名(逗号分隔)，用于评论关键词匹配
                                                  # 如："1号,一号,1号房车,豪华越野版"
```

在 `PublicQA` 类中添加：

```python
# 在 priority 字段后添加
linked_product_id = Column(Integer, ForeignKey('product_assets.id'), nullable=True)
                                                  # 关联的产品 ID，命中此Q&A时可自动切换
```

#### Task 1.3: 扩展 Repository

**文件**: `src/data/repository.py`

在 `ProductAssetRepository` 中添加：

```python
def find_by_alias(self, keyword: str) -> Optional[Dict[str, Any]]:
    """根据别名关键词查找产品"""
    pass  # 实现：遍历所有产品，匹配 product_alias 字段

def find_all_active(self) -> List[Dict[str, Any]]:
    """获取所有活跃产品（用于播放列表）"""
    pass
```

#### Task 1.4: 扩展 ProductStateService

**文件**: `src/data/services.py`

```python
def get_all_products(self) -> List[Dict[str, Any]]:
    """获取所有产品（用于播放列表初始化）"""
    return self.asset_repo.find_all()

def get_product_count(self) -> int:
    """获取产品总数"""
    pass
```

#### Task 1.5: 新增 playback 配置段

**文件**: `configs/config.yaml`

```yaml
# 播放引擎配置
playback:
  enabled: true                     # 是否启用自动播放
  loop_mode: "sequential"           # sequential | random
  default_duration: 60              # 每个产品默认展示时长（秒），0=按视频时长
  transition_delay: 2               # 产品切换过渡时间（秒）
  tick_interval_ms: 100             # 状态机 tick 间隔（毫秒）
  enable_comment_order: true        # 是否启用评论点播
  order_match_min_confidence: 0.6   # 点播匹配最低置信度
  order_cooldown_seconds: 10        # 点播冷却时间（秒），防止频繁切换
```

---

### Phase 2: OBS 场景控制器

#### Task 2.1: ObsController 实现

**文件**: `src/playback/obs_controller.py`

```python
"""OBS 场景/媒体源切换控制器"""

import logging
from typing import Dict, Any, Optional
from ..core.base import Configurable

logger = logging.getLogger(__name__)


class ObsController(Configurable):
    """
    OBS 场景切换控制器
    
    职责:
    - 管理产品→OBS 场景的映射
    - 切换 OBS 场景（SetCurrentProgramScene）
    - 控制媒体源播放/暂停（SetMediaSourceSettings）
    
    设计模式：外观模式 (Facade)
    封装 OBS WebSocket 的复杂调用为简单接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self._obs_client = None
        self._host = config.get('obs', {}).get('host', 'localhost')
        self._port = config.get('obs', {}).get('port', 4455)
        self._password = config.get('obs', {}).get('password', '')
        
        # 场景映射：{product_id: scene_name}
        self._scene_map: Dict[int, str] = {}
        
        # 媒体源映射：{product_id: source_name}
        self._media_source_map: Dict[int, str] = {}
    
    def _validate_config(self) -> bool:
        return bool(self._host and self._port)
    
    def connect(self) -> bool:
        """连接 OBS WebSocket（复用现有 _connect_obs 逻辑）"""
        pass
    
    def disconnect(self):
        """断开连接"""
        pass
    
    def register_scene(self, product_id: int, scene_name: str):
        """注册产品→场景映射"""
        self._scene_map[product_id] = scene_name
    
    def switch_to_product(self, product_id: int) -> bool:
        """
        切换到指定产品的 OBS 场景
        
        1. 调用 SetCurrentProgramScene 切换到对应场景
        2. 如果有媒体源，调用 TriggerMediaSourcePlay 开始播放
        """
        pass
    
    def get_current_scene(self) -> str:
        """获取当前 OBS 场景名"""
        pass
    
    def list_scenes(self) -> list:
        """获取所有可用场景"""
        pass
```

---

### Phase 3: 分段播放器

#### Task 3.1: SegmentPlayer 实现

**文件**: `src/playback/segment_player.py`

```python
"""基于 script_segments 的分段同步播放器"""

import logging
from typing import Dict, Any, List, Optional
from ..core.base import Base

logger = logging.getLogger(__name__)


class SegmentPlayer(Base):
    """
    分段播放器
    
    职责:
    - 根据 ProductAsset.script_segments 数据驱动播放
    - 在正确的时间点触发放映切换信号
    - 支持时间进度追踪
    
    segment 数据结构:
    {
        "start": 0,        # 起始秒数
        "end": 15,         # 结束秒数
        "text": "...",     # 此段对应的口播文案
        "visual": "wide"   # 可选：画面提示（wide/closeup/transition）
    }
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        
        # 当前产品信息
        self._current_product_id: Optional[int] = None
        self._segments: List[Dict] = []
        self._total_duration: float = 0.0
        
        # 播放状态
        self._elapsed: float = 0.0           # 已播放秒数
        self._current_segment_idx: int = -1  # 当前分段索引
        self._is_playing: bool = False
    
    def load_product(self, product_data: Dict[str, Any]):
        """加载产品及其分段数据"""
        self._current_product_id = product_data.get('id')
        self._segments = product_data.get('script_segments', [])
        self._total_duration = product_data.get('duration', 0)
        self._elapsed = 0.0
        self._current_segment_idx = -1
        self._is_playing = False
    
    def tick(self, delta_ms: int) -> Optional[int]:
        """
        每 tick 调用一次，推进播放进度
        
        Args:
            delta_ms: 距上次 tick 的毫秒数
            
        Returns:
            int: 新进入的分段索引，无变化时返回 None
        """
        if not self._is_playing:
            return None
        
        self._elapsed += delta_ms / 1000.0
        
        # 检查是否进入新分段
        new_idx = self._get_segment_at(self._elapsed)
        if new_idx != self._current_segment_idx:
            old = self._current_segment_idx
            self._current_segment_idx = new_idx
            return new_idx
        
        return None
    
    def get_current_segment(self) -> Optional[Dict]:
        """获取当前分段信息"""
        if 0 <= self._current_segment_idx < len(self._segments):
            return self._segments[self._current_segment_idx]
        return None
    
    def get_progress(self) -> float:
        """获取播放进度 0.0~1.0"""
        if self._total_duration <= 0:
            return 0.0
        return min(self._elapsed / self._total_duration, 1.0)
    
    def is_finished(self) -> bool:
        """是否播放完毕"""
        return self._elapsed >= self._total_duration
    
    def reset(self):
        """重置播放器"""
        self._elapsed = 0.0
        self._current_segment_idx = -1
        self._is_playing = False
    
    def _get_segment_at(self, elapsed: float) -> int:
        """根据已播放时间查找对应分段"""
        for i, seg in enumerate(self._segments):
            if seg['start'] <= elapsed <= seg['end']:
                return i
        return self._current_segment_idx
```

---

### Phase 4: 评论点播匹配器

#### Task 4.1: OrderMatcher 实现

**文件**: `src/playback/order_matcher.py`

```python
"""评论点播匹配器 — 对接现有 Q&A 系统"""

import logging
from typing import Dict, Any, Optional
from ..core.base import Base

logger = logging.getLogger(__name__)


class OrderMatcher(Base):
    """
    评论点播匹配器
    
    职责:
    - 接收评论 → 匹配产品
    - 复用 ReplyGeneratorHandler 的 Q&A 匹配算法
    - 返回匹配结果 (product_id, confidence)
    
    匹配优先级:
    1. 产品别名直接匹配 (product_alias 关键词)
    2. 私有 Q&A 匹配 → linked_product_id
    3. 公共 Q&A 匹配 → linked_product_id
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        self._min_confidence = config.get('playback', {}).get(
            'order_match_min_confidence', 0.6
        )
        self._cooldown = config.get('playback', {}).get(
            'order_cooldown_seconds', 10
        )
        self._last_match_time = 0.0
    
    def match(self, comment: str, products: list,
              qa_service=None, state_service=None) -> Optional[Dict[str, Any]]:
        """
        匹配评论到产品
        
        Args:
            comment: 用户评论文本
            products: 产品列表 [{id, name, product_alias, qa_pairs, ...}]
            qa_service: PublicQAService 实例
            state_service: ProductStateService 实例
            
        Returns:
            dict: {product_id, product_name, confidence, source, reply_text}
            或 None（未匹配到）
        """
        # 冷却检查
        import time
        if time.time() - self._last_match_time < self._cooldown:
            return None
        
        # 1. 别名直接匹配
        result = self._match_by_alias(comment, products)
        if result:
            return result
        
        # 2. 私有 Q&A 匹配
        result = self._match_by_private_qa(comment, products)
        if result:
            return result
        
        # 3. 公共 Q&A 匹配
        result = self._match_by_public_qa(comment, qa_service)
        if result:
            return result
        
        return None
    
    def _match_by_alias(self, comment: str, products: list) -> Optional[Dict]:
        """别名关键词匹配"""
        for product in products:
            aliases = (product.get('product_alias', '') or '').split(',')
            for alias in aliases:
                alias = alias.strip()
                if alias and alias in comment:
                    self._last_match_time = __import__('time').time()
                    return {
                        'product_id': product['id'],
                        'product_name': product['name'],
                        'confidence': 1.0,
                        'source': 'alias',
                        'reply_text': f"好的，马上带你看{product['name']}！"
                    }
        return None
    
    def _match_by_private_qa(self, comment: str, products: list) -> Optional[Dict]:
        """私有 Q&A 匹配 → linked product"""
        from ..content.reply_generator import ReplyGeneratorHandler
        # 复用现有匹配算法，检查匹配到的Q&A是否关联了产品
        pass
    
    def _match_by_public_qa(self, comment: str, qa_service) -> Optional[Dict]:
        """公共 Q&A 匹配 → linked_product_id"""
        pass
```

---

### Phase 5: PlaybackEngine 核心

#### Task 5.1: PlaybackEngine 完整实现

**文件**: `src/playback/engine.py`

核心类，整合 ObsController + SegmentPlayer + OrderMatcher，实现完整状态机。

关键方法：
- `start()` — 加载产品列表 → 切换到 LOADING → PLAYING
- `stop()` — 停止播放 → IDLE
- `pause()` / `resume()` — 暂停/恢复
- `switch_to_product(product_id)` — 手动切换（评论点播触发）
- `_tick()` — QTimer 回调，每 100ms 执行一次状态机推进
- `_next_product()` — 顺序/随机选择下一个产品

信号连接：
- `state_changed` → MainWindow 更新 UI 状态
- `product_switched` → MainWindow 更新当前产品展示
- `segment_progress` → MainWindow 更新进度条
- `log_message` → MainWindow 日志区

#### Task 5.2: PlaybackEngine 集成到 MainWindow

**文件**: `src/gui/main_window.py`

1. 在 `__init__` 中初始化 `PlaybackEngine`
2. 连接信号槽更新 UI
3. 在直播控制面板中添加播放控制按钮（▶ 开始循环 / ⏸ 暂停 / ⏭ 下一个）

---

### Phase 6: 评论点播链路打通

#### Task 6.1: 修改 ReplyGeneratorHandler

**文件**: `src/content/reply_generator.py`

在 `generate_reply()` 返回结果中增加：
```python
'order_product_id': Optional[int],   # 点播产品ID
'order_confidence': float,           # 点播置信度
```

#### Task 6.2: 修改 CommentAggregator 集成

**文件**: `src/data/services.py`

在 `CommentAggregator._process_comment()` 中增加点播检测：
1. 评论 → ReplyGeneratorHandler.generate_reply()
2. 如果返回 `order_product_id` → 通知 PlaybackEngine

#### Task 6.3: SmartResponder 集成点播提示

**文件**: `src/comment/responder.py`

增加点播回复话术模板：
```python
"order_confirm": [
    "好的，马上为{nickname}切换到{product_name}！",
    "收到！正在展示{product_name}，请稍等~"
]
```

---

### Phase 7: 评论实时抓取（douyin-live + WebHook 统一架构）

> **背景分析**：三平台评论抓取现状 — 抖音有成熟开源库（douyin-live），快手和视频号没有可靠方案。采用"抖音直连 + 统一 WebHook 接收器"架构。

```
┌──────────────────────────────────────────────────┐
│              评论数据来源层（外部）                 │
│                                                  │
│  douyin-live ──→ DouyinCommentListener           │
│  Selenium脚本 ──→ POST /webhook/comment ─────┐   │
│  付费API服务 ───→ POST /webhook/comment ──┐  │   │
│                                          │  │   │
└──────────────────────────────────────────│──│───┘
                                           ▼  ▼
┌──────────────────────────────────────────────────┐
│     src/comment/webhook_receiver.py (新增)        │
│                                                  │
│  统一 WebHook 接收器 — 标准化外部评论输入           │
│  数据格式:                                        │
│  {                                               │
│    "platform": "douyin|kuaishou|wechat",         │
│    "user_id": "xxx",                             │
│    "username": "昵称",                            │
│    "content": "评论内容"                           │
│  }                                               │
│                                                  │
│     ↓ 转为 Comment 对象                           │
│     ↓ 接入 CommentAggregator                      │
│     → ReplyGeneratorHandler                       │
│     → OrderMatcher (点播匹配)                      │
└──────────────────────────────────────────────────┘
```

#### 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/comment/webhook_receiver.py` | ⭐ 新增 | 统一 WebHook 评论接收器 |
| `src/comment/listener.py` | ✏️ 修改 | DouyinCommentListener 对接 douyin-live |
| `src/data/services.py` | ✏️ 修改 | CommentAggregator 注册 WebHook 来源 |
| `configs/config.yaml` | ✏️ 修改 | 新增 webhook 和直播房间配置 |
| `requirements.txt` | ✏️ 修改 | 添加 douyin-live 依赖 |

#### 配置变更

```yaml
# configs/config.yaml 新增
live_rooms:
  douyin:
    room_id: ""          # 抖音直播间 ID (从 URL 获取)
    webcast_url: ""       # 或直接填直播间 URL

webhook:
  enabled: true
  host: "0.0.0.0"
  port: 8888             # WebHook 接收端口
  auth_token: ""          # 可选：Bearer Token 鉴权
```

#### Task 7.1: WebHookReceiver 实现

**文件**: `src/comment/webhook_receiver.py`（新增）

```python
"""统一 WebHook 评论接收器 — 标准 HTTP 接口接收外部评论"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .listener import Comment

logger = logging.getLogger(__name__)


class WebHookHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    # 类变量：由 WebHookReceiver 设置
    comment_callback: Optional[Callable] = None
    auth_token: Optional[str] = None
    
    def do_POST(self):
        if self.path != '/webhook/comment':
            self.send_response(404)
            self.end_headers()
            return
        
        # Token 鉴权
        if self.auth_token:
            auth = self.headers.get('Authorization', '')
            if auth != f'Bearer {self.auth_token}':
                self.send_response(401)
                self.end_headers()
                return
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return
        
        # 必填字段验证
        required = ['platform', 'username', 'content']
        if not all(k in data for k in required):
            self.send_response(400)
            self.end_headers()
            return
        
        # 转发回调
        if self.comment_callback:
            self.comment_callback(data)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    
    def log_message(self, format, *args):
        pass  # 禁用 HTTP 日志，改用应用日志


class WebHookReceiver(QObject):
    """
    统一 WebHook 接收器
    
    在独立 QThread 中运行 HTTP 服务器，
    通过信号将评论传递给主线程。
    """
    
    comment_received = pyqtSignal(object)  # Comment
    server_error = pyqtSignal(str)
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        webhook_config = config.get('webhook', {})
        self._host = webhook_config.get('host', '0.0.0.0')
        self._port = webhook_config.get('port', 8888)
        self._auth_token = webhook_config.get('auth_token', '')
        
        self._server: Optional[HTTPServer] = None
        self._is_running = False
    
    def start(self):
        """启动 WebHook 服务器"""
        WebHookHandler.comment_callback = self._on_webhook_comment
        WebHookHandler.auth_token = self._auth_token
        
        self._server = HTTPServer((self._host, self._port), WebHookHandler)
        self._is_running = True
        
        logger.info(f"WebHook 接收器已启动: http://{self._host}:{self._port}/webhook/comment")
        
        # 在后台线程运行
        import threading
        thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        thread.start()
    
    def stop(self):
        """停止服务器"""
        if self._server:
            self._server.shutdown()
            self._is_running = False
            logger.info("WebHook 接收器已停止")
    
    def _on_webhook_comment(self, data: Dict[str, Any]):
        """处理 WebHook 评论 → 转为 Comment 对象 → 发射信号"""
        comment = Comment(
            platform=data['platform'],
            user_id=data.get('user_id', 'webhook_user'),
            username=data['username'],
            content=data['content']
        )
        self.comment_received.emit(comment)
```

#### Task 7.2: DouyinCommentListener 对接 douyin-live

**文件**: `src/comment/listener.py` — 替换 `DouyinCommentListener`

```python
class DouyinCommentListener(CommentListener):
    """
    抖音评论监听器 — 基于 douyin-live 开源库
    
    依赖: pip install douyin-live
    """
    
    def connect(self):
        """连接抖音直播间"""
        try:
            from douyin_live import DouyinLiveClient
            
            room_id = self.config.get('room_id', '')
            if not room_id:
                raise ValueError("缺少抖音直播间 ID (room_id)")
            
            self._ws_client = DouyinLiveClient(room_id)
            
            @self._ws_client.on('comment')
            def on_comment(msg):
                comment = Comment(
                    platform='douyin',
                    user_id=msg.get('user', {}).get('id', ''),
                    username=msg.get('user', {}).get('nickname', ''),
                    content=msg.get('content', '')
                )
                self._emit_comment(comment)
            
            self._ws_client.start()
            self.is_connected = True
            self.connected.emit()
            logger.info(f"抖音评论监听已连接: room_id={room_id}")
            
        except ImportError:
            logger.error("douyin-live 未安装: pip install douyin-live")
            self.error_occurred.emit("douyin-live 未安装")
        except Exception as e:
            logger.error(f"抖音评论连接失败: {e}")
            self.error_occurred.emit(str(e))
```

#### Task 7.3: CommentAggregator 集成 WebHook

**文件**: `src/data/services.py`

在 `CommentAggregator.__init__` 中新增：
```python
from ..comment.webhook_receiver import WebHookReceiver

self.webhook_receiver = WebHookReceiver(config)
self.webhook_receiver.comment_received.connect(self._on_webhook_comment)
```

#### Task 7.4: 外部调用示例

**抖音（douyin-live 直连）**：自动，无需额外操作。

**快手（Selenium 脚本示例）**：
```python
# scripts/kuaishou_comment_bridge.py
# 用 Selenium 打开快手直播间页面，定时抓取评论 DOM
# 抓到后 POST 到 http://localhost:8888/webhook/comment
import requests

requests.post('http://localhost:8888/webhook/comment', json={
    'platform': 'kuaishou',
    'user_id': 'user_123',
    'username': '快手观众A',
    'content': '这款房车多少钱？'
})
```

---

### Phase 8: 测试

#### Task 7.1: SegmentPlayer 测试

**文件**: `tests/test_segment_player.py`

```python
class TestSegmentPlayer:
    def test_load_product_segments(self): ...
    def test_tick_advances_progress(self): ...
    def test_segment_transition(self): ...
    def test_is_finished(self): ...
    def test_reset(self): ...
```

#### Task 7.2: OrderMatcher 测试

**文件**: `tests/test_order_matcher.py`

```python
class TestOrderMatcher:
    def test_alias_match_exact(self): ...
    def test_alias_match_partial(self): ...
    def test_no_match(self): ...
    def test_cooldown(self): ...
    def test_qa_match(self): ...
```

#### Task 7.3: PlaybackEngine 集成测试

**文件**: `tests/test_playback_engine.py`

```python
class TestPlaybackEngine:
    def test_init_state_is_idle(self): ...
    def test_start_transitions_to_playing(self): ...
    def test_stop_transitions_to_idle(self): ...
    def test_sequential_loop(self): ...
    def test_random_loop(self): ...
    def test_order_switch(self): ...
    def test_pause_resume(self): ...
```

---

## 📊 预计工作量

| Phase | 内容 | 新增文件 | 修改文件 | 预估时间 |
|-------|------|---------|---------|---------|
| Phase 0 | 口型同步（LivePortrait 实时） | 1 | 4 | 4h |
| Phase 1 | 基础设施（数据模型+配置） | 0 | 5 | 1h |
| Phase 2 | ObsController | 1 | 0 | 1.5h |
| Phase 3 | SegmentPlayer | 1 | 0 | 1.5h |
| Phase 4 | OrderMatcher | 1 | 0 | 1.5h |
| Phase 5 | PlaybackEngine 核心 | 2 | 1 | 2h |
| Phase 6 | 点播链路打通 | 0 | 3 | 1h |
| Phase 7 | 评论实时抓取 | 1 | 4 | 2h |
| Phase 8 | 测试 | 3 | 0 | 2h |
| **合计** | | **10 新文件** | **16 修改** | **~16.5h** |

---

## ⚠️ 前置依赖和注意事项

1. **OBS Studio 必须先安装并配置 WebSocket**（`obs-websocket` 插件），在 OBS 中预设好每个产品的场景和媒体源
2. **产品数据必须先录入** — `ProductAsset` 表中要有产品记录，包含 `product_alias` 和 `script_segments`
3. **分段标注工具** — 建议后续开发一个简单的标注 UI，让运营人员拖拽时间轴标注 `script_segments`
4. **OBS 场景命名规范** — 建议 `product_{id}_{name}` 格式，ObsController 自动推导场景名

---

## 🎯 验收标准

- [ ] 启动后自动按顺序（或随机）循环播放产品视频
- [ ] 每个产品播放时，OBS 自动切换到对应场景
- [ ] 分段信息正确追踪，进度条实时更新
- [ ] 评论包含产品别名时，自动切换到对应产品
- [ ] 点播有冷却时间，防止恶意刷屏
- [ ] 暂停/恢复/手动下一个 功能正常
- [ ] Wav2Lip 模型加载成功，口型视频生成可用
- [ ] 开播前批量预处理管线正常（TTS → Wav2Lip → 成品视频）
- [ ] 抖音评论实时监听可用（douyin-live 连接成功）
- [ ] WebHook 接收器正常接收外部评论并转发
- [ ] 所有新增模块有单元测试覆盖
