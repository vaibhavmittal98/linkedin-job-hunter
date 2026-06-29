"""
Job relevance scorer. 

Uses OpenRouter (OpenAI-compatible API) for LLM calls.
Scores based on user's CV text against job description.
"""

import json
import httpx
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def score_job(job_description: str, cv_text: str) -> tuple[float, str]:
    """Score a job 0-100 based on likelihood of passing screening."""
    prompt = f"""You are a recruiter screening applications. Score this candidate against the job on these criteria (each 0-10):

1. **Skills Match** - Does the candidate have the required technical skills?
2. **Experience Level** - Does their seniority/years match what's asked?
3. **Tech Stack Overlap** - How much overlap between their tools/languages and what's required?
4. **Domain Relevance** - Is their industry/domain experience relevant?
5. **Disqualifiers** - Any hard blockers? (language requirements, certifications, clearance they lack?) Score 10 if no blockers, 0 if major blocker.

Return ONLY a JSON object:
{{"skills_match": <0-10>, "experience_level": <0-10>, "tech_stack": <0-10>, "domain_relevance": <0-10>, "disqualifiers": <0-10>, "reason": "<one sentence summary>"}}

CANDIDATE CV:
{cv_text}

JOB DESCRIPTION:
{job_description[:3000]}
"""
    response = _call_llm(prompt)
    try:
        result = json.loads(response)
        # Weighted average
        raw_score = (
            result["skills_match"] * 0.30 +
            result["experience_level"] * 0.25 +
            result["tech_stack"] * 0.20 +
            result["domain_relevance"] * 0.10 +
            result["disqualifiers"] * 0.15
        ) * 10  # Scale to 0-100

        # If disqualifiers score is below 5, halve the total
        if result["disqualifiers"] < 5:
            score = raw_score * 0.5
        else:
            score = raw_score

        reason = (
            f"Skills: {result['skills_match']}/10 | "
            f"Experience: {result['experience_level']}/10 | "
            f"Tech: {result['tech_stack']}/10 | "
            f"Domain: {result['domain_relevance']}/10 | "
            f"Disqualifiers: {result['disqualifiers']}/10 — "
            f"{result.get('reason', '')}"
        )
        return round(score, 1), reason
    except (json.JSONDecodeError, KeyError, TypeError):
        return 0.0, ""


def _call_llm(prompt: str) -> str:
    """Call OpenRouter API."""
    if not settings.llm_api_key or settings.llm_api_key == "your_llm_key_here":
        raise NotImplementedError("LLM API key not configured")

    response = httpx.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
