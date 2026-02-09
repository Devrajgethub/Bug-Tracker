import sys
import os

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Attempting to import app.schemas...")
    from app import schemas
    print("Successfully imported app.schemas")
    print(f"UserResponse: {schemas.UserResponse}")
except Exception as e:
    print(f"Failed to import app.schemas: {e}")
    import traceback
    traceback.print_exc()
