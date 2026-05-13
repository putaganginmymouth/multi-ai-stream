# Multi-AI-Stream - Windows 部署指南

本文档详细说明如何在 Windows 系统上部署和运行 Multi-AI-Stream。

---

## 📋 系统要求

| 组件 | 最低配置 | 推荐配置 |
|-----|---------|---------|
| **操作系统** | Windows 10/11 | Windows 11 |
| **Python** | 3.10+ | 3.11+ |
| **内存** | 16GB RAM | 32GB RAM |
| **GPU** | GTX 1060 (可选) | RTX 3060+ (推荐) |
| **硬盘** | 50GB 可用空间 | 100GB SSD |

---

## 🚀 快速部署步骤

### Step 1: 安装 Python

1. **下载 Python 3.10+**
   - 访问：https://www.python.org/downloads/
   - 下载 Windows x86-64 installer

2. **安装时勾选 "Add Python to PATH"**
   ```
   ☑ Add python.exe to PATH  ← 重要!
   ```

3. **验证安装**
   ```cmd
   python --version
   # 应显示：Python 3.10.x 或更高
   ```

---

### Step 2: 克隆项目

```cmd
# 创建项目目录
cd C:\Users\YourName\Projects
mkdir multi-ai-stream
cd multi-ai-stream

# 克隆代码 (如已下载可跳过)
git clone https://github.com/yourusername/multi-ai-stream.git .
```

---

### Step 3: 创建虚拟环境

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 验证
python --version
```

---

### Step 4: 安装依赖

```cmd
# 升级 pip
python -m pip install --upgrade pip

# 安装核心依赖 (包含 PyQt6)
pip install -r requirements.txt

# 可选：安装开发依赖
pip install -r requirements-dev.txt
```

**注意**: 
- PyQt6 会自动下载 (~100MB)
- 如遇网络问题，可使用国内镜像:
  ```cmd
  pip install PyQt6 -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

---

### Step 5: 安装 OBS Studio

1. **下载 OBS**
   - 访问：https://obsproject.com/download
   - 选择 "Windows (portable)" 或 installer

2. **配置 obs-websocket**
   ```
   打开 OBS → 工具 → obs-websocket
   
   ☑ Enable server
   Port: 4455
   Password: (可选)
   
   点击 OK
   ```

---

### Step 6: 初始化数据库

```cmd
# 激活虚拟环境后运行
venv\Scripts\activate
python scripts/init_db.py
```

**输出**: `SQLite 数据库初始化完成：.\data\multi_ai_stream.db`

---

### Step 7: 启动 GUI

```cmd
python src/main.py
```

如果一切正常，会看到图形界面窗口。

---

## 🎯 LivePortrait 集成 (可选)

如需使用实时数字人功能，需要安装 LivePortrait:

### Windows 安装脚本

创建 `install_liveportrait.bat`:

```batch
@echo off
chcp 65001 >nul
echo ==============================================
echo Multi-AI-Stream LivePortrait 部署 (Windows)
echo ==============================================

set LP_DIR=%~dp0LivePortrait
set MODELS_DIR=%~dp0assets\avatars\liveportrait

echo [Step 1/3] Cloning LivePortrait...
if not exist "%LP_DIR%" (
    git clone https://github.com/KwaiVGI/LivePortrait.git "%LP_DIR%"
    echo ✅ Cloned!
) else (
    echo ℹ️  Already exists, skipping.
)

echo [Step 2/3] Installing dependencies...
cd /d "%LP_DIR%"
pip install -r requirements.txt
if errorlevel 1 (
    echo ⚠️ Some packages may have failed...
)

echo [Step 3/3] Downloading models...
if exist "models\warping_module.pth" (
    echo ℹ️ Models already downloaded.
) else (
    echo Downloading from HuggingFace...
    mkdir models
    curl -o "models\driving_extractor.pth" https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/driving_extractor.pth
    curl -o "models\motion_extractor.pth" https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/motion_extractor.pth
    curl -o "models\warping_module.pth" https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/warping_module.pth
    curl -o "models\spade_generator.pth" https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/spade_generator.pth
    
    if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"
    mklink /J "%MODELS_DIR%" "%LP_DIR%\models"
)

echo.
echo ==============================================
echo Installation complete!
echo ==============================================
pause
```

运行安装:
```cmd
install_liveportrait.bat
```

---

## 📦 打包成 EXE (可选)

使用 PyInstaller 将项目打包为独立可执行文件:

### Step 1: 安装 PyInstaller

```cmd
pip install pyinstaller upx
```

### Step 2: 运行打包脚本

```cmd
python scripts/build_exe.py
```

### Step 3: 查看结果

打包完成后，在 `dist\` 目录生成:
- `MultiAIStream.exe` - 主程序 (~150MB)
- 需要的 DLL 和配置文件会自动包含

### Step 4: 测试 EXE

```cmd
cd dist
MultiAIStream.exe
```

**注意**: 
- 首次运行可能需要安装 Visual C++ Redistributable
- 从 Windows Defender 白名单中排除项目目录

---

## 🔧 常见问题解决

### Q1: pip 连接超时

**解决方案**: 使用国内镜像源
```cmd
pip install PyQt6 -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### Q2: OBS WebSocket 连接失败

**检查步骤**:
1. 确认 OBS 已启动
2. 工具 → obs-websocket → 确保"启用服务器"已勾选
3. 端口应为 4455
4. 如设置了密码，在 `configs/config.yaml` 中填写

### Q3: PyQt6 导入失败

**解决方案**:
```cmd
# 重新安装
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6>=6.5.0

# Windows 特定：确保安装了 MSVC runtime
# 下载：https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Q4: LivePortrait GPU 不可用

**检查**:
```cmd
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

如显示 False，尝试安装 CPU 版本:
```cmd
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Q5: EXE 打包后运行报错 "DLL load failed"

**解决方案**:
1. 确保安装了 Visual C++ Redistributable
2. 在 PyInstaller 命令中添加 `--add-binary`:
   ```cmd
   pyinstaller --add-binary "path\to\opencv_python*.dll;." spec_file.spec
   ```

---

## 📊 性能优化建议

### Windows GPU 加速配置

1. **安装 CUDA 版 PyTorch** (NVIDIA GPU):
   ```cmd
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **验证 GPU 可用**:
   ```cmd
   python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
   ```

3. **OBS NVENC 编码** (降低 CPU 占用):
   ```
   OBS → 设置 → 输出
   视频编码器：NVIDIA NVENC H.264 (new)
   ```

---

## 📝 配置文件说明

### Windows 路径配置

在 `configs/config.yaml` 中，Windows 路径使用:

```yaml
# 正确写法 (正向斜杠或双反斜杠)
models_path: "./assets/avatars"
database:
  sqlite:
    path: ".\data\multi_ai_stream.db"

# 或使用原始字符串
avatar:
  live_portrait:
    inference_dir: r".\LivePortrait"
```

---

## 🎉 部署完成检查清单

- [ ] Python 3.10+ 已安装
- [ ] 项目代码已克隆到本地
- [ ] 虚拟环境已创建并激活
- [ ] PyQt6 和其他依赖已安装
- [ ] OBS Studio 已安装并配置 obs-websocket
- [ ] 数据库已初始化 (`data/multi_ai_stream.db` 存在)
- [ ] GUI 能正常启动运行

---

**版本**: v1.0  
**最后更新**: 2026-05-12  
**作者**: duanxiaobo
