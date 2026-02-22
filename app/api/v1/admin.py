# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.audit import AuditLog
from app.models.organization import User, Department, Position
from app.models.workflow import FormTemplate, Workflow, WorkflowStage, FormSubmission
from app.schemas.organization import DepartmentCreate, PositionCreate
from app.schemas.workflow import FormTemplateCreate, WorkflowCreate

router = APIRouter()

# --- Organization Management ---
@router.post("/departments")
def create_department(
    dept_in: DepartmentCreate, 
    db: Session = Depends(get_db), 
    current_admin=Depends(get_current_admin_user)
):
    dept = Department(**dept_in.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@router.post("/positions")
def create_position(
    pos_in: PositionCreate, 
    db: Session = Depends(get_db), 
    current_admin=Depends(get_current_admin_user)
):
    position = Position(**pos_in.model_dump())
    db.add(position)
    db.commit()
    db.refresh(position)
    return position

# --- Forms & Workflows Management ---
@router.post("/forms")
def create_form_template(
    form_in: FormTemplateCreate, 
    db: Session = Depends(get_db), 
    current_admin=Depends(get_current_admin_user)
):
    template = FormTemplate(**form_in.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.post("/workflows")
def create_workflow(
    workflow_in: WorkflowCreate, 
    db: Session = Depends(get_db), 
    current_admin=Depends(get_current_admin_user)
):
    # Create the workflow container
    workflow = Workflow(name=workflow_in.name, form_template_id=workflow_in.form_template_id)
    db.add(workflow)
    db.flush()

    # Create the conditional stages
    for stage_in in workflow_in.stages:
        stage = WorkflowStage(
            workflow_id=workflow.id,
            **stage_in.model_dump()
        )
        db.add(stage)
        
    db.commit()
    db.refresh(workflow)
    return workflow

from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.models.organization import User, UserPosition

@router.post("/users")
def create_employee(
    user_in: UserCreate, 
    position_id: UUID, 
    db: Session = Depends(get_db), 
    current_admin=Depends(get_current_admin_user)
):
    """Admin creates a user and assigns them to a position."""
    # 1. Create User
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True
    )
    db.add(new_user)
    db.flush() # Get the new_user.id

    # 2. Assign to Position
    user_pos = UserPosition(user_id=new_user.id, position_id=position_id)
    db.add(user_pos)
    
    db.commit()
    return {"message": f"User {new_user.full_name} created successfully!"}

@router.get("/users")
def get_all_users(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fetch all users in the system for the Admin Directory."""
    users = db.query(User).order_by(User.email).all()
    # Notice we aren't returning passwords!
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "is_admin": u.is_admin, "is_active": u.is_active} for u in users]

@router.get("/departments")
def get_all_departments(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fetch all organizational departments."""
    return db.query(Department).all()

@router.get("/positions")
def get_all_positions(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fetch all job positions and their hierarchy."""
    return db.query(Position).all()

@router.get("/forms")
def get_all_forms(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fetch all form templates (both active and draft)."""
    return db.query(FormTemplate).all()

@router.get("/workflows")
def get_all_workflows(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fetch all workflow routing engines."""
    return db.query(Workflow).all()

@router.get("/audit-logs")
def get_audit_logs(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fetch the latest 100 immutable audit logs for the platform."""
    # Using 'timestamp' for ordering
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    
    result = []
    for log in logs:
        # Using 'actor_id' to find the user
        user = None
        if log.actor_id:
            user = db.query(User).filter(User.id == log.actor_id).first()
            
        # Create a brief description from the snapshot for the UI
        desc_text = f"{log.action} performed on {log.entity_type}"
        if log.snapshot:
            # Just grab a preview of the JSON snapshot
            desc_text = str(log.snapshot)[:60] + "..." if len(str(log.snapshot)) > 60 else str(log.snapshot)

        result.append({
            "id": str(log.id),
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            "actor": user.full_name if user else "System",
            "role": "Admin/System" if not user else ("Super Admin" if user.is_admin else "User"),
            "action": log.action,
            "type": log.entity_type,  # Mapping to the UI's 'type' field
            "entity_id": str(log.entity_id)[:8].upper(), # Truncating UUID for the table
            "desc": desc_text
        })
    return result

@router.get("/stats")
def get_admin_dashboard_stats(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fetch live dashboard metrics."""
    # Count active users
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # Count requests sitting in PENDING state
    open_requests = db.query(FormSubmission).filter(FormSubmission.status == "PENDING").count()
    
    # Calculate completion rate
    total_requests = db.query(FormSubmission).count()
    completed_requests = db.query(FormSubmission).filter(FormSubmission.status == "COMPLETED").count()
    completion_rate = round((completed_requests / total_requests * 100), 1) if total_requests > 0 else 0

    return {
        "total_users": total_users,
        "open_requests": open_requests,
        "overdue_approvals": 0, # Setting to 0 for now unless you want complex datetime math
        "completion_rate": f"{completion_rate}%"
    }