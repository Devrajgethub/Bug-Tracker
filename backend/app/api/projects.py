# backend/app/api/projects.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Project, ProjectMember, UserRole
from app.schemas import (
    Project as ProjectSchema, 
    ProjectCreate, 
    ProjectUpdate,
    ProjectMemberCreate,
    UserResponse
)
from app.core.security import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

def check_project_permission(db: Session, project_id: int, user_id: int, required_role: UserRole = None):
    # Check if user is system admin
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == UserRole.ADMIN:
        return True # System admin has access to everything

    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project"
        )

    if required_role and membership.role != required_role:
        # Check hierarchy if needed, but for now simple equality
        # Or maybe allow if role is "higher"?
        # For simplicity, strict check or if required is ADMIN, only ADMIN.
        pass
        
    return membership

@router.get("/", response_model=List[ProjectSchema])
def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN:
        projects = db.query(Project).offset(skip).limit(limit).all()
    else:
        # Get projects where user is a member
        project_ids = db.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == current_user.id
        ).all()
        project_ids = [p[0] for p in project_ids]
        
        projects = db.query(Project).filter(
            Project.id.in_(project_ids)
        ).offset(skip).limit(limit).all()
    
    return projects

@router.post("/", response_model=ProjectSchema)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_project = Project(
        name=project.name,
        description=project.description,
        owner_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Add creator as admin member
    creator_role = project.creator_role or UserRole.ADMIN
    
    member = ProjectMember(
        project_id=db_project.id,
        user_id=current_user.id,
        role=creator_role
    )
    db.add(member)
    db.commit()
    
    return db_project

@router.get("/{project_id}", response_model=ProjectSchema)
def read_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    check_project_permission(db, project_id, current_user.id)
    return project

@router.put("/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Only Admin members can update
    # We need to get the membership to check role
    membership = check_project_permission(db, project_id, current_user.id)
    if membership is not True and membership.role != UserRole.ADMIN:
         raise HTTPException(status_code=403, detail="Only project admins can update project")
    
    if project_update.name:
        project.name = project_update.name
    if project_update.description:
        project.description = project_update.description
        
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Only Owner or System Admin can delete
    if project.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete project"
        )
        
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/members", response_model=List[UserResponse])
def read_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    check_project_permission(db, project_id, current_user.id)
    
    # Query User and their Project Role
    results = db.query(User, ProjectMember.role).join(
        ProjectMember,
        User.id == ProjectMember.user_id
    ).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    members = []
    for user, role in results:
        # Construct response with project-specific role
        member = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "theme_mode": user.theme_mode,
            "role": role
        }
        members.append(member)
    
    return members

@router.post("/{project_id}/members", response_model=UserResponse)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions
    membership = check_project_permission(db, project_id, current_user.id)
    
    # Allow ADMIN and MANAGER to add members
    is_admin_or_manager = False
    if membership is True: # System Admin
        is_admin_or_manager = True
    elif membership.role in [UserRole.ADMIN, UserRole.MANAGER]:
        is_admin_or_manager = True
        
    if not is_admin_or_manager:
         raise HTTPException(status_code=403, detail="Only project admins/managers can add members")

    # Find user to add
    user_to_add = db.query(User).filter(User.username == member_data.username).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already member
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_to_add.id
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    new_member = ProjectMember(
        project_id=project_id,
        user_id=user_to_add.id,
        role=member_data.role
    )
    db.add(new_member)
    db.commit()
    
    return user_to_add
