"""Pydantic schemas for deterministic Risk Trends responses."""

from pydantic import BaseModel, Field


class RiskTrendSummary(BaseModel):
    total_risks: int
    high_critical_risks: int
    active_risks: int
    previous_total_risks: int
    change_percent: float | None = None


class RiskTrendDay(BaseModel):
    date: str
    total: int
    critical: int
    high: int
    medium: int
    low: int


class RiskTrendBreakdownItem(BaseModel):
    name: str
    count: int


class RiskTrendDependency(BaseModel):
    dependency: str
    count: int


class RiskTrendCompany(BaseModel):
    available: bool = False
    total_relevant: int = 0
    direct: int = 0
    indirect: int = 0
    dependencies: list[RiskTrendDependency] = Field(default_factory=list)


class RiskTrendResponse(BaseModel):
    days: int
    start_date: str
    end_date: str
    comparison_start_date: str
    comparison_end_date: str
    summary: RiskTrendSummary
    daily: list[RiskTrendDay] = Field(default_factory=list)
    risk_type_breakdown: list[RiskTrendBreakdownItem] = Field(default_factory=list)
    category_breakdown: list[RiskTrendBreakdownItem] = Field(default_factory=list)
    company: RiskTrendCompany = Field(default_factory=RiskTrendCompany)
