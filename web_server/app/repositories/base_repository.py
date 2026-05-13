"""Base repository pattern implementation."""
from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod
from app.extensions import db
from app.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T], ABC):
    """Base repository with CRUD operations."""
    
    def __init__(self, model_class: T):
        self.model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        return self.model_class.query.get(id)
    
    def get_all(self, page: int = 1, per_page: int = 20, **filters):
        """Get all entities with pagination and filters."""
        query = self.model_class.query
        
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model_class, key) == value)
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    def create(self, **kwargs) -> T:
        """Create new entity."""
        entity = self.model_class(**kwargs)
        entity.save()
        return entity
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update entity."""
        entity = self.get_by_id(id)
        if entity:
            entity.update(**kwargs)
        return entity
    
    def delete(self, id: int) -> bool:
        """Delete entity."""
        entity = self.get_by_id(id)
        if entity:
            entity.delete()
            return True
        return False
    
    def exists(self, **filters) -> bool:
        """Check if entity exists."""
        query = self.model_class.query
        for key, value in filters.items():
            query = query.filter(getattr(self.model_class, key) == value)
        return query.first() is not None
    
    def count(self, **filters) -> int:
        """Count entities matching filters."""
        query = self.model_class.query
        for key, value in filters.items():
            query = query.filter(getattr(self.model_class, key) == value)
        return query.count()
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Bulk create entities."""
        entities = [self.model_class(**item) for item in items]
        db.session.bulk_save_objects(entities)
        db.session.commit()
        return entities
    
    def bulk_delete(self, ids: List[int]) -> int:
        """Bulk delete entities by IDs."""
        deleted_count = self.model_class.query.filter(
            self.model_class.id.in_(ids)
        ).delete(synchronize_session=False)
        db.session.commit()
        return deleted_count