# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base
from .enums import UserRole

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    theme_mode = Column(String, default="light") # light or dark
    avatar_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    resume_file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    certificate_file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    # Remove these lines:
    # created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owned_projects = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user")
    resume_file = relationship("File", foreign_keys=[resume_file_id], uselist=False)
    certificate_file = relationship("File", foreign_keys=[certificate_file_id], uselist=False)
