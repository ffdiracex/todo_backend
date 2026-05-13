from typing import Optional, Dict, Any, List
from datetime import datetime
from app.repositories.task_repository import TaskRepository
from app.models.task import TaskStatus, TaskPriority

class TaskService:
    """Service for handling task business logic."""

    def __init__(self):
        self.task_repo = TaskRepository()

    def create_task(self, user_id: int, task_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Create a new task for a user."""
        try:
            task = self.task_repo.create(
                user_id=user_id,
                title=task_data['title'],
                description=task_data.get('description'),
                priority=task_data.get('priority', TaskPriority.MEDIUM),
                due_date=task_data.get('due_date'),
                tags=task_data.get('tags'),
                estimated_minutes=task_data.get('estimated_minutes')
            )
            return task.to_dict(), None
        except Exception as e:
            return None, f'Failed to create task: {str(e)}'

    def get_user_tasks(self, user_id: int, page: int = 1, per_page: int = 20, filters: Dict = None) -> Dict:
        """Get user tasks with filtering and pagination."""
        if filters is None:
            filters = {}

        tasks = self.task_repo.get_by_user(user_id, page, per_page, **filters)
        statistics = self.task_repo.get_statistics(user_id)

        return {
         'tasks': [task.to_dict() for task in tasks.items],
         'pagination': {
         'page': tasks.page,
         'per_page': tasks.per_page,
         'total': tasks.total,
         'pages': tasks.pages
         },
         'statistics': statistics
        }

    def get_task(self, task_id: int, user_id: int) -> Optional[Dict]:
      """Get a single task if it belongs to the user."""
      task = self.task_repo.get_by_id(task_id)
      if task and task.user_id == user_id:
        return task.to_dict(include_subtasks=True)
      return None

    def update_task(self, task_id: int, user_id: int, update_data: Dict) -> tuple[bool, str, Optional[Dict]]:
        """Update a task if it belongs to the user."""
        task = self.task_repo.get_by_id(task_id)

        if not task:
            return False, 'Task not found', None

        if task.user_id != user_id:
            return False, 'Unauthorized access', None


        if 'progress_percentage' in update_data:
            task.set_progress(update_data.pop('progress_percentage'))


        allowed_fields = ['title', 'description', 'priority', 'due_date', 'tags', 'estimated_minutes']
        update_dict = {k: v for k, v in update_data.items() if k in allowed_fields and v is not None}

        if update_dict:
            task.update(**update_dict)
        return True, 'Task updated successfully', task.to_dict()

    def complete_task(self, task_id: int, user_id: int) -> tuple[bool, str]:
        """Mark a task as completed."""
        task = self.task_repo.get_by_id(task_id)

        if not task:
            return False, 'Task not found'

        if task.user_id != user_id:
            return False, 'Unauthorized access'

        task.complete()
        return True, 'Task marked as completed'

    def delete_task(self, task_id: int, user_id: int) -> tuple[bool, str]:
        """Delete a task if it belongs to the user."""
        task = self.task_repo.get_by_id(task_id)

        if not task:
            return False, 'Task not found'

        if task.user_id != user_id:
            return False, 'Unauthorized access'

        self.task_repo.delete(task_id)
        return True, 'Task deleted successfully'

    def get_overdue_tasks(self, user_id: int) -> List[Dict]:
        """Get all overdue tasks for a user."""
        tasks = self.task_repo.get_overdue_tasks(user_id)
        return [task.to_dict() for task in tasks]

    def get_tasks_due_soon(self, user_id: int, days: int = 3) -> List[Dict]:
        """Get tasks due in the next N days."""
        tasks = self.task_repo.get_tasks_due_soon(user_id, days)
        return [task.to_dict() for task in tasks]

    def bulk_update_status(self, task_ids: List[int], user_id: int, status: str) -> tuple[bool, str, int]:
        """Bulk update task statuses."""
        for task_id in task_ids:
            task = self.task_repo.get_by_id(task_id)
            if not task or task.user_id != user_id:
                return False, f'Task {task_id} not found or unauthorized', 0

            count = self.task_repo.bulk_update_status(task_ids, status)
        return True, f'Successfully updated {count} tasks', count

    def get_task_statistics(self, user_id: int) -> Dict:
        """Get comprehensive task statistics."""
        return self.task_repo.get_statistics(user_id)

    def search_tasks(self, user_id: int, query: str, page: int = 1, per_page: int = 20) -> Dict:
        """Search tasks by title and description."""
        from app.models.task import Task

        tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.title.contains(query) | Task.description.contains(query)
            ).paginate(page=page, per_page=per_page, error_out=False)

        return {
        'tasks': [task.to_dict() for task in tasks.items],
        'pagination': {
        'page': tasks.page,
        'per_page': tasks.per_page,
        'total': tasks.total,
        'pages': tasks.pages
            }
        }
