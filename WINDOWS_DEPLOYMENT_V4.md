# Multi-AI-Stream v4.0 — Windows 完整部署指南

> **版本**: v4.0  
> **创建日期**: 2026-05-14  
> **适用系统**: Windows 10/11 (64-bit)  
> **目标硬件**: RTX 3060+ / 8GB+ VRAM / 32GB RAM  

---

## 📋 目录

1. [当前状态分析](#当前状态分析)
2. [部署前检查清单](#部署前检查清单)
3. [Step 1: 环境安装](#step-1-环境安装)
4. [Step 2: 依赖安装](#step-2-依赖安装)
5. [Step 3: AI 模型下载](#step-3-ai-模型下载)
6. [Step 4: OBS Studio 配置](#step-4-obs-studio-配置)
7. [Step 5: API Key 与凭据配置](#step-5-api-key-与凭据配置)
8. [Step 6: 初始化数据库](#step-6-初始化数据库)
9. [Step 7: 录入产品数据](#step-7-录入产品数据)
10. [Step 8: 启动与验证](#step-8-启动与验证)
11. [故障排查](#故障排查)
12. [功能就绪度矩阵](#功能就绪度矩阵)

---

## 当前状态分析

### ✅ 代码已就绪

| 模块 | 状态 | 说明 |
|------|------|------|
| 核心架构 | ✅ | base.py, enums.py, exceptions.py, config.py |
| 平台接入层 | ✅ | Douyin/Kuaishou/WeChat RTMP 推流 |
| 内容生成 | ✅ | LLM文案(DeepSeek API) + TTS(Edge-TTS) |
| 播放引擎 | ✅ | v4.0 PlaybackEngine + ObsController + SegmentPlayer + OrderMatcher |
| 流式口型同步 | ✅ | StreamingLipSyncPipeline (LivePortrait 实时驱动) |
| 评论抓取 | ✅ | DouyinCommentListener (douyin-live) + WebHookReceiver |
| 评论回复 | ✅ | LLM四层降级 (LLM→公共QA→私有QA→默认) |
| 定时调度 | ✅ | SchedulerService (QTimer) |
| GUI | ✅ | PyQt6 MainWindow + SettingsDialog |
| 测试 | ✅ | 36 个测试用例 |

### ⚠️ 需要你手动准备的

| 项目 | 状态 | 说明 |
|------|------|------|
| Python 3.10+ | ⚠️ | 需安装 |
| CUDA 驱动 | ⚠️ | NVIDIA GPU 需要 |
| LivePortrait 模型 | ⚠️ | ~2GB，从 HuggingFace 下载 |
| 数字人形象图片 | ⚠️ | 一张正脸照片 (.jpg) |
| DeepSeek API Key | ⚠️ | 免费注册获取，$1.5 额度 |
| OBS Studio | ⚠️ | 需安装 + obs-websocket 插件 |
| 平台推流凭据 | ⚠️ | 抖音/快手的 RTMP 地址和推流密钥 |
| 产品数据 | ⚠️ | 需录入 ProductAsset 表 |

---

## 部署前检查清单

开始前确认你有以下内容：

```
[ ] NVIDIA 显卡驱动已安装 (nvidia-smi 能看到 GPU)
[ ] 稳定的网络连接 (用于下载模型和 API 调用)
[ ] GitHub 账号 (用于下载 LivePortrait 模型)
[ ] DeepSeek 账号 (platform.deepseek.com 注册)
[ ] 抖音创作者中心账号 (用于获取 RTMP 推流地址)
[ ] 一张数字人形象照片 (正脸、清晰、512x512 以上)
[ ] 房车/产品图片和视频素材
```

---

## Step 1: 环境安装

### 1.1 安装 Python 3.10+

```cmd
# 下载地址
https://www.python.org/downloads/

# 安装时勾选
☑ Add Python 3.x to PATH
☑ Install pip

# 验证
python --version
pip --version
```

### 1.2 验证 CUDA (NVIDIA GPU)

```cmd
# 命令行执行
nvidia-smi

# 应输出类似:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 546.xx    Driver Version: 546.xx    CUDA Version: 12.x          |
# +-----------------------------------------------------------------------------+
# | GPU  Name            TCC/WDDM  | Bus-Id        Disp.A | Memory-Usage        |
# | 0  NVIDIA GeForce RTX 3060     | ...            On     | 1234MiB /  8192MiB |
```

> 如果没有输出，去 https://www.nvidia.com/download/ 下载对应显卡驱动。

### 1.3 安装 Git

```cmd
# 下载
https://git-scm.com/download/win

# 验证
git --version
```

### 1.4 克隆项目

```cmd
cd C:\Projects
git clone https://github.com/putaganginmymouth/multi-ai-stream.git
cd multi-ai-stream
```

---

## Step 2: 依赖安装

### 2.1 创建虚拟环境

```cmd
python -m venv venv
venv\Scripts\activate

# 确认激活成功（命令行前有 (venv) 前缀）
```

### 2.2 安装核心依赖

```cmd
# 基础依赖（必须）
pip install PyQt6>=6.5
pip install sqlalchemy>=2.0
pip install pyyaml>=6.0
pip install numpy>=1.24
pip install pillow>=10.0
pip install opencv-python>=4.8

# AI/ML 依赖
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install onnxruntime-gpu>=1.16

# TTS 依赖
pip install edge-tts>=6.1

# 评论抓取
pip install douyin-live

# OBS 控制
pip install obs-websocket-py

# 可选：开发工具
pip install pytest pytest-cov
```

### 2.3 验证安装

```cmd
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
python -c "import PyQt6; print('PyQt6 OK')"
python -c "import edge_tts; print('Edge-TTS OK')"
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
```

---

## Step 3: AI 模型下载

### 3.1 LivePortrait 数字人模型 (~2GB)

```cmd
# 创建模型目录
mkdir assets\avatars\liveportrait

# 从 HuggingFace 下载
cd assets\avatars\liveportrait
git clone https://huggingface.co/KwaiVGI/LivePortrait hf_models

# 回项目根目录
cd ..\..\..
```

> 下载约 2GB，需稳定网络。也可用镜像：
> `git clone https://hf-mirror.com/KwaiVGI/LivePortrait hf_models`

### 3.2 放置数字人形象图片

```cmd
# 将你的数字人照片放到此目录
copy C:\your-avatar-photo.jpg assets\avatars\avatar.jpg
```

> 要求：正脸、清晰、无遮挡、建议 512x512 以上、JPG/PNG 格式

### 3.3 放置产品视频素材

```cmd
# 为每个产品创建视频文件
mkdir assets\videos
copy C:\your-product-videos\*.mp4 assets\videos\
```

---

## Step 4: OBS Studio 配置

### 4.1 安装 OBS Studio

```cmd
# 下载 OBS Studio
https://obsproject.com/download

# 安装 obs-websocket 插件
# OBS 28+ 版本已内置，无需额外安装
```

### 4.2 配置 OBS WebSocket

```
1. 打开 OBS Studio
2. 工具 → WebSocket 服务器设置
3. ☑ 启用 WebSocket 服务器
4. 服务器端口: 4455
5. 设置密码 (可选但建议设置)
6. 点击"确定"
```

### 4.3 为每个产品创建 OBS 场景

```
对每个产品（如"1号房车"），创建场景:

1. 场景 → 新建 → 命名: product_1_camper
2. 添加源:
   ├── 媒体源 → 选择产品视频文件 (assets/videos/product_1.mp4) → ☑ 循环
   ├── 图片 → 数字人形象 (assets/avatars/avatar.jpg) → 放在右下角
   └── 文字 → 产品名称 → 放在顶部
3. 对每个产品重复上述步骤
```

> **场景命名规范**: `product_{id}_{name}`  
> 如 product_1_camper, product_2_economy

---

## Step 5: API Key 与凭据配置

### 5.1 DeepSeek API Key

```
1. 访问 https://platform.deepseek.com
2. 注册账号（手机号即可）
3. API Keys → 创建新的 API Key
4. 复制 key（形如 sk-xxxxxxxx）
```

### 5.2 编辑配置文件

打开 `configs\config.yaml`，填写以下内容：

```yaml
# LLM 文案生成
llm:
  mode: "remote"
  remote:
    provider: "deepseek"
    api_key: "sk-your-deepseek-api-key-here"    # ← 填这里
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"

# TTS 语音合成 (Edge-TTS 免费，无需 API Key)
tts:
  engine: "edge"
  edge:
    voice: "zh-CN-XiaoxiaoNeural"

# OBS 连接
obs:
  host: "localhost"
  port: 4455
  password: "your-obs-password"    # ← OBS WebSocket 密码

# 平台推流凭据
platforms:
  douyin:
    enabled: true
    rtmp_url: "rtmp://live-push.douyin.com/live/"    # ← 从抖音创作者中心获取
    stream_key: "your-stream-key"                    # ← 推流密钥
  kuaishou:
    enabled: false                                    # 快手暂不可用
  wechat:
    enabled: false                                    # 视频号暂不可用

# 数字人形象
avatar:
  avatar_image: "assets/avatars/avatar.jpg"          # ← 数字人照片路径
```

### 5.3 获取抖音 RTMP 推流地址

```
1. 打开抖音创作者中心 https://creator.douyin.com
2. 直播管理 → 开始直播
3. 复制"服务器地址" (rtmp_url)
4. 复制"串流密钥" (stream_key)
5. 填入 configs/config.yaml
```

---

## Step 6: 初始化数据库

```cmd
cd C:\Projects\multi-ai-stream
venv\Scripts\activate

# 运行数据库初始化脚本
python scripts\init_db.py
```

应输出：
```
✅ 数据库初始化完成: data/multistream.db
   - platforms 表已创建
   - properties 表已创建
   - schedules 表已创建
   - product_assets 表已创建 (v4.0)
   ...
```

---

## Step 7: 录入产品数据

目前没有 GUI 数据录入界面，需要用 Python 脚本手动插入。

创建 `scripts\seed_data.py`：

```python
"""录入初始产品数据"""
import sys
sys.path.insert(0, 'src')

from data.repository import ProductAssetRepository, PublicQARepository, LiveRoomConfigRepository
from pathlib import Path

db_path = str(Path('data/multistream.db').absolute())
repo = ProductAssetRepository(db_path)

# === 录入产品 1: 豪华越野房车 ===
repo.save({
    'name': '1号房车 - 豪华越野版',
    'product_alias': '1号,一号,1号房车,豪华版,越野版,1号车',
    'video_path': 'assets/videos/product_1.mp4',
    'product_detail': '''
品牌: 远方房车
型号: 豪华越野版
长度: 5.9米 / 宽度: 2.4米 / 高度: 3.0米
价格: 88万
配置: 太阳能供电系统、四驱底盘、独立卫生间、双人床、厨房区
适合人群: 越野爱好者、长途旅行、家庭出游
    '''.strip(),
    'duration': 120,
    'script_text': '''
欢迎来到直播间！今天给大家带来的是这款豪华越野房车。
它全长5.9米，蓝牌C照就能开！搭载四驱底盘，什么路都能走。
顶部配备800W太阳能板，野外也能自给自足。
内部空间非常宽敞，双人床、独立卫生间、厨房一应俱全。
现在只要88万，首付20%，就能把移动的家开回家！
    '''.strip(),
    'script_segments': [
        {"start": 0, "end": 15, "text": "欢迎+外观展示", "visual": "wide"},
        {"start": 15, "end": 45, "text": "尺寸和驾驶资格介绍", "visual": "closeup"},
        {"start": 45, "end": 70, "text": "太阳能和配置介绍", "visual": "wide"},
        {"start": 70, "end": 95, "text": "内部空间展示", "visual": "closeup"},
        {"start": 95, "end": 120, "text": "价格和购买引导", "visual": "wide"},
    ],
    'qa_pairs': [
        {"question": "多少钱", "answer": "这款豪华越野版房车售价88万，首付20%只要17.6万就能开回家。", "keywords": ["价格", "多少钱", "报价"]},
        {"question": "油耗多少", "answer": "柴油2.8T发动机，百公里油耗约12升，高速更低。", "keywords": ["油耗", "费油"]},
        {"question": "能睡几个人", "answer": "标准配置双人床+卡座变床，可以睡4个人。", "keywords": ["睡觉", "床位", "住"]},
    ],
    'avatar_image_path': 'assets/avatars/avatar.jpg',
})

# === 录入产品 2 ===
repo.save({
    'name': '2号房车 - 经济舒适版',
    'product_alias': '2号,二号,2号房车,经济版,舒适版,2号车',
    'video_path': 'assets/videos/product_2.mp4',
    'product_detail': '...（按格式填写）',
    'duration': 90,
    'script_text': '...（按格式填写）',
    'script_segments': [
        {"start": 0, "end": 10, "text": "开场", "visual": "wide"},
        {"start": 10, "end": 90, "text": "详细介绍", "visual": "closeup"},
    ],
    'qa_pairs': [],
    'avatar_image_path': 'assets/avatars/avatar.jpg',
})

print(f"✅ 产品数据录入完成！")
print(f"   运行 python src/main.py 启动 GUI")
```

```cmd
# 执行数据录入
python scripts\seed_data.py
```

---

## Step 8: 启动与验证

### 8.1 启动应用

```cmd
cd C:\Projects\multi-ai-stream
venv\Scripts\activate
python src\main.py
```

应弹出 PyQt6 GUI 窗口：
```
┌──────────────────────────────────────────────┐
│  Multi-AI-Stream v4.0 - 数字人直播系统        │
├──────────────────────────────────────────────┤
│  📺 直播控制台  │  👤 数字人  │  📁 素材  │  ⏰ 定时  │
│                │             │           │           │
│  [▶ 开始直播]  │  引擎:      │ 产品列表   │ 定时任务   │
│  [⏹ 停止]     │  LivePortrait│           │           │
└──────────────────────────────────────────────┘
```

### 8.2 验证功能

```cmd
# 运行测试验证环境
python -m pytest tests\ -v --tb=short

# 应看到类似输出:
# test_segment_player.py ......... 12 passed
# test_order_matcher.py ........... 12 passed
# test_playback_engine.py ......... 12 passed
# test_platform.py ............... 6 passed
# test_avatar.py ................. 4 passed
# test_content.py ................ 5 passed
```

### 8.3 端到端验证流程

```
1. 打开 OBS Studio，确认 WebSocket 已启用
2. 启动 python src/main.py
3. 在"素材管理"面板确认产品列表不为空
4. 点击"开始直播"
5. 观察 OBS 场景是否自动切换
6. 在抖音开播，观察 RTMP 推流状态
7. 用另一台设备进入直播间，发评论"看看1号房车"
8. 观察是否自动切换到产品1
```

---

## 故障排查

### ❌ CUDA not available / torch 看不到 GPU

```cmd
# 重新安装 CUDA 版 PyTorch
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### ❌ OBS WebSocket 连接失败

```
1. 确认 OBS Studio 已打开
2. 工具 → WebSocket 服务器设置 → 确认已启用
3. 检查 configs/config.yaml 中 obs.host 和 obs.port 是否正确
4. 如果设置了密码，确认 config 中 password 字段匹配
```

### ❌ DeepSeek API 调用失败 / 401

```
1. 确认 api_key 已填入 configs/config.yaml
2. 确认 key 没有多余空格
3. 访问 https://platform.deepseek.com 确认账户余额充足
```

### ❌ 抖音推流失败

```
1. 确认 rtmp_url 和 stream_key 来自抖音创作者中心
2. 确认在抖音 APP 上已点击"开始直播"
3. 确认 OBS 推流指示灯为绿色
4. 抖音推流密钥有时效性，需每次重新获取
```

### ❌ LivePortrait 模型加载失败

```
1. 确认 assets/avatars/liveportrait/hf_models 目录存在
2. 重新执行 git clone:
   cd assets/avatars/liveportrait
   git clone https://huggingface.co/KwaiVGI/LivePortrait hf_models
3. 如果 GitHub 慢，用镜像:
   git clone https://hf-mirror.com/KwaiVGI/LivePortrait hf_models
```

### ❌ GUI 启动无响应 / 白屏

```
1. 确认 PyQt6 安装成功: pip show PyQt6
2. 尝试重装: pip uninstall PyQt6 -y && pip install PyQt6
3. 如果 Windows 缩放超过 100%，可能 UI 显示异常
4. 检查 Python 是 64 位版本
```

---

## 功能就绪度矩阵

| 功能 | 代码 | 环境依赖 | 可运行 |
|------|------|---------|--------|
| LLM 文案生成 | ✅ | DeepSeek API Key | ⚠️ 需配置 |
| TTS 语音合成 | ✅ | Edge-TTS (免费) | ✅ |
| 数字人口型同步 | ✅ | LivePortrait 模型 2GB | ⚠️ 需下载 |
| OBS 场景切换 | ✅ | OBS + WebSocket | ⚠️ 需安装OBS |
| 产品循环播放 | ✅ | 产品数据已录入 | ⚠️ 需录入 |
| 评论点播切换 | ✅ | 评论源 (douyin-live) | ⚠️ 需配置房间ID |
| 评论自动回复 | ✅ | DeepSeek API Key | ⚠️ 需配置 |
| RTMP 推流 | ✅ | 平台推流凭据 | ⚠️ 需配置 |
| 定时直播 | ✅ | - | ✅ |
| GUI 界面 | ✅ | PyQt6 | ⚠️ 需安装 |

---

## 最小可行部署 (MVP)

如果只想验证核心流程，按以下步骤即可：

```cmd
# 1. 安装最小依赖
pip install PyQt6 sqlalchemy pyyaml edge-tts numpy pillow opencv-python

# 2. 配置 DeepSeek API Key
notepad configs\config.yaml

# 3. 初始化数据库
python scripts\init_db.py

# 4. 录入 1 个测试产品
python scripts\seed_data.py    # 最少录入 1 个产品

# 5. 启动 GUI
python src\main.py

# 6. 在 GUI 中:
#    - 输入一段产品描述
#    - 点击"生成文案" → 看到 LLM 生成的文案
#    - 点击"合成语音" → 听到 TTS 朗读

# 不需要 OBS、不需要 LivePortrait、不需要推流凭据
# 这就是最简验证路径 🚀
```

---

**部署完成后，你拥有的是一个完整的数字人直播系统：**

```
产品信息
  → DeepSeek API 生成文案
    → Edge-TTS 合成语音
      → LivePortrait 实时对口型
        → OBS 合成画面
          → RTMP 推流到抖音
            → 观众评论
              → douyin-live 实时抓取
                → LLM 四级降级回复
                  → 点播匹配 → 切换产品
```

**预计完整部署时间**: 2-3 小时（含模型下载）
