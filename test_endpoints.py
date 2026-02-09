import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def test_register():
    print("Testing Registration...")
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "password123",
        "full_name": "Test User",
        "role": "developer"
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_login():
    print("\nTesting Login...")
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": "testuser",
        "password": "password123"
    }
    try:
        response = requests.post(url, data=data) # OAuth2 uses form data
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_register()
    test_login()
