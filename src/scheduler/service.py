"""
Scheduler Service - 定时任务调度服务
负责管理定时直播任务的创建、执行和状态追踪
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from sqlalchemy.orm import Session

from ..data.models import Schedule as ScheduleModel
from ..core.enums import LiveStatus

logger = logging.getLogger(__name__)


class ScheduledTask:
    """定时任务对象"""
    
    def __init__(self, schedule_id: int, platform: str, start_time: datetime, 
                 end_time: Optional[datetime] = None, config: Dict[str, Any] = None):
        self.id = schedule_id
        self.platform = platform
        self.start_time = start_time
        self.end_time = end_time
        self.config = config or {}
        
        # 任务状态
        self.status = 'pending'  # pending/running/completed/cancelled
        self.created_at = datetime.utcnow()
    
    def is_due(self) -> bool:
        """检查是否已到执行时间"""
        return datetime.utcnow() >= self.start_time and self.status == 'pending'
    
    def has_expired(self) -> bool:
        """检查是否已过期 (超过结束时间仍未启动)"""
        if self.end_time and datetime.utcnow() > self.end_time:
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'platform': self.platform,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }


class SchedulerService(QObject):
    """
    定时任务调度服务
    
    功能:
    - 管理定时直播任务的创建/删除/查询
    - 定期检查到期任务并自动触发推流
    - 通过信号槽与 UI 通信
    
    架构设计:
    ┌─────────────────────────────────────────────┐
    │         SchedulerService                    │
    ├─────────────────────────────────────────────┤
    │  tasks: Dict[int, ScheduledTask]           │
    │  check_timer: QTimer (每 30 秒检查一次)     │
    └─────────────────────────────────────────────┘
               ↓ signals
    ┌─────────────────────────────────────────────┐
    │         MainWindow UI                       │
    │  - task_added(ScheduledTask)               │
    │  - task_started(int, str)                  │
    │  - task_completed(int)                     |
    │  - task_cancelled(int)                     │
    └─────────────────────────────────────────────┘
    """
    
    # PyQt6 信号定义
    task_added = pyqtSignal(object)       # (ScheduledTask)
    task_started = pyqtSignal(int, str)   # (task_id, platform)
    task_completed = pyqtSignal(int)      # (task_id)
    task_cancelled = pyqtSignal(int)      # (task_id)
    log_message = pyqtSignal(str)         # (message)
    
    def __init__(self, db_session: Session, stream_manager=None):
        super().__init__()
        
        self.db_session = db_session
        
        # 定时任务缓存
        self.tasks: Dict[int, ScheduledTask] = {}
        
        # StreamManager 引用 (用于执行推流)
        self.stream_manager = stream_manager
        
        # 检查定时器 (每 30 秒检查一次到期任务)
        self.check_timer = QTimer()
        self.check_timer.setInterval(30000)  # 30 秒
        self.check_timer.timeout.connect(self._check_due_tasks)
        
        # 是否启用调度服务
        self.enabled = False
    
    def set_stream_manager(self, stream_manager):
        """设置 StreamManager 引用 (用于执行推流)"""
        self.stream_manager = stream_manager
        logger.info("SchedulerService: StreamManager 已绑定")
    
    def start(self):
        """启动调度服务"""
        if not self.enabled:
            self.enabled = True
            self.check_timer.start()
            logger.info("SchedulerService 已启动 (每 30 秒检查到期任务)")
    
    def stop(self):
        """停止调度服务"""
        if self.enabled:
            self.enabled = False
            self.check_timer.stop()
            logger.info("SchedulerService 已停止")
    
    def create_task(self, platform: str, start_time: datetime, 
                    end_time: Optional[datetime] = None, 
                    config: Dict[str, Any] = None) -> ScheduledTask:
        """
        创建定时任务
        
        Args:
            platform: 平台名称 (douyin/kuaishou/wechat)
            start_time: 开始时间
            end_time: 结束时间 (可选，用于单次任务自动停止)
            config: 推流配置
        
        Returns:
            ScheduledTask: 创建的任务对象
        """
        # 保存到数据库
        schedule_model = ScheduleModel(
            platform_id=None,  # TODO: 关联平台表 ID
            start_time=start_time,
            end_time=end_time,
            avatar_config=config.get('avatar_config', '{}') if config else '{}',
            script_template=config.get('script_template', '') if config else '',
            status='pending'
        )
        
        self.db_session.add(schedule_model)
        self.db_session.commit()
        
        # 创建任务对象
        task = ScheduledTask(
            schedule_id=schedule_model.id,
            platform=platform,
            start_time=start_time,
            end_time=end_time,
            config=config or {}
        )
        
        self.tasks[schedule_model.id] = task
        
        # 发送信号
        self.task_added.emit(task)
        self.log_message.emit(f"✅ 定时任务已创建：{platform} @ {start_time.strftime('%Y-%m-%d %H:%M')}")
        
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """删除定时任务"""
        if task_id not in self.tasks:
            logger.error(f"未找到任务 ID: {task_id}")
            return False
        
        # 从数据库删除
        schedule_model = self.db_session.query(ScheduleModel).filter_by(id=task_id).first()
        if schedule_model:
            self.db_session.delete(schedule_model)
            self.db_session.commit()
        
        # 从缓存删除
        del self.tasks[task_id]
        
        # 发送信号
        self.task_cancelled.emit(task_id)
        self.log_message.emit(f"🗑️ 定时任务已删除：ID={task_id}")
        
        return True
    
    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        """获取指定任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有任务 (按开始时间排序)"""
        return sorted(self.tasks.values(), key=lambda t: t.start_time)
    
    def _check_due_tasks(self):
        """检查到期任务并触发执行"""
        for task_id, task in list(self.tasks.items()):
            if task.is_due():
                logger.info(f"检测到到期任务：{task.platform} @ {task.start_time}")
                self._execute_task(task)
            elif task.has_expired():
                logger.warning(f"任务已过期：ID={task_id}, 平台={task.platform}")
                task.status = 'cancelled'
    
    def _execute_task(self, task: ScheduledTask):
        """执行定时任务 (启动推流)"""
        if task.status != 'pending':
            return
        
        try:
            # 更新状态
            task.status = 'running'
            
            # 发送信号
            self.task_started.emit(task.id, task.platform)
            self.log_message.emit(f"▶️ 开始执行定时任务：{task.platform}")
            
            # 集成 StreamManager - 启动实际推流
            if self.stream_manager:
                logger.info(f"SchedulerService: 调用 StreamManager.start_platform({task.platform})")
                success = self.stream_manager.start_platform(task.platform)
                
                if success:
                    self.log_message.emit(f"✅ 定时任务执行成功：{task.platform} 推流已启动")
                else:
                    self.log_message.emit(f"❌ 定时任务执行失败：{task.platform} 推流启动失败")
                    task.status = 'cancelled'
            else:
                # 无 StreamManager 时记录警告但仍标记为运行中 (用于测试)
                logger.warning("SchedulerService: stream_manager 未设置，仅模拟推流启动")
                
        except Exception as e:
            logger.error(f"执行定时任务失败：{e}")
            task.status = 'cancelled'
    
    def complete_task(self, task_id: int):
        """标记任务完成"""
        if task_id in self.tasks:
            self.tasks[task_id].status = 'completed'
            self.task_completed.emit(task_id)
            self.log_message.emit(f"✅ 定时任务已完成：ID={task_id}")
    
    def cancel_task(self, task_id: int):
        """取消定时任务"""
        if task_id in self.tasks:
            self.tasks[task_id].status = 'cancelled'
            self.task_cancelled.emit(task_id)
            self.log_message.emit(f"❌ 定时任务已取消：ID={task_id}")


class SimpleSchedulerService(SchedulerService):
    """
    简化版调度服务 - 用于开发测试
    
    不依赖数据库，纯内存管理定时任务
    """
    
    def __init__(self):
        super().__init__(db_session=None)
        self._next_id = 1000  # 模拟 ID 起始值
    
    def create_task(self, platform: str, start_time: datetime, 
                    end_time: Optional[datetime] = None, 
                    config: Dict[str, Any] = None) -> ScheduledTask:
        """创建内存中的定时任务"""
        task_id = self._next_id
        self._next_id += 1
        
        task = ScheduledTask(
            schedule_id=task_id,
            platform=platform,
            start_time=start_time,
            end_time=end_time,
            config=config or {}
        )
        
        self.tasks[task_id] = task
        self.task_added.emit(task)
        self.log_message.emit(f"📅 [SIM] 定时任务已创建：{platform} @ {start_time.strftime('%Y-%m-%d %H:%M')}")
        
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """删除内存中的定时任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.task_cancelled.emit(task_id)
            self.log_message.emit(f"🗑️ [SIM] 定时任务已删除：ID={task_id}")
            return True
        return False
