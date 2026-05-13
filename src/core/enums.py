"""
Enumerations for Multi-AI-Stream
系统枚举定义
"""

from enum import Enum, StrEnum


class PlatformType(StrEnum):
    """平台类型枚举"""
    DOUYIN = "douyin"           # 抖音
    KUAISHOU = "kuaishou"       # 快手  
    WECHAT = "wechat"           # 视频号 (WeChat)
    CUSTOM = "custom"           # 自定义 RTMP


class AvatarEngineType(StrEnum):
    """数字人生成引擎类型枚举"""
    LIVE_PORTRAIT = "live_portrait"   # LivePortrait (实时驱动)
    WAV2LIP = "wav2lip"               # Wav2Lip (离线生成)
    SADTALKER = "sadtalker"           # SadTalker (备选方案)


class LiveStatus(StrEnum):
    """直播状态枚举"""
    IDLE = "idle"                 # 空闲
    STARTING = "starting"         # 启动中
    LIVE = "live"                 # 直播中
    STOPPING = "stopping"         # 停止中
    ERROR = "error"               # 错误状态
    PAUSED = "paused"             # 暂停


class ScriptStage(StrEnum):
    """内容生成流水线阶段枚举"""
    SCRIPT_GENERATION = "script_generation"   # 文案生成
    TTS_SYNTHESIS = "tts_synthesis"           # TTS 合成
    LIP_SYNC = "lip_sync"                     # 口型同步


class LogLevel(StrEnum):
    """日志级别枚举 (兼容 logging)"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PropertyCategory(StrEnum):
    """房产分类枚举"""
    RVS = "rvs"                     # 房车 (RV)
    HOUSE = "house"                 # 普通房屋
    APARTMENT = "apartment"         # 公寓
    COMMERCIAL = "commercial"       # 商业地产


class StreamOutputMode(StrEnum):
    """推流输出模式枚举"""
    SINGLE = "single"               # 单路推流
    MULTI = "multi"                 # 多路并发 (OBS Multi-Output)


class DeviceType(StrEnum):
    """计算设备类型"""
    CPU = "cpu"
    CUDA = "cuda"                  # NVIDIA GPU
    MPS = "mps"                    # Apple Silicon
    AUTO = "auto"                  # 自动选择
