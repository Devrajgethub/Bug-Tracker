import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings
from app.core.security import verify_password, get_password_hash

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_admin():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if user:
            print(f"User found: {user.username} (ID: {user.id})")
            print(f"Role: {user.role}")
            
            # Check password
            is_valid = verify_password("admin123", user.hashed_password)
            print(f"Password 'admin123' valid: {is_valid}")
            
            if not is_valid:
                print("Resetting password to 'admin123'...")
                user.hashed_password = get_password_hash("admin123")
                db.commit()
                print("Password reset.")
        else:
            print("User 'admin@example.com' not found.")
            # Create user if not exists (optional, but good for dev)
            print("Creating admin user...")
            new_user = User(
                email="admin@example.com",
                username="admin",
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print("Admin user created.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
