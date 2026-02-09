# backend/app/api/tickets.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models import (
    User, Project, Ticket, TicketComment, ProjectMember, 
    TicketStatus, TicketType, TicketPriority, UserRole
)
from app.schemas import (
    Ticket as TicketSchema, 
    TicketCreate, 
    TicketUpdate,
    TicketComment as TicketCommentSchema,
    TicketCommentCreate
)
from app.core.security import get_current_user

router = APIRouter(prefix="/tickets", tags=["tickets"])

def check_ticket_permission(db: Session, project_id: int, user_id: int):
    # Check if user is system admin
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == UserRole.ADMIN:
        return True

    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project"
        )
    return membership

@router.get("/", response_model=List[TicketSchema])
def read_tickets(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = Query(None),
    status: Optional[TicketStatus] = Query(None),
    type: Optional[TicketType] = Query(None),
    priority: Optional[TicketPriority] = Query(None),
    assignee_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Ticket).options(
        joinedload(Ticket.creator),
        joinedload(Ticket.assignee),
        joinedload(Ticket.comments).joinedload(TicketComment.user)
    )
    
    if project_id:
        check_ticket_permission(db, project_id, current_user.id)
        query = query.filter(Ticket.project_id == project_id)
    else:
        # If no project specified, return tickets from all projects user is member of
        if current_user.role != UserRole.ADMIN:
            project_ids = db.query(ProjectMember.project_id).filter(
                ProjectMember.user_id == current_user.id
            ).all()
            project_ids = [p[0] for p in project_ids]
            
            if not project_ids:
                return []
            
            query = query.filter(Ticket.project_id.in_(project_ids))
    
    if status:
        query = query.filter(Ticket.status == status)
    if type:
        query = query.filter(Ticket.type == type)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if assignee_id:
        query = query.filter(Ticket.assignee_id == assignee_id)
    if search:
        query = query.filter(
            Ticket.title.ilike(f"%{search}%") | 
            Ticket.description.ilike(f"%{search}%")
        )
    
    tickets = query.offset(skip).limit(limit).all()
    
    return tickets

@router.post("/", response_model=TicketSchema)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_ticket_permission(db, ticket.project_id, current_user.id)
    
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        type=ticket.type,
        priority=ticket.priority,
        project_id=ticket.project_id,
        assignee_id=ticket.assignee_id,
        created_by_id=current_user.id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("/{ticket_id}", response_model=TicketSchema)
def read_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    check_ticket_permission(db, ticket.project_id, current_user.id)
    return ticket

@router.put("/{ticket_id}", response_model=TicketSchema)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Check general permission
    check_ticket_permission(db, ticket.project_id, current_user.id)
    
    # Additional update permission logic could go here (e.g., only creator/assignee/admin)
    # For now, allow any member to update
    
    # Get the update data, but only include fields that were actually sent in the request
    update_data = ticket_update.model_dump(exclude_unset=True)

    # Loop through the update data and apply it to the ticket object
    for field, value in update_data.items():
        setattr(ticket, field, value)
        
    db.commit()
    db.refresh(ticket)
    return ticket

@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Check permission
    check_ticket_permission(db, ticket.project_id, current_user.id)
    
    # Only creator or admin should delete
    if ticket.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        # Check if user is project admin
        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == ticket.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        
        if not membership or membership.role != UserRole.ADMIN:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only ticket creator or project admin can delete ticket"
            )

    db.delete(ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}

@router.post("/{ticket_id}/comments", response_model=TicketCommentSchema)
def create_comment(
    ticket_id: int,
    comment: TicketCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    check_ticket_permission(db, ticket.project_id, current_user.id)
    
    db_comment = TicketComment(
        content=comment.content,
        ticket_id=ticket_id,
        user_id=current_user.id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/{ticket_id}/comments", response_model=List[TicketCommentSchema])
def read_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    check_ticket_permission(db, ticket.project_id, current_user.id)
    
    comments = db.query(TicketComment).filter(
        TicketComment.ticket_id == ticket_id
    ).order_by(TicketComment.created_at.asc()).all()
    
    return comments
