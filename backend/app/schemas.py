# backend/app/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from .models.user import UserRole
from .models.ticket import TicketStatus, TicketType, TicketPriority

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    theme_mode: Optional[str] = "light"
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    resume_file_id: Optional[int] = None
    certificate_file_id: Optional[int] = None

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    theme_mode: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    role: UserRole

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: UserRole
    # Override theme_mode to ensure it's not None in response
    theme_mode: str = "light"

    @field_validator("theme_mode", mode="before")
    @classmethod
    def set_theme_mode(cls, v):
        return v or "light"

    model_config = ConfigDict(from_attributes=True)

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    creator_role: Optional[UserRole] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectMemberCreate(BaseModel):
    username: str
    role: UserRole = UserRole.USER

class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Ticket Schemas
class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TicketStatus = TicketStatus.TODO
    type: TicketType = TicketType.TASK
    priority: TicketPriority = TicketPriority.MEDIUM

class TicketCreate(TicketBase):
    project_id: int
    assignee_id: Optional[int] = None

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    type: Optional[TicketType] = None
    priority: Optional[TicketPriority] = None
    assignee_id: Optional[int] = None

class TicketCommentBase(BaseModel):
    content: str

class TicketCommentCreate(TicketCommentBase):
    pass

class TicketComment(TicketCommentBase):
    id: int
    ticket_id: int
    user_id: int
    created_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)

class Ticket(TicketBase):
    id: int
    project_id: int
    assignee_id: Optional[int] = None
    created_by_id: int
    created_at: datetime
    creator: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    comments: List[TicketComment] = []

    model_config = ConfigDict(from_attributes=True)

# Chat Schemas
class ChatRoomBase(BaseModel):
    name: str

class ChatRoomCreate(ChatRoomBase):
    project_id: int
    member_ids: Optional[List[int]] = None # List of user IDs to add to the room

class ChatRoomMembersUpdate(BaseModel):
    member_ids: List[int]

class ChatRoom(ChatRoomBase):
    id: int
    project_id: int
    created_by_id: int
    created_at: datetime
    is_direct: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    room_id: int

class ChatMessage(ChatMessageBase):
    id: int
    room_id: int
    user_id: int
    created_at: datetime
    user: Optional[UserResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# Auth Schema
class Token(BaseModel):
    access_token: str
    token_type: str
