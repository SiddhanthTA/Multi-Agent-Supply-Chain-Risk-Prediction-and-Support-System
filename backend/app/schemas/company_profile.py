from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEPENDENCY_CATEGORIES = {
    "materials": ["Semiconductors", "Batteries", "Copper", "Steel", "Aluminum", "Lithium", "Plastics", "Other", "None"],
    "fuel_energy": ["Petrol", "Diesel", "Natural Gas", "Electricity", "Coal", "Other", "None"],
    "logistics": ["Road", "Rail", "Sea", "Air", "Ports", "Warehousing", "Other", "None"],
    "technology": ["Cloud Services", "Semiconductors", "Telecom", "Data Centers", "Other", "None"],
    "geographic_exposure": ["India", "China", "Southeast Asia", "Europe", "North America", "Middle East", "Other", "None"],
}


class CompanyProfileRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    industry: str = Field(min_length=1, max_length=120)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)

    @field_validator("dependencies", mode="before")
    @classmethod
    def normalize_dependencies(cls, value):
        if not isinstance(value, dict):
            raise ValueError("dependencies must be an object keyed by dependency category")
        normalized = {}
        for category, values in value.items():
            if category not in DEPENDENCY_CATEGORIES:
                raise ValueError(f"Unknown dependency category: {category}")
            if not isinstance(values, list):
                raise ValueError(f"Dependency values for {category} must be a list")
            cleaned = []
            allowed = DEPENDENCY_CATEGORIES[category]
            for item in values:
                if not isinstance(item, str):
                    raise ValueError(f"Dependency values for {category} must be strings")
                item = item.strip()
                if item and item not in allowed:
                    raise ValueError(f"Unsupported dependency value for {category}: {item}")
                if item and item not in cleaned:
                    cleaned.append(item)
            if "None" in cleaned:
                cleaned = ["None"]
            normalized[category] = cleaned or ["None"]
        return normalized


class CompanyProfileResponse(BaseModel):
    company_name: str
    industry: str
    dependencies: Dict[str, List[str]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileDependencyOption(BaseModel):
    category: str
    options: List[str]


class CompanyRelevanceMatch(BaseModel):
    category: str
    value: str
    matched_terms: List[str] = Field(default_factory=list)
    matched_on: str


class CompanyRelevanceResult(BaseModel):
    event_id: int
    relevance: str
    label: str
    matched_dependencies: List[CompanyRelevanceMatch] = Field(default_factory=list)
    reason: str


class CompanyRelevanceEvent(BaseModel):
    event_id: int
    title: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    event_time: Optional[datetime] = None
    relevance: CompanyRelevanceResult


class CompanyRelevanceSummary(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    total_events: int
    direct_count: int
    indirect_count: int
    no_identified_count: int
    top_relevant_events: List[CompanyRelevanceEvent] = Field(default_factory=list)
    events: List[CompanyRelevanceEvent] = Field(default_factory=list)

