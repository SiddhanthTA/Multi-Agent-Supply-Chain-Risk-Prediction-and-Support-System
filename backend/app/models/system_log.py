from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)

    log_level = Column(String(50))

    module = Column(String(100))

    message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(
    Integer,
    ForeignKey("users.id"),
    nullable=True

)
    user = relationship(
    "User",
    back_populates="system_logs"
)