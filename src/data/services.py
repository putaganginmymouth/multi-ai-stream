"""
Data Services Layer - Business Logic Implementation
数据服务层 - 业务逻辑实现
"""

import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
from ..core.base import SingletonMeta

logger = logging.getLogger(__name__)


# ============================================================================
# PublicQAService (公共 Q&A 管理服务)
# ============================================================================

class PublicQAService(metaclass=SingletonMeta):
    """公共 Q&A 管理服务"""
    
    def __init__(self):
        from .repository import PublicQARepository
        
        # Use project root's data directory
        repo_root = Path(__file__).parent.parent.parent
        db_path = str(repo_root / 'data' / 'multistream.db')
        self.repository = PublicQARepository(db_path)
    
    def add_public_qa(self, question: str, answer: str, 
                     keywords: List[str] = None, priority: int = 50) -> int:
        """添加公共 Q&A"""
        
        qa_data = {
            'question': question,
            'answer': answer,
            'keywords': keywords or [],
            'priority': max(1, min(100, priority)),  # 限制在 1-100
            'enabled': True
        }
        
        qa_id = self.repository.save(qa_data)
        
        logger.info(f"添加公共 Q&A: {question} (ID: {qa_id})")
        return qa_id
    
    def update_public_qa(self, qa_id: int, **kwargs) -> bool:
        """更新公共 Q&A"""
        
        # 验证必填字段
        if 'question' in kwargs and not kwargs['question']:
            raise ValueError("问题不能为空")
        if 'answer' in kwargs and not kwargs['answer']:
            raise ValueError("回答不能为空")
        
        try:
            self.repository.save({**kwargs, 'id': qa_id})
            return True
        except Exception as e:
            logger.error(f"更新 Q&A 失败：{e}")
            return False
    
    def delete_public_qa(self, qa_ids: List[int]) -> int:
        """批量删除公共 Q&A"""
        
        count = self.repository.delete_batch(qa_ids)
        
        logger.info(f"批量删除 {count} 条公共 Q&A")
        return count
    
    def get_all_public_qa(self, enabled_only: bool = True) -> List[Dict]:
        """获取所有公共 Q&A (按优先级排序)"""
        
        qas = self.repository.find_all(enabled_only=enabled_only)
        
        return [
            {
                'id': qa['id'],
                'question': qa['question'],
                'answer': qa['answer'],
                'keywords': qa.get('keywords', []),
                'priority': qa.get('priority', 50),
                'enabled': qa.get('enabled', True)
            }
            for qa in qas
        ]
    
    def import_from_json(self, json_data: str) -> Dict[str, int]:
        """
        JSON 批量导入公共 Q&A
        
        Args:
            json_data: JSON 字符串，格式：
            [
                {
                    "question": "...",
                    "answer": "...",
                    "keywords": ["价格", "多少钱"],
                    "priority": 80
                },
                ...
            ]
        
        Returns:
            dict: {'success': N, 'failed': N, 'errors': [...]}
        """
        
        try:
            qa_list = json.loads(json_data)
            
            success_count = 0
            failed_count = 0
            errors = []
            
            for i, item in enumerate(qa_list):
                try:
                    # 验证必填字段
                    if not all(k in item for k in ['question', 'answer']):
                        raise ValueError("缺少必填字段 question/answer")
                    
                    self.add_public_qa(
                        question=item['question'],
                        answer=item['answer'],
                        keywords=item.get('keywords', []),
                        priority=item.get('priority', 50)
                    )
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"第{i+1}条导入失败：{str(e)}")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'errors': errors
            }
            
        except json.JSONDecodeError as e:
            return {'success': 0, 'failed': 0, 'errors': [f"JSON 格式错误：{str(e)}"]}
    
    def export_to_json(self) -> str:
        """导出为 JSON 字符串"""
        
        qas = self.get_all_public_qa(enabled_only=False)
        
        return json.dumps(qas, ensure_ascii=False, indent=2)


# ============================================================================
# ProductStateService (产品介绍状态管理)
# ============================================================================

class ProductStateService(metaclass=SingletonMeta):
    """产品介绍状态管理服务"""
    
    def __init__(self):
        from .repository import CurrentProductStateRepository, ProductAssetRepository
        
        repo_root = Path(__file__).parent.parent.parent
        db_path = str(repo_root / 'data' / 'multistream.db')
        
        self.state_repo = CurrentProductStateRepository(db_path)
        self.asset_repo = ProductAssetRepository(db_path)
    
    def set_current_product(self, product_id: int, product_name: str, 
                           product_detail: str) -> bool:
        """设置当前正在介绍的产品"""
        
        try:
            self.state_repo.set_current(product_id, product_name, product_detail)
            
            # 更新所有产品的 is_active 状态
            all_assets = self.asset_repo.find_all()
            for asset in all_assets:
                active = (asset['id'] == product_id)
                self.asset_repo.save({**asset, 'is_active': active})
            
            logger.info(f"设置当前产品介绍：{product_name} (ID: {product_id})")
            return True
            
        except Exception as e:
            logger.error(f"更新产品状态失败：{e}")
            return False
    
    def get_current_product(self) -> Optional[Dict[str, Any]]:
        """获取当前产品介绍的产品信息"""
        
        try:
            state = self.state_repo.get_current()
            
            if not state or not state.get('is_live'):
                return None
            
            # 获取产品的 Q&A 配置
            qa_pairs = []
            product_id = state.get('product_id')
            if product_id:
                asset = self.asset_repo.find_by_id(product_id)
                if asset and asset.get('qa_pairs'):
                    qa_pairs = asset['qa_pairs']
            
            return {
                'id': state.get('product_id'),
                'name': state.get('product_name'),
                'detail': state.get('product_detail'),
                'qa_pairs': qa_pairs,
                'started_at': state.get('started_at')
            }
            
        except Exception as e:
            logger.error(f"获取当前产品状态失败：{e}")
            return None
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """获取所有产品列表 (v4.0 — 用于播放引擎初始化)"""
        return self.asset_repo.find_all(active_only=False)

    def get_product_count(self) -> int:
        """获取产品总数 (v4.0)"""
        products = self.asset_repo.find_all(active_only=False)
        return len(products)

    def get_active_products(self) -> List[Dict[str, Any]]:
        """获取活跃产品列表 (v4.0 — 用于播放循环)"""
        return self.asset_repo.find_all(active_only=True)

    def end_current_showcase(self):
        """结束当前产品介绍"""
        
        try:
            self.state_repo.end_current()
            
            # 清除所有产品的 is_active 状态
            all_assets = self.asset_repo.find_all()
            for asset in all_assets:
                self.asset_repo.save({**asset, 'is_active': False})
            
            logger.info("结束产品介绍")
            
        except Exception as e:
            logger.error(f"结束产品状态失败：{e}")


# ============================================================================
# LiveRoomConfigService (直播间配置管理)
# ============================================================================

class LiveRoomConfigService(metaclass=SingletonMeta):
    """直播间配置管理服务"""
    
    def __init__(self):
        from .repository import LiveRoomConfigRepository
        
        repo_root = Path(__file__).parent.parent.parent
        db_path = str(repo_root / 'data' / 'multistream.db')
        
        self.repository = LiveRoomConfigRepository(db_path)
    
    def set_loop_mode(self, mode: str) -> bool:
        """设置循环模式"""
        
        if mode not in ['sequential', 'random']:
            logger.error(f"无效的循环模式：{mode}")
            return False
        
        config = self.repository.get_config()
        config['loop_mode'] = mode
        config['current_play_index'] = -1  # 重置索引
        
        try:
            self.repository.update_config(config)
            logger.info(f"设置循环模式：{mode}")
            return True
        except Exception as e:
            logger.error(f"更新配置失败：{e}")
            return False
    
    def get_loop_mode(self) -> str:
        """获取当前循环模式"""
        
        config = self.repository.get_config()
        return config.get('loop_mode', 'sequential')
    
    def enable_comment_order(self, enabled: bool) -> bool:
        """启用/禁用评论点播功能"""
        
        config = self.repository.get_config()
        config['enable_comment_order'] = enabled
        
        try:
            self.repository.update_config(config)
            logger.info(f"设置评论点播：{'已启用' if enabled else '已禁用'}")
            return True
        except Exception as e:
            logger.error(f"更新配置失败：{e}")
            return False


# ============================================================================
# CommentAggregator (多平台评论聚合器)
# ============================================================================

class CommentAggregator(metaclass=SingletonMeta):
    """多平台评论聚合与处理"""
    
    def __init__(self):
        from collections import defaultdict
        import time
        
        # 适配器注册
        self.adapters = {}  # platform_name -> adapter instance
        
        # 回调函数列表
        self._callbacks = []
        
        # 去重配置
        self.debounce_window = 3.0  # 同一用户 3s 内合并
        self.max_replies_per_user = 5  # 单用户每分钟最多回复次数
        
        # 状态追踪
        self.user_last_comment = defaultdict(float)  # user_id -> last_comment_time
        self.user_reply_count = defaultdict(int)     # user_id -> reply_count_in_minute
        
        # v4.0: WebHook 接收器 & 播放引擎引用
        self.webhook_receiver = None
        self.playback_engine = None
    
    def set_playback_engine(self, engine):
        """设置 PlaybackEngine 引用（用于评论点播）"""
        self.playback_engine = engine
    
    def setup_webhook(self, config: Dict[str, Any]):
        """初始化 WebHook 接收器 (v4.0)"""
        from ..comment.webhook_receiver import WebHookReceiver
        
        self.webhook_receiver = WebHookReceiver(config)
        self.webhook_receiver.comment_received.connect(self._on_webhook_comment)
        
        if config.get('webhook', {}).get('enabled', False):
            self.webhook_receiver.start()
    
    def _on_webhook_comment(self, comment):
        """处理 WebHook 评论 — 转为内部 Comment 对象并处理"""
        # 去重/过滤
        user_id = getattr(comment, 'user_id', '') or getattr(comment, 'username', 'unknown')
        current_time = time.time()
        
        last_time = self.user_last_comment.get(user_id, 0)
        if current_time - last_time < self.debounce_window:
            return
        
        self.user_last_comment[user_id] = current_time
        
        # 送入点播引擎
        if self.playback_engine:
            from ..data.services import get_public_qa_service
            qa_list = get_public_qa_service().get_all_public_qa(enabled_only=True)
            self.playback_engine.handle_comment(
                username=getattr(comment, 'username', ''),
                content=getattr(comment, 'content', ''),
                public_qa=qa_list
            )
        
        # 触发回调链
        for callback in self._callbacks:
            try:
                callback(comment)
            except Exception as e:
                logger.error(f"评论处理回调异常：{e}")
    
    def register_adapter(self, platform: str, adapter):
        """注册平台适配器"""
        
        self.adapters[platform] = adapter
        
        # 设置评论回调（如果适配器支持）
        if hasattr(adapter, 'on_comment'):
            @adapter.on_comment
            def handle_platform_comment(comment: Dict[str, Any]):
                comment['source_platform'] = platform
                self._process_comment(comment)
    
    def on_new_comment(self, callback):
        """注册全局评论回调"""
        
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def _process_comment(self, comment: Dict[str, Any]):
        """处理新评论 (去重/过滤)"""
        
        user_id = comment.get('user_id') or comment.get('username', 'unknown')
        current_time = time.time()
        
        # 1. 防刷屏：同一用户短时间内合并评论
        last_time = self.user_last_comment.get(user_id, 0)
        if current_time - last_time < self.debounce_window:
            logger.debug(f"过滤重复评论 (用户 {user_id})")
            return
        
        self.user_last_comment[user_id] = current_time
        
        # 2. 限制回复频率：单用户每分钟最多 N 次
        minute_key = f"{user_id}_{int(current_time // 60)}"
        
        if self.user_reply_count.get(minute_key, 0) >= self.max_replies_per_user:
            logger.warning(f"跳过高频用户 {user_id} (已达回复上限)")
            return
        
        # 3. 触发回调链
        for callback in self._callbacks:
            try:
                callback(comment)
            except Exception as e:
                logger.error(f"评论处理回调异常：{e}")
    
    def send_reply_to_platform(self, platform: str, user_id: str, reply_text: str):
        """向指定平台发送回复"""
        
        if platform not in self.adapters:
            logger.error(f"平台 {platform} 未注册")
            return False
        
        adapter = self.adapters[platform]
        
        try:
            success = adapter.send_reply(user_id, reply_text)
            
            # 更新回复计数
            minute_key = f"{user_id}_{int(time.time() // 60)}"
            self.user_reply_count[minute_key] = self.user_reply_count.get(minute_key, 0) + 1
            
            return success
            
        except Exception as e:
            logger.error(f"平台 {platform} 回复发送失败：{e}")
            return False
    
    def get_adapters(self):
        """获取所有已注册的适配器"""
        
        return self.adapters.copy()


# ============================================================================
# Global Service Accessors (全局服务访问器)
# ============================================================================

def get_public_qa_service():
    """获取公共 Q&A 服务单例"""
    
    return PublicQAService()


def get_product_state_service():
    """获取产品介绍状态服务单例"""
    
    return ProductStateService()


def get_live_room_config_service():
    """获取直播间配置服务单例"""
    
    return LiveRoomConfigService()


def get_comment_aggregator():
    """获取评论聚合器单例"""
    
    return CommentAggregator()
