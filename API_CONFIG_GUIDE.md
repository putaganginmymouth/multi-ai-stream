# LLM/TTS 远程 API 配置指南

## 📋 配置摘要

### ✅ 已完成的修改

1. **配置文件更新** (`configs/config.yaml`)
   - LLM: 新增 `remote`/`local` 双模式支持，默认使用远程 DeepSeek API
   - TTS: 保持 Edge-TTS 本地库方案（无需额外配置）

2. **系统设置 UI** (`src/gui/settings_dialog.py`, 30KB)
   - 独立的配置对话框
   - 标签页组织：LLM / TTS / OBS
   - 实时保存验证

3. **主窗口集成** (`src/gui/main_window.py`)
   - 新增"⚙️ 系统设置"菜单
   - 快捷键支持：Ctrl+L (LLM), Ctrl+T (TTS), Ctrl+, (全部)

4. **Script Generator 升级** (`src/content/script_generator.py`)
   - 集成 DeepSeek API 调用
   - 自动降级 fallback 机制

---

## 🚀 快速开始

### 1️⃣ 获取 DeepSeek API Key

访问 [DeepSeek 开放平台](https://platform.deepseek.com)：
- 注册/登录账号
- 创建新项目 → 获取 API Key
- **新用户赠送 $1.5 免费额度**（足够测试数百次调用）

### 2️⃣ 安装依赖

```bash
cd /Users/duanxiaobo/multi-ai-stream
pip install -r requirements.txt
# 已包含 requests>=2.31.0 (LLM API 请求库)
```

### 3️⃣ 启动并配置

```bash
python -m src.gui.main_window
```

**操作步骤：**
1. 点击菜单栏 **⚙️ 系统设置 → 系统设置 (全部)**
2. LLM 标签页：
   - Provider: DeepSeek（已默认）
   - API Key: 粘贴你的密钥
   - Base URL: https://api.deepseek.com/v1（已默认）
   - Model: deepseek-chat（已默认）
3. TTS 标签页：保持 Edge-TTS（已默认）
4. 点击 **💾 保存并应用**

---

## 📊 DeepSeek API 定价参考

| 模型 | 输入价格 | 输出价格 | 推荐场景 |
|------|---------|---------|----------|
| deepseek-chat | $0.27/1M tokens | $1.10/1M tokens | 文案生成（性价比高） |
| deepseek-coder | $0.27/1M tokens | $1.10/1M tokens | 代码辅助 |

**示例成本：**
- 一条房产文案约 200 字 ≈ 30 tokens
- 输入+输出总计≈60 tokens
- **单次调用成本：~$0.00004**（万分之四美元）
- $1.5 免费额度可生成 **约 37,500 条文案**

---

## 🔧 Edge-TTS 方案说明

### ✅ 为什么选择 Edge-TTS？

| 特性 | Edge-TTS (本地库) | Coqui-TTS (本地模型) |
|------|------------------|---------------------|
| **免费** | ✅ 完全免费 | ✅ 开源免费 |
| **音质** | ⭐⭐⭐⭐⭐ 微软 Neural TTS | ⭐⭐⭐⭐ 良好 |
| **速度** | ⚡ 快（云端） | 🐢 慢（需下载 2GB 模型） |
| **资源** | 💾 低（仅网络请求） | 💾 高（8GB+ RAM, 4GB+ VRAM） |
| **中文支持** | ⭐⭐⭐⭐⭐ 完美 | ⭐⭐⭐⭐ 良好 |
| **配置难度** | 🟢 无需 API Key | 🟡 需安装依赖 |

### 📦 Edge-TTS 已集成功能

```python
# src/content/tts_service.py
- edge_tts.Communicate(text, voice)  # 调用微软 Azure TTS
- 自动转换为 WAV 格式（内部使用 pydub）
- 支持中文语音：
  - zh-CN-XiaoxiaoNeural (晓晓，女声，推荐)
  - zh-CN-YunxiNeural (云希，男声)
  - zh-CN-XiaoyiNeural (晓伊，女声)
  - zh-CN-YunjianNeural (云健，男声)
```

**无需任何额外配置！** 系统已默认使用 Edge-TTS。

---

## 🖥️ Windows 硬件要求分析

### 你的配置：32GB RAM + 8GB VRAM

| 方案 | CPU | GPU | RAM | 是否可行 |
|------|-----|-----|-----|----------|
| **Edge-TTS** | ✅ 任意 | ❌ 不需要 | ✅ 2GB+ | ✅ **完全足够** |
| Coqui-TTS (XTTS v2) | ⚠️ i5/Ryzen 5 | ⚠️ GTX 1060 | ⚠️ 8GB+ | ✅ 勉强够用 |
| DeepSeek API | ✅ 任意 | ❌ 不需要 | ✅ 2GB+ | ✅ **完全足够** |

### 💡 结论

- **Edge-TTS**: 无需考虑硬件，只要有网络即可
- **DeepSeek API**: 远程调用，本地仅需处理文本
- **你的配置 (32G/8G)**: 对于 Edge-TTS + DeepSeek API 组合 **完全足够**

---

## 📝 修改文件清单

| 文件 | 变更内容 | 状态 |
|------|---------|------|
| `configs/config.yaml` | LLM 远程 API 配置项 | ✅ 已更新 |
| `src/gui/settings_dialog.py` | 新建系统设置对话框 (30KB) | ✅ 已创建 |
| `src/gui/__init__.py` | 导出 SettingsDialog | ✅ 已更新 |
| `src/gui/main_window.py` | 添加系统设置菜单入口 | ✅ 已更新 |
| `src/content/script_generator.py` | DeepSeek API 集成 | ✅ 已更新 |
| `requirements.txt` | 新增 requests 依赖 | ✅ 已更新 |

---

## 🧪 测试验证

运行以下命令快速测试配置：

```bash
cd /Users/duanxiaobo/multi-ai-stream
python -c "from src.content.script_generator import ScriptGeneratorHandler; print('✅ 导入成功')"
```

---

## ❓ FAQ

**Q: DeepSeek API Key 会保存在哪里？**  
A: 配置文件中（`configs/config.yaml`），建议将配置文件加入 `.gitignore`。

**Q: Edge-TTS 需要联网吗？**  
A: 是的，但已内置 `edge-tts` 库自动处理 HTTP 请求，无需额外配置。

**Q: 如果 DeepSeek API 不可用怎么办？**  
A: 系统会自动降级到 fallback 模式（生成示例文案），保证功能可用。

**Q: 能否切换回本地模型模式？**  
A: 在系统设置中切换 LLM 模式为"本地模型 (GGUF)"即可。

---

## 📞 支持资源

- **DeepSeek 文档**: https://platform.deepseek.com/docs
- **Edge-TTS PyPI**: https://pypi.org/project/edge-tts/
- **项目问题反馈**: GitHub Issues
