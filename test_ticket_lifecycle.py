import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"
USERNAME = "diwakar"
PASSWORD = "password123"

def get_auth_token():
    url = f"{BASE_URL}/auth/login"
    data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        sys.exit(1)
    return response.json()["access_token"]

def create_project(token):
    url = f"{BASE_URL}/projects/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Test Project", "description": "A project for testing tickets"}
    
    # Check if project exists or create one
    # For simplicity, just create and ignore if it fails (might duplicate if name not unique enforced? Schema doesn't show unique constraint on name, but let's see)
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201 or response.status_code == 200:
        return response.json()["id"]
    
    # If failed, maybe list projects and pick one
    response = requests.get(url, headers=headers)
    projects = response.json()
    if projects:
        return projects[0]["id"]
    
    print(f"Failed to create or find project: {response.text}")
    sys.exit(1)

def create_ticket(token, project_id):
    url = f"{BASE_URL}/tickets/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": "Test Ticket",
        "description": "Initial description",
        "project_id": project_id,
        "status": "todo",
        "type": "task",
        "priority": "medium"
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200 and response.status_code != 201:
        print(f"Failed to create ticket: {response.text}")
        sys.exit(1)
    print("Ticket created successfully.")
    return response.json()["id"]

def update_ticket(token, ticket_id):
    url = f"{BASE_URL}/tickets/{ticket_id}"
    headers = {"Authorization": f"Bearer {token}"}
    # Update only description and status
    data = {
        "description": "Updated description via refactored endpoint",
        "status": "in_progress"
    }
    response = requests.put(url, json=data, headers=headers)
    if response.status_code != 200:
        print(f"Failed to update ticket: {response.text}")
        sys.exit(1)
    
    updated_ticket = response.json()
    if updated_ticket["description"] == "Updated description via refactored endpoint" and updated_ticket["status"] == "in_progress":
        print("Ticket updated successfully (Refactor works!).")
    else:
        print("Ticket updated but values mismatch.")
        print(updated_ticket)

def main():
    print("Starting Ticket Lifecycle Test...")
    token = get_auth_token()
    print("Logged in.")
    
    project_id = create_project(token)
    print(f"Using Project ID: {project_id}")
    
    ticket_id = create_ticket(token, project_id)
    print(f"Created Ticket ID: {ticket_id}")
    
    update_ticket(token, ticket_id)
    print("Test Complete.")

if __name__ == "__main__":
    main()
