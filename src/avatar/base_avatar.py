"""
Avatar Engine Abstraction Layer - Base Avatar
数字人生成引擎基类，定义所有数字人引擎必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Iterator
import logging
import numpy as np
from ..core.base import Configurable
from ..core.enums import AvatarEngineType
from ..core.exceptions import AvatarError, ModelNotFoundError

logger = logging.getLogger(__name__)


class BaseAvatar(Configurable):
    """
    数字人生成引擎抽象基类
    
    所有具体引擎实现必须继承此类并实现以下方法:
    - generate_video() - 生成视频流
    - sync_lips() - 口型同步处理
    - load_model() - 加载模型
    - unload_model() - 卸载模型
    
    设计模式：策略模式 (Strategy Pattern)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数字人引擎
        
        Args:
            config: 引擎配置字典，包含模型路径、GPU 设置等
        """
        super().__init__(config)
        
        self._model_loaded = False
        self._model_path: str = config.get('models_path', './assets/avatars')
        self._device: str = config.get('device', 'auto')
        
        # 引擎特定配置
        self._engine_config = {k: v for k, v in config.items() 
                               if not k in ['models_path', 'device']}
    
    @abstractmethod
    def _validate_config(self):
        """验证引擎配置"""
        pass
    
    def load_model(self) -> bool:
        """
        加载模型
        
        Returns:
            bool: 是否成功加载
        """
        if self._model_loaded:
            logger.warning("模型已加载，跳过")
            return True
        
        try:
            self._load()
            self._model_loaded = True
            logger.info(f"数字人模型加载成功：{self.__class__.__name__}")
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败：{e}")
            return False
    
    def unload_model(self):
        """卸载模型"""
        if not self._model_loaded:
            return
        
        try:
            self._unload()
            self._model_loaded = False
            logger.info("数字人模型已卸载")
            
        except Exception as e:
            logger.error(f"模型卸载失败：{e}")
    
    @abstractmethod
    def _load(self):
        """加载模型的实现 (由子类实现)"""
        pass
    
    @abstractmethod
    def _unload(self):
        """卸载模型的实现 (由子类实现)"""
        pass
    
    @abstractmethod
    def generate_video(self, audio_path: str, image_path: str, 
                       output_path: Optional[str] = None) -> str:
        """
        生成数字人视频
        
        Args:
            audio_path: 音频文件路径 (TTS 输出)
            image_path: 数字人图片路径
            output_path: 输出视频路径 (可选)
            
        Returns:
            str: 生成的视频文件路径
        """
        pass
    
    def generate_stream(self, audio_data: bytes, image: np.ndarray, 
                        fps: int = 25) -> Iterator[np.ndarray]:
        """
        生成流式视频帧 (用于实时直播)
        
        Args:
            audio_data: 音频数据
            image: 数字人图像 (numpy array)
            fps: 帧率
            
        Yields:
            np.ndarray: 每一帧图像
        """
        # 默认实现：调用 generate_video 然后逐帧读取
        output_path = self.generate_video(
            audio_path=self._temp_audio_path(audio_data),
            image_path=self._temp_image_path(image)
        )
        
        yield from self._read_frames(output_path)
    
    def _temp_audio_path(self, audio_data: bytes) -> str:
        """临时音频文件路径"""
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        with open(path, 'wb') as f:
            f.write(audio_data)
        return path
    
    def _temp_image_path(self, image: np.ndarray) -> str:
        """临时图像文件路径"""
        import tempfile, os
        from PIL import Image
        
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        img = Image.fromarray(image)
        img.save(path)
        return path
    
    def _read_frames(self, video_path: str) -> Iterator[np.ndarray]:
        """从视频文件读取帧"""
        try:
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                yield frame_rgb
            
            cap.release()
            
        except Exception as e:
            logger.error(f"读取视频帧失败：{e}")
            raise AvatarError(f"视频帧读取错误：{e}")
    
    def sync_lips(self, audio_path: str, source_image: np.ndarray,
                  result_image: Optional[np.ndarray] = None) -> np.ndarray:
        """
        口型同步处理
        
        Args:
            audio_path: 音频文件路径
            source_image: 源图像 (数字人图片)
            result_image: 结果图像 (可选，用于复用内存)
            
        Returns:
            np.ndarray: 口型同步后的图像帧
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'name': self.__class__.__name__,
            'loaded': self._model_loaded,
            'path': self._model_path,
            'device': self._device
        }
