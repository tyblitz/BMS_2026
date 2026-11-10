import uuid
from sqlalchemy import Column, String, Boolean
from app.models.base import Base, AuditMixin


class User(Base, AuditMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Role: 'school', 'sdo', 'region', 'admin'
    role = Column(String(50), nullable=False, default="school", index=True)
    
    # Scoping attributes
    school_name = Column(String(150), nullable=True, index=True) # Maps to OperatingUnit
    division = Column(String(150), nullable=True, index=True)    # Maps to Division
    region = Column(String(150), nullable=True, index=True)      # Maps to Region
    
    is_active = Column(Boolean, default=True, nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        kwargs.setdefault("is_active", True)
        super().__init__(**kwargs)


