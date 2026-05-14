"""
WebHook Receiver - Unified Comment Ingestion Endpoint
统一 WebHook 评论接收器 (v4.0)

职责:
- 启动 HTTP 服务器接收外部评论
- 标准化评论数据格式
- 通过 PyQt6 信号传递给 CommentAggregator

设计模式：适配器模式 (Adapter)，将 HTTP 请求适配为 Comment 信号
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Callable, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from .listener import Comment

logger = logging.getLogger(__name__)


class WebHookHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器 — 类变量由 WebHookReceiver 设置"""

    comment_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    auth_token: Optional[str] = None

    def do_POST(self):
        if self.path != '/webhook/comment':
            self._respond(404, {'error': 'not found'})
            return

        # Token 鉴权
        if self.auth_token:
            auth = self.headers.get('Authorization', '')
            expected = f'Bearer {self.auth_token}'
            if auth != expected:
                self._respond(401, {'error': 'unauthorized'})
                return

        # 解析请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {'error': 'invalid JSON'})
            return

        # 必填字段验证
        required = ['platform', 'username', 'content']
        missing = [k for k in required if k not in data]
        if missing:
            self._respond(400, {'error': f'missing fields: {missing}'})
            return

        # 转发给回调
        if self.comment_callback:
            try:
                self.comment_callback(data)
            except Exception as e:
                logger.error(f"评论回调异常: {e}")

        self._respond(200, {'status': 'ok'})

    def do_GET(self):
        """健康检查端点"""
        if self.path == '/health':
            self._respond(200, {'status': 'healthy', 'service': 'webhook-receiver'})
        else:
            self._respond(404, {'error': 'not found'})

    def _respond(self, code: int, data: dict):
        """发送 JSON 响应"""
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """禁用默认 HTTP 日志，改用应用日志"""
        pass


class WebHookReceiver(QObject):
    """
    统一 WebHook 接收器

    在后台线程运行 HTTP 服务器，接收外部评论后通过信号发送。

    外部调用示例:
        POST http://localhost:8888/webhook/comment
        Content-Type: application/json
        Authorization: Bearer <token>

        {
            "platform": "kuaishou",
            "user_id": "user_123",
            "username": "观众A",
            "content": "这款房车多少钱？"
        }
    """

    comment_received = pyqtSignal(object)   # Comment 对象
    server_started = pyqtSignal(int)         # (port)
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)

    def __init__(self, config: Dict[str, Any]):
        super().__init__()

        webhook_cfg = config.get('webhook', {})
        self._host = webhook_cfg.get('host', '0.0.0.0')
        self._port = int(webhook_cfg.get('port', 8888))
        self._auth_token = webhook_cfg.get('auth_token', '')
        self._enabled = webhook_cfg.get('enabled', False)

        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._is_running = False

    def start(self):
        """启动 WebHook 服务器"""
        if not self._enabled:
            logger.info("WebHook 接收器未启用（webhook.enabled=false）")
            return

        if self._is_running:
            logger.warning("WebHook 接收器已在运行")
            return

        # 设置处理器类变量
        WebHookHandler.comment_callback = self._on_webhook_comment
        WebHookHandler.auth_token = self._auth_token or None

        try:
            self._server = HTTPServer((self._host, self._port), WebHookHandler)
        except OSError as e:
            logger.error(f"WebHook 端口 {self._port} 被占用: {e}")
            self.server_error.emit(str(e))
            return

        self._server_thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name='webhook-server'
        )
        self._server_thread.start()
        self._is_running = True

        logger.info(f"WebHook 接收器已启动: http://{self._host}:{self._port}/webhook/comment")
        self.server_started.emit(self._port)

    def stop(self):
        """停止 WebHook 服务器"""
        if not self._is_running:
            return

        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

        self._is_running = False
        logger.info("WebHook 接收器已停止")
        self.server_stopped.emit()

    def _on_webhook_comment(self, data: Dict[str, Any]):
        """将 WebHook 数据转为 Comment 对象并发射信号"""
        comment = Comment(
            platform=data.get('platform', 'unknown'),
            user_id=data.get('user_id', data.get('username', 'webhook_user')),
            username=data.get('username', 'anonymous'),
            content=data.get('content', ''),
            timestamp=data.get('timestamp')
        )
        logger.debug(f"[WebHook] {comment}")
        self.comment_received.emit(comment)

    def is_running(self) -> bool:
        return self._is_running
