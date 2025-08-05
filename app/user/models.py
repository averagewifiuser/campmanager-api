from app.extensions import db
from app._shared.models import BaseModel
from app.extensions import bcrypt

class User(BaseModel):
    """User model for camp managers and volunteers"""
    __tablename__ = 'users'
    
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('camp_manager', 'volunteer', name='user_roles'), 
                    default='camp_manager', nullable=False)
    
    # Relationships
    camps = db.relationship('Camp', backref='manager', lazy=True, cascade='all, delete-orphan')
    # expenses = db.relationship('Expense', backref='manager', lazy=True)
    registration_links = db.relationship('RegistrationLink', backref='manager', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self, for_api=False):
        """Override to exclude password_hash"""
        data = super().to_dict(for_api=for_api)
        data.pop('password_hash', None)
        return data
