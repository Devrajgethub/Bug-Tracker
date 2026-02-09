# backend/app/api/chat.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime
from .. import models, schemas, database
from ..core.security import get_current_user_token, get_user_from_token
from ..core.websocket import manager
import secrets
from datetime import timedelta
import os
import time

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/rooms/{room_id}/members", response_model=List[schemas.UserResponse])
def get_chat_room_members(
    room_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    is_member = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.room_id == room_id,
        models.ChatRoomMember.user_id == current_user.id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this chat room")

    members = db.query(models.User).join(
        models.ChatRoomMember,
        models.User.id == models.ChatRoomMember.user_id
    ).filter(
        models.ChatRoomMember.room_id == room_id
    ).all()
    return members

@router.post("/rooms/{room_id}/members")
def add_chat_room_members(
    room_id: int,
    body: schemas.ChatRoomMembersUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    db_room = db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    is_member = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.room_id == room_id,
        models.ChatRoomMember.user_id == current_user.id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this chat room")

    candidate_ids = list({int(user_id) for user_id in body.member_ids})
    
    if not candidate_ids:
        return {"added": 0}

    project_member_ids = db.query(models.ProjectMember.user_id).filter(
        models.ProjectMember.project_id == db_room.project_id,
        models.ProjectMember.user_id.in_(candidate_ids)
    ).all()
    project_member_ids = {row[0] for row in project_member_ids}

    existing_ids = db.query(models.ChatRoomMember.user_id).filter(
        models.ChatRoomMember.room_id == room_id,
        models.ChatRoomMember.user_id.in_(list(project_member_ids))
    ).all()
    existing_ids = {row[0] for row in existing_ids}

    to_add = [user_id for user_id in project_member_ids if user_id not in existing_ids]
    for user_id in to_add:
        db.add(models.ChatRoomMember(room_id=room_id, user_id=user_id))
    db.commit()

    return {"added": len(to_add)}

@router.post("/rooms", response_model=schemas.ChatRoom)
def create_chat_room(
    room: schemas.ChatRoomCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    # Check if user is a member of this project
    is_member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == room.project_id,
        models.ProjectMember.user_id == current_user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    
    db_room = models.ChatRoom(
        name=room.name,
        project_id=room.project_id,
        created_by_id=current_user.id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    
    # Determine which members to add
    if room.member_ids:
        # Verify these users are in the project
        project_members = db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == room.project_id,
            models.ProjectMember.user_id.in_(room.member_ids)
        ).all()
    else:
        # Add all project members to the room
        project_members = db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == room.project_id
        ).all()
    
    # Always ensure creator is added
    creator_included = False
    for member in project_members:
        if member.user_id == current_user.id:
            creator_included = True
        
        room_member = models.ChatRoomMember(
            room_id=db_room.id,
            user_id=member.user_id
        )
        db.add(room_member)
        
    if not creator_included and (not room.member_ids or current_user.id not in room.member_ids):
        # If creator was not in the list (or list was empty but creator not found for some reason), add them
        # Note: Creator must be a project member, which we checked at start.
        # But if room.member_ids was provided and creator was NOT in it, we should probably add them anyway
        # so they can see the room they created.
        room_member = models.ChatRoomMember(
            room_id=db_room.id,
            user_id=current_user.id
        )
        db.add(room_member)
    
    db.commit()
    
    return db_room

@router.get("/rooms", response_model=List[schemas.ChatRoom])
def get_chat_rooms(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    # Get all rooms where user is a member
    rooms = db.query(models.ChatRoom).join(
        models.ChatRoomMember,
        models.ChatRoom.id == models.ChatRoomMember.room_id
    ).filter(
        models.ChatRoomMember.user_id == current_user.id
    ).all()
    return rooms

@router.post("/dm", response_model=schemas.ChatRoom)
def start_direct_message(
    target_user_id: int,
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    # Verify both are project members
    me_member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == current_user.id
    ).first()
    target_member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == target_user_id
    ).first()
    if not me_member or not target_member:
        raise HTTPException(status_code=403, detail="Both users must be members of this project")
    # Find existing DM room between two users in this project
    existing_rooms = db.query(models.ChatRoom).filter(
        models.ChatRoom.project_id == project_id,
        models.ChatRoom.is_direct == True
    ).all()
    for room in existing_rooms:
        members = db.query(models.ChatRoomMember.user_id).filter(models.ChatRoomMember.room_id == room.id).all()
        member_ids = {row[0] for row in members}
        if member_ids == {current_user.id, target_user_id}:
            return room
    # Create new DM room
    name = f"DM:{current_user.id}:{target_user_id}"
    db_room = models.ChatRoom(
        name=name,
        project_id=project_id,
        created_by_id=current_user.id,
        is_direct=True
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    # Add both users
    db.add(models.ChatRoomMember(room_id=db_room.id, user_id=current_user.id))
    db.add(models.ChatRoomMember(room_id=db_room.id, user_id=target_user_id))
    db.commit()
    return db_room

@router.post("/rooms/{room_id}/invite-link")
def create_invite_link(
    room_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    room = db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    # Only members can create invite links
    is_member = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.room_id == room_id,
        models.ChatRoomMember.user_id == current_user.id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this chat room")
    # Create token
    token = secrets.token_urlsafe(16)
    invite = models.ChatRoomInvite(
        room_id=room_id,
        token=token,
        # Optional expiry, e.g., 7 days
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return {"token": invite.token, "invite_path": f"/api/chat/invite/{invite.token}"}

@router.post("/invite/{token}")
def accept_invite(
    token: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    invite = db.query(models.ChatRoomInvite).filter(models.ChatRoomInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Invite expired")
    room = db.query(models.ChatRoom).filter(models.ChatRoom.id == invite.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    # Must be a project member to join
    is_project_member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == room.project_id,
        models.ProjectMember.user_id == current_user.id
    ).first()
    if not is_project_member:
        raise HTTPException(status_code=403, detail="You must be a member of the project to join this room")
    # Add if not already a member
    existing = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.room_id == room.id,
        models.ChatRoomMember.user_id == current_user.id
    ).first()
    if not existing:
        db.add(models.ChatRoomMember(room_id=room.id, user_id=current_user.id))
        db.commit()
    return {"room_id": room.id, "joined": True}
@router.get("/rooms/{room_id}/messages", response_model=List[schemas.ChatMessage])
def get_chat_messages(
    room_id: int,
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    # Verify membership
    is_member = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.room_id == room_id,
        models.ChatRoomMember.user_id == current_user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this chat room")
        
    query = db.query(models.ChatMessage).join(
        models.User,
        models.ChatMessage.user_id == models.User.id
    ).filter(
        models.ChatMessage.room_id == room_id
    ).order_by(models.ChatMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    # Pydantic will handle nested user if relationship is present
    return query[::-1]

@router.post("/rooms/{room_id}/progress", response_model=schemas.ChatMessage)
def upload_progress_update(
    room_id: int,
    content: str = Form(""),
    file: UploadFile = File(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user_token)
):
    is_member = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.room_id == room_id,
        models.ChatRoomMember.user_id == current_user.id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this chat room")

    file_link = ""
    if file is not None:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "chat", str(room_id))
        os.makedirs(base_dir, exist_ok=True)
        ts = int(time.time())
        safe_name = f"progress_{ts}_{file.filename}"
        dest_path = os.path.join(base_dir, safe_name)
        with open(dest_path, "wb") as f:
            f.write(file.file.read())
        f_record = models.File(
            filename=safe_name,
            file_path=dest_path,
            content_type=file.content_type,
            project_id=None,
            folder_id=None,
            uploaded_by_id=current_user.id
        )
        db.add(f_record)
        db.commit()
        db.refresh(f_record)
        file_link = f"/api/files/{f_record.id}"

    msg_text = content.strip()
    if file_link:
        msg_text = (msg_text + "\n" + file_link).strip()

    db_message = models.ChatMessage(
        content=msg_text or "Progress update",
        room_id=room_id,
        user_id=current_user.id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = None
):
    db = database.SessionLocal()
    try:
        # Verify token
        try:
            user = get_user_from_token(token, db)
        except:
            await websocket.close(code=1008)
            return

        # Check if user is a member of this room
        is_member = db.query(models.ChatRoomMember).filter(
            models.ChatRoomMember.room_id == room_id,
            models.ChatRoomMember.user_id == user.id
        ).first()
        
        if not is_member:
            await websocket.close(code=1008)
            return
        
        await manager.connect_to_room(websocket, room_id, user.id)
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Save message to database
                db_message = models.ChatMessage(
                    content=message_data["content"],
                    room_id=room_id,
                    user_id=user.id
                )
                db.add(db_message)
                db.commit()
                db.refresh(db_message)
                
                # Broadcast to room members
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "message",
                        "id": db_message.id,
                        "content": db_message.content,
                        "user_id": user.id,
                        "username": user.username,
                        "created_at": db_message.created_at.isoformat()
                    }
                )
        except WebSocketDisconnect:
            manager.disconnect_from_room(websocket, room_id)
        except Exception as e:
            print(f"WebSocket error: {e}")
            manager.disconnect_from_room(websocket, room_id)
    finally:
        # काम खत्म होने पर database session को बंद करना ज़रूरी है
        db.close()
