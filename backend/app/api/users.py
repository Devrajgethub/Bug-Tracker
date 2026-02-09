from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{username}", response_model=UserResponse)
def get_user_profile(username: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == username).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u

@router.get("/search")
def search_users(query: str, db: Session = Depends(get_db)):
    q = db.query(User).filter(User.username.ilike(f"%{query}%")).limit(10).all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role} for u in q]
