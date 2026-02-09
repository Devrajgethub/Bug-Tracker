import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from app.models.ticket import Ticket, TicketComment
from app.models.user import User
from app.models.project import Project
from app.schemas import Ticket as TicketSchema
from app.core.config import settings
from app.database import Base # Import Base

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def reproduce():
    print(f"Connecting to {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    
    # Create tables if they don't exist
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Querying tickets...")
        query = db.query(Ticket).options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.comments).joinedload(TicketComment.user)
        )
        
        tickets = query.limit(5).all()
        print(f"Found {len(tickets)} tickets")

        print("Validating with Pydantic...")
        for t in tickets:
            print(f"Processing ticket {t.id}: {t.title}")
            # Try to convert to Pydantic model
            try:
                ticket_data = TicketSchema.model_validate(t)
                print(f"  Valid: {ticket_data.title}")
            except Exception as e:
                print(f"  ERROR validating ticket {t.id}: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"Database Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reproduce()
