"""Stateless Q&A chat about a job and the candidate's CV.

Nothing is persisted. The full message history round-trips through the request
body (like the ad-hoc cover letter flow). Context is always built server-side:
- CV comes from the authenticated user's stored cv_text.
- Job context (title/company/description) is optional; when absent the chat
  operates with the CV alone.
"""

import httpx
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _build_system_prompt(cv_text: str, title: str = "", company: str = "", description: str = "") -> str:
    """Compose the system prompt from CV + optional job context."""
    parts = [
        "You are a helpful assistant answering questions about a job application.",
        "Use the candidate's CV and, when provided, the job description as context.",
        "Be concise, direct, and honest. If the CV or job description doesn't cover "
        "something the user asks about, say so rather than inventing details.",
        "",
        "CANDIDATE CV:",
        cv_text or "(no CV provided)",
    ]

    job_lines = []
    if title:
        job_lines.append(f"- Title: {title}")
    if company:
        job_lines.append(f"- Company: {company}")
    if description:
        job_lines.append(f"- Description: {description[:3000]}")

    if job_lines:
        parts += ["", "JOB:", *job_lines]
    else:
        parts += ["", "No job description is available. Answer using only the CV."]

    return "\n".join(parts)


def _call_llm_messages(messages: list[dict]) -> str:
    """Call OpenRouter with a full message array (system + conversation).

    Separate from scorer._call_llm (which only sends a single user prompt) so
    the scoring/cover-letter flows are untouched.
    """
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
            "messages": messages,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def chat_about_job(
    history: list[dict],
    cv_text: str,
    title: str = "",
    company: str = "",
    description: str = "",
) -> str:
    """Answer questions given the CV and optional job context.

    `history` is the running conversation as a list of {role, content} dicts
    (roles: "user" / "assistant"). Only user/assistant turns are forwarded; the
    system prompt is always rebuilt server-side.
    """
    system_prompt = _build_system_prompt(cv_text, title, company, description)
    convo = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    messages = [{"role": "system", "content": system_prompt}, *convo]
    return _call_llm_messages(messages)
