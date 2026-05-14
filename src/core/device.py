"""
Device Detection Module - GPU/CUDA/MPS/CPU
设备自动检测模块，统一管理计算设备选择

使用:
    from core.device import get_device, get_optimal_device
    device = get_optimal_device()
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def is_cuda_available() -> bool:
    """检测 NVIDIA CUDA GPU 是否可用"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def is_mps_available() -> bool:
    """检测 Apple Silicon MPS 是否可用"""
    try:
        import torch
        return hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    except ImportError:
        return False


def get_device_count(device_type: str = "cuda") -> int:
    """获取指定类型设备数量"""
    if device_type == "cuda" and is_cuda_available():
        import torch
        return torch.cuda.device_count()
    return 1 if device_type == "cpu" else 0


def get_optimal_device(force: Optional[str] = None) -> str:
    """
    自动检测并使用最佳计算设备

    Args:
        force: 强制使用指定设备 (cuda/mps/cpu/auto)

    Returns:
        str: 设备类型字符串
    """
    if force and force != "auto":
        return force

    if is_cuda_available():
        logger.info("检测到 NVIDIA GPU — 使用 CUDA")
        return "cuda"

    if is_mps_available():
        logger.info("检测到 Apple Silicon GPU — 使用 MPS")
        return "mps"

    logger.info("未检测到 GPU — 使用 CPU")
    return "cpu"


def get_torch_device(device_str: Optional[str] = None) -> Any:
    """
    返回 PyTorch device 对象

    Args:
        device_str: 设备字符串 (cuda/mps/cpu/auto)，为 None 时自动检测

    Returns:
        torch.device 对象
    """
    import torch

    device_str = device_str or get_optimal_device()

    return torch.device(device_str)
