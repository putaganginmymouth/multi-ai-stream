# Multi-AI-Stream - 多平台数字人直播系统 v3.0

**版本**: 3.0  
**最后更新**: 2026-05-13  
**状态**: ✅ 核心架构完成，可立即运行测试

---

## 📋 项目概述

Multi-AI-Stream 是一个支持抖音、视频号、快手等多平台的数字人直播软件，具备以下核心功能：

### ✨ v3.0 新增功能

| 模块 | 功能描述 | 状态 |
|------|----------|------|
| **多平台并发推流** | StreamManager + MainWindow UI | ✅ Complete |
| **定时开关直播** | SchedulerService + SettingsDialog Tab | ✅ Complete |
| **Prompt 动态模板化** | ScriptGenerator v3.0 prompt_config | ✅ Complete |
| **实时评论回复** | CommentListener + Responder (Template) | ✅ Basic |

### 🎯 核心特性

- 🌐 **多平台接入**: 抖音/快手/视频号，策略模式易于扩展
- 👤 **数字人引擎**: LivePortrait/Wav2Lip 双支持（预留集成接口）
- 🤖 **LLM 文案生成**: DeepSeek API / 本地 GGUF 模型双模式
- 🔊 **TTS 语音合成**: Edge-TTS (免费) / Coqui-TTS / 讯飞 API
- ⏰ **定时任务**: 自动启停推流，支持多平台并发
- 💬 **评论回复**: 模板匹配 + LLM 智能回复（预留）

---

## 🚀 快速开始

### 1️⃣ 环境准备

```bash
# macOS/Windows/Linux (Python 3.10+)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install PyQt6 pyyaml sqlalchemy requests edge-tts
```

### 2️⃣ 启动应用

```bash
cd multi-ai-stream
python src/main.py
```

### 3️⃣ 配置系统设置

1. 点击菜单栏 **⚙️ 系统设置**
2. LLM 标签页：填写 DeepSeek API Key（新用户赠送$1.5 免费额度）
3. TTS 标签页：保持 Edge-TTS 默认配置
4. OBS 标签页：填写 WebSocket 连接信息

---

## 📁 项目结构

```
multi-ai-stream/
├── src/                          # 源代码目录
│   ├── core/                     # 核心基础设施
│   │   ├── base.py               # Base classes & ABCs
│   │   ├── enums.py              # 枚举定义 (LiveStatus, PlatformType)
│   │   ├── exceptions.py         # 自定义异常体系
│   │   └── config.py             # 配置管理单例
│   │
│   ├── platform_adapters/        # 平台接入层 (策略模式)
│   │   ├── base_platform.py      # Platform ABC
│   │   ├── factory.py            # PlatformFactory
│   │   ├── douyin_platform.py    # 抖音实现
│   │   ├── kuaishou_platform.py  # 快手实现
│   │   └── wechat_platform.py    # 视频号实现
│   │
│   ├── avatar/                   # 数字人生成层 (策略模式)
│   │   ├── base_avatar.py        # AvatarEngine ABC
│   │   ├── factory.py            # AvatarFactory
│   │   ├── live_portrait.py      # LivePortrait 引擎 ⚠️ Stub
│   │   └── wav2lip.py            # Wav2Lip 引擎 ⚠️ Incomplete
│   │
│   ├── content/                  # 内容生成引擎 (责任链模式)
│   │   ├── pipeline.py           # ContentPipeline
│   │   ├── script_generator.py   # LLM ScriptGeneratorHandler v3.0
│   │   ├── tts_service.py        # TTSHandler
│   │   └── asset_manager.py      # 素材库管理
│   │
│   ├── stream/                   # 推流管理器 (v3.0 New) ⭐
│   │   ├── stream_manager.py     # StreamManager (多路并发控制)
│   │   └── stream_worker.py      # StreamWorker (单路推流线程)
│   │
│   ├── scheduler/                # 定时调度器 (v3.0 New) ⭐
│   │   ├── service.py            # SchedulerService + ScheduledTask
│   │   └── __init__.py           # 模块导出
│   │
│   ├── comment/                  # 评论回复系统 (v3.0 New) ⭐
│   │   ├── listener.py           # CommentListener (WebSocket/API)
│   │   └── responder.py          # Responder (Template/Smart)
│   │
│   ├── gui/                      # PyQt6 GUI
│   │   ├── main_window.py        # MainWindow (多平台控制 UI) ⭐
│   │   └── settings_dialog.py    # SettingsDialog (LLM/TTS/OBS/Schedule Tabs)
│   │
│   ├── data/                     # 数据访问层 (Repository Pattern)
│   │   ├── models.py             # SQLAlchemy ORM Models
│   │   ├── repository.py         # Repository implementations
│   │   └── services.py           # Service layer
│   │
│   └── main.py                   # 程序入口点
│
├── configs/                      # 配置文件目录
│   └── config.yaml               # 主配置 (LLM/TTS/OBS/Platform)
│
├── tests/                        # 测试目录 ⭐ v3.0 Expanded
│   ├── conftest.py               # pytest fixtures
│   ├── test_core_components.py   # Core infrastructure tests ✅
│   ├── test_platform.py          # Platform adapter tests ✅ (6 passed)
│   ├── test_content.py           # Content pipeline tests ✅
│   ├── test_avatar.py            # Avatar engine tests ⚠️ Stub only
│   ├── test_stream_manager.py    # StreamManager tests ⭐ New v3.0
│   ├── test_scheduler_service.py # SchedulerService tests ⭐ New v3.0
│   └── test_comment_responder.py # Comment responder tests ⭐ New v3.0
│
├── assets/                       # 静态资源目录
│   ├── avatars/                  # 数字人模型文件
│   ├── backgrounds/              # 场景素材
│   └── templates/                # 文案模板
│
├── scripts/                      # 辅助脚本
│   ├── init_db.py                # 数据库初始化
│   ├── build_exe.py              # PyInstaller EXE 打包
│   └── check_status.sh           # 项目状态检查
│
├── output/                       # 运行时输出目录
│   ├── videos/                   # 生成的视频文件
│   └── audio/                    # TTS 音频文件
│
├── docs/                         # 文档目录 (可选)
│
├── README.md                     # ⭐ 本文档
├── ARCHITECTURE.md               # 📋 完整架构设计 (见下方链接)
├── DEPLOYMENT.md                 # 🚀 部署指南 (见下方链接)
├── USER_MANUAL.md                # 👤 用户手册 (见下方链接)
├── IMPLEMENTATION_REPORT.md      # 📊 实施报告 (见下方链接)
├── requirements.txt              # Python 依赖清单
├── requirements-dev.txt          # 开发依赖清单
└── pyproject.toml                # Python 项目配置
```

---

## 🔧 核心设计模式

### 1. 策略模式 - Platform/Avatar Factory

```python
# src/platform_adapters/factory.py
class PlatformFactory:
    @staticmethod
    def create(platform_type: str, config: dict) -> BasePlatform:
        if platform_type == "douyin":
            return DouyinPlatform(config)
        elif platform_type == "kuaishou":
            return KuaishouPlatform(config)
        # ...

# src/avatar/factory.py  
class AvatarFactory:
    @staticmethod
    def create(engine_type: str, config: dict):
        if engine_type == "live_portrait":
            return LivePortraitEngine(config)
        elif engine_type == "wav2lip":
            return Wav2LipEngine(config)
```

### 2. 责任链模式 - Content Pipeline

```python
# src/content/pipeline.py
class ContentPipeline:
    def __init__(self, config):
        self.handlers = {
            ScriptStage.SCRIPT_GENERATION: ScriptGeneratorHandler(config),
            ScriptStage.TTS_SYNTHESIS: TTSHandler(config)
        }
    
    def process(self, property_info):
        # 文案生成 → TTS 合成 → (可选) 口型同步
        script = self.handlers[SCRIPT].handle(property_info)
        audio_path = self.handlers[TTS].handle(script)
        return {'script': script, 'audio_path': audio_path}
```

### 3. Repository Pattern - Data Access Layer

```python
# src/data/repository.py
class PlatformRepository(ABC):
    @abstractmethod
    def save(self, platform: BasePlatform) -> int: ...
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[BasePlatform]: ...

class SQLitePlatformRepository(PlatformRepository):
    # SQLAlchemy ORM implementation
```

---

## 📊 测试状态 (v3.0)

```bash
# Run all tests
pytest tests/ -v

# Current status (2026-05-13):
✅ test_platform.py:          6 passed   (Platform Factory + Base Platform)
✅ test_content.py:           6 passed   (Pipeline + AssetManager)  
✅ test_core_components.py:   9 passed   (Models, Repository, Service, Adapter)
⚠️ test_avatar.py:           Stub tests only (LivePortrait not integrated)

🆕 New v3.0 tests (requires PyQt6):
- test_stream_manager.py     (12 test cases written)
- test_scheduler_service.py  (14 test cases written)
- test_comment_responder.py  (15 test cases written)
```

**覆盖率**: ~65% (核心模块), v3.0 新增模块待运行验证

---

## 📚 相关文档链接

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 完整技术架构、设计模式详解、API 配置指南 |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 跨平台部署步骤、故障排查、Docker 方案 |
| [USER_MANUAL.md](./USER_MANUAL.md) | GUI 功能教程、Prompt 配置、定时任务设置 |
| [IMPLEMENTATION_REPORT.md](./IMPLEMENTATION_REPORT.md) | v3.0 开发进度总结、代码统计、待办清单 |

---

## 🎯 下一步计划 (v3.1)

### P0 - 必须完成
- [ ] LivePortrait 实际集成测试（克隆项目 + 模型下载）
- [ ] OBS WebSocket 真实推流验证
- [ ] v3.0 新增模块单元测试运行

### P1 - 应该完成  
- [ ] SmartResponder LLM 集成 (预留接口完善)
- [ ] Prompt 配置 UI 优化（结构化表单）
- [ ] Comment Reply Tab UI 实现

### P2 - 可以完成
- [ ] Celery 分布式任务队列
- [ ] Web 管理后台开发
- [ ] Docker 容器化部署

---

## 📞 支持资源

- **项目主页**: GitHub (待创建)
- **问题反馈**: GitHub Issues
- **DeepSeek API**: https://platform.deepseek.com/docs
- **LivePortrait**: https://github.com/KwaiVGI/LivePortrait

---

**版本历史**:
- v3.0 (2026-05-13): 新增 StreamManager/SchedulerService/CommentResponder 模块，重构 MainWindow UI
- v1.0 (2026-05-12): 核心架构完成，Platform/Avatar/Content 基础框架

**维护者**: duanxiaobo  
**许可证**: MIT
