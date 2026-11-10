from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base


class CustomBase:
    def __init__(self, **kwargs):
        if "is_deleted" not in kwargs:
            kwargs["is_deleted"] = False
        if "created_on" not in kwargs:
            kwargs["created_on"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)


Base = declarative_base(cls=CustomBase)


class AuditMixin:
    """Mandatory Audit Trail & Soft-Delete Mixin for all entity tables."""
    created_on = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(100), default="system", nullable=False)
    
    edited_on = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))
    edited_by = Column(String(100), nullable=True)
    
    deleted_on = Column(DateTime, nullable=True)
    deleted_by = Column(String(100), nullable=True)
    
    is_deleted = Column(Boolean, default=False, server_default="0", nullable=False, index=True)

    def soft_delete(self, username: str):
        self.is_deleted = True
        self.deleted_on = datetime.now(timezone.utc)
        self.deleted_by = username

