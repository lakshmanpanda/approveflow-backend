# app/services/document_service.py
import hashlib
import io
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from minio import Minio
from fastapi import HTTPException

from app.core.config import settings
from app.models.audit import Document
from app.models.workflow import FormSubmission
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.user_repo = UserRepository(db)
        self.bucket_name = "signed-documents"
        
        # Initialize MinIO Client
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # Ensure bucket exists
        if not self.minio_client.bucket_exists(self.bucket_name):
            self.minio_client.make_bucket(self.bucket_name)

        # Setup Jinja2 HTML Templates
        self.jinja_env = Environment(loader=FileSystemLoader("app/templates"))

    def generate_final_document(self, submission_id: UUID) -> Document:
        """Generates a tamper-evident PDF and uploads to MinIO."""
        
        # 1. Gather all necessary data
        submission = self.db.query(FormSubmission).filter(FormSubmission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        submitter = self.user_repo.get_by_id(submission.submitter_id)
        audit_trail = self.audit_service.get_timeline_for_submission(submission_id)

        # 2. Prepare data for the template
        template_data = {
            "submission_id": str(submission.id),
            "created_at": submission.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "submitter_name": submitter.full_name,
            "submitter_email": submitter.email,
            "form_data": submission.form_data,
            "audit_trail": [
                {
                    "action": log.action,
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "actor_name": self.user_repo.get_by_id(log.actor_id).full_name if log.actor_id else "System",
                } for log in audit_trail
            ]
        }

        # 3. Render HTML and Convert to PDF
        template = self.jinja_env.get_template("document_template.html")
        html_content = template.render(**template_data)
        
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        if pisa_status.err:
            raise HTTPException(status_code=500, detail="Failed to generate PDF document")
        pdf_bytes = pdf_file.getvalue()

        # 4. Cryptographic Hashing for Tamper Evidence
        doc_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # 5. Upload to MinIO
        object_key = f"{datetime.utcnow().year}/{datetime.utcnow().month}/{submission_id}.pdf"
        self.minio_client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_key,
            data=io.BytesIO(pdf_bytes),
            length=len(pdf_bytes),
            content_type="application/pdf"
        )

        # 6. Save Record to Database
        document_record = Document(
            submission_id=submission_id,
            minio_object_key=object_key,
            document_hash=doc_hash
        )
        self.db.add(document_record)
        
        # 7. Log the generation
        self.audit_service.log_action(
            entity_id=submission_id,
            entity_type="SUBMISSION",
            action="DOCUMENT_GENERATED"
        )
        
        self.db.commit()
        return document_record

    def get_presigned_download_url(self, submission_id: UUID) -> dict:
        """Generates a secure, temporary download link for the frontend."""
        document = self.db.query(Document).filter(Document.submission_id == submission_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not generated yet.")

        # URL expires in 1 hour
        url = self.minio_client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=document.minio_object_key,
            expires=timedelta(hours=1)
        )
        
        return {
            "download_url": url,
            "document_hash": document.document_hash,
            "expires_in_seconds": 3600
        }