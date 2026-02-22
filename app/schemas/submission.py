# app/schemas/submission.py
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime

class FormSubmissionCreate(BaseModel):
    form_template_id: UUID
    form_data: Dict[str, Any]
    is_draft: bool = False # From UI: "Save as Draft"

class FormSubmissionResponse(BaseModel):
    id: UUID
    form_template_id: UUID
    submitter_id: UUID
    form_data: Dict[str, Any]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ApprovalAction(BaseModel):
    action: str # "APPROVE", "REJECT"
    comments: Optional[str] = None