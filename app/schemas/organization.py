# app/schemas/organization.py
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List

# --- Department ---
class DepartmentBase(BaseModel):
    name: str
    region: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

# --- Position ---
class PositionBase(BaseModel):
    title: str
    role_type: str # USER, MANAGER, HOD, ADMIN
    department_id: UUID
    parent_position_id: Optional[UUID] = None

class PositionCreate(PositionBase):
    pass

class PositionResponse(PositionBase):
    id: UUID
    department: DepartmentResponse
    model_config = ConfigDict(from_attributes=True)