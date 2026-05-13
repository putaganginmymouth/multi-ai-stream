"""
Platform Factory - Strategy Pattern Implementation
平台工厂类，根据类型创建对应的平台实例
"""

from typing import Dict, Any, Optional, Type
from .base_platform import BasePlatform
from .douyin_platform import DouyinPlatform
from .kuaishou_platform import KuaishouPlatform
from .wechat_platform import WeChatPlatform
from ..core.enums import PlatformType
from ..core.exceptions import MultiStreamError


class PlatformFactory:
    """
    平台工厂类
    
    使用示例:
        platform = PlatformFactory.create("douyin", config)
        # 或
        platform = PlatformFactory.create(PlatformType.DOUYIN, config)
    """
    
    _platform_map: Dict[str, Type[BasePlatform]] = {
        'douyin': DouyinPlatform,
        'kuaishou': KuaishouPlatform,
        'wechat': WeChatPlatform,
        'custom': BasePlatform  # 默认使用基类
    }
    
    @classmethod
    def register_platform(cls, platform_type: str, platform_class: Type[BasePlatform]):
        """注册新的平台类型"""
        cls._platform_map[platform_type.lower()] = platform_class
    
    @classmethod
    def create(cls, platform_type: str, config: Dict[str, Any]) -> BasePlatform:
        """
        创建平台实例
        
        Args:
            platform_type: 平台类型字符串或枚举
            config: 平台配置字典
            
        Returns:
            BasePlatform 实例
            
        Raises:
            MultiStreamError: 如果平台类型不存在
        """
        # 转换为小写字符串
        if isinstance(platform_type, PlatformType):
            platform_type = str(platform_type)
        
        platform_type = platform_type.lower()
        
        if platform_type not in cls._platform_map:
            available = list(cls._platform_map.keys())
            raise MultiStreamError(
                f"未知的平台类型：{platform_type}\n"
                f"可用类型：{available}",
                "PLATFORM_NOT_FOUND"
            )
        
        # 确保配置包含 type 字段
        config_with_type = config.copy()
        if 'type' not in config:
            config_with_type['type'] = platform_type
        
        platform_class = cls._platform_map[platform_type]
        return platform_class(config_with_type)
    
    @classmethod
    def create_batch(cls, platforms_config: Dict[str, Dict]) -> list:
        """
        批量创建平台实例
        
        Args:
            platforms_config: {platform_name: config_dict}
            
        Returns:
            BasePlatform 实例列表
        """
        return [
            cls.create(name, config)
            for name, config in platforms_config.items()
        ]
    
    @classmethod
    def get_available_types(cls) -> list:
        """获取所有可用的平台类型"""
        return list(cls._platform_map.keys())
