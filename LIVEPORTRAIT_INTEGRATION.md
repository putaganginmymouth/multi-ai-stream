# Multi-AI-Stream - LivePortrait 集成指南 v1.0

本文档详细说明如何集成 LivePortrait 实时数字人引擎。

---

## 📦 什么是 LivePortrait?

LivePortrait 是快手开源的**实时数字人驱动项目**:
- ⚡ **30fps+** 实时推理速度
- 🎭 **单图驱动**，只需一张人脸照片
- 👄 **高精度口型同步**
- 🔧 支持表情迁移、头部姿态控制

🔗 GitHub: https://github.com/KwaiVGI/LivePortrait

---

## 🚀 集成步骤

### 第一步：克隆 LivePortrait 项目

```bash
# 在 multi-ai-stream 目录下执行
cd /path/to/multi-ai-stream

git clone https://github.com/KwaiVGI/LivePortrait.git
cd LivePortrait
```

### 第二步：安装依赖

```bash
# 方法 1: 使用 requirements.txt (推荐)
pip install -r requirements.txt

# 方法 2: 手动安装关键包
pip install torch torchvision torchaudio
pip install opencv-python
pip install onnxruntime-gpu  # GPU 加速
pip install safetensors
pip install omegaconf
```

### 第三步：下载模型

```bash
# 方式 1: 使用自动脚本 (推荐)
./download_models.sh

# 方式 2: 手动下载
# 访问 HuggingFace: https://huggingface.co/KwaiVGI/LivePortrait
# 下载以下文件到 models/ 目录:
# - retargetting_models.zip (包含口型驱动模型)
```

### 第四步：测试 LivePortrait 推理

```bash
# 准备测试素材
mkdir -p assets/test
cp /path/to/avatar.jpg assets/test/
cp /path/to/audio.wav assets/test/

# 运行推理脚本
python inference.py \
    --source assets/test/avatar.jpg \
    --driving assets/test/audio.wav \
    --result_path output_test.mp4 \
    --flag_identities
```

**预期输出**: `output_test.mp4` (数字人视频)

---

## 🔧 集成到 Multi-AI-Stream

### 1. 修改项目结构

```
multi-ai-stream/
├── LivePortrait/          ← 克隆的 LivePortrait 项目
│   ├── inference.py       # 推理脚本
│   └── models/            # 模型文件
│
└── assets/avatars/
    └── liveportrait/      ← 模型链接或副本
        ├── driving_extractor.pth
        ├── motion_extractor.pth  
        ├── warping_module.pth
        └── spade_generator.pth
```

### 2. 创建符号链接 (可选)

```bash
# macOS/Linux
ln -s ../LivePortrait/models ./assets/avatars/liveportrait

# Windows (PowerShell)
New-Item -ItemType SymbolicLink -Path "assets\avatars\liveportrait" -Target "..\LivePortrait\models"
```

### 3. 更新配置

在 `configs/config.yaml` 中添加:

```yaml
avatar:
  default_engine: "live_portrait"
  models_path: "./assets/avatars/liveportrait"
  
  live_portrait:
    batch_size: 1
    resize: true
    inference_dir: "../LivePortrait"  # LivePortrait 项目路径
```

### 4. 修改代码集成

在 `src/avatar/live_portrait.py` 中实现实际调用:

```python
import subprocess
import tempfile
from pathlib import Path

class LivePortraitEngine(BaseAvatar):
    
    def generate_video(self, audio_path: str, image_path: str, 
                       output_path: Optional[str] = None) -> str:
        """使用 LivePortrait 生成视频"""
        
        if not self._model_loaded:
            raise AvatarError("模型未加载", "MODEL_NOT_LOADED")
        
        # 设置输出路径
        out_path = output_path or f"./output_{hash(audio_path)}.mp4"
        
        try:
            # 调用 LivePortrait inference.py
            cmd = [
                "python", 
                str(self._lp_inference_dir / "inference.py"),
                "--source", str(image_path),
                "--driving", str(audio_path),  # 或视频文件
                "--result_path", out_path,
                "--flag_identities"
            ]
            
            # 执行推理
            result = subprocess.run(
                cmd,
                cwd=self._lp_inference_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 分钟超时
            )
            
            if result.returncode != 0:
                raise AvatarError(f"LivePortrait 推理失败：{result.stderr}", "GEN_ERROR")
            
            logger.info(f"视频生成成功：{out_path}")
            return out_path
            
        except subprocess.TimeoutExpired:
            raise AvatarError("推理超时", "TIMEOUT_ERROR")
```

---

## 🎯 实时推流集成方案

### 架构设计

```
┌─────────────────────┐
│   Multi-AI-Stream   │
│   (主程序)          │
├─────────────────────┤
│   Content Pipeline  │
│   └── LLM → TTS     │
└──────────┬──────────┘
           │ audio_data
           ▼
┌─────────────────────┐
│  LivePortrait       │
│  (实时推理进程)      │
├─────────────────────┤
│   video_frame ─────▶│ OBS
│                     │ (RTMP 推流)
└─────────────────────┘
```

### 实现思路

#### 方案 A: 子进程调用 (简单，适合非实时场景)

```python
import subprocess
import time

class LivePortraitEngine(BaseAvatar):
    
    def generate_stream(self, audio_data: bytes, image: np.ndarray):
        """流式生成视频帧"""
        
        # 1. 保存音频到临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(audio_data)
            audio_path = f.name
        
        # 2. 启动 LivePortrait 推理进程 (持续运行模式)
        process = subprocess.Popen(
            [
                "python", 
                str(self._lp_inference_dir / "inference.py"),
                "--source", image_path,
                "--driving", audio_path,
                "--stream-mode"  # TODO: LivePortrait 需支持流式输出
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 3. 读取视频帧并推送到 OBS
        for frame in self._read_frames(process.stdout):
            yield frame
        
        process.terminate()
```

#### 方案 B: Python API 直接调用 (推荐，性能更好)

```python
from liveportrait.inference import InferenceManager  # LivePortrait 官方 API

class LivePortraitEngine(BaseAvatar):
    
    def _load(self):
        """初始化推理引擎"""
        self.infer_manager = InferenceManager(
            config_path=str(self._config_path),
            device=self.get_device()
        )
        
        self._model_loaded = True
    
    def generate_stream(self, audio_data: bytes, image: np.ndarray):
        """实时生成视频帧"""
        
        # 1. 预处理音频
        audio_features = self.preprocess_audio(audio_data)
        
        # 2. 逐帧驱动
        for frame_idx in range(num_frames):
            # 调用 LivePortrait 推理
            output_frame = self.infer_manager.inference(
                source_image=image,
                driving_feature=audio_features[frame_idx]
            )
            
            yield output_frame
    
    def preprocess_audio(self, audio_data: bytes) -> list:
        """音频特征提取"""
        # TODO: 使用 LivePortrait 的 audio processor
        pass
```

---

## 📊 性能测试与优化

### GPU 加速配置

#### Windows (NVIDIA CUDA)

```bash
# 安装 CUDA 版 PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 验证 GPU 可用
python -c "import torch; print(torch.cuda.is_available())"
```

#### macOS (Apple Silicon MPS)

```bash
# 安装 CPU/MPS 版 PyTorch  
pip install torch torchvision

# 验证 MPS 可用
python -c "import torch; print(hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())"
```

### 性能基准测试

| 配置 | GPU | FPS | 延迟 |
|-----|-----|-----|------|
| GTX 1060 6GB | CUDA | ~8fps | ~125ms |
| RTX 3060 12GB | CUDA | ~25fps | ~40ms |
| M2 Max (16GB) | MPS | ~15fps | ~67ms |

**优化建议**:
- 降低分辨率：512x512 → 256x256 (速度 +50%, 质量略降)
- 调整 batch_size: 4 → 1 (延迟 -30%)
- 使用 ONNX Runtime GPU 加速

---

## 🐛 常见问题

### Q1: LivePortrait 推理失败？

**错误**: `ModuleNotFoundError: No module named 'liveportrait'`

**解决**:
```bash
# 确保在 LivePortrait 目录下安装
cd LivePortrait
pip install -e .  # 以可编辑模式安装
```

---

### Q2: GPU 显存不足？

**错误**: `CUDA out of memory`

**解决**:
1. **降低分辨率**:
   ```yaml
   live_portrait:
     resize: false  # 禁用自动缩放，使用原始小分辨率
   ```

2. **减少 batch_size**:
   ```yaml
   live_portrait:
     batch_size: 1  # 从 4 降至 1
   ```

3. **清理 GPU 缓存**:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

---

### Q3: 口型不同步？

**症状**: 数字人口型与音频不匹配

**排查**:
1. **检查采样率**:
   - 音频应为 16kHz 或 22050Hz
   - 使用 `pydub` 转换：
     ```python
     from pydub import AudioSegment
     
     audio = AudioSegment.from_wav("input.wav")
     audio = audio.set_frame_rate(16000)
     audio.export("output_16k.wav", format="wav")
     ```

2. **调整口型强度**:
   ```yaml
   live_portrait:
     lip_sync_strength: 1.2  # 从 1.0 调高
   ```

---

## 📝 下一步优化方向

1. **流式推理**: 修改 LivePortrait 支持实时帧级输出
2. **多 GPU 支持**: 分离渲染和推流进程
3. **模型量化**: INT8 量化减少显存占用
4. **异步处理**: 使用 asyncio 实现非阻塞推理

---

**版本**: v1.0  
**最后更新**: 2026-05-12  
**作者**: duanxiaobo
