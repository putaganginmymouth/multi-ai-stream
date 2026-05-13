"""
Platform Adapters - 多平台评论捕获适配器层
提供统一的接口对接各平台的 WebSocket/API
"""

from typing import Dict, Any, Callable, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class WeComWebhookAdapter:
    """企业微信 Webhook 适配器 (视频号专用)"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self._is_connected = False
        self._comment_callbacks = []
    
    def connect(self) -> bool:
        """连接测试（Webhook 无需真正连接，仅验证 URL）"""
        
        try:
            test_msg = {
                "msgtype": "text",
                "text": {"content": "🔧 企业微信 Webhook 适配器已就绪"}
            }
            
            response = requests.post(
                self.webhook_url, 
                json=test_msg,
                timeout=5
            )
            
            if response.json().get('errcode') == 0:
                logger.info("✅ 企业微信 Webhook 连接成功")
                self._is_connected = True
                return True
            else:
                logger.error(f"❌ Webhook 验证失败：{response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook 连接异常：{e}")
            return False
    
    def disconnect(self):
        """断开连接（Webhook 无需操作）"""
        self._is_connected = False
    
    def on_comment(self, callback: Callable[[Dict], None]):
        """设置评论回调函数 (Webhook 仅支持发送，不支持接收)"""
        
        # Webhook 是单向的，这里用于注册回复发送回调
        logger.warning("企业微信 Webhook 仅支持发送消息，不支持接收评论")
    
    def send_comment(self, comment: Dict[str, Any]) -> bool:
        """发送评论到企业微信群 (用于监控)"""
        
        message = {
            "msgtype": "text",
            "text": {
                "content": f"@{comment.get('username', '用户')} {comment.get('text', '')}\n来自视频号直播间"
            }
        }
        
        try:
            response = requests.post(
                self.webhook_url, 
                json=message,
                timeout=5
            )
            
            success = response.json().get('errcode') == 0
            
            if success:
                logger.info(f"✅ 评论发送成功：{comment.get('text')}")
            else:
                logger.error(f"❌ 评论发送失败：{response.json()}")
            
            return success
            
        except Exception as e:
            logger.error(f"发送评论异常：{e}")
            return False
    
    def send_reply(self, user_id: str, reply_text: str) -> bool:
        """发送自动回复到企业微信群"""
        
        message = {
            "msgtype": "text",
            "text": {
                "content": f"@{user_id} {reply_text}"
            }
        }
        
        try:
            response = requests.post(
                self.webhook_url, 
                json=message,
                timeout=5
            )
            
            success = response.json().get('errcode') == 0
            
            if success:
                logger.info(f"✅ 回复发送成功：{reply_text}")
            else:
                logger.error(f"❌ 回复发送失败：{response.json()}")
            
            return success
            
        except Exception as e:
            logger.error(f"发送回复异常：{e}")
            return False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._is_connected


# ============================================================================
# Global Webhook Adapter Management
# ============================================================================

_wecom_adapter: Optional[WeComWebhookAdapter] = None


def get_wecom_adapter(webhook_url: str) -> WeComWebhookAdapter:
    """获取或创建 Webhook 适配器单例"""
    
    global _wecom_adapter
    
    if _wecom_adapter is None or _wecom_adapter.webhook_url != webhook_url:
        _wecom_adapter = WeComWebhookAdapter(webhook_url)
    
    return _wecom_adapter


def test_wecom_webhook() -> bool:
    """测试 Webhook 连接"""
    
    # 从环境变量或配置加载 URL
    import os
    webhook_url = os.environ.get('WECOM_WEBHOOK_URL', '')
    
    if not webhook_url:
        logger.error("未配置 WECOM_WEBHOOK_URL 环境变量")
        return False
    
    adapter = get_wecom_adapter(webhook_url)
    
    if adapter.connect():
        print("✅ Webhook 配置成功！")
        
        # 测试发送评论
        adapter.send_comment({
            'username': '张先生',
            'text': '这款房车多少钱？'
        })
        
        # 测试发送回复
        adapter.send_reply('张先生', '这款房车售价 88 万，性价比很高。感兴趣可以留言了解更多~')
    else:
        print("❌ Webhook 配置失败，请检查 URL 是否正确")
    
    return adapter.is_connected()


if __name__ == '__main__':
    test_wecom_webhook()
