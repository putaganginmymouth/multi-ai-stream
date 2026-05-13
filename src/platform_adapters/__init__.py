"""
Platform Layer - 平台适配层
提供多平台直播评论捕获与回复发送的统一接口
"""

from .adapters.wecom_webhook_adapter import (
    WeComWebhookAdapter,
    get_wecom_adapter,
    test_wecom_webhook
)


__all__ = [
    # Adapters
    'WeComWebhookAdapter',
    'get_wecom_adapter',
    'test_wecom_webhook'
]
