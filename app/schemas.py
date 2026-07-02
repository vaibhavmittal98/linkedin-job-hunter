from pydantic import BaseModel
from datetime import datetime


class JobOut(BaseModel):
    id: int
    linkedin_id: str | None
    title: str
    company: str
    company_logo: str | None
    company_url: str | None
    company_website: str | None
    location: str | None
    url: str | None
    apply_url: str | None
    description: str | None
    salary: str | None
    posted_at: str | None
    seniority_level: str | None
    employment_type: str | None
    job_function: str | None
    industries: str | None
    applicants_count: str | None
    applied: bool
    relevance_score: float | None
    score_reason: str | None
    scraped_at: datetime | None

    class Config:
        from_attributes = True


class CoverLetterOut(BaseModel):
    id: int
    job_id: int
    content: str
    created_at: datetime | None

    class Config:
        from_attributes = True


class UserProfileIn(BaseModel):
    name: str
    title: str
    summary: str
    skills: list[str]
    experience: list[str]
    preferences: dict


class UserProfileOut(UserProfileIn):
    id: int

    class Config:
        from_attributes = True


class ScrapeRequest(BaseModel):
    keywords: list[str]
    locations: list[str] = []
    max_results: int = 150
    scrape_all: bool = False
    published_at: str = ""  # "", "r86400", "r604800", "r2592000"


class AdhocCoverLetterRequest(BaseModel):
    description: str
    title: str | None = None
    company: str | None = None


class AdhocRefineRequest(BaseModel):
    content: str
    message: str
    title: str | None = None
    company: str | None = None


class AdhocPdfRequest(BaseModel):
    content: str
    title: str | None = None
    company: str | None = None
