# Multi-AI-Stream - 跨平台部署指南 v3.0

**版本**: 3.0  
**最后更新**: 2026-05-13  
**适用系统**: Windows / macOS / Linux

---

## 📋 目录

1. [快速开始](#快速开始)
2. [环境准备](#环境准备)
3. [依赖安装](#依赖安装)
4. [配置管理](#配置管理)
5. [启动应用](#启动应用)
6. [OBS WebSocket 设置](#obs-websocket-设置)
7. [故障排查](#故障排查)

---

## 🚀 快速开始 (30 分钟完成部署)

```bash
# Step 1: Clone project
git clone <your-repo-url> multi-ai-stream
cd multi-ai-stream

# Step 2: Create virtual environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows PowerShell

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Configure API keys (see below)
# Edit configs/config.yaml and fill in DeepSeek API Key

# Step 5: Launch application
python src/main.py
```

---

## 💻 环境准备

### 系统要求

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **OS** | Windows 10 / macOS 10.15 / Linux Ubuntu 20.04+ | Windows 11 / macOS 13+ / Linux Ubuntu 22.04+ | - |
| **CPU** | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 + | LLM inference needs decent CPU |
| **RAM** | 8GB | 16GB+ | Edge-TTS uses minimal RAM |
| **GPU** | Not required (Edge-TTS) | NVIDIA GTX 1060+ for LivePortrait | Optional, only if using local avatar engine |

### Python 版本要求

```bash
python --version  # Must be 3.10 or higher
```

---

## 📦 依赖安装

### 核心依赖 (requirements.txt)

```txt
# GUI Framework
PyQt6>=6.5.0

# Configuration & Data
pyyaml>=6.0
sqlalchemy>=2.0

# API Clients
requests>=2.31.0          # DeepSeek LLM API
edge-tts>=6.1.0           # Microsoft Azure TTS (free)

# AI/ML (Optional - for LivePortrait integration later)
torch>=2.0                # CUDA/MPS support
opencv-python>=4.8        # Image processing
numpy>=1.24               # Numerical operations

# Audio Processing
pydub>=0.25               # Audio format conversion
soundfile>=0.12           # WAV file handling

# OBS Control (Optional)
obs-websocket-py>=1.0     # OBS WebSocket API client

# Development Tools (requirements-dev.txt only)
pytest>=7.4               # Testing framework
black>=23.0               # Code formatting
isort>=5.12               # Import sorting
mypy>=1.5                 # Type checking
```

### 安装命令

```bash
# macOS/Linux
pip install -r requirements.txt

# Windows (PowerShell)
.\requirements.txt | ForEach-Object { pip install $_ }

# Or simply:
pip install PyQt6 pyyaml sqlalchemy requests edge-tts opencv-python numpy pydub soundfile obs-websocket-py pytest black isort mypy
```

### 验证安装

```bash
python -c "import PyQt6; import yaml; import sqlalchemy; print('✅ All core dependencies installed')"
```

---

## ⚙️ 配置管理

### config.yaml (主配置文件)

**位置**: `configs/config.yaml`

#### 1. DeepSeek LLM API Key

```yaml
llm:
  mode: "remote"  # Use remote API
  
  remote:
    provider: "deepseek"
    api_key: "YOUR_DEEPSEEK_API_KEY_HERE"  # ⚠️ Fill this in!
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"
```

**获取 API Key**: https://platform.deepseek.com  
**新用户福利**: $1.5 免费额度 (约 37,500 次文案生成)

#### 2. Edge-TTS Voice Selection

```yaml
tts:
  engine: "edge"  # Default, no configuration needed
  
  edge:
    voice: "zh-CN-XiaoxiaoNeural"  # Female voice (recommended)
                                  # Alternatives: zh-CN-YunxiNeural (male)
```

#### 3. OBS WebSocket Connection

```yaml
obs:
  host: "localhost"      # Default, change if OBS is on remote machine
  port: 4455             # Default WebSocket port
  password: ""           # Optional: Set in OBS → Tools → Websocket Server Settings
```

#### 4. Platform RTMP Configuration (Optional)

```yaml
platforms:
  douyin:
    enabled: false       # Enable when you have stream credentials
    type: "douyin"
    rtmp_url: ""         # From Douyin Creator Center
    stream_key: ""       # From Douyin Creator Center
  
  kuaishou:
    enabled: false
    type: "kuaishou"
    rtmp_url: ""
    stream_key: ""
  
  wechat:
    enabled: false
    type: "wechat"
    rtmp_url: ""
    stream_key: ""
```

---

## ▶️ 启动应用

### 方式 1: Python 直接运行 (推荐开发使用)

```bash
cd multi-ai-stream
python src/main.py
```

### 方式 2: GUI Launcher Script (macOS/Linux)

Create `launch.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python src/main.py
```

Make executable and run:
```bash
chmod +x launch.sh
./launch.sh
```

### 方式 3: Windows EXE (打包后)

**步骤**:
1. Install PyInstaller: `pip install pyinstaller`
2. Run build script: `python scripts/build_exe.py`
3. Launch from `dist/MultiAIStream.exe`

---

## 📹 OBS WebSocket 设置

### Step 1: Install obs-websocket Plugin

| Platform | Installation Method | Notes |
|----------|--------------------|-------|
| **Windows** | OBS Studio installer includes it | ✅ Pre-installed |
| **macOS** | Download from [obsproject.com](https://github.com/obssk/obs-websocket/releases) | ⚠️ Manual install required |

### Step 2: Configure WebSocket Server in OBS

1. Open OBS Studio
2. Go to **Tools → Websocket Server Settings**
3. Enable server: ✅ Check "Enable server"
4. Port: `4455` (default)
5. Password: Set a password (optional but recommended)
6. Click **OK**

### Step 3: Verify Connection

```bash
# Test connection from Python
python -c "from obswebsocket import obs_websocket; c = obs_websocket.obs_websocket(); c.connect('localhost', 4455); print('✅ Connected!' if c.is_connected() else '❌ Failed')"
```

---

## 🔧 故障排查

### Issue 1: PyQt6 Import Error

**错误**: `ModuleNotFoundError: No module named 'PyQt6'`

**解决**:
```bash
# macOS (Homebrew Python conflict)
pip uninstall PyQt6 PyQt5
pip install PyQt6

# Windows PowerShell
Remove-Module PyQt6 -ErrorAction SilentlyContinue
pip install --force-reinstall PyQt6
```

### Issue 2: DeepSeek API Key Error

**错误**: `ScriptGenerationError: deepseek API Key 未配置`

**解决**:
1. Open `configs/config.yaml`
2. Find `llm.remote.api_key` field
3. Paste your API key (no quotes)
4. Save file and restart application

### Issue 3: OBS WebSocket Connection Failed

**错误**: `PlatformError: OBS WebSocket 连接失败`

**排查步骤**:
1. Verify OBS is running
2. Check WebSocket server enabled in OBS settings
3. Confirm port matches (default 4455)
4. Test with curl: `curl ws://localhost:4455`

### Issue 4: Edge-TTS Voice Not Working

**症状**: TTS output has wrong voice or error

**解决**:
```yaml
# Try different voices in config.yaml
tts.edge.voice: "zh-CN-YunxiNeural"  # Male alternative
```

Available Chinese voices:
- `zh-CN-XiaoxiaoNeural` - Female (recommended)
- `zh-CN-YunxiNeural` - Male
- `zh-CN-XiaoyiNeural` - Female
- `zh-CN-YunjianNeural` - Male

### Issue 5: macOS Gatekeeper Blocks Application

**错误**: "MultiAIStream can't be opened because the developer cannot be verified"

**解决**:
```bash
# Allow from System Preferences
System Settings → Privacy & Security → Allow Anyway

# Or command line (not recommended for production)
sudo xattr -cr dist/MultiAIStream.app
```

### Issue 6: Permission Denied on Scripts

**错误**: `Permission denied: './launch.sh'`

**解决**:
```bash
chmod +x launch.sh
./launch.sh
```

---

## 🐛 高级故障排查

### Enable Debug Logging

Add to `configs/config.yaml`:
```yaml
logging:
  level: "DEBUG"  # Change from INFO to DEBUG
  file: "./logs/app_debug.log"
```

Logs will be written to `logs/app_debug.log` with full stack traces.

### Check Python Environment

```bash
# Verify Python version
python --version  # Should show 3.10+

# List installed packages
pip list | grep -E "PyQt6|pyyaml|sqlalchemy|requests"

# Check for conflicts
pip check
```

### Database Issues

If SQLite database corrupted:
```bash
# Backup current DB
cp data/multi_ai_stream.db data/multi_ai_stream.db.backup

# Reset database (will lose all scheduled tasks)
python scripts/init_db.py
```

---

## 📞 支持资源

| Resource | URL | Description |
|----------|-----|-------------|
| **DeepSeek API Docs** | https://platform.deepseek.com/docs | LLM API reference |
| **Edge-TTS PyPI** | https://pypi.org/project/edge-tts/ | TTS library documentation |
| **OBS WebSocket** | https://github.com/Palakis/obs-websocket | Plugin installation guide |
| **LivePortrait** | https://github.com/KwaiVGI/LivePortrait | Digital human engine (optional) |

---

## ✅ 部署检查清单

- [ ] Python 3.10+ installed and verified
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows no errors)
- [ ] `configs/config.yaml` edited with DeepSeek API Key
- [ ] OBS Studio running with WebSocket server enabled
- [ ] Application launched successfully (`python src/main.py`)
- [ ] Settings dialog opens without errors
- [ ] Platform checkboxes visible in MainWindow

---

**版本**: 3.0  
**最后更新**: 2026-05-13  
**维护者**: duanxiaobo
