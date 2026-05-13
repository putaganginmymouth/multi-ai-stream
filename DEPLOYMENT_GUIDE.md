# Multi-AI-Stream - 完整部署与运行指南 v1.0

**本文档整合了所有安装、配置和运行说明，一站式解决您的问题。**

---

## 📖 目录

1. [快速开始 (5 分钟)](#快速开始)
2. [详细安装步骤](#详细安装步骤)
3. [GUI 使用说明](#gui-使用说明)
4. [故障排查](#故障排查)
5. [下一步工作](#下一步工作)

---

## 🚀 快速开始 (5 分钟)

###  prerequisites - 前置条件

确保已安装:
- ✅ Python 3.10+ 
- ✅ Git (可选，用于克隆项目)

### Step-by-step

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/multi-ai-stream.git
cd multi-ai-stream

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖 (包含 PyQt6)
pip install -r requirements.txt

# 4. 初始化数据库
python scripts/init_db.py

# 5. 启动 GUI
python src/main.py
```

**完成!** 🎉 现在应该能看到图形界面。

---

## 🔧 详细安装步骤

### Windows 用户

1. **安装 Python**: https://www.python.org/downloads/ (勾选 "Add to PATH")

2. **克隆项目**:
   ```cmd
   git clone https://github.com/yourusername/multi-ai-stream.git
   cd multi-ai-stream
   ```

3. **创建虚拟环境并激活**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

4. **安装 PyQt6 和其他依赖**:
   ```cmd
   pip install -r requirements.txt
   
   # 如遇网络问题，使用镜像源:
   pip install PyQt6 -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

5. **安装 OBS Studio**:
   - 下载：https://obsproject.com/download
   - 配置 obs-websocket (端口 4455)

6. **初始化数据库并启动**:
   ```cmd
   python scripts/init_db.py
   python src/main.py
   ```

### macOS/Linux 用户

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/multi-ai-stream.git
cd multi-ai-stream

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python scripts/init_db.py

# 5. 启动 GUI
python src/main.py
```

---

## 📊 项目结构速览

```
multi-ai-stream/
├── src/                    # 源代码
│   ├── core/               # 核心基础设施 (base, enums, config)
│   ├── platform/           # 平台接入层 (抖音/快手/视频号)
│   ├── avatar/             # 数字人生成引擎 (LivePortrait/Wav2Lip)
│   ├── content/            # 内容生成 (LLM+TTS 流水线)
│   ├── gui/                # PyQt6 图形界面 ⭐
│   └── main.py             # 程序入口
│
├── configs/                # 配置文件
│   └── config.yaml         # 主配置
│
├── assets/                 # 静态资源 (头像、背景)
│
├── tests/                  # 测试文件
│
├── scripts/                # 辅助脚本 ⭐
│   ├── init_db.py          # 数据库初始化
│   ├── check_status.sh     # 状态检查
│   └── deploy_and_test.sh  # 一键部署
│
└── documentation/          # 文档 ⭐
    ├── README.md           # 项目说明
    ├── USER_GUIDE.md       # 详细使用手册
    ├── DESIGN_SPEC.md      # 架构设计文档
    └── WINDOWS_DEPLOYMENT.md # Windows 专属指南
```

---

## 🎯 GUI 使用说明

### 主界面功能

| 标签页 | 功能说明 |
|-------|---------|
| **📺 直播控制** | 选择平台、填写推流信息、启动/停止直播 |
| **👤 数字人配置** | 选择引擎类型 (LivePortrait/Wav2Lip)、调整参数 |
| **🏠 房源管理** | 添加/编辑二手房车产品信息 |
| **📁 素材管理** | 上传数字人头像、管理背景场景 |

### 开始直播流程

```
1. 切换到"📺 直播控制"标签页
   
2. 选择直播平台:
   └─ 下拉框：抖音 / 快手 / 视频号
   
3. 填写推流信息 (从平台创作者中心获取):
   ├─ RTMP URL: rtmp://live.xxx.com/xxx
   └─ Stream Key: your_stream_key_here
   
4. (可选) 选择数字人头像:
   └─ 📂 选择本地图片
   
5. 点击 ▶️ 开始直播
   
6. 观察进度条和状态标签

7. 需要停止时，点击 ⏹️ 停止直播
```

### 数字人配置建议

| 场景 | 推荐引擎 | FPS | 口型强度 |
|-----|---------|-----|---------|
| **实时直播** | LivePortrait | 25-30 | 1.0x |
| **离线录制** | Wav2Lip | 25 | 1.2x |

### TTS 语音选择

| 语音 | 适用场景 |
|-----|---------|
| **晓晓 (女声)** | 房产介绍、温馨风格 |
| **云希 (男声)** | 商务专业、稳重风格 |
| **晓伊 (女声)** | 年轻群体、活泼风格 |

---

## 🔍 故障排查

### 问题 1: GUI 启动失败 - "No module named 'PyQt6'"

**原因**: PyQt6 未安装或版本不兼容

**解决**:
```bash
# 激活虚拟环境后
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install "PyQt6>=6.5.0"

# Windows 用户额外:
# 下载并安装 Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

---

### 问题 2: OBS WebSocket 连接失败

**症状**: `[ERROR] OBS WebSocket 连接失败：Connection refused`

**检查清单**:
- [ ] OBS Studio 是否已启动？
- [ ] obs-websocket 插件是否启用？(工具 → obs-websocket)
- [ ] 端口号是否正确？(默认 4455)
- [ ] 如设置密码，配置文件是否一致？

**解决**:
```yaml
# configs/config.yaml
obs:
  host: "localhost"
  port: 4455
  password: ""  # 如 OBS 未设密码则留空
```

---

### 问题 3: PyQt6 界面空白或无响应

**原因**: macOS 透明化问题或 GPU 驱动冲突

**解决 (macOS)**:
```bash
# 设置环境变量后启动
export QT_MAC_WANTS_LAYER=1
python src/main.py
```

---

### 问题 4: LivePortrait 模型加载失败

**症状**: `ModelNotFoundError: LivePortrait 模型文件不存在`

**解决**:
```bash
# 方式 1: 使用自动安装脚本
bash scripts/install_liveportrait.sh

# 方式 2: 手动操作
cd multi-ai-stream
git clone https://github.com/KwaiVGI/LivePortrait.git
cd LivePortrait && pip install -r requirements.txt
./download_models.sh
```

---

### 问题 5: TTS 合成速度慢

**症状**: 10 秒音频需要 30+ 秒生成

**优化方案**:
```yaml
# configs/config.yaml
tts:
  engine: "edge"  # 改用 Edge-TTS (更快)
  
# 或降低采样率
tts:
  sample_rate: 16000  # 从 22050 降至 16000
```

---

### 问题 6: 推流卡顿/掉帧

**症状**: 直播画面卡顿，观众端显示"缓冲中"

**排查步骤**:
1. **检查网络带宽**:
   ```bash
   # 推荐上行速度
   - 720p30fps: ≥5 Mbps
   - 1080p60fps: ≥10 Mbps
   ```

2. **降低推流参数**:
   ```yaml
   output:
     default_bitrate: 2000  # Kbps (从 2500 降至)
     default_fps: 24        # fps
   ```

3. **使用硬件编码** (OBS):
   - Windows: NVIDIA NVENC / AMD AMF
   - macOS: VideoToolbox

---

## 📝 状态检查命令

运行以下命令快速了解项目状态:

```bash
# Linux/macOS
bash scripts/check_status.sh

# Windows PowerShell
.\scripts\check_status.ps1  # 待创建
```

**输出示例**:
```
[系统环境]
✅ Python 3.10.12
✅ pip3 available

[项目结构]
✅ src directory
✅ configs directory

[Python 依赖]
✅ PyQt6
✅ sqlalchemy
✅ pyyaml

[LIVEPORTRAIT 集成]
❌ LivePortrait not installed
```

---

## 🎯 下一步工作

### P0 - 必须完成 (核心功能)

1. **测试 GUI 运行**: `python src/main.py`
2. **配置直播平台**: 获取 RTMP URL + Stream Key
3. **OBS WebSocket 连接验证**

### P1 - 应该完成 (体验优化)

4. **LivePortrait 集成**: 按指南安装并测试实时驱动
5. **TTS/LLM 实际调用**: Coqui-TTS + Qwen-7B-GGUF
6. **单平台推流测试**

### P2 - 可以完成 (功能增强)

7. **多平台并发**: 同时开播抖音 + 快手
8. **定时任务**: Celery + Redis 调度系统
9. **Windows EXE 打包**: PyInstaller 部署方案

---

## 📞 技术支持

如遇文档未覆盖的问题:

1. **查看日志**: `logs/app.log`
2. **提交 Issue**: https://github.com/yourusername/multi-ai-stream/issues
3. **联系作者**: duanxiaobo

---

**版本**: v1.0  
**最后更新**: 2026-05-12  
**维护者**: duanxiaobo

---

## 📚 相关文档链接

| 文档 | 说明 |
|-----|------|
| [USER_GUIDE.md](./USER_GUIDE.md) | 详细功能使用手册 |
| [DESIGN_SPEC.md](./DESIGN_SPEC.md) | 架构设计文档 |
| [WINDOWS_DEPLOYMENT.md](./WINDOWS_DEPLOYMENT.md) | Windows 专属部署指南 |
| [LIVEPORTRAIT_INTEGRATION.md](./LIVEPORTRAIT_INTEGRATION.md) | LivePortrait 集成教程 |
