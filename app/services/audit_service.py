# app/services/audit_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.models.audit import AuditLog

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self, 
        entity_id: UUID, 
        entity_type: str, 
        action: str, 
        actor_id: Optional[UUID] = None, 
        snapshot: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Logs an immutable action. 
        entity_type: e.g., 'SUBMISSION', 'SYSTEM'
        action: e.g., 'SUBMITTED', 'APPROVED', 'DOCUMENT_GENERATED'
        """
        log_entry = AuditLog(
            entity_id=entity_id,
            entity_type=entity_type,
            action=action,
            actor_id=actor_id,
            snapshot=snapshot
        )
        self.db.add(log_entry)
        self.db.flush() # Flush so it's part of the current transaction
        return log_entry

    def get_timeline_for_submission(self, submission_id: UUID) -> list[AuditLog]:
        """Fetches the chronological history for the UI timeline."""
        return self.db.query(AuditLog).filter(
            AuditLog.entity_id == submission_id,
            AuditLog.entity_type == "SUBMISSION"
        ).order_by(AuditLog.timestamp.asc()).all()