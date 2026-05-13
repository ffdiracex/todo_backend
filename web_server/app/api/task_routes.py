"""Task API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.task_service import TaskService
from app.forms.task_forms import TaskForm, TaskEditForm, TaskFilterForm
from app.extensions import limiter, cache

task_bp = Blueprint('tasks', __name__)
task_service = TaskService()

@task_bp.route('', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def create_task():
    """Create a new task."""
    form = TaskForm()
    
    if not form.validate_on_submit():
        return jsonify({
            'success': False,
            'errors': form.errors
        }), 400
    
    task, error = task_service.create_task(current_user.id, form.data)
    
    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    return jsonify({
        'success': True,
        'task': task,
        'message': 'Task created successfully'
    }), 201

@task_bp.route('', methods=['GET'])
@login_required
@cache.cached(timeout=60, query_string=True)
def get_tasks():
    """Get user tasks with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    form = TaskFilterForm(request.args)
    filters = {
        'status': form.status.data if form.status.data else None,
        'priority': form.priority.data if form.priority.data else None,
        'tags': form.tag.data if form.tag.data else None
    }
    
    result = task_service.get_user_tasks(current_user.id, page, per_page, filters)
    
    return jsonify({
        'success': True,
        **result
    }), 200

@task_bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get a specific task."""
    task = task_service.get_task(task_id, current_user.id)
    
    if task:
        return jsonify({
            'success': True,
            'task': task
        }), 200
    
    return jsonify({
        'success': False,
        'error': 'Task not found'
    }), 404

@task_bp.route('/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update a task."""
    form = TaskEditForm()
    
    if not form.validate_on_submit():
        return jsonify({
            'success': False,
            'errors': form.errors
        }), 400
    
    success, message, task = task_service.update_task(task_id, current_user.id, form.data)
    
    if success:
        return jsonify({
            'success': True,
            'task': task,
            'message': message
        }), 200
    
    return jsonify({
        'success': False,
        'error': message
    }), 404 if 'not found' in message else 403

@task_bp.route('/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark task as completed."""
    success, message = task_service.complete_task(task_id, current_user.id)
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        }), 200
    
    return jsonify({
        'success': False,
        'error': message
    }), 404 if 'not found' in message else 403

@task_bp.route('/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    success, message = task_service.delete_task(task_id, current_user.id)
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        }), 200
    
    return jsonify({
        'success': False,
        'error': message
    }), 404 if 'not found' in message else 403

@task_bp.route('/overdue', methods=['GET'])
@login_required
def get_overdue_tasks():
    """Get overdue tasks."""
    tasks = task_service.get_overdue_tasks(current_user.id)
    
    return jsonify({
        'success': True,
        'tasks': tasks,
        'count': len(tasks)
    }), 200

@task_bp.route('/due-soon', methods=['GET'])
@login_required
def get_tasks_due_soon():
    """Get tasks due soon."""
    days = request.args.get('days', 3, type=int)
    tasks = task_service.get_tasks_due_soon(current_user.id, days)
    
    return jsonify({
        'success': True,
        'tasks': tasks,
        'count': len(tasks),
        'days': days
    }), 200

@task_bp.route('/statistics', methods=['GET'])
@login_required
@cache.cached(timeout=300)
def get_statistics():
    """Get task statistics."""
    stats = task_service.get_task_statistics(current_user.id)
    
    return jsonify({
        'success': True,
        'statistics': stats
    }), 200

@task_bp.route('/bulk-status', methods=['POST'])
@login_required
def bulk_update_status():
    """Bulk update task statuses."""
    data = request.get_json()
    
    if not data or 'task_ids' not in data or 'status' not in data:
        return jsonify({
            'success': False,
            'error': 'task_ids and status are required'
        }), 400
    
    success, message, count = task_service.bulk_update_status(
        data['task_ids'],
        current_user.id,
        data['status']
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'updated_count': count
        }), 200
    
    return jsonify({
        'success': False,
        'error': message
    }), 400

@task_bp.route('/search', methods=['GET'])
@login_required
def search_tasks():
    """Search tasks."""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    results = task_service.search_tasks(current_user.id, query, page, per_page)
    
    return jsonify({
        'success': True,
        **results
    }), 200