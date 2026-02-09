# backend/app/models/ticket.py
import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, backref
from ..database import Base
from datetime import datetime

# Updated Enums to match frontend
class TicketStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"

class TicketType(str, enum.Enum):
    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(TicketStatus), default=TicketStatus.TODO)
    type = Column(SQLAlchemyEnum(TicketType), default=TicketType.TASK) # Added
    priority = Column(SQLAlchemyEnum(TicketPriority), default=TicketPriority.MEDIUM)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", backref=backref("tickets", cascade="all, delete-orphan"))
    assignee = relationship("User", foreign_keys=[assignee_id], backref="assigned_tickets")
    creator = relationship("User", foreign_keys=[created_by_id], backref="created_tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")

class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    user = relationship("User", backref="ticket_comments")
