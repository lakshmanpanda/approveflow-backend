# app/repositories/workflow_repo.py
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional

from app.models.workflow import FormTemplate, Workflow, WorkflowStage

class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_form_template(self, template_id: UUID) -> Optional[FormTemplate]:
        return self.db.query(FormTemplate).filter(FormTemplate.id == template_id).first()

    def get_active_form_templates(self) -> list[FormTemplate]:
        return self.db.query(FormTemplate).filter(FormTemplate.is_active == True).all()

    def get_workflow_for_template(self, template_id: UUID) -> Optional[Workflow]:
        return self.db.query(Workflow).filter(Workflow.form_template_id == template_id).first()

    def get_workflow_stages(self, workflow_id: UUID) -> list[WorkflowStage]:
        """Returns the stages ordered correctly (Stage 1, Stage 2, etc.)."""
        return self.db.query(WorkflowStage).filter(
            WorkflowStage.workflow_id == workflow_id
        ).order_by(WorkflowStage.stage_order.asc()).all()