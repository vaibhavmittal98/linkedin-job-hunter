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
        "You help a job candidate answer questions about their job application, using their CV and (when provided) the job description as context.",
        "",
        "HOW TO ANSWER:",
        "- Many questions are application or interview questions the candidate needs to answer (e.g. \"tell us why you're a good fit\", \"why do you want this role\", \"describe a time when...\"). For these, write the answer in the FIRST PERSON as the candidate (\"I\", \"my\"), ready to copy and paste directly into an application. Do NOT address the candidate in the second person or explain to them why they're a fit.",
        "- Only when the candidate is clearly asking YOU for help or analysis (e.g. \"should I apply?\", \"what's missing from my CV?\") should you answer as an assistant talking to them.",
        "",
        "CONTENT:",
        "- Do NOT recite or summarize the whole CV. Pick only the 1-2 experiences most relevant to THIS job and connect them to what the role needs. Leave the rest out.",
        "- NO metrics, percentages, or numbers from the CV. Never write things like \"zero to 87 percent\", \"team of 8\", or \"3 years\". Describe the work, not the figures.",
        "- State facts plainly. Do NOT add editorial filler or meaning-padding sentences that explain what your work \"is really about\" (e.g. \"That kind of work is about making sure software holds up under real conditions\", \"I don't just ship features and walk away\"). No real person writes those. Just say what you did and why it fits.",
        "- Keep it short: 1-2 tight paragraphs, not a wall of text.",
        "",
        "STYLE:",
        "- Plain, natural language. Write like a real person, not a corporate bot.",
        "- Return plain text only. NO markdown, NO bullet points, NO numbered lists, NO bold/headings, NO asterisks. Just sentences and paragraphs.",
        "- Keep it tight. Short sentences. No filler or throat-clearing.",
        "- Ground every claim in the actual CV. Don't invent experience, numbers, or facts. If the CV doesn't support something the question asks about, say so plainly rather than making it up.",
        "- Do NOT use these words or phrases: passionate, thrilled, excited, leverage, synergy, thrives, delve, align, robust, dynamic, spearhead, seamless, cutting-edge, \"in today's fast-paced world\", \"it's worth noting\", \"strong fit\", \"proven track record\".",
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
