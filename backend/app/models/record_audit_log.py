import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Index
from app.models.base import Base


class RecordAuditLog(Base):
    """
    Immutable audit history table recording all modifications to financial line items.
    Preserves exact historical values, timestamps, users, and change reasons.
    """
    __tablename__ = "record_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String(36), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # CREATE, UPDATE, DELETE, RESTORE
    changed_by = Column(String(100), nullable=False, index=True)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    old_values = Column(Text, nullable=True)  # JSON string of old fields
    new_values = Column(Text, nullable=True)  # JSON string of new fields
    reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_audit_record_time", "record_id", "changed_at"),
    )
