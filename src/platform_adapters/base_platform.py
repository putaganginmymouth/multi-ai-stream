"""
Platform Abstraction Layer - Base Platform
平台接入层基类，定义所有直播平台必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from ..core.base import Configurable, Observable
from ..core.enums import LiveStatus, PlatformType
from ..core.exceptions import PlatformError, PlatformConnectionError

logger = logging.getLogger(__name__)


class BasePlatform(Configurable, Observable, ABC):
    """
    直播平台抽象基类
    
    所有具体平台实现必须继承此类并实现以下方法:
    - start_stream()
    - stop_stream()
    - get_status()
    - reconnect()
    
    设计模式：策略模式 (Strategy Pattern)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化平台
        
        Args:
            config: 平台配置字典，包含 rtmp_url, stream_key 等
        """
        super().__init__(config)
        
        self._status = LiveStatus.IDLE
        self._rtmp_url: str = config.get('rtmp_url', '')
        self._stream_key: str = config.get('stream_key', '')
        self._obs_client = None
        
        # 验证必要配置
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self):
        """验证平台配置是否有效"""
        pass
    
    @abstractmethod
    def _connect_obs(self) -> bool:
        """
        连接 OBS WebSocket
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def start_stream(self, rtmp_url: Optional[str] = None, 
                     stream_key: Optional[str] = None) -> bool:
        """
        开始推流
        
        Args:
            rtmp_url: RTMP 推流地址 (可选，覆盖配置)
            stream_key: 推流密钥 (可选，覆盖配置)
            
        Returns:
            bool: 是否成功启动
        """
        if rtmp_url:
            self._rtmp_url = rtmp_url
        if stream_key:
            self._stream_key = stream_key
        
        # 验证必填项
        if not self._rtmp_url or not self._stream_key:
            logger.error("RTMP URL 或 Stream Key 为空")
            return False
        
        try:
            # 连接 OBS
            if not self._connect_obs():
                raise PlatformConnectionError(
                    str(self.get_platform_type()), "OBS 连接失败"
                )
            
            # 设置推流配置
            self._configure_stream()
            
            # 启动推流
            self._do_start_stream()
            
            self._status = LiveStatus.LIVE
            self.notify('stream_started', {
                'platform': str(self.get_platform_type()),
                'rtmp_url': self._rtmp_url
            })
            
            return True
            
        except Exception as e:
            logger.error(f"启动推流失败：{e}")
            self._status = LiveStatus.ERROR
            self.notify('stream_error', {'error': str(e)})
            return False
    
    @abstractmethod
    def stop_stream(self) -> bool:
        """停止推流"""
        pass
    
    @abstractmethod
    def get_status(self) -> LiveStatus:
        """获取当前直播状态"""
        pass
    
    def _configure_stream(self):
        """配置推流参数 (由子类实现具体逻辑)"""
        pass
    
    @abstractmethod
    def _do_start_stream(self):
        """执行实际的启动操作 (由子类实现)"""
        pass
    
    @abstractmethod
    def _do_stop_stream(self):
        """执行实际的停止操作 (由子类实现)"""
        pass
    
    def get_platform_type(self) -> PlatformType:
        """获取平台类型枚举"""
        return PlatformType(self.config.get('type', 'custom'))
    
    def reconnect(self) -> bool:
        """重新连接 OBS"""
        try:
            self._disconnect_obs()
            return self._connect_obs()
        except Exception as e:
            logger.error(f"重连失败：{e}")
            return False
    
    def _disconnect_obs(self):
        """断开 OBS 连接 (由子类实现)"""
        pass
    
    def pause_stream(self) -> bool:
        """暂停推流"""
        try:
            self._do_pause()
            self._status = LiveStatus.PAUSED
            return True
        except Exception as e:
            logger.error(f"暂停失败：{e}")
            return False
    
    def resume_stream(self) -> bool:
        """恢复推流"""
        try:
            self._do_resume()
            self._status = LiveStatus.LIVE
            return True
        except Exception as e:
            logger.error(f"恢复失败：{e}")
            return False
    
    @abstractmethod
    def _do_pause(self):
        """执行暂停操作"""
        pass
    
    @abstractmethod
    def _do_resume(self):
        """执行恢复操作"""
        pass
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """获取推流统计数据"""
        return {
            'status': str(self._status),
            'rtmp_url': self._rtmp_url,
            'uptime': 0,  # 待实现
            'bitrate': 0  # 待实现
        }
