"""
Stream Manager Tests - 多平台推流管理器测试
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.stream.stream_manager import StreamManager, SimpleStreamWorker
from src.core.enums import LiveStatus


class TestStreamManager:
    """StreamManager 核心功能测试"""
    
    @pytest.fixture
    def sample_config(self):
        return {
            'obs': {'host': 'localhost', 'port': 4455},
            'platforms': {
                'douyin': {'rtmp_url': 'rtmp://test.com', 'stream_key': 'key1'},
                'kuaishou': {'rtmp_url': 'rtmp://test.com', 'stream_key': 'key2'},
                'wechat': {'rtmp_url': 'rtmp://test.com', 'stream_key': 'key3'}
            }
        }
    
    def test_init(self, sample_config):
        """测试初始化"""
        manager = StreamManager(sample_config, use_obs=False)
        
        assert manager.config == sample_config
        assert manager.use_obs is False
        assert len(manager.workers) == 0
        assert 'douyin' in manager.platform_status
    
    def test_is_platform_running_not_exist(self, sample_config):
        """测试不存在的平台状态检查"""
        manager = StreamManager(sample_config, use_obs=False)
        
        assert manager.is_platform_running('nonexistent') is False
    
    def test_start_platform_creates_worker(self, sample_config):
        """测试启动平台时创建 Worker"""
        manager = StreamManager(sample_config, use_obs=False)
        
        # 模拟 worker.start() 不阻塞
        original_start = SimpleStreamWorker.start
        SimpleStreamWorker.start = lambda self: None
        
        success = manager.start_platform('douyin')
        
        assert 'douyin' in manager.workers
        assert manager.is_platform_running('douyin') is True
        
        # 恢复原始方法
        SimpleStreamWorker.start = original_start
    
    def test_start_platform_already_running(self, sample_config):
        """测试重复启动已运行的平台"""
        manager = StreamManager(sample_config, use_obs=False)
        
        # 模拟 worker
        mock_worker = Mock()
        mock_worker.start_stream.return_value = True
        manager.workers['douyin'] = mock_worker
        manager.platform_status['douyin'] = LiveStatus.LIVE
        
        success = manager.start_platform('douyin')
        
        assert success is True  # 已运行返回 True
    
    def test_stop_platform(self, sample_config):
        """测试停止平台"""
        manager = StreamManager(sample_config, use_obs=False)
        
        # 模拟 worker
        mock_worker = Mock()
        mock_worker.stop_stream.return_value = True
        manager.workers['douyin'] = mock_worker
        manager.platform_status['douyin'] = LiveStatus.LIVE
        
        success = manager.stop_platform('douyin')
        
        assert success is True
        assert manager.is_platform_running('douyin') is False
    
    def test_stop_platform_not_running(self, sample_config):
        """测试停止未运行的平台"""
        manager = StreamManager(sample_config, use_obs=False)
        
        # 模拟 worker
        mock_worker = Mock()
        manager.workers['douyin'] = mock_worker
        
        success = manager.stop_platform('douyin')
        
        assert success is True  # 未运行返回 True
    
    def test_stop_all_platforms(self, sample_config):
        """测试停止所有平台"""
        manager = StreamManager(sample_config, use_obs=False)
        
        # 模拟多个 worker
        for platform in ['douyin', 'kuaishou']:
            mock_worker = Mock()
            mock_worker.stop_stream.return_value = True
            manager.workers[platform] = mock_worker
            manager.platform_status[platform] = LiveStatus.LIVE
        
        manager.stop_all_platforms()
        
        assert not manager.is_platform_running('douyin')
        assert not manager.is_platform_running('kuaishou')
    
    def test_get_active_platforms(self, sample_config):
        """测试获取运行中的平台列表"""
        manager = StreamManager(sample_config, use_obs=False)
        
        # 设置部分平台为运行状态
        manager.platform_status['douyin'] = LiveStatus.LIVE
        
        active = manager.get_active_platforms()
        
        assert 'douyin' in active
    
    def test_get_worker(self, sample_config):
        """测试获取 Worker 实例"""
        manager = StreamManager(sample_config, use_obs=False)
        
        mock_worker = Mock()
        manager.workers['douyin'] = mock_worker
        
        worker = manager.get_worker('douyin')
        
        assert worker is mock_worker
    
    def test_get_status_summary(self, sample_config):
        """测试获取状态摘要"""
        manager = StreamManager(sample_config, use_obs=False)
        
        # 设置部分平台为运行状态
        manager.platform_status['douyin'] = LiveStatus.LIVE
        
        summary = manager.get_status_summary()
        
        assert 'douyin' in summary
        assert summary['douyin']['status'] == 'LIVE'


class TestSimpleStreamWorker:
    """SimpleStreamWorker 模拟模式测试"""
    
    @pytest.fixture
    def sample_config(self):
        return {
            'obs': {'host': 'localhost', 'port': 4455},
            'platforms': {}
        }
    
    def test_init(self, sample_config):
        """测试初始化"""
        worker = SimpleStreamWorker('douyin', sample_config)
        
        assert worker.platform == 'douyin'
        assert worker._rtmp_url == ''
        assert worker._stream_key == ''
    
    def test_start_stream_no_credentials(self, sample_config):
        """测试无凭证时启动失败"""
        worker = SimpleStreamWorker('douyin', sample_config)
        
        success = worker.start_stream()
        
        assert success is False
    
    def test_get_stream_stats(self, sample_config):
        """测试获取推流统计"""
        worker = SimpleStreamWorker('douyin', sample_config)
        
        stats = worker.get_stream_stats()
        
        assert 'status' in stats
        assert 'rtmp_url' in stats
