# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, projects, tickets, chat # Added chat
from app.database import engine, Base
# Ensure models are imported so tables are registered
from app import models
from app.models.ticket import TicketComment # Explicit import
from app.core.config import settings
from sqlalchemy import inspect
from sqlalchemy import text

print(f"Server starting with DATABASE_URL: {settings.DATABASE_URL}")

# Debug: Print registered tables
print("DEBUG: Registered tables in Base.metadata:")
for table in Base.metadata.tables.keys():
    print(f" - {table}")

# Create tables
print("DEBUG: Running create_all...")
Base.metadata.create_all(bind=engine)
print("DEBUG: create_all finished.")

# Lightweight migrations for new columns
insp = inspect(engine)
with engine.begin() as conn:
    user_cols = [c['name'] for c in insp.get_columns('users')]
    if 'avatar_url' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN avatar_url VARCHAR NULL'))
    if 'description' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN description TEXT NULL'))
    if 'resume_file_id' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN resume_file_id INTEGER NULL'))
    if 'certificate_file_id' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN certificate_file_id INTEGER NULL'))
    chat_cols = [c['name'] for c in insp.get_columns('chat_rooms')]
    if 'is_direct' not in chat_cols:
        conn.execute(text('ALTER TABLE chat_rooms ADD COLUMN is_direct BOOLEAN DEFAULT FALSE'))

app = FastAPI(title="BugTracker API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
from app.api import files as files_router
app.include_router(files_router.router, prefix="/api")
from app.api import users as users_router
app.include_router(users_router.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(chat.router, prefix="/api") # Added

@app.get("/")
async def root():
    return {"message": "BugTracker API is running"}
