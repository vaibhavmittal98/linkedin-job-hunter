"""Scheduled job management with persistence."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
scheduler.start()


def add_scrape_schedule(job_id: str, hour: int, minute: int, keywords: list[str], locations: list[str], max_results: int, scrape_all: bool, published_at: str, cv_text: str, frequency: str = "daily", day_of_week: str = "mon"):
    """Add or replace a scheduled scrape job."""
    from app.routers.jobs import _run_scrape

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if frequency == "weekly":
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
    else:
        trigger = CronTrigger(hour=hour, minute=minute)

    scheduler.add_job(
        _run_scrape,
        trigger=trigger,
        id=job_id,
        args=[keywords, locations, max_results, scrape_all, published_at, cv_text, job_id],
        replace_existing=True,
    )


def remove_schedule(job_id: str):
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def list_schedules() -> list[dict]:
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "next_run": str(job.next_run_time),
            "trigger": str(job.trigger),
        }
        for job in jobs
    ]


def reload_schedules_from_db():
    """Reload all saved schedules from DB on server start."""
    from app.db import SessionLocal
    from app.models import ScheduledScrape
    import json

    db = SessionLocal()
    try:
        for s in db.query(ScheduledScrape).all():
            add_scrape_schedule(
                job_id=s.job_id,
                hour=s.hour,
                minute=s.minute,
                keywords=json.loads(s.keywords) if s.keywords else [],
                locations=json.loads(s.locations) if s.locations else [],
                max_results=s.max_results,
                scrape_all=s.scrape_all,
                published_at=s.published_at or "",
                cv_text=s.cv_text,
                frequency=s.frequency or "daily",
                day_of_week=s.day_of_week or "mon",
            )
    finally:
        db.close()
