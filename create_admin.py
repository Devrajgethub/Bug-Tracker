import requests

BASE_URL = "http://127.0.0.1:8000/api"

def create_test_user():
    username = "admin_user"
    password = "password123"
    email = "admin@example.com"
    
    print(f"Creating user: {username} / {password}")
    
    payload = {
        "email": email,
        "username": username,
        "password": password,
        "full_name": "Admin User",
        "role": "admin"
    }
    
    try:
        # 1. Register
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        if response.status_code == 200:
            print("[SUCCESS] Registration successful!")
        elif response.status_code == 400 and "already registered" in response.text:
            print("[INFO] User already exists (that's fine).")
        else:
            print(f"[ERROR] Registration failed: {response.status_code} - {response.text}")
            return

        # 2. Login Check
        print("Verifying login...")
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": username, "password": password} # Form data for OAuth2
        )
        
        if login_response.status_code == 200:
            print("[SUCCESS] Login Verified!")
            print(f"Token received: {login_response.json().get('access_token')[:20]}...")
            print("\nPLEASE USE THESE CREDENTIALS IN THE BROWSER:")
            print(f"Username: {username}")
            print(f"Password: {password}")
        else:
            print(f"[FAIL] Login failed during verification: {login_response.status_code}")
            print(login_response.text)

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    create_test_user()
