"""
Comment Module - 评论监听与回复模块
包含 CommentListener (评论监听器) 和 Responder (自动回复引擎)
"""

from .listener import CommentListener, SimpleCommentListener
from .responder import Responder, TemplateResponder, SimpleResponder

__all__ = [
    'CommentListener', 
    'SimpleCommentListener',
    'Responder', 
    'TemplateResponder',
    'SimpleResponder'
]
