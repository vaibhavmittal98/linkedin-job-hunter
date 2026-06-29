"""Scheduled job management with persistence."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
scheduler.start()


def add_scrape_schedule(job_id: str, hour: int, minute: int, linkedin_url: str, max_results: int, scrape_all: bool, split_by_location: bool, split_country: str, cv_text: str):
    """Add or replace a scheduled scrape job."""
    from app.routers.jobs import _run_scrape

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        _run_scrape,
        trigger=CronTrigger(hour=hour, minute=minute),
        id=job_id,
        args=[linkedin_url, max_results, scrape_all, split_by_location, split_country, cv_text, job_id, False],
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

    db = SessionLocal()
    try:
        for s in db.query(ScheduledScrape).all():
            add_scrape_schedule(
                job_id=s.job_id,
                hour=s.hour,
                minute=s.minute,
                linkedin_url=s.linkedin_url,
                max_results=s.max_results,
                scrape_all=s.scrape_all,
                split_by_location=s.split_by_location,
                split_country=s.split_country,
                cv_text=s.cv_text,
            )
    finally:
        db.close()
