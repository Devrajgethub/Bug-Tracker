import sys
import os
import requests

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000/api"

def test_login():
    print("Testing login with admin credentials...")
    login_data = {
        "username": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("Login Successful!")
            token = response.json()["access_token"]
            print(f"Token: {token[:20]}...")
            return token
        else:
            print("Login Failed.")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_login()
