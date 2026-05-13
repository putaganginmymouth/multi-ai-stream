"""
Pytest Fixtures and Configuration
测试配置和夹具
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        'app': {'name': 'Test', 'version': '1.0.0'},
        'obs': {'host': 'localhost', 'port': 4455},
        'avatar': {'default_engine': 'live_portrait'},
        'llm': {'model': 'test-model'},
        'tts': {'engine': 'coqui'}
    }


@pytest.fixture
def sample_platform_config():
    """平台配置示例"""
    return {
        'type': 'douyin',
        'rtmp_url': 'rtmp://test.example.com/live',
        'stream_key': 'test_stream_key'
    }


@pytest.fixture
def sample_avatar_config():
    """数字人引擎配置示例"""
    return {
        'type': 'live_portrait',
        'models_path': './assets/avatars'
    }
