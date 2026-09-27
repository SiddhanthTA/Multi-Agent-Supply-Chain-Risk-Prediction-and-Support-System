from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    company_name = Column(String(255), nullable=False)
    industry = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="company_profile")
    dependencies = relationship(
        "CompanyDependency",
        back_populates="company_profile",
        cascade="all, delete-orphan",
    )


class CompanyDependency(Base):
    __tablename__ = "company_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "company_profile_id",
            "category",
            "value",
            name="uq_company_dependency_value",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    company_profile_id = Column(
        Integer,
        ForeignKey("company_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(50), nullable=False, index=True)
    value = Column(String(100), nullable=False)

    company_profile = relationship("CompanyProfile", back_populates="dependencies")
