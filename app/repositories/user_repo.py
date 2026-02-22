# app/repositories/user_repo.py
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.organization import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: UUID) -> User:
        return self.db.query(User).filter(User.id == user_id).first()