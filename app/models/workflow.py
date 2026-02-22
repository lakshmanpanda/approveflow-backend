# app/models/workflow.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class FormTemplate(Base):
    __tablename__ = "form_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    form_schema = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)

    workflows = relationship("Workflow", back_populates="template")

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_template_id = Column(UUID(as_uuid=True), ForeignKey("form_templates.id"))
    name = Column(String, nullable=False)

    template = relationship("FormTemplate", back_populates="workflows")
    stages = relationship("WorkflowStage", back_populates="workflow", order_by="WorkflowStage.stage_order")

class WorkflowStage(Base):
    __tablename__ = "workflow_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    stage_order = Column(Integer, nullable=False)
    required_role = Column(String, nullable=False) # e.g., "MANAGER"
    conditions = Column(JSONB, nullable=True) # e.g., {"leave_days": {">": 3}}

    workflow = relationship("Workflow", back_populates="stages")

class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_template_id = Column(UUID(as_uuid=True), ForeignKey("form_templates.id"))
    submitter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    form_data = Column(JSONB, nullable=False)
    status = Column(String, default="DRAFT") # DRAFT, PENDING, APPROVED, REJECTED, COMPLETED
    current_stage_id = Column(UUID(as_uuid=True), ForeignKey("workflow_stages.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submitter = relationship("User", back_populates="submissions")
    approval_requests = relationship("ApprovalRequest", back_populates="submission")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("form_submissions.id"))
    stage_id = Column(UUID(as_uuid=True), ForeignKey("workflow_stages.id"))
    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    action_timestamp = Column(DateTime, nullable=True)

    submission = relationship("FormSubmission", back_populates="approval_requests")

