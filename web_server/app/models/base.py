"""Base model with common functionality."""
from datetime import datetime
from app.extensions import db

class BaseModel(db.Model):
    """Abstract base model with common fields and methods."""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """Save model to database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete model from database."""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        from sqlalchemy.orm import class_mapper
        return {column.key: getattr(self, column.key) 
                for column in class_mapper(self.__class__).columns}
    
    @classmethod
    def get_by_id(cls, id: int):
        """Get model by ID."""
        return cls.query.get(id)