from pydantic import BaseModel, Field
from typing import Any

class ResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=120)
    industry_hint: str | None = None
    focus_area: str | None = None
    sources: list[str] = Field(default_factory=list)

class SourceSummary(BaseModel):
    title: str
    url: str
    extracted_chars: int
    summary: str

class ResearchReport(BaseModel):
    company_name: str
    industry_hint: str | None = None
    focus_area: str | None = None
    executive_summary: str
    company_overview: str
    competitors: list[dict[str, Any]]
    swot: dict[str, list[str]]
    market_signals: list[str]
    strategic_recommendations: list[str]
    sources: list[SourceSummary]
    markdown_report: str

class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str
