// API Client
const API = {
    async request(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(endpoint, options);
        return await response.json();
    },
    
    async createTask(taskData) {
        return this.request('/api/tasks', 'POST', taskData);
    },
    
    async getTasks(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/tasks?${queryString}`);
    },
    
    async updateTask(taskId, taskData) {
        return this.request(`/api/tasks/${taskId}`, 'PUT', taskData);
    },
    
    async completeTask(taskId) {
        return this.request(`/api/tasks/${taskId}/complete`, 'POST');
    },
    
    async deleteTask(taskId) {
        return this.request(`/api/tasks/${taskId}`, 'DELETE');
    },
    
    async getStatistics() {
        return this.request('/api/tasks/statistics');
    },
    
    async getOverdueTasks() {
        return this.request('/api/tasks/overdue');
    }
};

// Task Manager Class
class TaskManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadTasks();
        this.loadStatistics();
    }
    
    bindEvents() {
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createTask();
        });
    }
    
    async createTask() {
        const taskData = {
            title: document.getElementById('title').value,
            description: document.getElementById('description').value,
            priority: document.getElementById('priority').value,
            due_date: document.getElementById('due_date').value,
            tags: document.getElementById('tags').value
        };
        
        const result = await API.createTask(taskData);
        
        if (result.success) {
            this.showNotification('Task created successfully!', 'success');
            document.getElementById('taskForm').reset();
            this.loadTasks();
            this.loadStatistics();
        } else {
            this.showNotification(result.error || 'Failed to create task', 'danger');
        }
    }
    
    async loadTasks() {
        const result = await API.getTasks({ per_page: 50 });
        
        if (result.success) {
            const pendingTasks = result.tasks.filter(t => t.status === 'pending');
            const completedTasks = result.tasks.filter(t => t.status === 'completed');
            
            this.renderTasks(pendingTasks, 'pendingTasks');
            this.renderTasks(completedTasks, 'completedTasks');
            
            const overdueResult = await API.getOverdueTasks();
            if (overdueResult.success) {
                this.renderTasks(overdueResult.tasks, 'overdueTasks');
            }
        }
    }
    
    renderTasks(tasks, containerId) {
        const container = document.getElementById(containerId);
        
        if (!tasks || tasks.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No tasks found</div>';
            return;
        }
        
        container.innerHTML = tasks.map(task => this.createTaskCard(task)).join('');
        
        // Bind event handlers for task actions
        tasks.forEach(task => {
            const completeBtn = document.getElementById(`complete-${task.id}`);
            const deleteBtn = document.getElementById(`delete-${task.id}`);
            const editBtn = document.getElementById(`edit-${task.id}`);
            
            if (completeBtn) {
                completeBtn.onclick = () => this.markComplete(task.id);
            }
            if (deleteBtn) {
                deleteBtn.onclick = () => this.deleteTask(task.id);
            }
            if (editBtn) {
                editBtn.onclick = () => this.editTask(task.id);
            }
        });
    }
    
    createTaskCard(task) {
        const priorityClass = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'urgent': 'danger'
        }[task.priority] || 'secondary';
        
        const isOverdue = task.is_overdue ? '<span class="badge bg-danger">Overdue</span>' : '';
        
        return `
            <div class="card mb-3 task-card" data-task-id="${task.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title">${this.escapeHtml(task.title)}</h5>
                        <div>
                            <span class="badge bg-${priorityClass}">${task.priority}</span>
                            ${isOverdue}
                        </div>
                    </div>
                    ${task.description ? `<p class="card-text">${this.escapeHtml(task.description)}</p>` : ''}
                    <div class="text-muted small">
                        ${task.due_date ? `<div>Due: ${new Date(task.due_date).toLocaleString()}</div>` : ''}
                        ${task.tags && task.tags.length ? `<div>Tags: ${task.tags.map(t => `<span class="badge bg-secondary me-1">${t}</span>`).join('')}</div>` : ''}
                    </div>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-success" id="complete-${task.id}">✓ Complete</button>
                        <button class="btn btn-sm btn-primary" id="edit-${task.id}">✎ Edit</button>
                        <button class="btn btn-sm btn-danger" id="delete-${task.id}">🗑 Delete</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async markComplete(taskId) {
        const result = await API.completeTask(taskId);
        
        if (result.success) {
            this.showNotification('Task completed!', 'success');
            this.loadTasks();
            this.loadStatistics();
        } else {
            this.showNotification(result.error || 'Failed to complete task', 'danger');
        }
    }
    
    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) return;
        
        const result = await API.deleteTask(taskId);
        
        if (result.success) {
            this.showNotification('Task deleted!', 'success');
            this.loadTasks();
            this.loadStatistics();
        } else {
            this.showNotification(result.error || 'Failed to delete task', 'danger');
        }
    }
    
    async editTask(taskId) {
        // Implement edit functionality with modal
        const newTitle = prompt('Enter new task title:');
        if (newTitle) {
            const result = await API.updateTask(taskId, { title: newTitle });
            if (result.success) {
                this.showNotification('Task updated!', 'success');
                this.loadTasks();
            }
        }
    }
    
    async loadStatistics() {
        const result = await API.getStatistics();
        
        if (result.success) {
            const stats = result.statistics;
            const statsHtml = `
                <div class="list-group">
                    <div class="list-group-item d-flex justify-content-between">
                        <span>Total Tasks:</span>
                        <strong>${stats.total}</strong>
                    </div>
                    <div class="list-group-item d-flex justify-content-between">
                        <span>Completed:</span>
                        <strong>${stats.completed}</strong>
                    </div>
                    <div class="list-group-item d-flex justify-content-between">
                        <span>Pending:</span>
                        <strong>${stats.pending}</strong>
                    </div>
                    <div class="list-group-item d-flex justify-content-between">
                        <span>In Progress:</span>
                        <strong>${stats.in_progress}</strong>
                    </div>
                    <div class="list-group-item d-flex justify-content-between">
                        <span>Overdue:</span>
                        <strong class="text-danger">${stats.overdue}</strong>
                    </div>
                    <div class="list-group-item d-flex justify-content-between">
                        <span>Completion Rate:</span>
                        <strong>${stats.completion_rate.toFixed(1)}%</strong>
                    </div>
                </div>
            `;
            document.getElementById('statistics').innerHTML = statsHtml;
        }
    }
    
    showNotification(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new TaskManager();
});