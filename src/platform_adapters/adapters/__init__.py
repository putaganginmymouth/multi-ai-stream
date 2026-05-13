"""
Platform Adapters - 多平台评论捕获适配器层
提供统一的接口对接各平台的 WebSocket/API
"""

from .wecom_webhook_adapter import (
    WeComWebhookAdapter,
    get_wecom_adapter,
    test_wecom_webhook
)


__all__ = [
    'WeComWebhookAdapter',
    'get_wecom_adapter',
    'test_wecom_webhook'
]
