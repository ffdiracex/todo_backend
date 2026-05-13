"""Task forms with validation."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from datetime import datetime

class TaskForm(FlaskForm):
    """Task creation form."""
    
    title = StringField('Task Title', validators=[
        DataRequired(message='Task title is required'),
        Length(min=1, max=200, message='Title must be between 1 and 200 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Length(max=2000, message='Description cannot exceed 2000 characters')
    ])
    
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    
    due_date = DateTimeField('Due Date', format='%Y-%m-%dT%H:%M', validators=[
        Optional()
    ])
    
    tags = StringField('Tags', validators=[
        Length(max=200, message='Tags cannot exceed 200 characters'),
        Optional()
    ])
    
    estimated_minutes = IntegerField('Estimated Minutes', validators=[
        Optional(),
        NumberRange(min=1, max=10080, message='Estimated time must be between 1 and 10080 minutes')
    ])
    
    def validate_due_date(self, field):
        """Validate that due date is in the future."""
        if field.data and field.data < datetime.utcnow():
            raise ValidationError('Due date must be in the future')
    
    def validate_tags(self, field):
        """Validate tags format."""
        if field.data:
            tags = [tag.strip() for tag in field.data.split(',')]
            if len(tags) > 10:
                raise ValidationError('Maximum 10 tags allowed')
            for tag in tags:
                if not tag or len(tag) > 30:
                    raise ValidationError('Each tag must be between 1 and 30 characters')

class TaskEditForm(TaskForm):
    """Task editing form (optional fields)."""
    
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ])
    
    progress_percentage = IntegerField('Progress', validators=[
        NumberRange(min=0, max=100, message='Progress must be between 0 and 100')
    ])

class TaskFilterForm(FlaskForm):
    """Task filtering form."""
    
    status = SelectField('Status', choices=[
        ('', 'All'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], default='')
    
    priority = SelectField('Priority', choices=[
        ('', 'All'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='')
    
    tag = StringField('Tag', validators=[
        Length(max=30)
    ])
    
    sort_by = SelectField('Sort By', choices=[
        ('created_at', 'Created Date'),
        ('due_date', 'Due Date'),
        ('priority', 'Priority'),
        ('title', 'Title')
    ], default='created_at')
    
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc')