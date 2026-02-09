import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def verify_theme_mode():
    print("--- Verifying Theme Mode ---")
    # Login as admin or existing user
    username = "admin_user"
    password = "password123"
    
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get User Profile
    # Assuming there is a 'me' endpoint or similar, let's check auth.py or user.py
    # Usually it's /users/me or /auth/me. Let's try to find it in previous search or guess.
    # Actually, let's look at list_users.py output, it showed user fields.
    # But via API is better.
    
    # Let's try to update user theme (if there is an update endpoint)
    # Or just check the schema response if we can fetch user.
    pass

def check_db_schema():
    print("--- Verifying DB Schema (Direct) ---")
    from sqlalchemy import create_engine, inspect
    from app.core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    columns = inspector.get_columns('users')
    theme_found = False
    for col in columns:
        if col['name'] == 'theme_mode':
            theme_found = True
            print(f"✅ Found column 'theme_mode' in 'users' table. Type: {col['type']}")
            break
    
    if not theme_found:
        print("❌ 'theme_mode' column NOT found in 'users' table.")

if __name__ == "__main__":
    check_db_schema()
