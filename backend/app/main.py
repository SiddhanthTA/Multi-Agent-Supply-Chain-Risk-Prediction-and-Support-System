from fastapi import FastAPI
from sqlalchemy import text, inspect
from fastapi.staticfiles import StaticFiles
import os

from app.database.database import Base, engine
from app.models import *

from app.routers import (
    user,
    event,
    risk,
    prediction,
    recommendation,
    correlation,
    ai_log,
    system_log,
    auth,
    location,
    investigation,
)

from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.ai_pipeline import cleanup_stale_normal_weather_risks

# Create all database tables
Base.metadata.create_all(bind=engine)


def ensure_event_metadata_columns():
    """Add missing event metadata columns to existing databases without deleting data."""
    inspector = inspect(engine)
    if not inspector.has_table('events'):
        return

    columns = {col['name'] for col in inspector.get_columns('events')}
    additions = {
        'source': 'VARCHAR(500)',
        'source_type': 'VARCHAR(100)',
        'category': 'VARCHAR(100)',
        'published_at': 'TIMESTAMP',
        'received_at': 'TIMESTAMP',
    }

    for column_name, column_type in additions.items():
        if column_name in columns:
            continue
        try:
            if engine.dialect.name == 'sqlite':
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE events ADD COLUMN {column_name} {column_type}"))
            else:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE events ADD COLUMN {column_name} {column_type}"))
        except Exception:
            pass


ensure_event_metadata_columns()

# app = FastAPI(
#     title="AI Supply Chain Risk Intelligence API",
#     version="1.0.0",
# )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Supply Chain Risk Intelligence API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(user.router)
app.include_router(event.router)
app.include_router(risk.router)
app.include_router(prediction.router)
app.include_router(recommendation.router)
app.include_router(correlation.router)
app.include_router(ai_log.router)
app.include_router(system_log.router)
app.include_router(auth.router)
app.include_router(location.router)
app.include_router(investigation.router)

# Ensure uploads directory exists and mount it
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# -----------------------------
# Application Startup
# -----------------------------
@app.on_event("startup")
def startup_event():
    start_scheduler()
    
    # Create default admin if DB is empty
    from app.database.database import SessionLocal, engine
    from app.crud.user import get_users, create_user
    from app.schemas.user import UserCreate
    
    # Safe SQLite migration for new columns
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)"))
    except Exception:
        pass # Column might already exist
        
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN profile_image VARCHAR(255)"))
    except Exception:
        pass

    db = SessionLocal()
    try:
        users = get_users(db)
        if len(users) == 0:
            create_user(db, UserCreate(
                username="Admin",
                email="admin@supplysentry.com",
                password="admin",
                role="admin"
            ))
            print("Default admin user created: admin@supplysentry.com / admin")

        cleanup_stale_normal_weather_risks(db)
        print("Checked and normalized stale normal-weather risk records.")
    finally:
        db.close()


# -----------------------------
# Application Shutdown
# -----------------------------
@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()


# -----------------------------
# Root Endpoint
# -----------------------------
@app.get("/")
def root():
    return {
        "message": "AI Supply Chain Risk Intelligence Backend is Running 🚀"
    }


# -----------------------------
# Database Health Check
# -----------------------------
@app.get("/health")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "Connected Successfully ✅"
        }

    except Exception as e:
        return {
            "database": "Connection Failed ❌",
            "error": str(e)
        }