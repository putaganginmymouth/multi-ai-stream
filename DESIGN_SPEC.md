================================================================================
Multi-AI-Stream - 多平台数字人直播系统
架构设计文档 v1.1 (优化版)
================================================================================

【项目概述】
============
一个支持抖音、视频号、快手等多平台的数字人直播软件，可定时/分时开启直播，
根据输入的二手房车产品信息自动生成讲解内容并驱动数字人进行口型同步直播。

【核心原则】
============
1. 代码优雅：遵循 SOLID 原则，合理使用设计模式
2. 跨平台兼容：macOS 开发 + Windows 部署无缝迁移
3. 性能优化：GPU 加速、资源复用、低内存占用
4. 可扩展性：策略模式支持新平台/数字人快速接入


================================================================================
【一、技术选型】
================================================================================

┌──────────────┬─────────────────────────────────────────────────────┐
│   模块       │                  选型方案                          │
├──────────────┼─────────────────────────────────────────────────────┤
│ 开发语言     │ Python 3.10+ (跨平台生态丰富)                       │
│ GUI          │ PyQt6 (资源占用小，Windows/Mac 兼容性好)             │
│ OBS 控制     │ python-obs-studio + obs-websocket                  │
│ GPU 加速     │ CUDA(NVIDIA)/MPS(Apple Silicon)                    │
│ 数据库       │ SQLite(轻量)/PostgreSQL(生产级)                     │
│ 任务调度     │ Celery(异步任务队列)                                │
│ LLM          │ Qwen-7B-GGUF (本地部署，4-bit 量化)                 │
│ TTS          │ Coqui-TTS(开源)/Edge-TTS(免费)/讯飞 API(商用)       │
│ 数字人       │ LivePortrait(实时直播)/Wav2Lip(离线素材)            │
└──────────────┴─────────────────────────────────────────────────────┘


================================================================================
【二、项目目录结构】
================================================================================

multi-ai-stream/
├── src/
│   ├── __init__.py
│   ├── main.py                 # 程序入口点
│   │
│   ├── core/                   # 核心基础设施
│   │   ├── __init__.py
│   │   ├── base.py             # Base classes & ABCs
│   │   ├── enums.py            # 枚举定义
│   │   ├── exceptions.py       # 自定义异常
│   │   └── config.py           # 配置管理 (单例模式)
│   │
│   ├── platform/               # 平台接入层 (策略模式)
│   │   ├── __init__.py
│   │   ├── base_platform.py    # Platform ABC
│   │   ├── factory.py          # 工厂类
│   │   ├── douyin_platform.py  # 抖音实现
│   │   ├── kuaishou_platform.py# 快手实现
│   │   └── wechat_platform.py  # 视频号实现
│   │
│   ├── avatar/                 # 数字人生成层 (策略模式)
│   │   ├── __init__.py
│   │   ├── base_avatar.py      # AvatarEngine ABC
│   │   ├── factory.py          # 工厂类
│   │   ├── live_portrait.py    # LivePortrait 实现
│   │   └── wav2lip.py          # Wav2Lip 实现
│   │
│   ├── content/                # 内容生成引擎 (责任链模式)
│   │   ├── __init__.py
│   │   ├── pipeline.py         # 内容生成流水线
│   │   ├── script_generator.py # LLM 脚本生成
│   │   ├── tts_service.py      # TTS 服务
│   │   └── asset_manager.py    # 素材库管理
│   │
│   ├── scheduler/              # 直播调度器
│   │   ├── __init__.py
│   │   ├── task_queue.py       # Celery 配置
│   │   ├── live_scheduler.py   # 定时调度逻辑
│   │   └── multi_stream.py     # 多平台并发控制
│   │
│   ├── gui/                    # PyQt6 GUI
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口
│   │   ├── live_panel.py       # 直播控制面板
│   │   └── settings_dialog.py  # 设置对话框
│   │
│   └── data/                   # 数据层 (Repository Pattern)
│       ├── __init__.py
│       ├── models.py           # SQLAlchemy Models
│       └── repository.py       # Repository 实现
│
├── configs/                    # 配置文件
│   ├── config.yaml             # 主配置
│   ├── platforms.yaml          # 平台配置模板
│   └── avatars.yaml            # 数字人配置模板
│
├── assets/                     # 静态资源
│   ├── avatars/                # 数字人模型文件
│   ├── backgrounds/            # 场景素材
│   └── templates/              # 文案模板
│
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── test_platform.py
│   ├── test_avatar.py
│   ├── test_content.py
│   └── conftest.py             # pytest fixtures
│
├── scripts/                    # 辅助脚本
│   ├── init_db.py              # 数据库初始化
│   ├── install_deps.py         # 依赖安装脚本
│   └── build_exe.py            # PyInstaller 打包脚本
│
├── logs/                       # 日志目录 (运行时生成)
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
└── DESIGN_SPEC.md              # 本文档

================================================================================
【三、核心设计模式】
================================================================================

1. 策略模式 (Strategy Pattern) - 平台接入层
   ===========================================
   
   class Platform(ABC):
       @abstractmethod
       def start_stream(self, rtmp_url: str, stream_key: str) -> bool: ...
       
       @abstractmethod
       def stop_stream(self) -> bool: ...
       
       @abstractmethod
       def get_status(self) -> LiveStatus: ...

   class DouyinPlatform(Platform):
       def __init__(self, config: dict):
           self.config = config
           
       def start_stream(...):
           # 实现抖音推流逻辑
   
   class KuaishouPlatform(Platform):
       # 快手实现...

   # Factory 类
   class PlatformFactory:
       @staticmethod
       def create(platform_type: str, config: dict) -> Platform:
           if platform_type == "douyin":
               return DouyinPlatform(config)
           elif platform_type == "kuaishou":
               return KuaishouPlatform(config)
           # ...

2. 策略模式 - 数字人生成层
   =========================
   
   class AvatarEngine(ABC):
       @abstractmethod
       def generate_video(self, audio_path: str, image: np.ndarray) -> VideoStream: ...
       
       @abstractmethod
       def sync_lips(self, audio: str, video_frame: np.ndarray) -> np.ndarray: ...

   class LivePortraitEngine(AvatarEngine):
       # 实时数字人生成...

3. 责任链模式 (Chain of Responsibility) - 内容生成流水线
   ======================================================
   
   class ContentPipeline:
       def __init__(self):
           self.handlers = [
               ScriptGeneratorHandler(),    # LLM 文案生成
               TTSHandler(),                # TTS 音频合成
               LipSyncHandler()             # 口型同步处理
           ]
       
       def process(self, property_info: str) -> VideoStream:
           result = property_info
           for handler in self.handlers:
               if handler.can_handle(result):
                   result = handler.handle(result)
           return result

4. Repository Pattern - 数据访问层
   ================================
   
   class PlatformRepository(ABC):
       @abstractmethod
       def save(self, platform: Platform) -> int: ...
       
       @abstractmethod
       def find_by_id(self, id: int) -> Optional[Platform]: ...

   class SQLitePlatformRepository(PlatformRepository):
       # SQLite 实现...


================================================================================
【四、配置管理方案】
================================================================================

config.yaml (主配置文件):
-------------------------
app:
  name: "Multi-AI-Stream"
  version: "1.0.0"
  log_level: "INFO"
  
obs:
  host: "localhost"
  port: 4455
  password: ""  # OBS WebSocket 密码
  
avatar:
  default_engine: "live_portrait"
  models_path: "./assets/avatars"

llm:
  model: "qwen/Qwen-7B-Chat-GGUF"
  quantization: "q4_0"
  
tts:
  engine: "coqui"  # coqui / edge / iflytek
  
database:
  type: "sqlite"  # sqlite / postgresql
  path: "./data/multi_ai_stream.db"

platforms:
  douyin:
    enabled: true
    rtmp_url: ""
    stream_key: ""
  kuaishou:
    enabled: false
    rtmp_url: ""
    stream_key: ""


================================================================================
【五、跨平台兼容性方案】
================================================================================

1. PyTorch 后端适配
   =================
   
   # src/core/device.py
   def get_device():
       """自动检测并使用合适的计算设备"""
       try:
           import torch
           if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
               return torch.device('mps')  # Apple Silicon
           elif torch.cuda.is_available():
               return torch.device('cuda')  # NVIDIA GPU
           else:
               return torch.device('cpu')   # CPU fallback
       except ImportError:
           return torch.device('cpu')

2. OBS WebSocket 跨平台
   =====================
   
   - macOS: 需手动安装 obs-websocket 插件 (从官网下载)
   - Windows: OBS Studio 安装包自带
   
   # src/platform/base_platform.py
   def _connect_obs(self):
       try:
           self.obs_client = OBSWebSocket(
               address=f"ws://{self.config['obs']['host']}:{self.config['obs']['port']}",
               password=self.config['obs'].get('password', '')
           )
           self.obs_client.connect()
       except ConnectionError as e:
           logger.warning(f"OBS WebSocket 连接失败：{e}")
           # 降级到 FFmpeg 推流模式


================================================================================
【六、错误处理与日志】
==================

1. 自定义异常体系
   ===============
   
   class MultiStreamError(Exception): ...
   
   class PlatformError(MultiStreamError): 
       """平台相关错误"""
       
   class AvatarError(MultiStreamError):
       """数字人生成错误"""
       
   class ContentError(MultiStreamError):
       """内容生成错误"""

2. 日志配置
   =========
   
   # src/core/logging_config.py
   def setup_logger(name: str, log_file: str = "logs/app.log"):
       logger = logging.getLogger(name)
       logger.setLevel(logging.INFO)
       
       # 文件处理器
       file_handler = FileHandler(log_file)
       file_handler.setFormatter(formatter)
       
       # 控制台处理器
       console_handler = ConsoleHandler()
       console_handler.setFormatter(terminal_formatter)
       
       logger.addHandler(file_handler)
       logger.addHandler(console_handler)
       return logger


================================================================================
【七、性能优化策略】
==================

1. GPU 资源管理
   =============
   
   - OBS 视频编码：使用 NVENC (NVIDIA) / VideoToolbox (macOS)
   - 数字人渲染：独立进程，避免与 OBS 争抢显存
   
2. 模型加载优化
   =============
   
   - 单例模式复用 LLM/TTS 模型实例
   - 批量推理减少 GPU 切换开销
   
3. 打包体积控制
   =============
   
   PyInstaller 配置：
   - EXCLUDES: ['tkinter', 'unittest', 'test']
   - UPX 压缩：启用
   - 目标体积：<150MB (不含模型文件)


================================================================================
【八、开发路线图】
==================

Phase 1: 核心架构搭建 (5-7 天)
├── [P0] src/core/ - 基础框架
├── [P0] src/platform/ - 平台接入层 ABC + Factory
├── [P0] src/avatar/ - 数字人引擎 ABC + LivePortrait 集成
└── [P1] config.yaml + 配置管理

Phase 2: 内容生成流水线 (5-7 天)
├── [P0] src/content/pipeline.py - 责任链实现
├── [P0] LLM+TTS 集成测试
└── [P1] 素材库管理


Phase 3: OBS 推流集成 (3-5 天)
├── [P0] python-obs-studio 连接测试
├── [P0] 多平台 RTMP 推流实现
└── [P1] 场景切换控制

Phase 4: GUI 开发 (7-10 天)
├── [P0] PyQt6 主窗口框架
├── [P0] 直播控制面板
└── [P1] 设置对话框 + 素材管理界面

Phase 5: 测试与优化 (3-5 天)
├── [P1] 单元测试覆盖核心模块
├── [P1] 性能调优
└── [P2] Windows EXE 打包


================================================================================
【九、依赖清单】
==================

requirements.txt:
-----------------
# 核心依赖
PyQt6>=6.5.0
python-obs-studio>=2.3
sqlalchemy>=2.0
pyyaml>=6.0

# AI/ML 相关
torch>=2.0
transformers>=4.35
sentencepiece>=0.1.99
onnxruntime-gpu>=1.16  # GPU 加速

# TTS
coqui-tts>=0.24
edge-tts>=6.1.0

# 音频处理
pydub>=0.25
soundfile>=0.12

# 任务调度
celery>=5.3.0
redis>=5.0  # 可选，用于分布式任务队列

# 其他
opencv-python>=4.8
numpy>=1.24
pillow>=10.0

requirements-dev.txt:
---------------------
pytest>=7.4
pytest-cov>=4.1
black>=23.0
isort>=5.12
mypy>=1.5


================================================================================
【十、关键 API 设计】
==================

1. Platform 接口
   ==============
   
   platform = PlatformFactory.create("douyin", config)
   platform.start_stream()           # 开始推流
   platform.stop_stream()            # 停止推流  
   status = platform.get_status()    # 获取状态
   
2. AvatarEngine 接口
   ==================
   
   avatar = AvatarFactory.create("live_portrait", config)
   video_stream = avatar.generate(
       audio_path="tts_output.mp3",
       image="avatar.jpg"
   )

3. ContentPipeline 接口
   =====================
   
   pipeline = ContentPipeline()
   script = pipeline.generate_script(property_info)  # LLM 生成文案
   audio_path = pipeline.synthesize_tts(script)      # TTS 合成音频
   
4. GUI 主窗口
   ===========
   
   app = QApplication(sys.argv)
   window = MainWindow()
   window.show()
   sys.exit(app.exec())


================================================================================
【十一、部署方案】
==================

方案 A: Windows EXE (个人使用，推荐)
====================================
1. 在 Windows 上运行 build_exe.py
2. 生成 multi_ai_stream.exe (~150MB)
3. 用户只需双击 exe + 安装 OBS Studio


方案 B: macOS DMG (开发者使用)
==============================
1. 在 macOS 上打包
2. 生成 .dmg 安装包
3. 需用户手动安装 obs-websocket 插件


方案 C: Docker (服务器部署)
===========================
docker-compose.yml:
services:
  app:
    build: .
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]


================================================================================
【十二、注意事项】
==================

1. 直播平台资质要求
   -----------------
   □ 抖音直播：需要实名认证，企业号可多账号开播
   □ 快手直播：需要实名认证
   □ 视频号：需要微信认证
   
   建议先用个人号测试 RTMP 推流功能


2. OBS WebSocket 配置
   ===================
   
   OBS Studio -> 工具 -> obs-websocket:
   - 启用服务器：是
   - 端口：4455
   - 密码：设置 (可选)
   
3. GPU 要求
   =========
   
   LivePortrait 最低要求：
   - NVIDIA GTX 1060 6GB (或同级)
   - macOS: M1/M2/M3 芯片
   
   Wav2Lip 降级方案：
   - CPU 可用但速度慢 (~1fps)


================================================================================

文档版本：v1.1 (优化版)
最后更新：2026-05-12
作者：duanxiaobo
