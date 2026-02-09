from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.models.ticket import Ticket, TicketStatus, TicketType, TicketPriority
from app.models.project import Project, ProjectMember
import traceback

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

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def setup_data():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.merge(mock_user)
    
    project = Project(id=1, name="Test Project", description="Test Desc", owner_id=1)
    db.add(project)
    
    member = ProjectMember(project_id=1, user_id=1, role=UserRole.ADMIN)
    db.add(member)
    
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
    db.close()

def reproduce():
    setup_data()
    try:
        print("Sending request...")
        response = client.get("/api/tickets/?limit=5")
        print(f"Response status: {response.status_code}")
        if response.status_code == 500:
            print("Response text:", response.text)
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
