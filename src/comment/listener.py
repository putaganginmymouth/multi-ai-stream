"""
Comment Listener - 直播间评论监听器
支持 WebSocket/API 获取实时评论
"""

import logging
from typing import Dict, Any, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class Comment:
    """评论内容对象"""
    
    def __init__(self, platform: str, user_id: str, username: str, 
                 content: str, timestamp: Optional[int] = None):
        self.platform = platform
        self.user_id = user_id
        self.username = username
        self.content = content
        self.timestamp = timestamp or int(__import__('time').time())
    
    def __repr__(self):
        return f"Comment({self.platform}, {self.username}: {self.content})"


class CommentListener(QObject):
    """
    评论监听器基类
    
    功能:
    - 连接直播平台 WebSocket/API
    - 实时获取直播间评论
    - 通过信号槽将评论传递给 UI/Responder
    
    子类需要实现:
    - _connect(): 建立连接
    - _parse_comment(raw): 解析原始数据为 Comment 对象
    """
    
    # PyQt6 信号定义
    comment_received = pyqtSignal(object)  # (Comment)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, platform: str, config: Dict[str, Any]):
        super().__init__()
        
        self.platform = platform  # douyin/kuaishou/wechat
        self.config = config
        
        # 连接状态
        self.is_connected = False
        self._ws_client = None  # WebSocket 客户端 (子类实现)
        
        # 评论处理回调
        self.comment_handler: Optional[Callable[[Comment], None]] = None
    
    def connect(self):
        """建立评论监听连接"""
        raise NotImplementedError("子类必须实现 _connect()")
    
    def disconnect(self):
        """断开连接"""
        if self.is_connected and self._ws_client:
            try:
                self._ws_client.close()
            except:
                pass
        
        self.is_connected = False
        self.disconnected.emit()
        logger.info(f"CommentListener[{self.platform}] 已断开")
    
    def on_comment(self, handler: Callable[[Comment], None]):
        """设置评论处理回调"""
        self.comment_handler = handler
    
    def _emit_comment(self, comment: Comment):
        """发射评论信号"""
        if self.comment_handler:
            self.comment_handler(comment)
        
        # 同时发送信号供 UI 使用
        self.comment_received.emit(comment)


class SimpleCommentListener(CommentListener):
    """
    简化版评论监听器 - 用于开发测试
    
    模拟接收评论，不连接真实 WebSocket
    """
    
    def __init__(self, platform: str, config: Dict[str, Any]):
        super().__init__(platform, config)
        
        # 模拟评论数据
        self._mock_users = ["用户 123", "直播间观众 A", "房产爱好者", "看房小李"]
        self._mock_comments = [
            "这个房子多少钱一平？",
            "在哪里啊？",
            "面积多大？",
            "装修怎么样？",
            "可以贷款吗？",
            "欢迎新来的朋友！",
            "直播间人好多"
        ]
        
        # 模拟定时器
        self._mock_timer = QTimer()
        self._mock_timer.setInterval(5000)  # 每 5 秒模拟一条评论
        self._mock_timer.timeout.connect(self._simulate_comment)
    
    def connect(self):
        """启动模拟模式"""
        logger.info(f"SimpleCommentListener[{self.platform}] 已启动 (模拟模式)")
        
        # 立即发送一条欢迎评论
        comment = Comment(
            platform=self.platform,
            user_id="mock_001",
            username="系统",
            content=f"欢迎来到{self.platform}直播间！"
        )
        self._emit_comment(comment)
        
        # 开始模拟评论流
        self.is_connected = True
        self.connected.emit()
        self._mock_timer.start()
    
    def disconnect(self):
        """停止模拟"""
        self._mock_timer.stop()
        super().disconnect()
    
    def _simulate_comment(self):
        """模拟接收一条评论"""
        import random
        
        comment = Comment(
            platform=self.platform,
            user_id=f"mock_{random.randint(100, 999)}",
            username=random.choice(self._mock_users),
            content=random.choice(self._mock_comments)
        )
        
        self._emit_comment(comment)
        logger.debug(f"[SIM] {comment}")


class DouyinCommentListener(CommentListener):
    """
    抖音评论监听器 (预留实现)
    
    TODO: 集成抖音 WebSocket API
    https://live.douyin.com/webcast/room/web/enter/
    """
    
    def connect(self):
        """连接抖音直播间"""
        # TODO: 实现真实的 WebSocket 连接
        raise NotImplementedError("抖音评论监听器暂未实现，请使用 SimpleCommentListener 测试")


class KuaishouCommentListener(CommentListener):
    """
    快手评论监听器 (预留实现)
    
    TODO: 集成快手 WebSocket API
    """
    
    def connect(self):
        """连接快手直播间"""
        raise NotImplementedError("快手评论监听器暂未实现，请使用 SimpleCommentListener 测试")


class WechatCommentListener(CommentListener):
    """
    视频号评论监听器 (预留实现)
    
    TODO: 集成微信视频号 WebSocket API
    """
    
    def connect(self):
        """连接视频号直播间"""
        raise NotImplementedError("视频号评论监听器暂未实现，请使用 SimpleCommentListener 测试")
