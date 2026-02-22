# app/services/workflow_engine.py (Part A)
from typing import Dict, Any

class ConditionEvaluator:
    """Safely evaluates JSON logic against form submission data."""
    
    OPERATORS = {
        ">": lambda x, y: float(x) > float(y) if x is not None and y is not None else False,
        "<": lambda x, y: float(x) < float(y) if x is not None and y is not None else False,
        ">=": lambda x, y: float(x) >= float(y) if x is not None and y is not None else False,
        "<=": lambda x, y: float(x) <= float(y) if x is not None and y is not None else False,
        "==": lambda x, y: str(x).lower() == str(y).lower(),
        "!=": lambda x, y: str(x).lower() != str(y).lower(),
        "IN": lambda x, y: x in y if isinstance(y, list) else False
    }

    @classmethod
    def evaluate(cls, conditions: Dict[str, Any], form_data: Dict[str, Any]) -> bool:
        """
        Example conditions: {"leave_days": {">": 3}, "category": {"==": "SICK"}}
        If it returns True, the stage is REQUIRED.
        If it returns False, the stage is SKIPPED.
        """
        if not conditions:
            return True # No conditions means the stage is always required

        for field, check in conditions.items():
            user_value = form_data.get(field)
            
            for op_symbol, threshold in check.items():
                if op_symbol not in cls.OPERATORS:
                    raise ValueError(f"Unknown operator strictly forbidden: {op_symbol}")
                
                # If any condition fails, the whole block evaluates to False
                if not cls.OPERATORS[op_symbol](user_value, threshold):
                    return False
                    
        return True # All conditions passed

# app/services/workflow_engine.py (Part B)
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.workflow_repo import WorkflowRepository
from app.repositories.submission_repo import SubmissionRepository
from app.services.org_service import OrgService
from app.models.workflow import FormSubmission, ApprovalRequest
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService

class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.wf_repo = WorkflowRepository(db)
        self.sub_repo = SubmissionRepository(db)
        self.org_service = OrgService(db)

    def process_new_submission(self, submitter_id: UUID, template_id: UUID, form_data: dict, is_draft: bool):
        """Called when user clicks 'Submit' or 'Save as Draft' in the UI."""
        # 1. Create the base record
        submission = self.sub_repo.create_submission(template_id, submitter_id, form_data, is_draft)
        
        # 2. If it's a draft, stop here.
        if is_draft:
            self.db.commit()
            return submission

        # 3. If it's a real submission, start the engine!
        self._advance_workflow(submission)
        self.db.commit()
        return submission

    def process_approval(self, approval_request_id: UUID, actor_id: UUID, action: str, comments: str = None):
        """Called when a Manager clicks 'Approve' or 'Reject' in the UI."""
        req = self.db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_request_id).first()
        
        if not req or req.status != "PENDING":
            raise HTTPException(status_code=400, detail="Request is invalid or already processed.")
        if req.assigned_user_id != actor_id:
            raise HTTPException(status_code=403, detail="You are not authorized to approve this step.")

        # Update the request
        req.status = "APPROVED" if action == "APPROVE" else "REJECTED"
        req.action_timestamp = datetime.utcnow()
        # Note: In Part 5, we will add Audit Logging here for the `comments`.

        submission = req.submission

        if action == "REJECTED":
            self.sub_repo.update_submission_status(submission.id, "REJECTED")
            self.db.commit()
            return {"message": "Submission rejected. Workflow terminated."}

        # If approved, move to the next stage
        self._advance_workflow(submission, current_stage_id=req.stage_id)
        self.db.commit()
        return {"message": "Approved successfully. Advanced to next stage."}

    def _advance_workflow(self, submission: FormSubmission, current_stage_id: UUID = None):
        """
        The Brain: Figures out what happens next.
        """
        # 1. Get the workflow blueprint
        workflow = self.wf_repo.get_workflow_for_template(submission.form_template_id)
        if not workflow:
            raise HTTPException(status_code=500, detail="No workflow attached to this form.")

        # 2. Fetch all stages sequentially
        stages = self.wf_repo.get_workflow_stages(workflow.id)
        
        # 3. Determine the *next* stage to evaluate
        next_stage_index = 0
        if current_stage_id:
            for idx, stage in enumerate(stages):
                if stage.id == current_stage_id:
                    next_stage_index = idx + 1
                    break

        # 4. Recursively evaluate upcoming stages until one passes its conditions
        while next_stage_index < len(stages):
            target_stage = stages[next_stage_index]
            
            # Evaluate JSON logic (e.g., leave_days > 3)
            is_required = ConditionEvaluator.evaluate(target_stage.conditions, submission.form_data)
            
            if is_required:
                # Logic passed! We must route to this stage.
                approver_id = self.org_service.get_approver_for_user(
                    submitter_id=submission.submitter_id,
                    required_role=target_stage.required_role
                )
                
                # Create the inbox item for the manager
                self.sub_repo.create_approval_request(submission.id, target_stage.id, approver_id)
                self.sub_repo.update_submission_status(submission.id, "PENDING", target_stage.id)
                return # Exit loop, waiting for human action

            # If condition failed (e.g., leave_days is only 2), skip this stage and check the next one.
            next_stage_index += 1

        # 5. If we loop through all stages and none are left to process, the workflow is COMPLETE.
        self.sub_repo.update_submission_status(submission.id, "COMPLETED")

        # Log the completion securely
        audit_service = AuditService(self.db)
        audit_service.log_action(
            entity_id=submission.id, 
            entity_type="SUBMISSION", 
            action="COMPLETED", 
            snapshot=submission.form_data
        )

        # Generate the final tamper-proof PDF in MinIO
        doc_service = DocumentService(self.db)
        doc_service.generate_final_document(submission.id)