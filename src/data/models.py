"""
Data Models - SQLAlchemy ORM Definitions
数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Platform(Base):
    """平台配置表"""
    
    __tablename__ = 'platforms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 平台名称 (如"抖音")
    platform_type = Column(String(50), nullable=False)  # 类型枚举 (douyin/kuaishou/wechat)
    rtmp_url = Column(String(500))  # RTMP 服务器地址
    stream_key = Column(String(200))  # 推流密钥
    enabled = Column(Boolean, default=True)  # 是否启用
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    live_sessions = relationship("LiveSession", back_populates="platform")


class LiveSession(Base):
    """直播会话表"""
    
    __tablename__ = 'live_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_id = Column(Integer, ForeignKey('platforms.id'))  # 关联平台 ID
    
    start_time = Column(DateTime)  # 开始时间
    end_time = Column(DateTime)  # 结束时间
    status = Column(String(50), default='idle')  # idle/starting/live/stopping/error/paused
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    platform = relationship("Platform", back_populates="live_sessions")


class Property(Base):
    """房源/产品信息表"""
    
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # 产品名称
    description = Column(Text)  # 详细描述
    
    price = Column(Float)  # 价格
    area = Column(String(50))  # 面积/尺寸
    location = Column(String(200))  # 位置
    
    images = Column(Text)  # 图片路径 JSON 数组
    tags = Column(Text)  # 标签 JSON 数组
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Schedule(Base):
    """定时任务表"""
    
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_id = Column(Integer, ForeignKey('platforms.id'))  # 关联平台 ID
    
    start_time = Column(DateTime, nullable=False)  # 开始时间
    end_time = Column(DateTime)  # 结束时间 (可选，用于单次任务)
    
    avatar_config = Column(Text)  # 数字人配置 JSON
    script_template = Column(String(200))  # 脚本模板 ID
    
    status = Column(String(50), default='pending')  # pending/running/completed/cancelled
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    platform = relationship("Platform")


class AvatarLog(Base):
    """数字人生成日志表"""
    
    __tablename__ = 'avatar_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('live_sessions.id'))  # 关联直播会话
    
    avatar_type = Column(String(50))  # 数字人类型 (live_portrait/wav2lip)
    video_path = Column(String(500))  # 生成的视频路径
    audio_path = Column(String(500))  # 音频文件路径
    
    duration = Column(Integer)  # 时长 (秒)
    file_size = Column(Integer)  # 文件大小 (字节)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ProductAsset(Base):
    """房车产品资产表"""
    
    __tablename__ = 'product_assets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)           # 产品名称，如"1 号房车 - 豪华越野版"
    product_alias = Column(String(500), default='')      # 🔗 产品别名(逗号分隔)，用于评论关键词匹配 (v4.0)
    video_path = Column(String(500), nullable=False)     # 视频文件路径
    product_detail = Column(Text, nullable=False)        # 📝 产品详细信息
    
    # 元数据 (FFmpeg 提取)
    duration = Column(Float)                              # 视频时长 (秒)
    width = Column(Integer)                               # 分辨率宽
    height = Column(Integer)                              # 分辨率高
    
    # 文案对齐信息
    script_text = Column(Text)                            # 📄 生成的介绍文案
    script_segments = Column(JSON, default=list)         # 🔗 分段标注 [{"start": 0, "end": 15, "text": "..."}]
    
    # Q&A 配置 (私有 Q&A)
    qa_pairs = Column(JSON, default=list)                 # [
                                                            #   {
                                                            #     "question": "价格多少？",
                                                            #     "answer": "...",
                                                            #     "keywords": ["价格", "多少钱"],
                                                            #     "auto_reply_weight": 0.8
                                                            #   }
                                                            # ]
    
    is_active = Column(Boolean, default=False)            # 是否正在介绍中
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PublicQA(Base):
    """公共 Q&A 表 (全局共享)"""
    
    __tablename__ = 'public_qa'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(500), nullable=False)        # 问题
    answer = Column(Text, nullable=False)                 # 回答
    
    keywords = Column(JSON, default=list)                 # 关键字列表
    enabled = Column(Boolean, default=True)               # 是否启用
    priority = Column(Integer, default=50)                # 优先级 (1-100)
    linked_product_id = Column(Integer, ForeignKey('product_assets.id'), nullable=True)
                                                          # 🔗 关联产品ID，命中此Q&A时可自动切换 (v4.0)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurrentProductState(Base):
    """当前产品介绍状态表"""
    
    __tablename__ = 'current_product_state'
    
    id = Column(Integer, primary_key=True, default=1)     # 固定为 1 行
    
    product_id = Column(Integer, ForeignKey('product_assets.id'))
    product_name = Column(String(200))
    product_detail = Column(Text)
    
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime)
    is_live = Column(Boolean, default=False)


class LiveRoomConfig(Base):
    """直播间配置表"""
    
    __tablename__ = 'live_room_config'
    
    id = Column(Integer, primary_key=True, default=1)
    
    loop_mode = Column(String(20), default='sequential')  # sequential | random
    enable_comment_order = Column(Boolean, default=True)  # 是否启用评论点播
    use_public_qa = Column(Boolean, default=True)         # 是否使用公共 Q&A
    qa_match_min_confidence = Column(Float, default=0.6)  # 最低置信度
    
    current_play_index = Column(Integer, default=-1)      # -1 表示未开始 (顺序模式追踪)
    
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SystemConfig(Base):
    """系统配置表"""
    
    __tablename__ = 'system_configs'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)



