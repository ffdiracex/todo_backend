"""Task repository with specialized queries."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import and_, or_
from app.models.task import Task, TaskStatus, TaskPriority
from app.repositories.base_repository import BaseRepository

class TaskRepository(BaseRepository[Task]):
    """Repository for Task model with additional methods."""
    
    def __init__(self):
        super().__init__(Task)
    
    def get_by_user(self, user_id: int, page: int = 1, per_page: int = 20, **filters):
        """Get tasks for a specific user with filters."""
        query = Task.query.filter_by(user_id=user_id)
        
        if 'status' in filters and filters['status']:
            query = query.filter_by(status=filters['status'])
        if 'priority' in filters and filters['priority']:
            query = query.filter_by(priority=filters['priority'])
        if 'tags' in filters and filters['tags']:
            tag = filters['tags']
            query = query.filter(Task.tags.like(f'%{tag}%'))
        
        return query.order_by(Task.priority.desc(), Task.due_date.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    def get_overdue_tasks(self, user_id: int) -> List[Task]:
        """Get overdue tasks for a user."""
        return Task.query.filter(
            and_(
                Task.user_id == user_id,
                Task.status != TaskStatus.COMPLETED,
                Task.due_date < datetime.utcnow(),
                Task.due_date.isnot(None)
            )
        ).order_by(Task.due_date.asc()).all()
    
    def get_tasks_by_priority(self, user_id: int, priority: TaskPriority) -> List[Task]:
        """Get tasks by priority level."""
        return Task.query.filter_by(
            user_id=user_id,
            priority=priority,
            status=TaskStatus.PENDING
        ).order_by(Task.due_date.asc()).all()
    
    def get_tasks_due_soon(self, user_id: int, days: int = 3) -> List[Task]:
        """Get tasks due within specified days."""
        from datetime import timedelta
        end_date = datetime.utcnow() + timedelta(days=days)
        
        return Task.query.filter(
            and_(
                Task.user_id == user_id,
                Task.status != TaskStatus.COMPLETED,
                Task.due_date <= end_date,
                Task.due_date >= datetime.utcnow()
            )
        ).order_by(Task.due_date.asc()).all()
    
    def get_completed_tasks_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Task]:
        """Get tasks completed within date range."""
        return Task.query.filter(
            and_(
                Task.user_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= start_date,
                Task.completed_at <= end_date
            )
        ).all()
    
    def get_statistics(self, user_id: int) -> dict:
        """Get task statistics for a user."""
        total = Task.query.filter_by(user_id=user_id).count()
        completed = Task.query.filter_by(user_id=user_id, status=TaskStatus.COMPLETED).count()
        pending = Task.query.filter_by(user_id=user_id, status=TaskStatus.PENDING).count()
        in_progress = Task.query.filter_by(user_id=user_id, status=TaskStatus.IN_PROGRESS).count()
        overdue = self.get_overdue_tasks(user_id).count()
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'overdue': overdue,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }
    
    def bulk_update_status(self, task_ids: List[int], status: TaskStatus) -> int:
        """Bulk update task statuses."""
        return Task.query.filter(Task.id.in_(task_ids)).update(
            {Task.status: status}, synchronize_session=False
        )
    
    def archive_old_tasks(self, days: int = 30) -> int:
        """Archive tasks completed more than N days ago."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return Task.query.filter(
            and_(
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at <= cutoff_date
            )
        ).update({Task.status: TaskStatus.ARCHIVED}, synchronize_session=False)