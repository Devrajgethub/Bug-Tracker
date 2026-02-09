import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def create_or_update_user():
    username = "diwakar"
    password = "password123"
    email = "diwakar@example.com"
    
    print(f"Attempting to ensure user '{username}' exists...")
    
    # Try to login first to see if user exists and password works
    login_url = f"{BASE_URL}/auth/login"
    login_data = {"username": username, "password": password}
    
    try:
        response = requests.post(login_url, data=login_data)
        if response.status_code == 200:
            print(f"✅ User '{username}' already exists and password is correct.")
            print(f"👉 Username: {username}")
            print(f"👉 Password: {password}")
            return
        elif response.status_code == 401:
            print(f"User '{username}' exists but password might be different. (Or login failed)")
            # We can't easily reset password via API without admin endpoints or direct DB access
            # But let's try to register, maybe it doesn't exist?
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return

    # Try to register
    register_url = f"{BASE_URL}/auth/register"
    register_data = {
        "email": email,
        "username": username,
        "password": password,
        "full_name": "Diwakar User",
        "role": "developer" # or admin
    }
    
    try:
        response = requests.post(register_url, json=register_data)
        if response.status_code == 201:
            print(f"✅ User '{username}' created successfully!")
            print(f"👉 Username: {username}")
            print(f"👉 Password: {password}")
        elif response.status_code == 400:
            detail = response.json().get('detail', '')
            if "already registered" in detail:
                 print(f"⚠️ User '{username}' or email '{email}' already exists.")
                 print(f"If you forgot the password, please use the 'admin_user' / 'password123' account created earlier to manage users, or ask me to reset the database.")
            else:
                print(f"❌ Registration failed: {response.text}")
        else:
            print(f"❌ Registration failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Error during registration: {e}")

if __name__ == "__main__":
    create_or_update_user()
