"""
Platform Layer Tests
平台接入层测试
"""

import pytest
from src.platform_adapters.factory import PlatformFactory
from src.core.enums import PlatformType


class TestPlatformFactory:
    """Platform Factory 测试"""
    
    def test_create_douyin_platform(self, sample_platform_config):
        """测试创建抖音平台实例"""
        platform = PlatformFactory.create("douyin", sample_platform_config)
        
        assert platform is not None
        assert str(platform.get_platform_type()) == "douyin"
    
    def test_create_kuaishou_platform(self):
        """测试创建快手平台实例"""
        config = {
            'type': 'kuaishou',
            'rtmp_url': 'rtmp://test.com',
            'stream_key': 'key'
        }
        
        platform = PlatformFactory.create("kuaishou", config)
        assert platform is not None
        assert str(platform.get_platform_type()) == "kuaishou"
    
    def test_create_wechat_platform(self):
        """测试创建视频号平台实例"""
        config = {
            'type': 'wechat',
            'rtmp_url': 'rtmp://test.com',
            'stream_key': 'key'
        }
        
        platform = PlatformFactory.create("wechat", config)
        assert platform is not None
    
    def test_create_invalid_platform(self):
        """测试创建不存在平台类型应抛出异常"""
        with pytest.raises(Exception):  # MultiStreamError
            PlatformFactory.create("invalid_platform", {})
    
    def test_get_available_types(self):
        """测试获取可用平台类型列表"""
        types = PlatformFactory.get_available_types()
        
        assert 'douyin' in types
        assert 'kuaishou' in types
        assert 'wechat' in types


class TestBasePlatform:
    """Base Platform 抽象类测试"""
    
    def test_platform_type_enum(self, sample_platform_config):
        """测试平台类型枚举转换"""
        platform = PlatformFactory.create("douyin", sample_platform_config)
        
        from src.core.enums import PlatformType
        assert platform.get_platform_type() == PlatformType.DOUYIN
