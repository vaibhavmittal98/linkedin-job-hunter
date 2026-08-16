import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Job, CoverLetter, UserProfile
from app.schemas import JobOut, JobListOut, FilterOptionsOut, CoverLetterOut, ScrapeRequest, UserProfileIn, UserProfileOut, AdhocCoverLetterRequest, AdhocRefineRequest, AdhocPdfRequest, JobChatRequest, ChatRequest
from app.services.scraper import scrape_linkedin_jobs
from app.services.scorer import score_job
from app.services.sponsor import is_sponsor
from app.services.cover_letter import generate_cover_letter, refine_cover_letter_adhoc
from app.services.chat import chat_about_job
from app.services.pdf_generator import generate_pdf, generate_pdf_adhoc
from app.auth import get_current_user

router = APIRouter(prefix="/api")


@router.get("/jobs", response_model=JobListOut)
def list_jobs(
    min_score: float = 0,
    search: str = "",
    seniority: str = "",
    employment_type: str = "",
    location: str = "",
    applied: str = "",  # "", "applied", "not_applied"
    time_period: str = "",  # "", "day", "week", "month"
    ind_sponsor: str = "",  # "", "sponsor", "non_sponsor"
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """List jobs for the current user with server-side filtering and pagination.

    Read-only: this only issues SELECT/COUNT queries — no DB writes or schema changes.
    """
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    query = db.query(Job).filter(Job.user_id == user.id)

    if min_score > 0:
        query = query.filter(Job.relevance_score >= min_score)
    if search:
        like = f"%{search}%"
        query = query.filter((Job.title.ilike(like)) | (Job.company.ilike(like)))
    if seniority:
        query = query.filter(Job.seniority_level == seniority)
    if employment_type:
        query = query.filter(Job.employment_type == employment_type)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if applied == "applied":
        query = query.filter(Job.applied.is_(True))
    elif applied == "not_applied":
        query = query.filter(Job.applied.is_(False))
    if ind_sponsor == "sponsor":
        query = query.filter(Job.ind_sponsor.is_(True))
    elif ind_sponsor == "non_sponsor":
        # Treat NULL (not yet evaluated) as non-sponsor for filtering purposes.
        query = query.filter((Job.ind_sponsor.is_(False)) | (Job.ind_sponsor.is_(None)))
    if time_period in ("day", "week", "month"):
        days = {"day": 1, "week": 7, "month": 30}[time_period]
        # posted_at is stored as ISO 'YYYY-MM-DD', so lexicographic >= matches chronological.
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = query.filter(Job.posted_at >= cutoff)

    total = query.count()
    items = (
        query.order_by(Job.relevance_score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/jobs/filter-options", response_model=FilterOptionsOut)
def job_filter_options(db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Distinct seniority levels and employment types for the current user's jobs."""
    seniority_rows = (
        db.query(Job.seniority_level)
        .filter(Job.user_id == user.id, Job.seniority_level.isnot(None), Job.seniority_level != "")
        .distinct()
        .all()
    )
    type_rows = (
        db.query(Job.employment_type)
        .filter(Job.user_id == user.id, Job.employment_type.isnot(None), Job.employment_type != "")
        .distinct()
        .all()
    )
    return {
        "seniority_levels": sorted(r[0] for r in seniority_rows),
        "employment_types": sorted(r[0] for r in type_rows),
    }


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/scrape")
def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Scrape jobs in background."""
    background_tasks.add_task(_run_scrape, req.keywords, req.locations, req.max_results, req.scrape_all, req.published_at, user.cv_text, "manual", user.id, req.job_type)
    return {"status": "started", "message": "Scraping started. Jobs will appear on the dashboard soon."}


def _run_scrape(keywords: list[str], locations: list[str], max_results: int, scrape_all: bool, published_at: str, cv_text: str, schedule_job_id: str = "manual", user_id: int = None, job_type: str = ""):
    """Background scrape task."""
    from app.db import SessionLocal
    from app.models import ScrapeRun
    from datetime import datetime

    db = SessionLocal()
    try:
        raw_jobs = scrape_linkedin_jobs(keywords, locations, max_results, scrape_all, published_at, job_type)
        added = 0
        for raw in raw_jobs:
            existing = db.query(Job).filter(Job.linkedin_id == raw.get("linkedin_id"), Job.user_id == user_id).first()
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
                user_id=user_id,
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
                ind_sponsor=is_sponsor(raw.get("company") or ""),
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


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Delete a job."""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    db.query(CoverLetter).filter(CoverLetter.job_id == job_id).delete()
    db.delete(job)
    db.commit()
    return {"status": "deleted"}


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


@router.post("/jobs/{job_id}/chat")
def job_chat(job_id: int, req: JobChatRequest, db: Session = Depends(get_db), user: UserProfile = Depends(get_current_user)):
    """Stateless Q&A about a specific job, with CV + job description as context.

    History is supplied by the client on every call; nothing is stored.
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")

    reply = chat_about_job(
        [m.model_dump() for m in req.messages],
        user.cv_text,
        title=job.title or "",
        company=job.company or "",
        description=job.description or "",
    )
    return {"reply": reply}


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


@router.post("/cover-letter/adhoc")
def create_adhoc_cover_letter(req: AdhocCoverLetterRequest, user: UserProfile = Depends(get_current_user)):
    """Generate a standalone cover letter from a pasted job description (not stored)."""
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")
    job_dict = {"title": req.title or "", "company": req.company or "", "description": req.description}
    content = generate_cover_letter(job_dict, user.cv_text)
    return {"content": content}


@router.post("/cover-letter/adhoc/refine")
def refine_adhoc_cover_letter(req: AdhocRefineRequest, user: UserProfile = Depends(get_current_user)):
    """Refine a standalone cover letter (not stored)."""
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")
    content = refine_cover_letter_adhoc(req.content, req.message, user.cv_text, req.title or "", req.company or "")
    return {"content": content}


@router.post("/cover-letter/adhoc/pdf")
def download_adhoc_cover_letter_pdf(req: AdhocPdfRequest, user: UserProfile = Depends(get_current_user)):
    """Download a standalone cover letter as PDF.

    The 'Application for <title> at <company>' line is only rendered when
    BOTH title and company are provided.
    """
    if req.title and req.company:
        title, company = req.title, req.company
    else:
        title, company = "", ""
    pdf_bytes = generate_pdf_adhoc(req.content, title, company, user.cv_text or "")
    filename = f"cover_letter_{company.replace(' ', '_')}.pdf" if company else "cover_letter.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/chat")
def standalone_chat(req: ChatRequest, user: UserProfile = Depends(get_current_user)):
    """Stateless Q&A with CV as context and an optional pasted job description.

    When no description is provided, the chat operates with the CV alone.
    History is supplied by the client on every call; nothing is stored.
    """
    if not user.cv_text:
        raise HTTPException(400, "Upload your CV first")

    reply = chat_about_job(
        [m.model_dump() for m in req.messages],
        user.cv_text,
        title=req.title or "",
        company=req.company or "",
        description=req.description or "",
    )
    return {"reply": reply}


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
