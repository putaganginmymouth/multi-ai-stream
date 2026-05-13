"""
Stream Worker - 单平台推流工作线程
负责控制单个平台的 RTMP 推流过程
"""

import logging
from typing import Dict, Any, Optional
try:
    from obswebsocket import obs_websocket
except ImportError:
    obs_websocket = None

from ..core.base import Base
from ..core.enums import LiveStatus
from ..core.exceptions import PlatformError

logger = logging.getLogger(__name__)


class StreamWorker(Base):
    """
    单路推流工作线程
    
    功能:
    - 连接 OBS WebSocket
    - 启动/停止推流
    - 监控推流状态
    - 通过信号槽与 UI 通信
    
    使用场景:
    - 被 StreamManager 管理，每个平台一个实例
    - 继承自 QThread，在独立线程中运行
    """
    
    # PyQt6 信号定义
    log_signal = None
    status_signal = None
    progress_signal = None
    
    def __init__(self, platform: str, config: Dict[str, Any]):
        super().__init__()
        
        self.platform = platform  # 平台名称：douyin/kuaishou/wechat
        self.config = config      # 完整配置
        
        # RTMP 配置 (从 config 中提取)
        platform_config = config.get('platforms', {}).get(platform, {})
        self._rtmp_url = platform_config.get('rtmp_url', '')
        self._stream_key = platform_config.get('stream_key', '')
        
        # OBS 客户端实例
        self._obs_client: Optional[object] = None
        
        # 运行状态
        self.is_running = False
        self.live_status = LiveStatus.IDLE
        
        # 推流统计
        self.total_bytes_sent = 0
        self.fps = 0
        self.bitrate = 0
    
    def _validate_config(self) -> bool:
        """验证平台配置"""
        if not self._rtmp_url:
            raise PlatformError(f"{self.platform}推流 URL 不能为空", "CONFIG_ERROR")
        
        if not self._stream_key:
            raise PlatformError(f"{self.platform}推流密钥不能为空", "CONFIG_ERROR")
        
        return True
    
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
                logger.info(f"OBS WebSocket 已断开")
            except Exception as e:
                logger.error(f"断开 OBS 连接失败：{e}")
    
    def start_stream(self) -> bool:
        """开始推流"""
        try:
            # 验证配置
            self._validate_config()
            
            # 连接 OBS
            if not self._connect_obs():
                return False
            
            # 设置输出路径 (RTMP)
            output_config = {
                'output_path': self._rtmp_url,
                'output_key': self._stream_key,
                'output_use_audio': True,
                'output_use_video': True,
                'output_max_bitrate': self.config.get('output', {}).get('default_bitrate', 2500),
                'output_kbps': self.config.get('output', {}).get('default_bitrate', 2500),
            }
            
            # 启动输出 (OBS WebSocket API)
            if hasattr(self._obs_client, 'send'):
                self._obs_client.send("SetOutputSettings", {
                    "outputName": "simple_output",
                    "outputSettings": output_config
                })
            
            # 开始推流
            self._obs_client.send("StartService", {"type": "rtmp"})
            
            self.is_running = True
            self.live_status = LiveStatus.LIVE
            logger.info(f"✅ {self.platform} 直播已启动")
            
            return True
            
        except Exception as e:
            logger.error(f"启动推流失败：{e}")
            return False
    
    def stop_stream(self) -> bool:
        """停止推流"""
        try:
            if not self.is_running:
                return True  # 已停止，无需操作
            
            # 停止推流
            if self._obs_client and self._obs_client.is_connected():
                self._obs_client.send("StopService", {"type": "rtmp"})
            
            self.is_running = False
            self.live_status = LiveStatus.IDLE
            logger.info(f"❌ {self.platform} 直播已停止")
            
            return True
            
        except Exception as e:
            logger.error(f"停止推流失败：{e}")
            return False
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """获取推流状态统计"""
        return {
            'platform': self.platform,
            'is_running': self.is_running,
            'status': self.live_status.value,
            'total_bytes_sent': self.total_bytes_sent,
            'fps': self.fps,
            'bitrate': self.bitrate,
        }
    
    def run(self):
        """线程主函数 - 由 QThread 调用"""
        logger.info(f"StreamWorker[{self.platform}] 启动")
        
        # 注意：实际推流控制需要在外部通过 start_stream/stop_stream 调用
        # 这里主要用于日志记录和状态维护
        while self.is_running:
            # 定期检查推流状态
            import time
            time.sleep(1)
            
            if self._obs_client and self._obs_client.is_connected():
                try:
                    stats = self._obs_client.send("GetStreamingStats")
                    if stats:
                        self.total_bytes_sent = stats.get('bytesSent', 0)
                        self.fps = stats.get('avgFrameRate', 0)
                        self.bitrate = stats.get('outputBitrate', 0)
                except:
                    pass
    
    def stop(self):
        """停止线程"""
        self.is_running = False


class SimpleStreamWorker(StreamWorker):
    """
    简化版 Stream Worker - 不依赖 OBS，直接推流测试用
    
    用于开发阶段快速验证多路并发逻辑，实际生产环境使用 StreamWorker
    """
    
    def __init__(self, platform: str, config: Dict[str, Any]):
        super().__init__(platform, config)
        self._simulated = True  # 模拟模式标记
    
    def start_stream(self) -> bool:
        """模拟推流启动"""
        try:
            # 验证配置
            self._validate_config()
            
            logger.info(f"🚀 [SIM] {self.platform} 开始推流...")
            self.is_running = True
            self.live_status = LiveStatus.LIVE
            
            # 模拟推流过程
            import time
            for i in range(10):
                if not self.is_running:
                    break
                time.sleep(1)
                self.total_bytes_sent += 1024 * 500  # 模拟 500KB/s
            
            return True
            
        except Exception as e:
            logger.error(f"启动推流失败：{e}")
            return False
    
    def stop_stream(self) -> bool:
        """模拟停止推流"""
        self.is_running = False
        self.live_status = LiveStatus.IDLE
        logger.info(f"🛑 [SIM] {self.platform} 停止推流")
        return True
