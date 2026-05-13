"""
Responder - 评论自动回复引擎
支持模板匹配和 LLM 智能回复
"""

import logging
from typing import Dict, Any, Optional, List
from random import choice

logger = logging.getLogger(__name__)


class Responder:
    """
    自动回复引擎基类
    
    功能:
    - 接收评论并生成回复
    - 支持模板匹配和 LLM 智能回复
    - 频率控制，防止 spam
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 最小回复间隔 (秒)
        self.min_delay = config.get('min_delay_seconds', 5)
        
        # 上次回复时间
        self.last_reply_time = 0
    
    def should_reply(self) -> bool:
        """检查是否应该回复 (频率控制)"""
        import time
        if time.time() - self.last_reply_time < self.min_delay:
            return False
        return True
    
    def on_comment(self, comment) -> Optional[str]:
        """处理评论并生成回复"""
        if not self.should_reply():
            logger.debug(f"跳过回复：频率控制")
            return None
        
        response = self._generate_response(comment)
        
        if response:
            self.last_reply_time = __import__('time').time()
        
        return response
    
    def _generate_response(self, comment) -> Optional[str]:
        """生成回复 (子类实现)"""
        raise NotImplementedError("子类必须实现 _generate_response()")


class TemplateResponder(Responder):
    """
    模板匹配回复器
    
    使用预设话术库，通过关键词匹配触发回复
    响应速度快 (<2 秒)，适合高频场景
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 默认话术模板 (v3.0)
        self.templates = {
            "welcome": [
                "欢迎{nickname}来到直播间！",
                "感谢{nickname}的关注！",
                "{nickname}好，欢迎来到我们的直播间~"
            ],
            "price_inquiry": [
                "价格方面，这套房源总价 500 万，首付只需 150 万哦~",
                "具体价格可以私聊我获取详细报价单~",
                "不同户型价格略有差异，欢迎私信咨询！"
            ],
            "location_inquiry": [
                "我们项目位于市中心核心地段，地铁直达！",
                "周边有商场、学校、医院，生活非常方便~",
                "交通超级便利，开车 10 分钟到市中心！"
            ],
            "area_inquiry": [
                "我们有 89㎡、120㎡、150㎡等多种户型可选！",
                "面积从 89 平到 200 平都有，满足不同家庭需求~",
                "得房率很高，实际使用面积比建筑面积多 10% 左右！"
            ],
            "decoration": [
                "都是精装修交付，可以直接拎包入住！",
                "装修风格现代简约，适合各种审美~",
                "装修标准 3000 元/平，品牌建材环保安全！"
            ],
            "loan_inquiry": [
                "支持公积金贷款和商业贷款两种方案~",
                "首付最低 30%，月供压力不大！",
                "我们有合作的银行，贷款利率优惠！"
            ],
            "generic_thanks": [
                "感谢关注，有问题随时问~",
                "谢谢支持，欢迎多逛逛直播间！",
                "感谢喜欢，点个关注不迷路~"
            ]
        }
    
    def _generate_response(self, comment) -> Optional[str]:
        """根据评论关键词匹配话术"""
        content = comment.content.lower()
        
        # 欢迎类
        if any(w in content for w in ["欢迎", "来了", "大家好"]):
            nickname = comment.username.replace("用户", "")
            return choice(self.templates["welcome"]).format(nickname=nickname)
        
        # 价格相关
        elif any(w in content for w in ["价格", "多少钱", "多少", "预算", "首付"]):
            return choice(self.templates["price_inquiry"])
        
        # 位置相关
        elif any(w in content for w in ["哪里", "位置", "地址", "在哪", "地段"]):
            return choice(self.templates["location_inquiry"])
        
        # 面积相关
        elif any(w in content for w in ["面积", "多大", "平", "平米", "大小"]):
            return choice(self.templates["area_inquiry"])
        
        # 装修相关
        elif any(w in content for w in ["装修", "精装", "简装", "风格"]):
            return choice(self.templates["decoration"])
        
        # 贷款相关
        elif any(w in content for w in ["贷款", "首付", "月供", "公积金"]):
            return choice(self.templates["loan_inquiry"])
        
        # 感谢类
        elif any(w in content for w in ["谢谢", "感谢", "辛苦了"]):
            return choice(self.templates["generic_thanks"])
        
        # 无匹配
        else:
            logger.debug(f"未匹配到话术：{content}")
            return None


class SimpleResponder(TemplateResponder):
    """
    简化版回复器 - 用于测试
    
    固定回复，不进行关键词匹配
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_response = "感谢关注！有问题欢迎随时提问~"
    
    def _generate_response(self, comment) -> Optional[str]:
        """总是回复固定内容"""
        return self.default_response


class SmartResponder(Responder):
    """
    智能回复器 (预留实现)
    
    结合 LLM 生成个性化回复
    
    TODO: 
    - 集成 LLM API
    - 根据产品知识库生成准确回复
    - 延迟提示 UI 反馈
    """
    
    def __init__(self, config: Dict[str, Any], llm_client=None):
        super().__init__(config)
        
        self.llm_client = llm_client
        self.templates = TemplateResponder(config).templates
    
    def _generate_response(self, comment) -> Optional[str]:
        """优先使用模板，无匹配时调用 LLM"""
        # 先尝试模板匹配 (快速响应)
        template_resp = TemplateResponder(self.config)._generate_response(comment)
        if template_resp:
            return template_resp
        
        # 无匹配时调用 LLM (较慢，但有延迟提示 UI)
        if self.llm_client:
            try:
                prompt = f"用户评论：{comment.content}\n作为房产销售专家，请简短回复（20 字以内）"
                response = self.llm_client.generate(prompt)
                return response[:50]  # 限制长度
            except Exception as e:
                logger.error(f"LLM 生成回复失败：{e}")
                return None
        
        return None
