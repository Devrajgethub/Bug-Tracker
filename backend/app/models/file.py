# backend/app/models/file.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, backref
from ..database import Base
from datetime import datetime

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", backref=backref("folders", cascade="all, delete-orphan"))
    creator = relationship("User", backref="created_folders")
    parent = relationship("Folder", remote_side=[id])
    # Fixed warning by adding overlaps parameter
    children = relationship("Folder", overlaps="parent") 
    files = relationship("File", back_populates="folder", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", backref=backref("files", cascade="all, delete-orphan"))
    folder = relationship("Folder", back_populates="files")
    uploader = relationship("User", backref="uploaded_files", foreign_keys=[uploaded_by_id])
