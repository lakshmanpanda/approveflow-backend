# app/repositories/submission_repo.py
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.workflow import FormSubmission, ApprovalRequest

class SubmissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_submission(
        self, 
        template_id: UUID, 
        submitter_id: UUID, 
        form_data: Dict[str, Any], 
        is_draft: bool
    ) -> FormSubmission:
        """Handles both 'Save as Draft' and 'Submit' actions from the UI."""
        submission = FormSubmission(
            form_template_id=template_id,
            submitter_id=submitter_id,
            form_data=form_data,
            status="DRAFT" if is_draft else "PENDING"
        )
        self.db.add(submission)
        self.db.flush() # Flush to get the ID without committing the whole transaction yet
        return submission

    def update_submission_status(self, submission_id: UUID, new_status: str, current_stage_id: UUID = None):
        submission = self.db.query(FormSubmission).filter(FormSubmission.id == submission_id).first()
        if submission:
            submission.status = new_status
            if current_stage_id:
                submission.current_stage_id = current_stage_id
            self.db.add(submission)

    def create_approval_request(self, submission_id: UUID, stage_id: UUID, assigned_user_id: UUID) -> ApprovalRequest:
        request = ApprovalRequest(
            submission_id=submission_id,
            stage_id=stage_id,
            assigned_user_id=assigned_user_id,
            status="PENDING"
        )
        self.db.add(request)
        return request

    def get_pending_approvals_for_user(self, user_id: UUID) -> List[ApprovalRequest]:
        """Populates the 'My Approvals' dashboard in the UI."""
        return self.db.query(ApprovalRequest).filter(
            ApprovalRequest.assigned_user_id == user_id,
            ApprovalRequest.status == "PENDING"
        ).all()