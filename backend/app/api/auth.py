# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta 
from app.database import get_db
from app.models.user import User
from app.models.file import File as FileModel
from app.schemas import Token, UserCreate, UserResponse, UserUpdate
from app.core.security import authenticate_user, create_access_token, get_password_hash
from app.core.config import settings
from .deps import get_current_active_user
import os
import time

# यहाँ पर "/auth" prefix जोड़ा गया है
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user_username = db.query(User).filter(User.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # --- DEBUGGING PRINTS ---
    print(f"🔍 DEBUG: Login attempt received for username: '{form_data.username}'")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        print(f"❌ DEBUG: Authentication FAILED for user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    print(f"✅ DEBUG: Authentication SUCCESSFUL for user '{user.username}'")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if user_update.email and user_update.email != current_user.email:
        db_user = db.query(User).filter(User.email == user_update.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = user_update.email
    
    if user_update.full_name:
        current_user.full_name = user_update.full_name
        
    if user_update.theme_mode:
        current_user.theme_mode = user_update.theme_mode
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    if user_update.description is not None:
        current_user.description = user_update.description
        
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/upload", response_model=dict)
def upload_profile_file(
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if file_type not in ("resume", "certificate"):
        raise HTTPException(status_code=400, detail="Invalid file_type")
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "users", str(current_user.id))
    os.makedirs(base_dir, exist_ok=True)
    ts = int(time.time())
    safe_name = f"{file_type}_{ts}_{file.filename}"
    dest_path = os.path.join(base_dir, safe_name)
    
    with open(dest_path, "wb") as f:
        f.write(file.file.read())
    
    f_record = FileModel(
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
    
    if file_type == "resume":
        current_user.resume_file_id = f_record.id
    else:
        current_user.certificate_file_id = f_record.id
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return {"file_id": f_record.id}

@router.post("/me/upload-avatar", response_model=UserResponse)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "users", str(current_user.id))
    os.makedirs(base_dir, exist_ok=True)
    ts = int(time.time())
    safe_name = f"avatar_{ts}_{file.filename}"
    dest_path = os.path.join(base_dir, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file.file.read())
    f_record = FileModel(
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
    current_user.avatar_url = f"/api/files/{f_record.id}"
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
