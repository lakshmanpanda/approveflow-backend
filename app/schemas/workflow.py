# app/schemas/workflow.py
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Form Template ---
class FormTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    form_schema: Dict[str, Any] # The JSON schema for the dynamic form

class FormTemplateCreate(FormTemplateBase):
    pass

class FormTemplateResponse(FormTemplateBase):
    id: UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# --- Workflow Stages ---
class WorkflowStageBase(BaseModel):
    stage_order: int
    required_role: str
    conditions: Optional[Dict[str, Any]] = None

class WorkflowStageCreate(WorkflowStageBase):
    pass

class WorkflowStageResponse(WorkflowStageBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

# --- Workflow ---
class WorkflowBase(BaseModel):
    name: str
    form_template_id: UUID

class WorkflowCreate(WorkflowBase):
    stages: List[WorkflowStageCreate]

class WorkflowResponse(WorkflowBase):
    id: UUID
    stages: List[WorkflowStageResponse]
    model_config = ConfigDict(from_attributes=True)