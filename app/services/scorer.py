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
2. **Experience Level** - Does their seniority/years match what's asked? Score strictly. If the role clearly requires substantially more experience/seniority than the CV shows (e.g. a senior/lead role and the CV is junior, or the role asks for N+ years the CV clearly lacks), score 3 or below. Do not give the benefit of the doubt.
3. **Tech Stack Overlap** - How much overlap between their tools/languages and what's required?
4. **Domain Relevance** - Is their industry/domain experience relevant?
5. **Disqualifiers** - Hard blockers the candidate CANNOT satisfy. Score 10 if none. Score 0-2 (HARD FAIL) if there is a real blocker. Check these thoroughly:
   - **Spoken/working language:** If the job description is written in a language other than English, or explicitly requires fluency/proficiency in a specific spoken language (e.g. German, French, Dutch), and the CV does NOT mention that language, treat it as a HARD blocker (score 0-2). Do not assume the candidate speaks a language that is not stated in the CV. (Note: programming languages are NOT spoken languages — judge those under Tech Stack, not here.)
   - Required certifications, licenses, security clearance, or legal work authorization the CV does not show.
   - Any other explicit "must have" requirement the candidate clearly cannot meet.
   When in doubt about whether a requirement is a hard blocker, and the CV gives no evidence the candidate meets it, lean toward scoring it as a blocker.

Return ONLY a JSON object:
{{"skills_match": <0-10>, "experience_level": <0-10>, "tech_stack": <0-10>, "domain_relevance": <0-10>, "disqualifiers": <0-10>, "reason": "<one sentence summary; if there is a hard blocker, state it explicitly>"}}

CANDIDATE CV:
{cv_text}

JOB DESCRIPTION:
{job_description[:3000]}
"""
    response = _call_llm(prompt, reasoning_effort=settings.llm_reasoning_effort)
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

        # Disqualifiers act as a gate, not just another weighted criterion:
        # - Hard blocker (<=2): cap the score very low regardless of other criteria.
        # - Soft concern (3-4): halve the total.
        if result["disqualifiers"] <= 2:
            score = min(raw_score, 15.0)
        elif result["disqualifiers"] < 5:
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


def _call_llm(prompt: str, reasoning_effort: str = "") -> str:
    """Call OpenRouter API.

    `reasoning_effort` is opt-in and used only by relevance scoring. When set
    (e.g. "high" or "xhigh"), extended thinking is requested via OpenRouter's
    `reasoning` field. Empty string = no reasoning (default), which keeps the
    cover-letter refine flow that also calls this function unchanged.
    """
    if not settings.llm_api_key or settings.llm_api_key == "your_llm_key_here":
        raise NotImplementedError("LLM API key not configured")

    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}

    response = httpx.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
