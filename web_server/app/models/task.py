from datetime import datetime
from typing import Optional, List
from enum import Enum
from .base import BaseModel
from app.extensions import db

class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

class TaskStatus(str, Enum):
    """Task status states."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'

class Task(BaseModel):
    """Task model for todo items."""
    
    __tablename__ = 'tasks'
    
    # Core fields
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Status and priority
    status = db.Column(db.String(20), default=TaskStatus.PENDING, index=True)
    priority = db.Column(db.String(20), default=TaskPriority.MEDIUM, index=True)
    
    # Dates
    due_date = db.Column(db.DateTime, index=True)
    completed_at = db.Column(db.DateTime)
    reminder_at = db.Column(db.DateTime)
    
    # Progress
    progress_percentage = db.Column(db.Integer, default=0)
    
    # Metadata
    tags = db.Column(db.String(200))  # Comma-separated tags
    estimated_minutes = db.Column(db.Integer)
    actual_minutes = db.Column(db.Integer)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    owner = db.relationship('User', back_populates='tasks')
    
    # Parent-child task relationships
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __init__(self, title: str, user_id: int, **kwargs):
        """Initialize task."""
        self.title = title
        self.user_id = user_id
        super().__init__(**kwargs)
    
    def complete(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        self.save()
    
    def archive(self) -> None:
        """Archive task."""
        self.status = TaskStatus.ARCHIVED
        self.save()
    
    def set_progress(self, percentage: int) -> None:
        """Set task progress percentage."""
        if 0 <= percentage <= 100:
            self.progress_percentage = percentage
            if percentage == 100:
                self.complete()
            elif self.status == TaskStatus.COMPLETED and percentage < 100:
                self.status = TaskStatus.IN_PROGRESS
            elif self.status == TaskStatus.PENDING and percentage > 0:
                self.status = TaskStatus.IN_PROGRESS
            self.save()
    
    def add_subtask(self, title: str, **kwargs) -> 'Task':
        """Create a subtask."""
        subtask = Task(title=title, user_id=self.user_id, parent_task_id=self.id, **kwargs)
        subtask.save()
        return subtask
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date and self.status != TaskStatus.COMPLETED:
            return datetime.utcnow() > self.due_date
        return False
    
    @property
    def can_start(self) -> bool:
        """Check if task can be started."""
        return self.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
    
    @property
    def tags_list(self) -> List[str]:
        """Get tags as list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to task."""
        current_tags = self.tags_list
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = ', '.join(current_tags)
            self.save()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from task."""
        current_tags = self.tags_list
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ', '.join(current_tags) if current_tags else None
            self.save()
    
    def get_completion_time_estimate(self) -> Optional[int]:
        """Get estimated time remaining in minutes."""
        if self.status == TaskStatus.COMPLETED:
            return 0
        if self.estimated_minutes:
            return max(0, self.estimated_minutes - (self.actual_minutes or 0))
        return None
    
    def to_dict(self, include_subtasks: bool = False) -> dict:
        """Convert task to dictionary."""
        data = super().to_dict()
        data['is_overdue'] = self.is_overdue
        data['completion_estimate'] = self.get_completion_time_estimate()
        data['tags'] = self.tags_list
        
        if include_subtasks:
            data['subtasks'] = [subtask.to_dict() for subtask in self.subtasks]
        
        return data
    
    def __repr__(self) -> str:
        return f'<Task {self.title} - {self.status}>'