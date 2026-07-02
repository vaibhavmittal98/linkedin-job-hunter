"""Cover letter generator using LLM."""

from app.services.scorer import _call_llm


def _get_name(cv_text: str) -> str:
    """Extract name from first line of CV."""
    lines = [l.strip() for l in cv_text.strip().split("\n") if l.strip()]
    name = lines[0] if lines else "Applicant"
    if name.isupper():
        name = name.title()
    return name


def generate_cover_letter(job: dict, cv_text: str) -> str:
    """Generate a tailored cover letter for a specific job."""
    name = _get_name(cv_text)
    prompt = f"""Write a cover letter for this job application.

Rules:
- Write like a real person. Conversational, professional, but not stiff.
- NO metrics, NO percentages, NO numbers from the CV. Don't say "0% to 87%" or "team of 8".
- Don't list or repeat CV bullet points. The recruiter already has the CV.
- Instead, briefly connect your relevant experience to what THEY need. Show you understand the role.
- Pick 1-2 areas where your background clearly fits and explain WHY you'd be effective, not WHAT you did.
- Keep it to 3 short paragraphs. Under 150 words total.
- No subject line. Start with "Hi [Company] Team,"
- NO buzzwords. No "passionate", "thrilled", "excited", "leverage", "synergy", "thrives".
- Don't be pretentious. Don't explain why you're a good fit in abstract terms. Just state facts simply.
- No self-praise like "I'm used to balancing X with Y" — just say what you did.
- End with "Best regards,\\n{name}". Only once. No other sign-off.

CANDIDATE CV:
{cv_text}

JOB:
- Title: {job.get('title', '')}
- Company: {job.get('company', '')}
- Description: {job.get('description', '')[:2000]}

Write the cover letter:
"""
    return _call_llm(prompt)


def refine_cover_letter_adhoc(current: str, feedback: str, cv_text: str, title: str = "", company: str = "") -> str:
    """Refine a standalone (ad-hoc) cover letter based on user feedback.

    Isolated from the job-based refine flow in routers/jobs.py.
    """
    name = _get_name(cv_text)
    job_lines = []
    if title:
        job_lines.append(f"- Title: {title}")
    if company:
        job_lines.append(f"- Company: {company}")
    job_block = "\n".join(job_lines) if job_lines else "- (not specified)"

    prompt = f"""Here is a cover letter that was written for a job application. The user wants changes.

CURRENT COVER LETTER:
{current}

JOB:
{job_block}

CANDIDATE CV:
{cv_text}

USER FEEDBACK: {feedback}

Rewrite the cover letter incorporating the feedback. Keep the same style rules:
- Conversational, professional, no buzzwords, no pretentious language
- No metrics/numbers from CV
- Don't regurgitate the CV
- Don't be abstract about why you're a good fit — just state facts
- Short and human
- End with "Best regards,\\n{name}" only once

Return ONLY the new cover letter text, nothing else.
"""
    return _call_llm(prompt)
