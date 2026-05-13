# Multi-AI-Stream - 完整使用指南 v1.0

本文档详细介绍如何使用 Multi-AI-Stream 数字人直播系统。

---

## 📚 目录

1. [快速开始](#快速开始)
2. [安装部署](#安装部署)
3. [配置说明](#配置说明)
4. [功能使用](#功能使用)
5. [常见问题](#常见问题)
6. [故障排查](#故障排查)

---

## 🚀 快速开始

### 第一步：准备环境

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/multi-ai-stream.git
cd multi-ai-stream

# 2. 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装核心依赖
pip install -r requirements.txt
```

### 第二步：配置 OBS Studio

1. **下载并安装 OBS Studio**
   - Windows: https://obsproject.com/download
   - macOS: https://obsproject.com/download

2. **启用 WebSocket 插件**
   ```
   工具 (Tools) → obs-websocket 设置
   ├── ☑ 启用服务器
   ├── 端口：4455
   └── 密码：(可选，建议设置)
   ```

### 第三步：获取直播平台推流信息

| 平台 | 获取方式 |
|-----|---------|
| **抖音** | 抖音创作者中心 → 直播管理 → PC 直播 → RTMP 地址 + 推流码 |
| **快手** | 快手创作者服务平台 → 直播助手 → 推流地址 |
| **视频号** | 微信视频助手 → 直播伴侣 → 获取推流信息 |

### 第四步：启动程序

```bash
# 方式 1: Python 直接运行
python src/main.py

# 方式 2: 使用入口点 (需先安装)
pip install -e .
multi-ai-stream
```

---

## 📦 安装部署

### 系统要求

| 组件 | 最低配置 | 推荐配置 |
|-----|---------|---------|
| **CPU** | 4 核 | 8 核+ |
| **内存** | 16GB | 32GB+ |
| **GPU** | GTX 1060 6GB | RTX 3060+ (12GB) |
| **硬盘** | 50GB 可用空间 | 100GB SSD |

### Windows 部署

```bash
# 1. 安装 Python 3.10+
# 从 https://www.python.org/downloads/ 下载并安装

# 2. 安装项目依赖
pip install -r requirements.txt

# 3. (可选) 打包成 EXE
python scripts/build_exe.py

# 生成的文件位置: dist/MultiAIStream.exe
```

### macOS 部署

```bash
# 1. 使用 Homebrew 安装 Python
brew install python@3.10

# 2. 安装项目依赖
pip3 install -r requirements.txt

# 3. 运行程序
python3 src/main.py
```

### Docker 部署 (可选)

```bash
# 构建镜像
docker build -t multi-ai-stream .

# 运行容器 (需要 GPU 支持)
docker run --gpus all \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/assets:/app/assets \
  -p 8080:8080 \
  multi-ai-stream
```

---

## ⚙️ 配置说明

### 配置文件位置

```
multi-ai-stream/
└── configs/
    └── config.yaml  ← 主配置文件
```

### 核心配置项

#### 1. OBS 连接配置

```yaml
obs:
  host: "localhost"      # OBS 主机地址 (本地部署填 localhost)
  port: 4455             # WebSocket 端口 (与 OBS 设置一致)
  password: ""           # WebSocket 密码 (如未设置则留空)
```

#### 2. 数字人生成引擎

```yaml
avatar:
  default_engine: "live_portrait"  # live_portrait / wav2lip
  
  # LivePortrait 配置
  live_portrait:
    batch_size: 1
    resize: true
    
  # Wav2Lip 配置  
  wav2lip:
    height: 512
    width: 512
    fps: 25
```

#### 3. LLM 文案生成

```yaml
llm:
  model: "qwen/Qwen-7B-Chat-GGUF"  # 模型路径或 HuggingFace ID
  quantization: "q4_0"              # q4_0 / q5_k_m / q8_0
  
  # 提示词模板
  system_prompt: |
    你是一位专业的二手房车销售专家...
```

#### 4. TTS 语音合成

```yaml
tts:
  engine: "coqui"  # coqui / edge / iflytek
  
  # Coqui-TTS 配置
  coqui:
    model: "tts_models/multilingual/multi-dataset/xtts_v2"
    language: "zh"
  
  # Edge-TTS 配置  
  edge:
    voice: "zh-CN-XiaoxiaoNeural"
```

#### 5. 平台推流配置

```yaml
platforms:
  douyin:        # 抖音
    enabled: true
    type: "douyin"
    rtmp_url: "rtmp://live.douyin.com/xxx"
    stream_key: "your_stream_key_here"
    
  kuaishou:      # 快手  
    enabled: false
    type: "kuaishou"
    rtmp_url: ""
    stream_key: ""
```

### 配置文件编辑技巧

1. **YAML 语法注意事项**
   - 使用空格缩进 (2 个或 4 个)
   - 字符串用双引号包裹更稳妥
   - 注释以 `#` 开头

2. **动态加载配置**
   ```bash
   # 通过环境变量指定配置文件路径
   export MULTI_STREAM_CONFIG=/path/to/custom_config.yaml
   python src/main.py
   ```

---

## 🎯 功能使用

### 1️⃣ 直播控制 (主面板)

#### 开始直播流程

```
┌─────────────────────────────────────┐
│  1. 选择直播平台                     │
│     └── 抖音 / 快手 / 视频号          │
│                                     │
│  2. 填写推流信息                     │
│     ├── RTMP URL                    │
│     └── Stream Key                  │
│                                     │
│  3. 选择数字人头像                   │
│     └── 📂 选择本地图片              │
│                                     │
│  4. 点击 ▶️ 开始直播                 │
└─────────────────────────────────────┘
```

#### 推流状态监控

- **进度条**: 显示连接/推流进度 (0-100%)
- **状态标签**: 实时显示当前状态
  - `等待启动...` → 初始状态
  - `正在连接...` → 连接 OBS
  - `🔴 直播中 | HH:MM:SS` → 运行中
  - `✅ 直播已停止` → 已完成

#### 停止直播

```
点击 ⏹️ 停止直播按钮
→ 弹出确认对话框
→ 确认后停止推流
→ 状态重置为"等待启动"
```

---

### 2️⃣ 数字人配置

#### 引擎选择

| 引擎 | 特点 | 适用场景 |
|-----|------|---------|
| **LivePortrait** | 实时驱动，30fps+ | 直播推流、实时互动 |
| **Wav2Lip** | 离线生成，高质量 | 预录制内容、素材库 |

#### LivePortrait 参数调优

```yaml
# 口型同步强度 (0.5 - 2.0)
lip_sync_strength: 1.0   # 默认值
  - < 1.0: 更自然的口型，但可能不够精确
  - > 1.0: 更精准的口型匹配

# 帧率设置 (15 - 60 fps)
fps: 25                  # 推荐：25-30fps
  - 直播推流建议：25-30fps
  - 高质量录制可设：48-60fps
```

#### TTS 语音选择

| 语音 | 性别 | 特点 |
|-----|------|------|
| **zh-CN-XiaoxiaoNeural** | 女声 | 温柔亲切，适合房产介绍 |
| **zh-CN-YunxiNeural** | 男声 | 稳重专业，适合商务场景 |
| **zh-CN-XiaoyiNeural** | 女声 | 活泼自然，适合年轻群体 |

---

### 3️⃣ 素材管理

#### 上传数字人头像

```
1. 切换到"📁 素材管理"标签页
2. 点击"👤 数字人头像"区域的"📤 上传"按钮
3. 选择 JPG/PNG 格式的图片
4. 上传成功后显示在列表中
```

**图片要求**:
- 格式：JPG / PNG
- 分辨率：建议 512x512 或更高
- 内容：正面人脸，清晰可见

#### 管理背景场景

```
支持分类存储:
assets/backgrounds/
├── living_room/    # 客厅场景
├── office/         # 办公场景  
└── outdoor/        # 户外场景
```

---

### 4️⃣ 房源信息管理

#### 添加房源信息

```
1. 切换到"🏠 房源管理"标签页
2. 点击 "➕ 添加房源"
3. 输入房源名称
4. (可选) 编辑详细信息
```

**字段说明**:
| 字段 | 说明 |
|-----|------|
| **名称** | 房源标题 (如"中环二手房 A") |
| **价格** | 售价，单位：万元 |
| **面积** | 建筑面积，单位：平方米 |
| **位置** | 地理位置描述 |

---

### 5️⃣ 内容生成流程

完整的数字人直播内容生成链路:

```
房源信息
   ↓
[LLM] 文案生成 → "这套房子位于市中心..."
   ↓  
[TTS] 语音合成 → speech.wav (音频文件)
   ↓
[Avatar] 口型同步 → video.mp4 (数字人视频)
   ↓
[OBS] RTMP 推流 → 抖音/快手/视频号直播
```

#### 各阶段参数配置

**LLM 文案生成**:
- 系统提示词在 `config.yaml` 中配置
- 支持自定义模板

**TTS 语音合成**:
```yaml
tts:
  engine: "coqui"      # 选择引擎
  voice: "zh-CN-XiaoxiaoNeural"  # 选择语音
  speed: 1.0           # 语速 (0.8-1.2)
```

---

## ❓ 常见问题

### Q1: OBS WebSocket 连接失败？

**症状**: 
```
[ERROR] OBS WebSocket 连接失败：Connection refused
```

**解决方案**:
1. 确认 OBS 已启动
2. 检查 obs-websocket 插件是否启用
3. 验证端口号 (默认 4455)
4. 如设置了密码，确保配置文件中一致

---

### Q2: LivePortrait 模型加载失败？

**症状**:
```
[WARNING] LivePortrait 未安装，请运行:
  git clone https://github.com/KwaiVGI/LivePortrait
  cd LivePortrait && pip install -r requirements.txt
```

**解决方案**:
```bash
# 1. 克隆项目
git clone https://github.com/KwaiVGI/LivePortrait
cd LivePortrait

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载模型
./download_models.sh
```

---

### Q3: TTS 合成速度慢？

**症状**: 
- Coqui-TTS 生成 10 秒音频需要 30+ 秒

**优化建议**:
1. **使用 Edge-TTS** (推荐):
   ```yaml
   tts:
     engine: "edge"  # 更快，免费
   ```
   
2. **启用 GPU 加速**:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. **降低采样率**:
   ```yaml
   tts:
     sample_rate: 16000  # 默认 22050，更低更快
   ```

---

### Q4: 推流卡顿/掉帧？

**症状**:
- 直播画面卡顿
- 观众端显示"缓冲中"

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
     default_bitrate: 2000  # 从 2500 降至 2000 Kbps
     default_fps: 24        # 从 30 降至 24 fps
   ```

3. **使用硬件编码**:
   - Windows: NVIDIA NVENC / AMD AMF
   - macOS: VideoToolbox
   
---

### Q5: EXE 打包后运行报错？

**症状**:
```
ImportError: DLL load failed while importing xxx
```

**解决方案**:
1. **确保依赖完整**:
   ```bash
   # 重新安装所有依赖
   pip install -r requirements.txt
   
   # 检查缺失的 DLL
   python scripts/check_deps.py
   ```

2. **增加打包体积**:
   ```python
   # build_exe.py 中添加
   datas=[
       ('assets/avatars', 'assets/avatars'),
       ('models/*', 'models'),
   ]
   ```

---

## 🔧 故障排查

### 日志文件位置

```
multi-ai-stream/logs/app.log  ← 应用日志
```

### 查看实时日志

```bash
# Linux/macOS
tail -f logs/app.log

# Windows (PowerShell)
Get-Content logs/app.log -Wait -Tail 50
```

### 常见错误代码

| 错误码 | 含义 | 解决方案 |
|-----|------|---------|
| `PLATFORM_CONN_ERROR` | OBS 连接失败 | 检查 OBS 是否启动 |
| `MODEL_NOT_FOUND` | 模型文件缺失 | 确认模型路径正确 |
| `TTS_ERROR` | TTS 合成失败 | 检查 TTS 引擎配置 |
| `DEPENDENCY_ERROR` | 依赖未安装 | 运行 pip install |

### 调试模式

```bash
# 启用详细日志
export MULTI_STREAM_LOG_LEVEL=DEBUG
python src/main.py
```

---

## 📞 技术支持

如遇到文档未覆盖的问题:

1. **查看项目 Issues**: https://github.com/yourusername/multi-ai-stream/issues
2. **提交 Issue**: 提供错误日志和复现步骤
3. **联系作者**: duanxiaobo

---

**版本**: v1.0  
**最后更新**: 2026-05-12  
**维护者**: duanxiaobo
