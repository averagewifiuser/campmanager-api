
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String
import uuid

from app.extensions import db

class BaseModel(db.Model):
    """Base model with common fields and methods"""
    __abstract__ = True
    
    # Use String for better SQLite compatibility
    id = db.Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def save(self):
        """Save the current instance to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the current instance from database"""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """Update instance with provided kwargs"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return self
    
    def to_dict(self, for_api=False):
        """Convert model instance to dictionary
        
        Args:
            for_api (bool): If True, returns raw objects for API serialization.
                           If False, converts datetime and UUID to strings.
        """
       
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            try:
                if for_api:
                    # For API serialization, return raw objects for Marshmallow to handle
                    if isinstance(value, uuid.UUID):
                        result[column.name] = str(value)
                    else:
                        result[column.name] = value
                else:
                    # For general use, convert to strings
                    if isinstance(value, datetime):
                        result[column.name] = value.isoformat()
                    elif isinstance(value, uuid.UUID):
                        result[column.name] = str(value)
                    elif value is not None and hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')) and not isinstance(value, str):
                        # Handle datetime-like objects that might not be datetime instances, but exclude strings
                        try:
                            result[column.name] = value.isoformat()
                        except (AttributeError, TypeError):
                            result[column.name] = str(value)
                    else:
                        result[column.name] = value
            except Exception as e:
                print(value)
                print(f"Error converting column {column.name}: {str(e)}")
        return result
