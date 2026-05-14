'''
Base Classes and Abstract Base Classes
基础类和抽象基类定义
'''

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from threading import Lock


class SingletonMeta(type):
    """线程安全的单例元类
    
    用法:
        class MyService(metaclass=SingletonMeta):
            def __init__(self):
                self.data = []
    """
    _instances: Dict[type, Any] = {}
    _lock = Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Base:
    """
    所有业务类的基类
    提供通用功能和工具方法
    """
    
    def __init__(self, **kwargs):
        """初始化基类"""
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
        
        # 动态设置属性
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            **{k: v for k, v in self.__dict__.items() 
               if not k.startswith('_')}
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"


@dataclass
class BaseEntity:
    """
    数据实体基类 (用于 Repository Pattern)
    """
    id: Optional[int] = None
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class Observable(ABC):
    """
    可观察对象基类 (观察者模式)
    用于直播状态通知等场景
    """
    
    def __init__(self):
        self._observers: list = []
    
    def subscribe(self, callback):
        """订阅事件"""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unsubscribe(self, callback):
        """取消订阅"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def notify(self, event_type: str, data: Any = None):
        """通知所有观察者"""
        for observer in self._observers:
            try:
                observer(event_type, data)
            except Exception as e:
                print(f"Observer error: {e}")


class Configurable(ABC):
    """
    可配置类基类
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def _validate_config(self) -> bool:
        """验证配置是否有效"""
        pass


class Streamable(ABC):
    """
    可流式输出接口
    """
    
    @abstractmethod
    def stream(self) -> Any:
        """返回流式数据"""
        pass
