from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from app.main import app
from app.database import Base, get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.models.project import Project, ProjectMember
from app.models.ticket import Ticket, TicketStatus, TicketType, TicketPriority

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock user
mock_user = User(
    id=1,
    email="test@example.com",
    username="testuser",
    full_name="Test User",
    hashed_password="hashed_secret",
    role=UserRole.USER,
    is_active=True
)

def override_get_current_user():
    return mock_user

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test user in DB (so foreign keys work)
    # Use merge to avoid session attachment issues with global object
    db.merge(mock_user)
    
    # Create a project
    project = Project(id=1, name="Test Project", description="Test Desc", owner_id=1)
    db.add(project)
    
    # Add member
    member = ProjectMember(project_id=1, user_id=1, role=UserRole.ADMIN)
    db.add(member)
    
    # Create a ticket
    ticket = Ticket(
        id=1,
        title="Test Ticket",
        description="Test Ticket Desc",
        project_id=1,
        created_by_id=1,
        status=TicketStatus.TODO,
        type=TicketType.TASK,
        priority=TicketPriority.MEDIUM
    )
    db.add(ticket)
    
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)

def test_create_comment():
    response = client.post(
        "/api/tickets/1/comments",
        json={"content": "This is a test comment"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "This is a test comment"
    assert data["ticket_id"] == 1
    assert data["user_id"] == 1
    assert "id" in data

def test_get_comments():
    # First create a comment
    client.post(
        "/api/tickets/1/comments",
        json={"content": "Comment 1"}
    )
    client.post(
        "/api/tickets/1/comments",
        json={"content": "Comment 2"}
    )
    
    # Get comments
    response = client.get("/api/tickets/1/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "Comment 1"
    assert data[1]["content"] == "Comment 2"

def test_list_tickets_with_relations():
    # Create comment
    client.post(
        "/api/tickets/1/comments",
        json={"content": "Test Comment"}
    )
    
    response = client.get("/api/tickets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    ticket = next(t for t in data if t["id"] == 1)
    
    # Check relations
    assert ticket["creator"]["id"] == 1
    assert len(ticket["comments"]) == 1
    assert ticket["comments"][0]["content"] == "Test Comment"
    assert ticket["comments"][0]["user"]["id"] == 1

def test_update_ticket_status():
    # Update status to IN_PROGRESS
    response = client.put(
        "/api/tickets/1",
        json={"status": "in_progress"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    
    # Verify persistence
    response = client.get("/api/tickets/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"

def test_filter_tickets():
    # Create another ticket with different attributes
    response = client.post(
        "/api/tickets/",
        json={
            "title": "Bug Ticket",
            "description": "This is a bug",
            "project_id": 1,
            "status": "in_progress",
            "type": "bug",
            "priority": "high"
        }
    )
    assert response.status_code == 200
    
    # Test filter by status
    response = client.get("/api/tickets/?status=todo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    
    response = client.get("/api/tickets/?status=in_progress")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Bug Ticket"
    
    # Test filter by type
    response = client.get("/api/tickets/?type=bug")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "bug"
    
    # Test filter by priority
    response = client.get("/api/tickets/?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["priority"] == "high"
    
    # Test search
    response = client.get("/api/tickets/?search=Bug")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Bug Ticket"

def test_delete_ticket_authorization():
    # Create a second user (non-admin, non-creator)
    user2 = User(
        id=2,
        email="user2@example.com",
        username="user2",
        full_name="User Two",
        hashed_password="hashed_secret",
        role=UserRole.USER,
        is_active=True
    )
    
    # Add user2 to DB and project
    db = TestingSessionLocal()
    db.merge(user2)
    member = ProjectMember(project_id=1, user_id=2, role=UserRole.USER)
    db.add(member)
    db.commit()
    db.close()
    
    # Override dependency to use user2
    def override_get_current_user_2():
        return user2
    
    app.dependency_overrides[get_current_user] = override_get_current_user_2
    
    try:
        # Try to delete ticket 1 (created by user 1)
        response = client.delete("/api/tickets/1")
        assert response.status_code == 403
    finally:
        # Restore dependency
        app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Delete as creator (user 1)
    response = client.delete("/api/tickets/1")
    assert response.status_code == 200
    
    # Verify deletion
    response = client.get("/api/tickets/1")
    assert response.status_code == 404
