# 企业微信 Webhook 配置指南 - 视频号直播评论接入

**版本**: v1.0  
**创建日期**: 2026-05-13  
**适用平台**: 微信视频号 (WeChat Channels)  

---

## 📋 目录

1. [快速配置步骤](#1-快速配置步骤)
2. [Webhook URL 获取](#2-webhook-url-获取)
3. [API 使用说明](#3-api-使用说明)
4. [Python 集成代码](#4-python-集成代码)
5. [常见问题](#5-常见问题)

---

## 1. 快速配置步骤 (5 分钟完成)

### 步骤 1: 创建企业微信群

```bash
方式 A: 使用个人微信
├─ 打开微信 → 群聊 → 发起群聊
└─ 选择 3 个以上好友 → 命名群组（如"视频号直播测试"）

方式 B: 使用企业微信 (推荐)
├─ 登录 https://work.weixin.qq.com/
├─ 创建企业（个人可免费试用）
└─ 添加成员 → 创建部门群聊
```

### 步骤 2: 添加自定义机器人

1. **打开群聊设置**
   ```bash
   微信/企业微信 → 进入群组 → 点击右上角"..." → 群管理
   ```

2. **添加机器人**
   ```bash
   群管理 → 快捷回复/机器人 → 添加入群机器人
   ```

3. **配置机器人信息**
   - **名称**: 选择任意名称（如"直播评论助手"）
   - **头像**: 上传任意图片（可选）
   - **安全设置**: ⚠️ **重要！必须验证密钥**

4. **添加 Webhook URL**
   ```bash
   机器人详情 → 点击"管理" → 复制 Webhook 地址
   ```

---

## 2. Webhook URL 获取

### 2.1 URL 格式

```python
# 企业微信群机器人 Webhook URL 格式
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"

# 示例（已脱敏）
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### 2.2 URL 验证

```bash
# 测试 Webhook 是否可用
curl -X POST "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"text","text":{"content":"测试消息"}}'

# 预期返回
{
    "errcode": 0,
    "errmsg": "ok"
}
```

---

## 3. API 使用说明

### 3.1 发送文本消息 (评论接收)

**请求格式**:
```json
POST https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
Content-Type: application/json

{
    "msgtype": "text",
    "text": {
        "content": "@User123 这款房车价格多少？\n来自视频号直播间"
    },
    "mentioned_list": ["@all"]
}
```

**Python 示例**:
```python
import requests
import json

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"

def send_comment_to_group(comment: dict):
    """发送评论到企业微信群"""
    
    message = {
        "msgtype": "text",
        "text": {
            "content": f"@{comment['username']} {comment['text']}\n来自视频号直播间"
        },
        "mentioned_list": ["@all"]  # 全员提醒（可选）
    }
    
    response = requests.post(WEBHOOK_URL, json=message)
    
    if response.json().get('errcode') == 0:
        print("✅ 评论发送成功")
        return True
    else:
        print(f"❌ 发送失败：{response.json()}")
        return False

# 使用示例
send_comment_to_group({
    'username': '张先生',
    'text': '这款房车多少钱？'
})
```

---

### 3.2 系统回复 (自动回复)

**请求格式**:
```json
POST https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
Content-Type: application/json

{
    "msgtype": "text",
    "text": {
        "content": "@User123 这款房车售价 88 万，性价比很高。感兴趣可以留言了解更多~"
    }
}
```

**Python 示例**:
```python
def send_reply_to_user(user_id: str, reply_text: str):
    """发送自动回复到企业微信群"""
    
    message = {
        "msgtype": "text",
        "text": {
            "content": f"@{user_id} {reply_text}"
        }
    }
    
    response = requests.post(WEBHOOK_URL, json=message)
    
    return response.json().get('errcode') == 0

# 使用示例
send_reply_to_user("张先生", "这款房车售价 88 万，性价比很高。感兴趣可以留言了解更多~")
```

---

### 3.3 发送 Markdown 消息 (富文本)

**请求格式**:
```json
POST https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
Content-Type: application/json

{
    "msgtype": "markdown",
    "markdown": {
        "content": "**房车介绍**\n\n- 价格：88 万\n- 尺寸：5.9m × 2.4m × 3.0m\n- **配置**: 柴油发电机、太阳能板、净水系统"
    }
}
```

---

## 4. Python 集成代码

### 4.1 WeComWebhookAdapter (完整实现)

```python
# src/platform/adapters/wecom_webhook_adapter.py
import requests
import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class WeComWebhookAdapter:
    """企业微信 Webhook 适配器 (视频号专用)"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self._is_connected = False
    
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
    
    def send_comment(self, comment: Dict[str, Any]) -> bool:
        """发送评论到企业微信群"""
        
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


# 全局实例管理
_wecom_adapter: Optional[WeComWebhookAdapter] = None


def get_wecom_adapter(webhook_url: str) -> WeComWebhookAdapter:
    """获取或创建 Webhook 适配器单例"""
    
    global _wecom_adapter
    
    if _wecom_adapter is None or _wecom_adapter.webhook_url != webhook_url:
        _wecom_adapter = WeComWebhookAdapter(webhook_url)
    
    return _wecom_adapter


def test_wecom_webhook():
    """测试 Webhook 连接"""
    
    # 替换为你的实际 URL
    WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
    
    adapter = get_wecom_adapter(WEBHOOK_URL)
    
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


if __name__ == '__main__':
    test_wecom_webhook()
```

---

### 4.2 配置文件集成

**config.yaml**:
```yaml
# 企业微信 Webhook 配置 (视频号专用)
wecom:
  enabled: true                    # 是否启用
  webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
  
  # 发送配置
  send_comment_to_group: true      # 是否将评论发送到群（用于监控）
  auto_reply_enabled: true         # 是否自动回复
  
  # 提醒配置
  mention_all_on_comment: false    # 新评论时@所有人（建议关闭避免打扰）
```

---

## 5. 常见问题 (FAQ)

### Q1: Webhook URL 复制后无法使用？

**A**: 检查以下几点：
1. ✅ URL 是否完整（包含 `key=YOUR_KEY` 部分）
2. ✅ 是否误加了引号或空格
3. ✅ 机器人是否在同一个群内

**验证方法**:
```python
import requests

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

response = requests.post(WEBHOOK_URL, json={
    "msgtype": "text",
    "text": {"content": "测试"}
})

print(response.json())  # {"errcode": 0, "errmsg": "ok"} = 成功
```

---

### Q2: 发送消息后群内无响应？

**A**: 可能原因：
1. ⚠️ **安全设置未验证**: 添加机器人时必须勾选"启用安全设置"并填写 IP 白名单（留空即可）
2. ❌ **URL 错误**: Webhook URL 已失效，需重新生成
3. 🚫 **被移出群聊**: 企业微信账号被移除群组

**解决方法**:
```bash
1. 进入群管理 → 机器人管理 → 删除旧机器人
2. 重新添加入群机器人
3. 复制新 URL 并测试
```

---

### Q3: 能否@特定用户？

**A**: 企业微信 Webhook **不支持** @特定成员，仅支持：
- ✅ `@all` - 全员提醒（需在企业微信后台开启权限）
- ❌ `@username` - 无法指定具体用户

**替代方案**: 
```python
# 发送回复时，在内容中提及用户名即可
message = {
    "text": {
        "content": f"张先生 这款房车售价 88 万，性价比很高。感兴趣可以留言了解更多~"
    }
}
```

---

### Q4: 消息有字数限制吗？

**A**: 是的：
- **文本消息**: 最多 1000 字（约 2000 字符）
- **Markdown 消息**: 最多 3000 字
- **图片/视频**: 不支持 Webhook 直接发送

---

### Q5: 能否接收评论而不是只发送？

**A**: ❌ **企业微信 Webhook 仅支持单向发送**（从系统到群）

**视频号评论接收方案**:
1. ✅ **官方方案**: 需申请视频号开放平台 API（审核周期长）
2. ⭐ **推荐方案**: 
   - 将视频号直播推流到 OBS
   - 使用第三方工具（如"直播评论助手"OBS 插件）捕获评论
   - 通过 Webhook 发送到企业微信群监控

---

## 📞 技术支持

| 资源 | 链接 |
|------|------|
| 企业微信官方文档 | https://work.weixin.qq.com/api/doc |
| 企业微信机器人 API | https://work.weixin.qq.com/api/doc/90000/90135/91770 |
| 视频号开放平台 | https://channels.weixin.qq.com/ |

---

**文档版本历史**:
- v1.0 (2026-05-13): 初始版本，基础配置 + API 使用指南
