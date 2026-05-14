"""
Repository Layer - Data Access Abstraction
数据访问层 (Repository Pattern)
"""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


class PlatformRepository(ABC):
    """平台仓库抽象基类"""
    
    @abstractmethod
    def save(self, platform: Dict[str, Any]) -> int:
        """保存/更新平台配置，返回 ID"""
        pass
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 查找平台"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Dict[str, Any]]:
        """获取所有平台配置"""
        pass
    
    @abstractmethod
    def delete(self, id: int):
        """删除平台配置"""
        pass


class LiveSessionRepository(ABC):
    """直播会话仓库抽象基类"""
    
    @abstractmethod
    def create(self, session_data: Dict[str, Any]) -> int:
        """创建直播会话，返回 ID"""
        pass
    
    @abstractmethod
    def update_status(self, id: int, status: str):
        """更新会话状态"""
        pass
    
    @abstractmethod
    def find_by_platform(self, platform_id: int) -> List[Dict[str, Any]]:
        """根据平台 ID 查找会话"""
        pass


class PropertyRepository(ABC):
    """房源信息仓库抽象基类"""
    
    @abstractmethod
    def save(self, property_data: Dict[str, Any]) -> int:
        """保存房源信息，返回 ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Dict[str, Any]]:
        """获取所有房源信息"""
        pass


class SQLitePlatformRepository(PlatformRepository):
    """SQLite 平台仓库实现"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def save(self, platform: Dict[str, Any]) -> int:
        """保存平台配置"""
        with self.engine.connect() as conn:
            if 'id' in platform and platform['id']:
                # 更新
                conn.execute(text("""
                    UPDATE platforms 
                    SET name=:name, rtmp_url=:rtmp_url, stream_key=:stream_key, enabled=:enabled
                    WHERE id=:id
                """), platform)
            else:
                # 插入
                result = conn.execute(text("""
                    INSERT INTO platforms (name, platform_type, rtmp_url, stream_key, enabled)
                    VALUES (:name, :platform_type, :rtmp_url, :stream_key, :enabled)
                """), platform)
                return result.lastrowid
        
        conn.commit()
        return platform.get('id')
    
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 查找"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM platforms WHERE id=:id"), {'id': id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
    
    def find_all(self) -> List[Dict[str, Any]]:
        """获取所有"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM platforms ORDER BY id"))
            return [dict(row._mapping) for row in result]
    
    def delete(self, id: int):
        """删除"""
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM platforms WHERE id=:id"), {'id': id})
            conn.commit()


class SQLiteLiveSessionRepository(LiveSessionRepository):
    """SQLite 直播会话仓库实现"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def create(self, session_data: Dict[str, Any]) -> int:
        """创建会话"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO live_sessions (platform_id, start_time, end_time, status)
                VALUES (:platform_id, :start_time, :end_time, :status)
            """), session_data)
            conn.commit()
            return result.lastrowid
    
    def update_status(self, id: int, status: str):
        """更新状态"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                UPDATE live_sessions SET status=:status WHERE id=:id
            """), {'status': status, 'id': id})
            conn.commit()
    
    def find_by_platform(self, platform_id: int) -> List[Dict[str, Any]]:
        """按平台查询"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM live_sessions WHERE platform_id=:id ORDER BY created_at DESC
            """), {'id': platform_id})
            return [dict(row._mapping) for row in result]


class SQLitePropertyRepository(PropertyRepository):
    """SQLite 房源仓库实现"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def save(self, property_data: Dict[str, Any]) -> int:
        """保存房源信息"""
        with self.engine.connect() as conn:
            if 'id' in property_data and property_data['id']:
                # 更新
                conn.execute(text("""
                    UPDATE properties 
                    SET name=:name, description=:description, price=:price, area=:area, location=:location
                    WHERE id=:id
                """), property_data)
            else:
                # 插入
                result = conn.execute(text("""
                    INSERT INTO properties (name, description, price, area, location, images, tags)
                    VALUES (:name, :description, :price, :area, :location, :images, :tags)
                """), property_data)
                return result.lastrowid
        
        conn.commit()
        return property_data.get('id')
    
    def find_all(self) -> List[Dict[str, Any]]:
        """获取所有"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM properties ORDER BY created_at DESC"))
            return [dict(row._mapping) for row in result]


class ProductAssetRepository:
    """产品资产仓库 (SQLite 实现)"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def save(self, asset_data: Dict[str, Any]) -> int:
        """保存/更新产品资产，返回 ID"""
        
        with self.engine.connect() as conn:
            if 'id' in asset_data and asset_data['id']:
                # 更新
                conn.execute(text("""
                    UPDATE product_assets 
                    SET name=:name, product_alias=:product_alias, video_path=:video_path, product_detail=:product_detail,
                        duration=:duration, width=:width, height=:height,
                        script_text=:script_text, script_segments=:script_segments,
                        qa_pairs=:qa_pairs, is_active=:is_active
                    WHERE id=:id
                """), asset_data)
            else:
                # 插入
                result = conn.execute(text("""
                    INSERT INTO product_assets (name, product_alias, video_path, product_detail, duration, 
                                                width, height, script_text, script_segments, qa_pairs, is_active)
                    VALUES (:name, :product_alias, :video_path, :product_detail, :duration, 
                            :width, :height, :script_text, :script_segments, :qa_pairs, :is_active)
                """), asset_data)
                conn.commit()
                return result.lastrowid
        
        return asset_data.get('id')
    
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 查找"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM product_assets WHERE id=:id"), {'id': id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
    
    def find_all(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """获取所有产品资产"""
        with self.engine.connect() as conn:
            if active_only:
                result = conn.execute(text("SELECT * FROM product_assets WHERE is_active=true ORDER BY id"))
            else:
                result = conn.execute(text("SELECT * FROM product_assets ORDER BY created_at DESC"))
            return [dict(row._mapping) for row in result]
    
    def find_by_alias(self, keyword: str) -> Optional[Dict[str, Any]]:
        """根据别名关键词查找产品 (v4.0)"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM product_assets"), {})
            rows = [dict(row._mapping) for row in result]
            for row in rows:
                aliases = (row.get('product_alias', '') or '').split(',')
                for alias in aliases:
                    if alias.strip() and alias.strip() in keyword:
                        return row
        return None

    def update_qa_pairs(self, asset_id: int, qa_pairs: list):
        """更新产品的 Q&A 配置"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                UPDATE product_assets SET qa_pairs=:qa_pairs WHERE id=:id
            """), {'qa_pairs': json.dumps(qa_pairs), 'id': asset_id})
            conn.commit()
    
    def delete(self, id: int):
        """删除产品资产"""
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM product_assets WHERE id=:id"), {'id': id})
            conn.commit()


class PublicQARepository:
    """公共 Q&A 仓库 (SQLite 实现)"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def save(self, qa_data: Dict[str, Any]) -> int:
        """保存/更新公共 Q&A，返回 ID"""
        
        with self.engine.connect() as conn:
            if 'id' in qa_data and qa_data['id']:
                # 更新
                conn.execute(text("""
                    UPDATE public_qa 
                    SET question=:question, answer=:answer, keywords=:keywords,
                        enabled=:enabled, priority=:priority
                    WHERE id=:id
                """), qa_data)
            else:
                # 插入
                result = conn.execute(text("""
                    INSERT INTO public_qa (question, answer, keywords, enabled, priority)
                    VALUES (:question, :answer, :keywords, :enabled, :priority)
                """), qa_data)
                conn.commit()
                return result.lastrowid
        
        return qa_data.get('id')
    
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 查找"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM public_qa WHERE id=:id"), {'id': id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
    
    def find_all(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """获取所有公共 Q&A"""
        with self.engine.connect() as conn:
            if enabled_only:
                result = conn.execute(text("""
                    SELECT * FROM public_qa WHERE enabled=true 
                    ORDER BY priority DESC, id ASC
                """))
            else:
                result = conn.execute(text("SELECT * FROM public_qa ORDER BY priority DESC"))
            
            return [dict(row._mapping) for row in result]
    
    def delete(self, qa_id: int):
        """删除公共 Q&A"""
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM public_qa WHERE id=:id"), {'id': qa_id})
            conn.commit()
    
    def delete_batch(self, qa_ids: List[int]):
        """批量删除公共 Q&A"""
        if not qa_ids:
            return
        
        with self.engine.connect() as conn:
            placeholders = ','.join(['?' for _ in qa_ids])
            conn.execute(text(f"DELETE FROM public_qa WHERE id IN ({placeholders}"), tuple(qa_ids))
            conn.commit()


class CurrentProductStateRepository:
    """当前产品介绍状态仓库 (单行记录)"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def get_current(self) -> Optional[Dict[str, Any]]:
        """获取当前产品介绍状态"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM current_product_state WHERE id=1"))
            row = result.fetchone()
            return dict(row._mapping) if row else None
    
    def set_current(self, product_id: int, product_name: str, product_detail: str):
        """设置当前产品介绍"""
        from datetime import datetime
        
        with self.engine.connect() as conn:
            # 先清除之前的状态
            conn.execute(text("""
                UPDATE current_product_state 
                SET is_live=false, ended_at=:ended_at WHERE id=1
            """), {'ended_at': datetime.now().isoformat()})
            
            # 更新当前产品状态
            conn.execute(text("""
                UPDATE current_product_state 
                SET product_id=:product_id, product_name=:product_name, 
                    product_detail=:product_detail, started_at=:started_at, is_live=true
                WHERE id=1
            """), {
                'product_id': product_id,
                'product_name': product_name,
                'product_detail': product_detail,
                'started_at': datetime.now().isoformat()
            })
            
            conn.commit()
    
    def end_current(self):
        """结束当前产品介绍"""
        from datetime import datetime
        
        with self.engine.connect() as conn:
            conn.execute(text("""
                UPDATE current_product_state 
                SET is_live=false, ended_at=:ended_at WHERE id=1
            """), {'ended_at': datetime.now().isoformat()})
            
            conn.commit()


class LiveRoomConfigRepository:
    """直播间配置仓库"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def get_config(self) -> Dict[str, Any]:
        """获取直播间配置"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM live_room_config WHERE id=1"))
            row = result.fetchone()
            return dict(row._mapping) if row else {
                'loop_mode': 'sequential',
                'enable_comment_order': True,
                'use_public_qa': True,
                'qa_match_min_confidence': 0.6,
                'current_play_index': -1
            }
    
    def update_config(self, config: Dict[str, Any]):
        """更新直播间配置"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                UPDATE live_room_config SET 
                    loop_mode=:loop_mode,
                    enable_comment_order=:enable_comment_order,
                    use_public_qa=:use_public_qa,
                    qa_match_min_confidence=:qa_match_min_confidence,
                    current_play_index=:current_play_index
                WHERE id=1
            """), config)
            
            conn.commit()


class SystemConfigRepository:
    """系统配置仓库"""
    
    def __init__(self, db_path: str):
        from sqlalchemy import create_engine, text
        
        self.engine = create_engine(f'sqlite:///{db_path}')
    
    def get_value(self, key: str) -> Optional[str]:
        """根据 key 获取配置值"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT value FROM system_configs WHERE key=:key"), {'key': key})
            row = result.fetchone()
            return row[0] if row else None
    
    def set_value(self, key: str, value: str, description: str = ""):
        """设置配置值"""
        with self.engine.connect() as conn:
            # 检查是否存在
            existing = conn.execute(
                text("SELECT id FROM system_configs WHERE key=:key"), 
                {'key': key}
            ).fetchone()
            
            if existing:
                conn.execute(text("""
                    UPDATE system_configs SET value=:value, description=:description WHERE key=:key
                """), {'value': value, 'description': description, 'key': key})
            else:
                conn.execute(text("""
                    INSERT INTO system_configs (key, value, description) VALUES (:key, :value, :description)
                """), {'key': key, 'value': value, 'description': description})
            
            conn.commit()
    
    def get_all(self) -> Dict[str, str]:
        """获取所有配置"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT key, value FROM system_configs"))
            return {row[0]: row[1] for row in result}


# 数据库连接工厂
_db_engine = None


def get_db_session(db_path: str = None):
    """获取数据库引擎"""
    global _db_engine
    
    if db_path is None:
        from pathlib import Path
        base_dir = Path(__file__).parent.parent.parent
        db_path = str(base_dir / 'data' / 'multistream.db')
    
    if _db_engine is None or _db_engine.url.database != db_path:
        from sqlalchemy import create_engine
        _db_engine = create_engine(f'sqlite:///{db_path}')
    
    return _db_engine
