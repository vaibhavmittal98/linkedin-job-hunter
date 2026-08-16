"""Schedule routes."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import UserProfile, ScheduledScrape, ScrapeRun
from app.auth import get_current_user
from app.services.scheduler import add_scrape_schedule, remove_schedule, list_schedules

router = APIRouter(prefix="/api/schedules")


class ScheduleRequest(BaseModel):
    keywords: list[str]
    locations: list[str] = []
    max_results: int = 150
    scrape_all: bool = False
    published_at: str = ""
    job_type: str = ""  # "", "full-time", "part-time", "contract", "internship", "temporary"
    hour: int = 2
    minute: int = 0
    frequency: str = "daily"  # "daily" or "weekly"
    day_of_week: str = "mon"  # mon, tue, wed, thu, fri, sat, sun (for weekly)


@router.post("")
def create_schedule(req: ScheduleRequest, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Create a scheduled scrape job."""
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")

    job_id = f"scrape_{user.username}_{hash('_'.join(req.keywords)) % 10000}"

    # Save to DB
    existing = db.query(ScheduledScrape).filter(ScheduledScrape.job_id == job_id).first()
    if existing:
        db.delete(existing)

    schedule = ScheduledScrape(
        job_id=job_id,
        user_id=user.id,
        username=user.username,
        keywords=json.dumps(req.keywords),
        locations=json.dumps(req.locations),
        max_results=req.max_results,
        scrape_all=req.scrape_all,
        published_at=req.published_at,
        job_type=req.job_type,
        hour=req.hour,
        minute=req.minute,
        frequency=req.frequency,
        day_of_week=req.day_of_week,
        cv_text=user.cv_text,
    )
    db.add(schedule)
    db.commit()

    # Add to in-memory scheduler
    add_scrape_schedule(
        job_id=job_id,
        hour=req.hour,
        minute=req.minute,
        keywords=req.keywords,
        locations=req.locations,
        max_results=req.max_results,
        scrape_all=req.scrape_all,
        published_at=req.published_at,
        cv_text=user.cv_text,
        frequency=req.frequency,
        day_of_week=req.day_of_week,
        user_id=user.id,
        job_type=req.job_type,
    )

    freq_str = "daily" if req.frequency == "daily" else f"weekly on {req.day_of_week}"
    return {"status": "created", "job_id": job_id, "runs_at": f"{req.hour:02d}:{req.minute:02d} {freq_str}"}


@router.put("/{job_id}")
def update_schedule(job_id: str, req: ScheduleRequest, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Update an existing scheduled scrape in place (keeps the same job_id)."""
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")

    schedule = db.query(ScheduledScrape).filter(ScheduledScrape.job_id == job_id, ScheduledScrape.username == user.username).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")

    schedule.keywords = json.dumps(req.keywords)
    schedule.locations = json.dumps(req.locations)
    schedule.max_results = req.max_results
    schedule.scrape_all = req.scrape_all
    schedule.published_at = req.published_at
    schedule.job_type = req.job_type
    schedule.hour = req.hour
    schedule.minute = req.minute
    schedule.frequency = req.frequency
    schedule.day_of_week = req.day_of_week
    # Refresh the CV snapshot so edits pick up the latest CV.
    schedule.cv_text = user.cv_text
    db.commit()

    # Re-register with the in-memory scheduler (replaces the existing job).
    add_scrape_schedule(
        job_id=job_id,
        hour=req.hour,
        minute=req.minute,
        keywords=req.keywords,
        locations=req.locations,
        max_results=req.max_results,
        scrape_all=req.scrape_all,
        published_at=req.published_at,
        cv_text=user.cv_text,
        frequency=req.frequency,
        day_of_week=req.day_of_week,
        user_id=user.id,
        job_type=req.job_type,
    )

    freq_str = "daily" if req.frequency == "daily" else f"weekly on {req.day_of_week}"
    return {"status": "updated", "job_id": job_id, "runs_at": f"{req.hour:02d}:{req.minute:02d} {freq_str}"}


@router.get("")
def get_schedules(user: UserProfile = Depends(get_current_user), db: Session = Depends(get_db)):
    """List user's scheduled jobs."""
    schedules = db.query(ScheduledScrape).filter(ScheduledScrape.username == user.username).all()
    return [
        {
            "id": s.job_id,
            "keywords": json.loads(s.keywords) if s.keywords else [],
            "locations": json.loads(s.locations) if s.locations else [],
            "hour": s.hour,
            "minute": s.minute,
            "max_results": s.max_results,
            "scrape_all": s.scrape_all,
            "published_at": s.published_at or "",
            "job_type": s.job_type or "",
            "frequency": s.frequency or "daily",
            "day_of_week": s.day_of_week or "mon",
        }
        for s in schedules
    ]


@router.delete("/{job_id}")
def delete_schedule(job_id: str, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Remove a scheduled job."""
    schedule = db.query(ScheduledScrape).filter(ScheduledScrape.job_id == job_id, ScheduledScrape.username == user.username).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")

    db.delete(schedule)
    db.commit()
    remove_schedule(job_id)
    return {"status": "deleted"}


@router.get("/{job_id}/history")
def get_schedule_history(job_id: str, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Get run history for a schedule."""
    runs = db.query(ScrapeRun).filter(ScrapeRun.job_id == job_id).order_by(ScrapeRun.ran_at.desc()).limit(20).all()
    return [
        {
            "ran_at": str(r.ran_at),
            "jobs_added": r.jobs_added,
            "total_scraped": r.total_scraped,
            "status": r.status,
            "error": r.error_message,
        }
        for r in runs
    ]
