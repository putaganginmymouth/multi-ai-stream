"""
Stream Manager - 多平台推流管理器
负责管理多个 StreamWorker 实例，实现多路并发推流控制
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .stream_worker import StreamWorker, SimpleStreamWorker
from ..core.enums import LiveStatus

logger = logging.getLogger(__name__)


class StreamManager(QObject):
    """
    多平台推流管理器
    
    功能:
    - 管理多个平台的推流 Worker 实例
    - 独立控制每个平台的启停状态
    - 通过信号槽与 UI 通信，不阻塞主线程
    
    架构设计:
    ┌─────────────────────────────────────────────┐
    │           StreamManager                     │
    ├─────────────────────────────────────────────┤
    │  workers: Dict[str, StreamWorker]          │
    │  - douyin: StreamWorker                    │
    │  - kuaishou: StreamWorker                  │
    │  - wechat: StreamWorker                    │
    └─────────────────────────────────────────────┘
               ↓ signals
    ┌─────────────────────────────────────────────┐
    │           MainWindow UI                     │
    │  - platform_started(str)                   │
    │  - platform_stopped(str)                   │
    │  - status_changed(str, str)                │
    └─────────────────────────────────────────────┘
    """
    
    # PyQt6 信号定义
    platform_started = pyqtSignal(str)      # (platform_name)
    platform_stopped = pyqtSignal(str)      # (platform_name)
    status_changed = pyqtSignal(str, str)   # (platform_name, status)
    log_message = pyqtSignal(str)           # (message)
    
    def __init__(self, config: Dict[str, Any], use_obs: bool = True):
        super().__init__()
        
        self.config = config
        self.use_obs = use_obs  # 是否使用 OBS（False 时使用模拟模式）
        
        # 平台 Worker 字典
        self.workers: Dict[str, StreamWorker] = {}
        
        # 平台状态追踪
        self.platform_status: Dict[str, LiveStatus] = {
            'douyin': LiveStatus.IDLE,
            'kuaishou': LiveStatus.IDLE,
            'wechat': LiveStatus.IDLE,
        }
        
        # 支持的 platform 列表
        self.supported_platforms = ['douyin', 'kuaishou', 'wechat']
    
    def get_worker(self, platform: str) -> Optional[StreamWorker]:
        """获取指定平台的 Worker 实例"""
        return self.workers.get(platform)
    
    def is_platform_running(self, platform: str) -> bool:
        """检查平台是否正在运行"""
        if platform not in self.platform_status:
            return False
        return self.platform_status[platform] == LiveStatus.LIVE
    
    def start_platform(self, platform: str) -> bool:
        """
        启动指定平台的推流
        
        Args:
            platform: 平台名称 (douyin/kuaishou/wechat)
        
        Returns:
            bool: 是否成功启动
        """
        if platform not in self.supported_platforms:
            logger.error(f"不支持的平台：{platform}")
            return False
        
        # 检查是否已在运行
        if self.is_platform_running(platform):
            logger.warning(f"{platform} 已经在运行中")
            return True
        
        # 创建 Worker (如果不存在)
        if platform not in self.workers:
            worker_class = StreamWorker if self.use_obs else SimpleStreamWorker
            self.workers[platform] = worker_class(platform, self.config)
        
        worker = self.workers[platform]
        
        try:
            # 启动推流 (在 Worker 线程中执行)
            success = worker.start_stream()
            
            if success:
                self.platform_status[platform] = LiveStatus.LIVE
                self.platform_started.emit(platform)
                self.status_changed.emit(platform, "running")
                logger.info(f"✅ {platform} 推流已启动")
                
                # 启动 Worker 线程
                worker.start()
            
            return success
            
        except Exception as e:
            logger.error(f"启动 {platform} 推流失败：{e}")
            self.status_changed.emit(platform, f"error: {str(e)}")
            return False
    
    def stop_platform(self, platform: str) -> bool:
        """
        停止指定平台的推流
        
        Args:
            platform: 平台名称 (douyin/kuaishou/wechat)
        
        Returns:
            bool: 是否成功停止
        """
        if platform not in self.platform_status:
            logger.error(f"未知平台：{platform}")
            return False
        
        # 检查是否在运行
        if not self.is_platform_running(platform):
            logger.warning(f"{platform} 未在运行中")
            return True
        
        worker = self.workers.get(platform)
        if not worker:
            logger.error(f"未找到 {platform} Worker")
            return False
        
        try:
            # 停止推流
            success = worker.stop_stream()
            
            if success:
                self.platform_status[platform] = LiveStatus.IDLE
                self.platform_stopped.emit(platform)
                self.status_changed.emit(platform, "stopped")
                logger.info(f"❌ {platform} 推流已停止")
            
            return success
            
        except Exception as e:
            logger.error(f"停止 {platform} 推流失败：{e}")
            return False
    
    def stop_all_platforms(self):
        """停止所有平台的推流"""
        for platform in self.supported_platforms:
            self.stop_platform(platform)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取所有平台的状态摘要"""
        summary = {}
        for platform in self.supported_platforms:
            worker = self.workers.get(platform)
            if worker:
                summary[platform] = {
                    'status': self.platform_status[platform].value,
                    'is_running': self.is_platform_running(platform),
                    'stats': worker.get_stream_stats() if hasattr(worker, 'get_stream_stats') else {}
                }
            else:
                summary[platform] = {
                    'status': LiveStatus.IDLE.value,
                    'is_running': False,
                    'stats': {}
                }
        return summary
    
    def get_active_platforms(self) -> list:
        """获取正在运行的平台列表"""
        return [p for p in self.supported_platforms if self.is_platform_running(p)]
    
    def cleanup(self):
        """清理资源 - 停止所有推流并释放连接"""
        logger.info("开始清理 StreamManager 资源...")
        
        # 停止所有平台
        self.stop_all_platforms()
        
        # 断开所有 OBS 连接
        for platform, worker in self.workers.items():
            if hasattr(worker, '_disconnect_obs'):
                worker._disconnect_obs()
        
        logger.info("StreamManager 资源清理完成")
