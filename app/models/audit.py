# app/models/audit.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), nullable=False) # Polymorphic (Submission ID, User ID, etc.)
    entity_type = Column(String, nullable=False) # "SUBMISSION", "SYSTEM", "APPROVAL"
    action = Column(String, nullable=False) # "SUBMIT", "APPROVE", "DOCUMENT_GENERATED"
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    snapshot = Column(JSONB, nullable=True) # Immutable record at the time

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("form_submissions.id"))
    minio_object_key = Column(String, nullable=False)
    document_hash = Column(String, nullable=False)