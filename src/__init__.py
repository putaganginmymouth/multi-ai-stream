"""
Multi-AI-Stream - Main Package
多平台数字人直播系统 v2.0
"""

from .data import (
    # Models
    ProductAsset, PublicQA, CurrentProductState, LiveRoomConfig,
    
    # Services
    get_public_qa_service, get_product_state_service,
    get_live_room_config_service, get_comment_aggregator,
)

from .content import ReplyGeneratorHandler


__version__ = '2.0.0'
__all__ = [
    # Models
    'ProductAsset',
    'PublicQA', 
    'CurrentProductState',
    'LiveRoomConfig',
    
    # Services
    'get_public_qa_service',
    'get_product_state_service',
    'get_live_room_config_service',
    'get_comment_aggregator',
    
    # Content
    'ReplyGeneratorHandler'
]
