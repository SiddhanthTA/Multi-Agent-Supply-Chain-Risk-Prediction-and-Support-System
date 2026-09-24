from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_image = Column(String(255), nullable=True)

    role = Column(String(50), nullable=False, default="analyst")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    system_logs = relationship(
        "SystemLog",
        back_populates="user"
    )

    monitored_locations = relationship(
        "MonitoredLocation",
        back_populates="user",
        cascade="all, delete-orphan"
    )