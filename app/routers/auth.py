import os
import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import UserProfile, Job
from app.auth import hash_password, verify_password, create_access_token, get_current_user

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

router = APIRouter(prefix="/api/auth")


@router.post("/signup")
async def signup(
    username: str = Form(...),
    password: str = Form(...),
    cv: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Create account with username, password, and CV upload."""
    if db.query(UserProfile).filter(UserProfile.username == username).first():
        raise HTTPException(400, "Username already taken")

    # Save PDF to disk
    pdf_bytes = await cv.read()
    cv_path = os.path.join(UPLOAD_DIR, f"{username}_cv.pdf")
    with open(cv_path, "wb") as f:
        f.write(pdf_bytes)

    # Extract text for LLM usage
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    cv_text = ""
    for page in doc:
        cv_text += page.get_text()
    doc.close()

    if not cv_text.strip():
        os.remove(cv_path)
        raise HTTPException(400, "Could not extract text from CV")

    user = UserProfile(
        username=username,
        password_hash=hash_password(password),
        cv_text=cv_text,
    )
    db.add(user)
    db.commit()

    token = create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Login with username and password."""
    user = db.query(UserProfile).filter(UserProfile.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_me(user: UserProfile = Depends(get_current_user)):
    """Get current user info."""
    return {"username": user.username, "has_cv": bool(user.cv_text)}


@router.post("/update-cv")
async def update_cv(
    background_tasks: BackgroundTasks,
    cv: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Update CV and re-score all non-applied jobs."""
    import os
    import fitz

    pdf_bytes = await cv.read()

    # Save PDF
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    cv_path = os.path.join(upload_dir, f"{user.username}_cv.pdf")
    with open(cv_path, "wb") as f:
        f.write(pdf_bytes)

    # Extract text
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    cv_text = ""
    for page in doc:
        cv_text += page.get_text()
    doc.close()

    if not cv_text.strip():
        raise HTTPException(400, "Could not extract text from CV")

    user.cv_text = cv_text
    db.commit()

    # Re-score non-applied jobs in background
    background_tasks.add_task(_rescore_jobs, cv_text)

    return {"status": "ok", "message": "CV updated. Re-scoring jobs in background."}


def _rescore_jobs(cv_text: str):
    """Re-score all non-applied jobs with new CV."""
    from app.db import SessionLocal
    from app.services.scorer import score_job

    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.applied == False).all()
        for job in jobs:
            if not job.description:
                continue
            try:
                score, reason = score_job(job.description, cv_text)
                job.relevance_score = score
                job.score_reason = reason
            except Exception:
                continue
        db.commit()
    finally:
        db.close()
