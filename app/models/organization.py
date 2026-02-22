# app/models/organization.py
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    positions = relationship("UserPosition", back_populates="user")
    submissions = relationship("FormSubmission", back_populates="submitter")

class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    region = Column(String) # e.g., "North America", "Global" from UI

    positions = relationship("Position", back_populates="department")

class Position(Base):
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    role_type = Column(String, nullable=False) # e.g., USER, MANAGER, HOD, ADMIN
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    parent_position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id"), nullable=True)

    department = relationship("Department", back_populates="positions")
    users = relationship("UserPosition", back_populates="position")

class UserPosition(Base):
    __tablename__ = "user_positions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id"), primary_key=True)
    start_date = Column(Date, nullable=True)
    
    user = relationship("User", back_populates="positions")
    position = relationship("Position", back_populates="users")