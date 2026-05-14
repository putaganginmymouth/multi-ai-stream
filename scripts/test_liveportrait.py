"""
LivePortrait 端到端测试脚本 (v4.0)
测试数字人生成 + 口型同步 + 流式管线

用法:
    cd E:\agent-project\multi-ai-stream
    python scripts\test_liveportrait.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_dependency(name: str, import_cmd: str = None) -> bool:
    """检查依赖是否可用"""
    try:
        if import_cmd:
            exec(import_cmd)
        else:
            __import__(name)
        print(f"  ✅ {name}")
        return True
    except ImportError:
        print(f"  ❌ {name} — 未安装")
        return False


def test_01_dependencies():
    """Step 1: 检查所有依赖"""
    print_header("Step 1: 依赖检查")

    results = {
        'torch': check_dependency('torch'),
        'cv2': check_dependency('cv2', 'import cv2'),
        'numpy': check_dependency('numpy', 'import numpy'),
        'PIL': check_dependency('PIL', 'from PIL import Image'),
        'soundfile': check_dependency('soundfile'),
        'yaml': check_dependency('yaml', 'import yaml'),
    }

    # 特殊检查：torch CUDA
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            print(f"  ✅ CUDA: {torch.cuda.get_device_name(0)} ({torch.cuda.device_count()} GPU)")
        else:
            print(f"  ⚠️ CUDA 不可用 — 将使用 CPU 模式（速度较慢）")
    except ImportError:
        pass

    missing = [k for k, v in results.items() if not v]
    if missing:
        print(f"\n  ❌ 缺少依赖: {', '.join(missing)}")
        print(f"  运行: pip install {' '.join(missing)}")
        return False
    return True


def test_02_liveportrait_deployment():
    """Step 2: 检查 LivePortrait 部署状态"""
    print_header("Step 2: LivePortrait 部署检查")

    from src.avatar.live_portrait import LivePortraitEngine

    engine = LivePortraitEngine({})
    status = engine.get_deploy_status()

    print(f"  代码仓库: {status['repo_path']}")
    print(f"          存在: {'✅' if status['repo_exists'] else '❌'}")
    print(f"  模型权重: {status['weights_path']}")
    print(f"          存在: {'✅' if status['weights_exist'] else '❌'}")
    print(f"  CUDA:     {'✅' if status['cuda_available'] else '⚠️ CPU 模式'}")

    if status['missing_weights']:
        print(f"\n  ❌ 缺失权重文件 ({len(status['missing_weights'])} 个):")
        for w in status['missing_weights']:
            print(f"     - {w}")
        print(f"\n  请从 HuggingFace 下载权重:")
        print(f"    git clone https://huggingface.co/KwaiVGI/LivePortrait {status['weights_path']}")
        return None

    if not status['repo_exists']:
        print(f"\n  ❌ 代码仓库不存在")
        print(f"  运行: git clone https://github.com/KwaiVGI/LivePortrait {status['repo_path']}")
        return None

    print(f"\n  ✅ LivePortrait 已就绪")
    return engine


def test_03_model_loading(engine):
    """Step 3: 测试模型加载"""
    print_header("Step 3: 模型加载测试")

    try:
        engine.load_model()
        info = engine.get_engine_info()
        print(f"  模型状态: {'✅ 已加载' if info['loaded'] else '❌ 加载失败'}")
        print(f"  设备:     {info['device']}")
        print(f"  引擎:     {info['name']} v{info['version']}")
        return True
    except Exception as e:
        print(f"  ❌ 模型加载失败: {e}")
        print(f"\n  可能原因:")
        print(f"  1. LivePortrait 仓库未安装依赖: cd assets/avatars/liveportrait/repo && pip install -r requirements.txt")
        print(f"  2. GPU 显存不足 (需要 ~4GB VRAM)")
        print(f"  3. 模型文件损坏，重新下载")
        return False


def test_04_video_generation(engine):
    """Step 4: 测试视频生成（找一张测试图片 + 10秒静音）"""
    print_header("Step 4: 视频生成测试")

    # 创建测试素材
    import numpy as np
    from PIL import Image

    test_dir = Path("output/test_liveportrait")
    test_dir.mkdir(parents=True, exist_ok=True)

    # 创建一张 256x256 的测试图片（如果没有真实照片）
    test_image = str(test_dir / "test_avatar.jpg")
    if not Path(test_image).exists():
        img = Image.new('RGB', (256, 256), color=(200, 180, 160))
        img.save(test_image)
        print(f"  创建测试图片: {test_image} (256x256)")

    # 创建 3 秒静音 WAV
    test_audio = str(test_dir / "test_silence.wav")
    if not Path(test_audio).exists():
        try:
            import soundfile as sf
            silence = np.zeros(3 * 16000, dtype=np.float32)  # 3秒, 16kHz
            sf.write(test_audio, silence, 16000)
            print(f"  创建测试音频: {test_audio} (3秒静音)")
        except ImportError:
            import wave
            import struct
            with wave.open(test_audio, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                for _ in range(3 * 16000):
                    wf.writeframes(struct.pack('<h', 0))
            print(f"  创建测试音频: {test_audio} (3秒静音, wave fallback)")

    # 尝试生成
    try:
        output = str(test_dir / "test_output.mp4")
        print(f"  输入: {test_audio} + {test_image}")
        print(f"  输出: {output}")
        print(f"  正在生成...")

        result = engine.generate_video(test_audio, test_image, output)
        size_mb = Path(result).stat().st_size / 1024 / 1024
        print(f"  ✅ 视频已生成: {result} ({size_mb:.1f}MB)")
        return True

    except Exception as e:
        print(f"  ❌ 视频生成失败: {e}")
        return False


def test_05_streaming_frames(engine):
    """Step 5: 测试流式帧生成"""
    print_header("Step 5: 流式帧生成测试")

    test_dir = Path("output/test_liveportrait")
    test_image = str(test_dir / "test_avatar.jpg")
    test_audio = str(test_dir / "test_silence.wav")

    if not Path(test_image).exists() or not Path(test_audio).exists():
        print("  ⚠️ 跳过 — 测试素材不存在（先运行 Step 4）")
        return False

    try:
        print(f"  流式生成中 (3秒 @ 30fps ≈ 90帧)...")
        frame_count = 0
        for frame in engine.generate_stream(test_audio, test_image, fps=30):
            frame_count += 1
            if frame_count == 1:
                print(f"  首帧尺寸: {frame.shape}")

        print(f"  ✅ 流式生成完成: {frame_count} 帧")
        return frame_count > 0

    except Exception as e:
        print(f"  ❌ 流式生成失败: {e}")
        return False


def test_06_unload_model(engine):
    """Step 6: 卸载模型"""
    print_header("Step 6: 模型卸载")
    try:
        engine.unload_model()
        print(f"  ✅ 模型已卸载")
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            print(f"  GPU 显存已释放 (当前占用: {allocated:.1f}GB)")
        return True
    except Exception as e:
        print(f"  ⚠️ 卸载异常: {e}")
        return False


def main():
    print("=" * 60)
    print("  LivePortrait 数字人生成 — 端到端测试")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  项目根: {Path(__file__).parent.parent}")
    print("=" * 60)

    results = {}

    # Step 1: 依赖
    results['deps'] = test_01_dependencies()
    if not results['deps']:
        print("\n⚠️ 请先安装缺失的依赖后再测试")
        print("  pip install torch torchvision opencv-python numpy pillow soundfile")
        return 1

    # Step 2: 部署
    engine = test_02_liveportrait_deployment()
    results['deploy'] = engine is not None
    if engine is None:
        print("\n⚠️ LivePortrait 未部署，请参考 WINDOWS_DEPLOYMENT_V4.md")
        return 1

    # Step 3: 加载
    results['load'] = test_03_model_loading(engine)
    if not results['load']:
        return 1

    # Step 4: 生成
    results['video'] = test_04_video_generation(engine)

    # Step 5: 流式
    results['stream'] = test_05_streaming_frames(engine)

    # Step 6: 卸载
    results['unload'] = test_06_unload_model(engine)

    # 总结
    print_header("测试总结")
    all_pass = True
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  🎉 全部测试通过！数字人口型同步功能就绪。")
        return 0
    else:
        print(f"\n  ⚠️ 部分测试未通过，请检查上述错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
