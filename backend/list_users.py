import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("Users:")
        for u in users:
            print(f"id={u.id} email={u.email} username={u.username} role={u.role} active={u.is_active}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
