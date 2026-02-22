# app/api/v1/submissions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.organization import User
from app.models.workflow import FormSubmission
from app.schemas.submission import FormSubmissionCreate, ApprovalAction
from app.services.workflow_engine import WorkflowService
from app.services.document_service import DocumentService
from app.services.audit_service import AuditService
from app.repositories.submission_repo import SubmissionRepository
from app.repositories.workflow_repo import WorkflowRepository

router = APIRouter()

@router.get("/forms/active")
def get_active_forms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns available forms for the user to submit (e.g., Leave Request, Procurement)."""
    repo = WorkflowRepository(db)
    return repo.get_active_form_templates()

@router.post("/")
def submit_form(
    submission_in: FormSubmissionCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """User submits a new form or saves as draft."""
    wf_service = WorkflowService(db)
    submission = wf_service.process_new_submission(
        submitter_id=current_user.id,
        template_id=submission_in.form_template_id,
        form_data=submission_in.form_data,
        is_draft=submission_in.is_draft
    )
    return {"message": "Success", "submission_id": submission.id, "status": submission.status}

@router.get("/my-requests")
def get_my_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Populates the 'My Requests' datatable in the frontend dashboard."""
    return db.query(FormSubmission).filter(FormSubmission.submitter_id == current_user.id).all()

@router.get("/pending-approvals")
def get_pending_approvals(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Populates the 'My Approvals' inbox for managers/HODs."""
    repo = SubmissionRepository(db)
    approvals = repo.get_pending_approvals_for_user(current_user.id)
    return [
        {
            "approval_request_id": app.id,
            "submission_id": app.submission.id,
            "form_data": app.submission.form_data,
            "submitter": app.submission.submitter.full_name,
            "assigned_at": app.action_timestamp
        } for app in approvals
    ]

@router.post("/approvals/{approval_id}/action")
def process_approval_action(
    approval_id: UUID,
    action_in: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manager approves or rejects a request."""
    wf_service = WorkflowService(db)
    result = wf_service.process_approval(
        approval_request_id=approval_id,
        actor_id=current_user.id,
        action=action_in.action,
        comments=action_in.comments
    )
    return result

@router.get("/{submission_id}/timeline")
def get_submission_timeline(
    submission_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Fetches the immutable audit trail for the visual timeline UI."""
    audit_svc = AuditService(db)
    return audit_svc.get_timeline_for_submission(submission_id)

@router.get("/{submission_id}/download")
def download_final_document(
    submission_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Returns a temporary MinIO pre-signed URL for the generated PDF."""
    doc_svc = DocumentService(db)
    return doc_svc.get_presigned_download_url(submission_id)