"""
Avatar Engine Factory - Strategy Pattern Implementation
数字人生成引擎工厂类
"""

from typing import Dict, Any, Optional, Type
import logging
from .base_avatar import BaseAvatar
from .live_portrait import LivePortraitEngine
from .wav2lip import Wav2LipEngine
from ..core.enums import AvatarEngineType
from ..core.exceptions import MultiStreamError, AvatarEngineNotFoundError

logger = logging.getLogger(__name__)


class AvatarFactory:
    """
    数字人生成引擎工厂类
    
    使用示例:
        avatar = AvatarFactory.create("live_portrait", config)
        # 或
        avatar = AvatarFactory.create(AvatarEngineType.LIVE_PORTRAIT, config)
    """
    
    _engine_map: Dict[str, Type[BaseAvatar]] = {
        'live_portrait': LivePortraitEngine,
        'wav2lip': Wav2LipEngine,
        'sadtalker': None  # 预留
    }
    
    @classmethod
    def register_engine(cls, engine_type: str, engine_class: Type[BaseAvatar]):
        """注册新的引擎类型"""
        cls._engine_map[engine_type.lower()] = engine_class
    
    @classmethod
    def create(cls, engine_type: str, config: Dict[str, Any]) -> BaseAvatar:
        """
        创建数字人引擎实例
        
        Args:
            engine_type: 引擎类型字符串或枚举
            config: 引擎配置字典
            
        Returns:
            BaseAvatar 实例
            
        Raises:
            AvatarEngineNotFoundError: 如果引擎类型不存在
        """
        # 转换为小写字符串
        if isinstance(engine_type, AvatarEngineType):
            engine_type = str(engine_type)
        
        engine_type = engine_type.lower()
        
        if engine_type not in cls._engine_map:
            available = [k for k, v in cls._engine_map.items() if v is not None]
            raise AvatarEngineNotFoundError(
                f"未知的引擎类型：{engine_type}\n"
                f"可用类型：{available}"
            )
        
        engine_class = cls._engine_map[engine_type]
        
        # 确保配置包含 engine_type 字段
        config_with_type = config.copy()
        if 'type' not in config:
            config_with_type['type'] = engine_type
        
        return engine_class(config_with_type)
    
    @classmethod
    def get_engine(cls, engine_type: str, config: Dict[str, Any]) -> BaseAvatar:
        """获取引擎实例 (带缓存，类似单例)"""
        # 这里可以添加缓存逻辑
        return cls.create(engine_type, config)
    
    @classmethod
    def get_available_engines(cls) -> list:
        """获取所有可用的引擎类型"""
        return [k for k, v in cls._engine_map.items() if v is not None]
