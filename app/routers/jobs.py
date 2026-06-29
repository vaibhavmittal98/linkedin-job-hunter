import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Job, CoverLetter, UserProfile
from app.schemas import JobOut, CoverLetterOut, ScrapeRequest, UserProfileIn, UserProfileOut
from app.services.scraper import scrape_linkedin_jobs
from app.services.scorer import score_job
from app.services.cover_letter import generate_cover_letter
from app.services.pdf_generator import generate_pdf
from app.auth import get_current_user

router = APIRouter(prefix="/api")


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(min_score: float = 0, db: Session = Depends(get_db)):
    query = db.query(Job)
    if min_score > 0:
        query = query.filter(Job.relevance_score >= min_score)
    return query.order_by(Job.relevance_score.desc()).all()


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/scrape")
def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Scrape jobs in background."""
    background_tasks.add_task(_run_scrape, req.keywords, req.location, req.max_results, req.scrape_all, req.split_by_location, req.split_country, user.cv_text, "manual")
    return {"status": "started", "message": "Scraping started. Jobs will appear on the dashboard soon."}


def _run_scrape(keywords: str, location: str, max_results: int, scrape_all: bool, split_by_location: bool, split_country: str, cv_text: str, schedule_job_id: str = "manual", last_24h: bool = False):
    """Background scrape task."""
    from app.db import SessionLocal
    from app.models import ScrapeRun
    from datetime import datetime

    db = SessionLocal()
    try:
        raw_jobs = scrape_linkedin_jobs(keywords, location, max_results, scrape_all, split_by_location, split_country, last_24h)
        added = 0
        for raw in raw_jobs:
            existing = db.query(Job).filter(Job.linkedin_id == raw.get("linkedin_id")).first()
            if existing:
                continue

            score = None
            score_reason = None
            if raw.get("description") and cv_text:
                try:
                    score, score_reason = score_job(raw["description"], cv_text)
                except (NotImplementedError, Exception):
                    score = None

            job = Job(
                linkedin_id=raw.get("linkedin_id"),
                title=raw["title"],
                company=raw["company"],
                company_logo=raw.get("company_logo"),
                company_url=raw.get("company_url"),
                company_website=raw.get("company_website"),
                company_description=raw.get("company_description"),
                company_address=raw.get("company_address"),
                company_employees_count=raw.get("company_employees_count"),
                location=raw.get("location"),
                url=raw.get("url"),
                apply_url=raw.get("apply_url"),
                description=raw.get("description"),
                description_html=raw.get("description_html"),
                salary=raw.get("salary"),
                posted_at=raw.get("posted_at"),
                seniority_level=raw.get("seniority_level"),
                employment_type=raw.get("employment_type"),
                job_function=raw.get("job_function"),
                industries=raw.get("industries"),
                applicants_count=raw.get("applicants_count"),
                benefits=raw.get("benefits"),
                job_poster_name=raw.get("job_poster_name"),
                job_poster_profile_url=raw.get("job_poster_profile_url"),
                relevance_score=score,
                score_reason=score_reason,
            )
            db.add(job)
            added += 1

        run = ScrapeRun(job_id=schedule_job_id, ran_at=datetime.utcnow(), jobs_added=added, total_scraped=len(raw_jobs), status="success")
        db.add(run)
        db.commit()
    except Exception as e:
        run = ScrapeRun(job_id=schedule_job_id, ran_at=datetime.utcnow(), jobs_added=0, total_scraped=0, status="error", error_message=str(e))
        db.add(run)
        db.commit()
    finally:
        db.close()


@router.post("/jobs/{job_id}/score")
def score_single_job(job_id: int, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Score a single job's relevance."""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")

    score, reason = score_job(job.description or "", user.cv_text)
    job.relevance_score = score
    job.score_reason = reason
    db.commit()
    return {"score": score, "reason": reason}


@router.post("/jobs/{job_id}/apply")
def mark_applied(job_id: int, db: Session = Depends(get_db)):
    """Mark a job as applied."""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.applied = True
    db.commit()
    return {"status": "applied"}


@router.post("/jobs/{job_id}/unapply")
def mark_unapplied(job_id: int, db: Session = Depends(get_db)):
    """Mark a job as not applied."""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.applied = False
    db.commit()
    return {"status": "unapplied"}


@router.post("/jobs/{job_id}/cover-letter", response_model=CoverLetterOut)
def create_cover_letter(job_id: int, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Generate a cover letter for a specific job."""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")

    existing = db.query(CoverLetter).filter(CoverLetter.job_id == job_id).first()
    if existing:
        return existing

    job_dict = {"title": job.title, "company": job.company, "description": job.description}
    content = generate_cover_letter(job_dict, user.cv_text)
    letter = CoverLetter(job_id=job_id, content=content)
    db.add(letter)
    db.commit()
    db.refresh(letter)
    return letter


@router.get("/jobs/{job_id}/cover-letter", response_model=CoverLetterOut)
def get_cover_letter(job_id: int, db: Session = Depends(get_db)):
    letter = db.query(CoverLetter).filter(CoverLetter.job_id == job_id).first()
    if not letter:
        raise HTTPException(404, "No cover letter for this job")
    return letter


@router.post("/jobs/{job_id}/cover-letter/refine")
def refine_cover_letter(job_id: int, feedback: dict, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Refine a cover letter based on user feedback."""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    letter = db.query(CoverLetter).filter(CoverLetter.job_id == job_id).first()
    if not letter:
        raise HTTPException(404, "Generate a cover letter first")

    from app.services.scorer import _call_llm

    name = user.cv_text.strip().split("\n")[0] if user.cv_text else "Applicant"
    prompt = f"""Here is a cover letter that was written for a job application. The user wants changes.

CURRENT COVER LETTER:
{letter.content}

JOB:
- Title: {job.title}
- Company: {job.company}

CANDIDATE CV:
{user.cv_text}

USER FEEDBACK: {feedback.get("message", "")}

Rewrite the cover letter incorporating the feedback. Keep the same style rules:
- Conversational, professional, no buzzwords, no pretentious language
- No metrics/numbers from CV
- Don't regurgitate the CV
- Don't be abstract about why you're a good fit — just state facts
- Short and human
- End with "Best regards,\n{name}" only once

Return ONLY the new cover letter text, nothing else.
"""
    new_content = _call_llm(prompt)
    letter.content = new_content
    db.commit()
    db.refresh(letter)
    return {"content": letter.content}


@router.get("/jobs/{job_id}/cover-letter/pdf")
def download_cover_letter_pdf(job_id: int, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Download cover letter as PDF."""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    letter = db.query(CoverLetter).filter(CoverLetter.job_id == job_id).first()
    if not letter:
        raise HTTPException(404, "No cover letter for this job")

    pdf_bytes = generate_pdf(letter.content, job.title, job.company, user.cv_text or "")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cover_letter_{job.company.replace(' ', '_')}.pdf"},
    )


@router.post("/profile", response_model=UserProfileOut)
def save_profile(data: UserProfileIn, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)

    profile.name = data.name
    profile.title = data.title
    profile.summary = data.summary
    profile.skills = json.dumps(data.skills)
    profile.experience = json.dumps(data.experience)
    profile.preferences = json.dumps(data.preferences)
    db.commit()
    db.refresh(profile)

    return UserProfileOut(
        id=profile.id,
        name=profile.name,
        title=profile.title,
        summary=profile.summary,
        skills=data.skills,
        experience=data.experience,
        preferences=data.preferences,
    )


@router.get("/profile", response_model=UserProfileOut | None)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        return None
    return UserProfileOut(
        id=profile.id,
        name=profile.name,
        title=profile.title,
        summary=profile.summary,
        skills=json.loads(profile.skills) if profile.skills else [],
        experience=json.loads(profile.experience) if profile.experience else [],
        preferences=json.loads(profile.preferences) if profile.preferences else {},
    )
