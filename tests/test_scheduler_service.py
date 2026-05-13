"""
Scheduler Service Tests - 定时任务调度服务测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from src.scheduler.service import SchedulerService, ScheduledTask, SimpleSchedulerService


class TestScheduledTask:
    """ScheduledTask 对象测试"""
    
    def test_is_due_not_yet(self):
        """测试未到执行时间"""
        future_time = datetime.utcnow() + timedelta(hours=1)
        task = ScheduledTask(1, 'douyin', future_time)
        
        assert task.is_due() is False
    
    def test_is_due_passed(self):
        """测试已过执行时间"""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        task = ScheduledTask(1, 'douyin', past_time)
        
        assert task.is_due() is True
    
    def test_is_due_pending_required(self):
        """测试只有 pending 状态才算到期"""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        task = ScheduledTask(1, 'douyin', past_time)
        task.status = 'running'
        
        assert task.is_due() is False
    
    def test_has_expired(self):
        """测试过期检查"""
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow() - timedelta(minutes=10)  # 已结束
        task = ScheduledTask(1, 'douyin', start_time, end_time=end_time)
        
        assert task.has_expired() is True
    
    def test_has_expired_not_yet(self):
        """测试未过期"""
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow() + timedelta(hours=1)  # 还未结束
        task = ScheduledTask(1, 'douyin', start_time, end_time=end_time)
        
        assert task.has_expired() is False
    
    def test_to_dict(self):
        """测试转换为字典"""
        start_time = datetime.utcnow()
        task = ScheduledTask(1, 'douyin', start_time, config={'key': 'value'})
        
        d = task.to_dict()
        
        assert d['id'] == 1
        assert d['platform'] == 'douyin'
        assert d['status'] == 'pending'


class TestSchedulerService:
    """SchedulerService 核心功能测试"""
    
    @pytest.fixture
    def mock_db_session(self):
        session = Mock()
        return session
    
    def test_init_with_stream_manager(self, mock_db_session):
        """测试初始化时绑定 StreamManager"""
        mock_sm = Mock()
        service = SchedulerService(mock_db_session, stream_manager=mock_sm)
        
        assert service.stream_manager is mock_sm
    
    def test_set_stream_manager(self, mock_db_session):
        """测试动态设置 StreamManager"""
        service = SchedulerService(mock_db_session)
        
        new_sm = Mock()
        service.set_stream_manager(new_sm)
        
        assert service.stream_manager is new_sm
    
    def test_create_task_in_memory(self, mock_db_session):
        """测试创建内存任务 (SimpleSchedulerService)"""
        service = SimpleSchedulerService()
        
        start_time = datetime.utcnow() + timedelta(minutes=5)
        task = service.create_task('douyin', start_time, config={'key': 'value'})
        
        assert task.id in service.tasks
        assert task.platform == 'douyin'
        assert task.status == 'pending'
    
    def test_delete_task(self, mock_db_session):
        """测试删除任务"""
        service = SimpleSchedulerService()
        
        start_time = datetime.utcnow() + timedelta(minutes=5)
        task = service.create_task('douyin', start_time)
        task_id = task.id
        
        result = service.delete_task(task_id)
        
        assert result is True
        assert task_id not in service.tasks
    
    def test_delete_nonexistent_task(self, mock_db_session):
        """测试删除不存在的任务"""
        service = SimpleSchedulerService()
        
        result = service.delete_task(9999)
        
        assert result is False
    
    def test_get_all_tasks_sorted(self, mock_db_session):
        """测试获取所有任务 (按时间排序)"""
        service = SimpleSchedulerService()
        
        # 创建多个不同时间的任务
        task1 = service.create_task('douyin', datetime.utcnow() + timedelta(hours=2))
        task2 = service.create_task('kuaishou', datetime.utcnow() + timedelta(minutes=5))
        task3 = service.create_task('wechat', datetime.utcnow() + timedelta(hours=1))
        
        tasks = service.get_all_tasks()
        
        assert len(tasks) == 3
        # 验证按开始时间排序
        assert tasks[0].start_time <= tasks[1].start_time <= tasks[2].start_time
    
    def test_check_due_tasks(self, mock_db_session):
        """测试检查到期任务"""
        service = SimpleSchedulerService()
        
        # 创建一个已过期的任务
        past_time = datetime.utcnow() - timedelta(minutes=5)
        task = service.create_task('douyin', past_time)
        
        # 触发检查 (手动调用，不等待定时器)
        service._check_due_tasks()
        
        assert task.status == 'running'


class TestSchedulerIntegration:
    """SchedulerService 与 StreamManager 集成测试"""
    
    def test_execute_task_with_stream_manager(self, mock_db_session):
        """测试带 StreamManager 的任务执行"""
        # Mock StreamManager
        mock_sm = Mock()
        mock_sm.start_platform.return_value = True
        
        service = SchedulerService(mock_db_session, stream_manager=mock_sm)
        
        # 创建到期任务
        past_time = datetime.utcnow() - timedelta(minutes=5)
        task = ScheduledTask(1, 'douyin', past_time)
        service.tasks[1] = task
        
        # 执行任务
        service._execute_task(task)
        
        assert task.status == 'running'
        mock_sm.start_platform.assert_called_once_with('douyin')
    
    def test_execute_task_stream_manager_failure(self, mock_db_session):
        """测试 StreamManager 推流失败时的处理"""
        # Mock StreamManager 返回失败
        mock_sm = Mock()
        mock_sm.start_platform.return_value = False
        
        service = SchedulerService(mock_db_session, stream_manager=mock_sm)
        
        past_time = datetime.utcnow() - timedelta(minutes=5)
        task = ScheduledTask(1, 'douyin', past_time)
        service.tasks[1] = task
        
        # 执行任务
        service._execute_task(task)
        
        assert task.status == 'cancelled'
