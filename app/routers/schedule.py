"""Schedule routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import UserProfile, ScheduledScrape, ScrapeRun
from app.auth import get_current_user
from app.services.scheduler import add_scrape_schedule, remove_schedule, list_schedules

router = APIRouter(prefix="/api/schedules")


class ScheduleRequest(BaseModel):
    linkedin_url: str
    max_results: int = 10
    scrape_all: bool = False
    split_by_location: bool = False
    split_country: str = ""
    hour: int = 2
    minute: int = 0


@router.post("")
def create_schedule(req: ScheduleRequest, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Create a scheduled scrape job."""
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")

    job_id = f"scrape_{user.username}_{hash(req.linkedin_url) % 10000}"

    # Save to DB
    existing = db.query(ScheduledScrape).filter(ScheduledScrape.job_id == job_id).first()
    if existing:
        db.delete(existing)

    schedule = ScheduledScrape(
        job_id=job_id,
        username=user.username,
        linkedin_url=req.linkedin_url,
        max_results=req.max_results,
        scrape_all=req.scrape_all,
        split_by_location=req.split_by_location,
        split_country=req.split_country,
        hour=req.hour,
        minute=req.minute,
        cv_text=user.cv_text,
    )
    db.add(schedule)
    db.commit()

    # Add to in-memory scheduler
    add_scrape_schedule(
        job_id=job_id,
        hour=req.hour,
        minute=req.minute,
        linkedin_url=req.linkedin_url,
        max_results=req.max_results,
        scrape_all=req.scrape_all,
        split_by_location=req.split_by_location,
        split_country=req.split_country,
        cv_text=user.cv_text,
    )

    return {"status": "created", "job_id": job_id, "runs_at": f"{req.hour:02d}:{req.minute:02d} daily"}


@router.get("")
def get_schedules(user: UserProfile = Depends(get_current_user), db: Session = Depends(get_db)):
    """List user's scheduled jobs."""
    schedules = db.query(ScheduledScrape).filter(ScheduledScrape.username == user.username).all()
    return [
        {
            "id": s.job_id,
            "linkedin_url": s.linkedin_url,
            "hour": s.hour,
            "minute": s.minute,
            "scrape_all": s.scrape_all,
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
