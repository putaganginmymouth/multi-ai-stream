"""
Database Initialization Script
数据库初始化脚本
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def init_database():
    """初始化数据库"""
    from core.config import get_config
    
    config = get_config()
    db_type = config.get('database.type', 'sqlite')
    
    if db_type == 'sqlite':
        _init_sqlite(config)
    elif db_type == 'postgresql':
        _init_postgresql(config)
    else:
        print(f"Unsupported database type: {db_type}")


def _init_sqlite(config):
    """初始化 SQLite 数据库"""
    from sqlalchemy import create_engine, text
    
    db_path = config.get('database.sqlite.path', './data/multi_ai_stream.db')
    
    # 确保目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    with engine.connect() as conn:
        # 创建平台表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform_type TEXT NOT NULL,
                rtmp_url TEXT,
                stream_key TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建直播会话表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS live_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'idle',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (platform_id) REFERENCES platforms(id)
            )
        """))
        
        # 创建房源信息表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL,
                area TEXT,
                location TEXT,
                images TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建定时任务表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                avatar_config TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (platform_id) REFERENCES platforms(id)
            )
        """))
        
        conn.commit()
    
    print(f"SQLite 数据库初始化完成：{db_path}")


def _init_postgresql(config):
    """初始化 PostgreSQL 数据库"""
    from sqlalchemy import create_engine, text
    
    engine = create_engine(
        f"postgresql://{config.get('database.postgresql.username', '')}:"
        f"{config.get('database.postgresql.password', '')}@"
        f"{config.get('database.postgresql.host', 'localhost')}:"
        f"{config.get('database.postgresql.port', 5432)}"
        f"/{config.get('database.postgresql.database', 'multi_ai_stream')}"
    )
    
    with engine.connect() as conn:
        # 创建表 (与 SQLite 相同)
        tables = [
            """CREATE TABLE IF NOT EXISTS platforms (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                platform_type TEXT NOT NULL,
                rtmp_url TEXT,
                stream_key TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS live_sessions (
                id SERIAL PRIMARY KEY,
                platform_id INTEGER REFERENCES platforms(id),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'idle',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table_sql in tables:
            conn.execute(text(table_sql))
        
        conn.commit()
    
    print("PostgreSQL 数据库初始化完成")


if __name__ == '__main__':
    init_database()
