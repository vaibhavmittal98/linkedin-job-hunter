---
name: linkedin-cover-letters
description: Use when modifying cover letter generation, refinement, PDF export, style rules, or the ad-hoc letter flow in linkedin-job-hunter.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin-job-hunter, cover-letters, llm, pdf, openrouter]
    related_skills: [linkedin-project-overview, linkedin-frontend, linkedin-scoring]
---

# Cover Letters — LinkedIn Job Hunter

## Generation (`app/services/cover_letter.py`)

### Style Rules (in prompt)
- Conversational, professional, not stiff
- NO metrics, percentages, numbers from CV
- Don't list or repeat CV bullet points
- Show WHY you'd be effective, not WHAT you did
- Max 3 paragraphs, under 150 words
- No subject line. Start with "Hi [Company] Team,"
- NO buzzwords: passionate, thrilled, excited, leverage, synergy, thrives
- Don't be pretentious or abstract
- End with "Best regards,\n[Name]" (extracted from CV first line)

### Name Extraction
```python
def _get_name(cv_text: str) -> str:
    lines = [l.strip() for l in cv_text.strip().split("\n") if l.strip()]
    name = lines[0] if lines else "Applicant"
    if name.isupper():
        name = name.title()
    return name
```

## Refinement (`POST /api/jobs/{id}/cover-letter/refine`)
- Takes `{"message": "make it shorter"}` 
- Sends current letter + CV + job + feedback to LLM
- Same style rules enforced in refinement prompt
- Updates letter in-place in DB

## PDF Export (`app/services/pdf_generator.py`)

### Layout
1. Name (bold, centered, 16pt Helvetica)
2. Contact info (9pt, gray) — phone, location, email (separated by |)
3. "LinkedIn Profile" (blue, clickable link)
4. Horizontal line separator
5. "Application for [Title] at [Company]" (italic)
6. Letter body (11pt, paragraphs)

### Contact Extraction
- Parses first 5 lines of CV for @, +, linkedin
- Splits by ⋄ or | characters
- Adds `https://` to LinkedIn URLs
- LinkedIn rendered as clickable link via `pdf.cell(link=url)`

### Unicode Handling
`_sanitize()` replaces curly quotes, em-dashes, etc. with latin-1 compatible chars.

## Endpoints
- `POST /api/jobs/{id}/cover-letter` — generate (or return existing)
- `POST /api/jobs/{id}/cover-letter/refine` — iterative editing
- `GET /api/jobs/{id}/cover-letter` — get existing
- `GET /api/jobs/{id}/cover-letter/pdf` — download PDF (requires auth, fetched via blob in frontend)

## Standalone / Ad-Hoc Cover Letters (no DB)
For jobs not in the DB. Nothing persisted — letter text round-trips through the request body.
- `POST /api/cover-letter/adhoc` — body `{description, title?, company?}` → `{content}`
- `POST /api/cover-letter/adhoc/refine` — body `{content, message, title?, company?}` → `{content}`
- `POST /api/cover-letter/adhoc/pdf` — body `{content, title?, company?}` → PDF bytes
- `title`/`company` are optional; the "Application for X at Y" PDF line renders ONLY when BOTH are present.
- PDF uses `generate_pdf_adhoc()` (separate from `generate_pdf` so the job-based flow is untouched).

## Frontend
- Job-based: `JobDetail.tsx` shows the letter with a refine box + Download PDF.
- Standalone: `CoverLetter.tsx` page (route `/cover-letter`) — title/company/description inputs, generate, refine, Download PDF.
- Both refine boxes use the shared `components/RefineBox.tsx`.
- Both pages also have a stateless Q&A chat card (`components/ChatBox.tsx`) — separate from the cover letter refine flow.

## Common Pitfalls
1. **Mixing refine with chat** — the cover letter refine endpoint (`/refine`) and the Q&A chat (`/chat`) are separate features with different backends. Don't confuse them.
2. **Style rules drifting** — both generation and refinement prompts enforce the same style rules. If you change one, change both.
3. **PDF contact extraction is fragile** — relies on CV first 5 lines having @, +, linkedin. If the CV format changes, extraction may break silently.
4. **Ad-hoc vs job-based PDF generators** — `generate_pdf_adhoc()` and `generate_pdf()` are separate functions. A fix in one doesn't automatically apply to the other.
5. **Unicode in PDF** — `_sanitize()` handles common curly quotes/dashes but may miss edge cases. Test with non-ASCII CVs.