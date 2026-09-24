import sys
sys.path.append('backend')
from app.database.database import SessionLocal
from app.crud.user import create_user
from app.schemas.user import UserCreate

db = SessionLocal()
try:
    u = UserCreate(username="debug3", email="debug3@example.com", password="password")
    user = create_user(db, u)
    print("Success:", user.id)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
