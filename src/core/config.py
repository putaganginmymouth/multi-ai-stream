"""
Configuration Manager - Singleton Pattern
配置管理类，使用单例模式确保全局唯一配置实例
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .base import Base
from .exceptions import ConfigError
from .enums import DeviceType


class ConfigManager(Base):
    """
    配置管理器 (单例模式)
    
    使用示例:
        config = ConfigManager.get_instance()
        rtmp_url = config.get('platforms.douyin.rtmp_url')
    """
    
    _instance: Optional['ConfigManager'] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径 (相对于项目根目录)
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        super().__init__()
        
        self._config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._app_root = Path(__file__).parent.parent.parent
        
        self._load_config()
        self._initialized = True
    
    @classmethod
    def get_instance(cls, config_path: str = "configs/config.yaml") -> 'ConfigManager':
        """获取单例实例"""
        if cls._instance is None or cls._instance._config_path != config_path:
            cls._instance = cls(config_path)
        return cls._instance
    
    def _validate_config(self) -> bool:
        """验证配置完整性"""
        required_keys = ['app', 'obs', 'avatar', 'llm', 'tts', 'database', 'platforms']
        for key in required_keys:
            if key not in self._config:
                return False
        return True

    def _load_config(self):
        """加载配置文件"""
        try:
            # 支持环境变量覆盖配置路径
            env_path = os.environ.get('MULTI_STREAM_CONFIG')
            if env_path and os.path.exists(env_path):
                config_path = Path(env_path)
            else:
                config_path = self._app_root / self._config_path
            
            if not config_path.exists():
                # 使用默认配置
                self._config = self._get_default_config()
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
                
        except Exception as e:
            print(f"加载配置文件失败：{e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            'app': {
                'name': 'Multi-AI-Stream',
                'version': '1.0.0',
                'log_level': 'INFO'
            },
            'obs': {
                'host': 'localhost',
                'port': 4455,
                'password': ''
            },
            'avatar': {
                'default_engine': 'live_portrait',
                'models_path': './assets/avatars'
            },
            'llm': {
                'model': 'qwen/Qwen-7B-Chat-GGUF',
                'quantization': 'q4_0'
            },
            'tts': {
                'engine': 'coqui'  # coqui / edge / iflytek
            },
            'database': {
                'type': 'sqlite',
                'path': './data/multi_ai_stream.db'
            },
            'platforms': {
                'douyin': {'enabled': False, 'rtmp_url': '', 'stream_key': ''},
                'kuaishou': {'enabled': False, 'rtmp_url': '', 'stream_key': ''},
                'wechat': {'enabled': False, 'rtmp_url': '', 'stream_key': ''}
            },
            'device': {
                'type': 'auto'  # auto / cuda / mps / cpu
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键 (如 'app.name' 或 'platforms.douyin.rtmp_url')
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_device(self) -> DeviceType:
        """获取计算设备类型"""
        device = self.get('device.type', 'auto')
        return DeviceType(device)
    
    def is_platform_enabled(self, platform_type: str) -> bool:
        """检查平台是否启用"""
        platforms = self._config.get('platforms', {})
        platform_config = platforms.get(platform_type, {})
        return platform_config.get('enabled', False)
    
    def get_platform_config(self, platform_type: str) -> Dict[str, Any]:
        """获取平台配置"""
        platforms = self._config.get('platforms', {})
        return platforms.get(platform_type, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self._config.copy()
    
    def save(self, path: Optional[str] = None):
        """保存配置到文件"""
        save_path = Path(path) if path else (self._app_root / self._config_path)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)


# 全局配置实例
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager.get_instance()
    return _config_manager
