from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    linkedin_id = Column(String, unique=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    company_logo = Column(String)
    company_url = Column(String)
    company_website = Column(String)
    company_description = Column(Text)
    company_address = Column(Text)  # JSON
    company_employees_count = Column(Integer)
    location = Column(String)
    url = Column(String, unique=True)
    apply_url = Column(String)
    description = Column(Text)
    description_html = Column(Text)
    salary = Column(String)
    posted_at = Column(String)
    seniority_level = Column(String)
    employment_type = Column(String)
    job_function = Column(String)
    industries = Column(String)
    applicants_count = Column(String)
    benefits = Column(Text)  # JSON
    job_poster_name = Column(String)
    job_poster_profile_url = Column(String)
    relevance_score = Column(Float)
    score_reason = Column(Text)
    applied = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    cover_letter = relationship("CoverLetter", back_populates="job", uselist=False)


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), unique=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="cover_letter")


class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    title = Column(String)
    summary = Column(Text)
    skills = Column(Text)  # JSON array stored as text
    experience = Column(Text)  # JSON array stored as text
    preferences = Column(Text)  # JSON: desired roles, locations, salary, etc.
    cv_text = Column(Text)  # Full CV text extracted from uploaded PDF


class ScheduledScrape(Base):
    __tablename__ = "scheduled_scrapes"

    id = Column(Integer, primary_key=True)
    job_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    linkedin_url = Column(String, nullable=False)
    max_results = Column(Integer, default=10)
    scrape_all = Column(Boolean, default=False)
    split_by_location = Column(Boolean, default=False)
    split_country = Column(String, default="")
    hour = Column(Integer, default=2)
    minute = Column(Integer, default=0)
    cv_text = Column(Text)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True)
    job_id = Column(String, nullable=False)  # schedule job_id
    ran_at = Column(DateTime, default=datetime.utcnow)
    jobs_added = Column(Integer, default=0)
    total_scraped = Column(Integer, default=0)
    status = Column(String, default="success")  # success / error
    error_message = Column(Text)
