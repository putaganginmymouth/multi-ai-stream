# Multi-AI-Stream - 用户手册 v3.0

**版本**: 3.0  
**最后更新**: 2026-05-13  
**适用对象**: 数字人直播系统最终用户

---

## 📚 目录

1. [快速开始](#快速开始)
2. [界面概览](#界面概览)
3. [功能详解](#功能详解)
4. [配置管理](#配置管理)
5. [常见问题](#常见问题)

---

## 🚀 快速开始 (10 分钟上手)

### Step 1: 启动应用

```bash
cd multi-ai-stream
python src/main.py
```

### Step 2: 配置 DeepSeek API Key

1. 点击菜单栏 **⚙️ 系统设置** → **系统设置 (全部)**
2. LLM Tab → API Key 字段填写你的密钥
3. 点击 **💾 保存并应用**

> 💡 **获取 API Key**: https://platform.deepseek.com (新用户赠送$1.5 免费额度)

### Step 3: 开始推流

1. 勾选要直播的平台 (抖音/快手/视频号)
2. 填写 RTMP URL 和 Stream Key
3. 点击 **▶️ 启动选中的平台**

---

## 🖥️ 界面概览

### MainWindow 主窗口

```
┌─────────────────────────────────────────────────────────────┐
│  🎬 Multi-AI-Stream - 数字人直播系统 v3.0              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  📺 直播控制台                                        │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                      │  │
│  │  🌐 直播平台选择                                     │  │
│  │  ☑️ 抖音   [rtmp://live.douyin.com/...] [••••]      │  │
│  │  ☑️ 快手   [rtmp://xx.kuaishou.com/...] [••••]      │  │
│  │  ☐ 视频号 [rtmp://live.weixin.qq.com/] [••••]      │  │
│  │                                                      │  │
│  │  ▶️ 启动选中的平台    ⏹️ 停止所有平台                │  │
│  │                                                      │  │
│  │  📊 推流统计                                         │  │
│  │  ┌─────────┬──────┬──────┬────────┐                 │  │
│  │  │ 平台   │状态  │流量  │FPS/码率│                │  │
│  │  ├─────────┼──────┼──────┼────────┤                 │  │
│  │  │抖音    │🟢运行中│1.2GB │30fps   │                │  │
│  │  │快手    │🔴停止  │0B    │-       │                │  │
│  │  └─────────┴──────┴──────┴────────┘                 │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  👤 数字人配置                                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Engine: [LivePortrait ▼]                            │  │
│  │  Model Path: ./assets/avatars/liveportrait           │  │
│  │  FPS: [25 ▲▼] Resolution: 512x512                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ⏰ 定时任务配置                                       │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  📅 定时任务列表                                      │  │
│  │  ┌─────────┬────────────┬────────────┬────────┐     │  │
│  │  │平台    │开始时间   │结束时间    │状态    │操作  │     │
│  │  ├─────────┼────────────┼────────────┼────────┤     │  │
│  │  │抖音    │2026-05-14 9:00│2026-05-14 17:00│待执行│删除│     │
│  │  └─────────┴────────────┴────────────┴────────┘     │  │
│  │                                                      │  │
│  │  ➕ 新增定时任务    🟢启动调度服务 / 🔴停止           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  📝 Live Log: ✅ 抖音推流已启动 | ⏰ 定时任务创建成功       │
└─────────────────────────────────────────────────────────────┘
```

### SettingsDialog 设置对话框

```
┌──────────────────────────────────────────────────────────┐
│  🔧 系统设置                                      v1.0  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 🤖 LLM 文案生成                                     │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ Mode: [Remote API ▼]                              │  │
│  │ Provider: [DeepSeek ▼]                            │  │
│  │ API Key: [••••••••••••••••••••••••••••••••]      │  │
│  │ Base URL: https://api.deepseek.com/v1             │  │
│  │ Model: deepseek-chat                              │  │
│  │                                                    │  │
│  │ 📝 Dynamic Prompt Template (v3.0):                │  │
│  │ ┌──────────────────────────────────────────────┐  │  │
│  │ │ 你是一位专业的{role}专家，擅长介绍{product_type}.│  │  │
│  │ │ 【产品信息】                                  │  │  │
│  │ │ {property_info}                              │  │  │
│  │ └──────────────────────────────────────────────┘  │  │
│  │                                                    │  │
│  │ Prompt Config:                                    │  │
│  │ Role: [二手房车销售专家]                          │  │
│  │ Product Type: [房产和房车产品]                    │  │
│  │ Selling Points: ☑核心地段 ☑精装修 ☑性价比高      │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 🔊 TTS 语音合成                                     │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ Engine: [Edge-TTS ▼] (免费，无需配置)              │  │
│  │ Voice: [zh-CN-XiaoxiaoNeural ▼]                   │  │
│  │   - zh-CN-XiaoxiaoNeural (女声，推荐)              │  │
│  │   - zh-CN-YunxiNeural (男声)                       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 📹 OBS 推流设置                                     │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ Host: [localhost]                                  │  │
│  │ Port: [4455]                                       │  │
│  │ Password: []                                       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ ⏰ 定时开关直播                                     │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ Scheduler Status: [🟢 Running / 🔴 Stopped]        │  │
│  │ Check Interval: [30 seconds]                       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│              ↩️ 重置    ❌ 取消      💾 保存并应用          │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 功能详解

### 1. 直播控制台 (主面板)

#### 多平台并发推流

**操作步骤**:
1. **选择平台**: 勾选抖音/快手/视频号复选框
2. **填写凭证**: 
   - RTMP URL: 从直播平台创作者中心获取
   - Stream Key: 推流密钥（密码形式显示）
3. **启动推流**: 点击 ▶️ 启动选中的平台
4. **监控状态**: 查看 📊 推流统计表格

**批量控制**:
- **▶️ 启动选中的平台**: 同时启动所有勾选的平台
- **⏹️ 停止所有平台**: 一键停止所有正在运行的推流

#### 实时状态监控

| 指标 | 说明 |
|------|------|
| **流量** | 已发送数据量 (GB/MB) |
| **FPS** | 当前帧率 (15-60) |
| **码率** | 推流比特率 (Kbps) |

#### 彩色日志系统

```
[INFO] 🟢 抖音推流已启动
[WARNING] ⚠️ 快手未在运行中
[ERROR] 🔴 OBS WebSocket 连接失败
```

---

### 2. 数字人配置

#### Engine 选择

| 引擎 | 状态 | 说明 |
|------|------|------|
| **LivePortrait** | ⚠️ Stub | 预留接口，需集成实际 API |
| **Wav2Lip** | ⚠️ Incomplete | 基础结构已创建 |

#### 参数配置

```yaml
# config.yaml
avatar:
  default_engine: "live_portrait"
  
  live_portrait:
    batch_size: 1        # 推理批次大小
    resize: true         # 自动缩放图像
  
  wav2lip:
    height: 512          # 输出高度
    width: 512           # 输出宽度
    fps: 25              # 帧率
```

---

### 3. 定时任务配置 (v3.0 New) ⭐

#### 创建定时任务

**操作步骤**:
1. 切换到 **⏰ 定时开关直播** Tab
2. 点击 ➕ 新增定时任务按钮
3. 填写表单:
   - **平台**: 选择抖音/快手/视频号
   - **开始时间**: 使用日期时间选择器
   - **结束时间**: (可选) 自动停止推流
4. 点击 ✅ 确认创建

#### 调度服务控制

| 按钮 | 功能 |
|------|------|
| 🟢 **启动调度服务** | 开始每 30 秒检查到期任务 |
| 🔴 **停止调度服务** | 暂停定时任务检查 |

#### 任务状态说明

| Status | 含义 |
|--------|------|
| **Pending** | 待执行，等待到时间 |
| **Running** | 正在推流中 |
| **Completed** | 已完成 (自动停止) |
| **Cancelled** | 已取消/过期 |

---

### 4. LLM Prompt 配置 (v3.0 New) ⭐

#### Dynamic Template Support

系统支持动态占位符填充的提示词模板:

```yaml
llm.system_prompt_template: |
  你是一位专业的{role}专家，擅长用生动的语言介绍{product_type}产品。
  
  【产品信息】
  {property_info}
  
  【核心卖点】
  {selling_points}
```

**可用占位符**:
- `{role}` - 角色设定 (如"二手房车销售专家")
- `{product_type}` - 产品类型 (如"房产和房车产品")
- `{property_info}` - 具体房源/产品信息
- `{selling_points}` - 核心卖点列表

#### Prompt Config UI

在 **⚙️ 系统设置 → LLM Tab** 中配置:

| 字段 | 说明 | 示例 |
|------|------|------|
| **Role** | AI 角色设定 | "二手房车销售专家" |
| **Product Type** | 产品类型分类 | "房产和房车产品" |
| **Selling Points** | 核心卖点 (可多选) | ☑核心地段 ☑精装修 ☑性价比高 |

---

### 5. TTS 语音合成

#### Edge-TTS (推荐，免费)

无需配置 API Key，系统默认使用。

**可用中文语音**:
| Voice | Gender | Description |
|-------|--------|-------------|
| `zh-CN-XiaoxiaoNeural` | Female | 温柔亲切 ⭐推荐 |
| `zh-CN-YunxiNeural` | Male | 稳重专业 |
| `zh-CN-XiaoyiNeural` | Female | 活泼自然 |
| `zh-CN-YunjianNeural` | Male | 清晰干练 |

#### Coqui-TTS (本地模型，需下载)

```yaml
tts:
  engine: "coqui"
  
  coqui:
    model: "tts_models/multilingual/multi-dataset/xtts_v2"
    language: "zh"
```

**注意**: Coqui-TTS 需要约 8GB RAM + 4GB VRAM，适合有 GPU 的用户。

---

### 6. OBS WebSocket 集成

#### 配置步骤

1. **OBS Studio → Tools → Websocket Server Settings**
2. Enable server: ✅ Check
3. Port: `4455` (default)
4. Password: (可选，建议设置)

#### GUI 配置界面

在 **⚙️ 系统设置 → OBS Tab**:
- Host: `localhost` (或远程 OBS IP)
- Port: `4455`
- Password: (如设置了密码则填写)

---

## ⚙️ 配置管理

### config.yaml 核心字段速查表

| Section | Key | Default | Description |
|---------|-----|---------|-------------|
| **app** | name | "Multi-AI-Stream" | 应用名称 |
| | version | "3.0.0" | 版本号 |
| | log_level | "INFO" | DEBUG/INFO/WARNING/ERROR |
| **obs** | host | "localhost" | OBS WebSocket 主机 |
| | port | 4455 | WebSocket 端口 |
| | password | "" | WebSocket 密码 |
| **llm** | mode | "remote" | remote/local |
| | remote.api_key | "" | ⚠️ DeepSeek API Key (必填) |
| | prompt_config.role | "二手房车销售专家" | AI 角色设定 |
| **tts** | engine | "edge" | coqui/edge/iflytek |
| | edge.voice | "zh-CN-XiaoxiaoNeural" | TTS 语音选择 |
| **platforms.douyin** | enabled | false | 抖音推流开关 |
| | rtmp_url | "" | RTMP 地址 ⚠️必填 |
| | stream_key | "" | 推流密钥 ⚠️必填 |

### 配置文件编辑技巧

1. **YAML 语法**:
   - 使用空格缩进 (2 或 4 个)
   - 字符串建议用双引号包裹
   - `#` 开头为注释

2. **热重载**:
   ```bash
   # 修改 config.yaml 后重启应用即可生效
   python src/main.py
   ```

3. **安全提示**:
   - ⚠️ API Key 不要提交到 Git!
   - ✅ 将 `configs/config.yaml` 加入 `.gitignore`

---

## ❓ 常见问题

### Q1: DeepSeek API Key 在哪里获取？

**A**: https://platform.deepseek.com  
- 注册/登录账号
- 创建项目 → 获取 API Key
- **新用户福利**: $1.5 免费额度 (约 37,500 次调用)

### Q2: Edge-TTS 需要联网吗？

**A**: 是的，Edge-TMS 使用微软 Azure TTS 云服务。  
但已内置 `edge-tts` Python 库自动处理 HTTP 请求，无需额外配置 API Key。

### Q3: OBS WebSocket 连接失败怎么办？

**排查步骤**:
1. ✅ 确认 OBS Studio 正在运行
2. ✅ 检查 obs-websocket 插件是否启用 (Tools → Websocket Server Settings)
3. ✅ 验证端口号匹配 (默认 4455)
4. ✅ 如设置了密码，确保 config.yaml 中一致

### Q4: 如何切换 TTS 语音？

**A**: 
1. ⚙️ 系统设置 → TTS Tab
2. Voice 下拉框选择其他语音
3. 💾 保存并应用

或编辑 `config.yaml`:
```yaml
tts.edge.voice: "zh-CN-YunxiNeural"  # 切换为男声
```

### Q5: 定时任务不执行？

**排查**:
1. ✅ 调度服务是否启动 (🟢 Running)
2. ✅ 检查开始时间是否已过 (过去的时间不会触发)
3. ✅ 查看 Live Log 是否有错误信息
4. ⚙️ Settings → Schedule Tab 确认 Check Interval (默认 30 秒)

### Q6: 推流卡顿/掉帧？

**优化建议**:
1. **降低码率**: `output.default_bitrate: 2000` (从 2500 降至 2000 Kbps)
2. **降低 FPS**: `output.default_fps: 24` (从 30 降至 24 fps)
3. **检查网络带宽**: 
   - 720p30fps ≥ 5 Mbps 上行
   - 1080p60fps ≥ 10 Mbps 上行

### Q7: LivePortrait 集成失败？

**A**: v3.0 中 LivePortrait 引擎为 Stub 实现，需手动集成:

```bash
# Step 1: Clone project
git clone https://github.com/KwaiVGI/LivePortrait.git

# Step 2: Install dependencies
pip install -r LivePortrait/requirements.txt

# Step 3: Download models
cd LivePortrait && ./download_models.sh

# Step 4: Update src/avatar/live_portrait.py with actual API calls
```

详见 [ARCHITECTURE.md](./ARCHITECTURE.md) → "LivePortrait Integration"

---

## 📞 支持资源

| Resource | URL | Description |
|----------|-----|-------------|
| **项目主页** | (待创建 GitHub Repo) | Issue 反馈、功能请求 |
| **DeepSeek API Docs** | https://platform.deepseek.com/docs | LLM API 参考文档 |
| **Edge-TTS PyPI** | https://pypi.org/project/edge-tts/ | TTS 库文档 |
| **OBS WebSocket** | https://github.com/Palakis/obs-websocket | Plugin installation guide |

---

## 📝 更新日志 (v3.0)

### New Features
- ⭐ Multi-platform concurrent streaming (StreamManager + StreamWorker)
- ⭐ Scheduled task management (SchedulerService)
- ⭐ Dynamic prompt template support ({role}, {product_type}, etc.)
- ⭐ Comment reply system (TemplateResponder with 8 preset templates)
- ⭐ Enhanced MainWindow UI with multi-platform control panel

### Bug Fixes
- ✅ Fixed `result` variable scope error in ContentPipeline
- ✅ Fixed import path in test_platform.py
- ✅ Enabled StreamManager integration in SchedulerService

### Code Improvements
- 📈 ~43KB new code across 8 files (~1,095 LOC)
- 🧪 Added 41+ new test cases for v3.0 modules
- 🎨 Updated GUI with Schedule Tab and multi-platform checkboxes

---

**版本**: 3.0  
**最后更新**: 2026-05-13  
**维护者**: duanxiaobo
