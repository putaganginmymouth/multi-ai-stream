"""
Douyin Platform Implementation
抖音直播平台实现
"""

import logging
from typing import Dict, Any, Optional
try:
    from obswebsocket import obs_websocket
except ImportError:
    obs_websocket = None

from .base_platform import BasePlatform
from ..core.enums import LiveStatus
from ..core.exceptions import PlatformError

logger = logging.getLogger(__name__)


class DouyinPlatform(BasePlatform):
    """
    抖音直播平台实现
    
    使用 OBS WebSocket API 控制推流
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 抖音 RTMP 服务器地址 (从官网获取)
        self._douyin_servers = [
            "rtmp://live-push.douyin.com/live/",
            "rtmp://pull-flv-l1.douyin.com/live/"
        ]
        
        # OBS 客户端实例
        self._obs_client: Optional[object] = None
    
    def _validate_config(self):
        """验证抖音平台配置"""
        if not self._rtmp_url:
            raise PlatformError("抖音推流 URL 不能为空", "CONFIG_ERROR")
        
        if not self._stream_key:
            raise PlatformError("抖音推流密钥不能为空", "CONFIG_ERROR")
    
    def _connect_obs(self) -> bool:
        """连接 OBS WebSocket"""
        try:
            if obs_websocket is None:
                logger.error("obs-websocket 未安装，请运行：pip install obs-websocket-py")
                return False
            
            # 从配置获取 OBS 连接信息
            host = self.config.get('obs', {}).get('host', 'localhost')
            port = self.config.get('obs', {}).get('port', 4455)
            password = self.config.get('obs', {}).get('password', '')
            
            self._obs_client = obs_websocket.obs_websocket()
            self._obs_client.connect(host, port, password)
            
            # 测试连接
            if self._obs_client.is_connected():
                logger.info(f"OBS WebSocket 连接成功：{host}:{port}")
                return True
            
        except Exception as e:
            logger.error(f"OBS WebSocket 连接失败：{e}")
        
        return False
    
    def _disconnect_obs(self):
        """断开 OBS 连接"""
        if self._obs_client and self._obs_client.is_connected():
            try:
                self._obs_client.disconnect()
            except Exception as e:
                logger.warning(f"断开 OBS 连接时出错：{e}")
    
    def _configure_stream(self):
        """配置推流参数"""
        if not self._obs_client:
            return
        
        try:
            # 设置 RTMP 服务器地址
            self._obs_client.call('SetServiceSettings', {
                'services': {
                    'service': 'douyin_custom',
                    'settings': {
                        'server': self._rtmp_url,
                        'key': self._stream_key
                    }
                }
            })
            
            # 设置输出参数 (比特率、分辨率等)
            self._obs_client.call('SetOutputSettings', {
                'outputType': 'rtmp_output',
                'outputId': 'simple_rtmp_output',
                'settings': {
                    'service': 'douyin_custom',
                    'key': self._stream_key,
                    'rate_control': 'CBR',
                    'bitrate': 2500,  # Kbps
                    'cache_size': 0,
                    'max_bitrate': 3000,
                    'reconnect': True,
                    'retry_delay': 2,
                    'max_retries': 10,
                    'codec': 'libx264',
                    'muxer_type': 'flv_muxer'
                }
            })
            
        except Exception as e:
            logger.error(f"配置推流参数失败：{e}")
    
    def start_stream(self, rtmp_url: Optional[str] = None, 
                     stream_key: Optional[str] = None) -> bool:
        """开始抖音直播"""
        
        if rtmp_url:
            self._rtmp_url = rtmp_url
        if stream_key:
            self._stream_key = stream_key
        
        # 验证配置
        try:
            self._validate_config()
        except Exception as e:
            logger.error(f"配置验证失败：{e}")
            return False
        
        try:
            # 连接 OBS
            if not self._connect_obs():
                raise PlatformError("OBS WebSocket 连接失败", "CONN_ERROR")
            
            # 配置推流参数
            self._configure_stream()
            
            # 启动推流
            self._obs_client.call('StartStream')
            
            self._status = LiveStatus.LIVE
            logger.info(f"抖音直播已启动：{self._rtmp_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"启动抖音直播失败：{e}")
            self._status = LiveStatus.ERROR
            return False
    
    def stop_stream(self) -> bool:
        """停止抖音直播"""
        try:
            if self._obs_client and self._obs_client.is_connected():
                self._obs_client.call('StopStream')
                
                # 等待一小段时间确认停止
                import time
                time.sleep(0.5)
            
            self._status = LiveStatus.IDLE
            logger.info("抖音直播已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止抖音直播失败：{e}")
            return False
    
    def get_status(self) -> LiveStatus:
        """获取当前状态"""
        if self._obs_client and self._obs_client.is_connected():
            try:
                stream_stats = self._obs_client.call('GetStreamingStatus')
                if stream_stats.get('streaming', False):
                    return LiveStatus.LIVE
            except Exception as e:
                logger.warning(f"获取流状态失败：{e}")
        
        return self._status
    
    def _do_start_stream(self):
        """执行启动操作"""
        if self._obs_client:
            self._obs_client.call('StartStream')
    
    def _do_stop_stream(self):
        """执行停止操作"""
        if self._obs_client and self._obs_client.is_connected():
            try:
                self._obs_client.call('StopStream')
            except Exception as e:
                logger.error(f"停止推流失败：{e}")
    
    def _do_pause(self):
        """暂停推流"""
        # OBS 不支持直接暂停 RTMP，需要手动处理
        logger.warning("OBS 暂不支持 RTMP 暂停功能")
    
    def _do_resume(self):
        """恢复推流"""
        logger.info("恢复推流")
