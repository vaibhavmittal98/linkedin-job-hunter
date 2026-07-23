---
name: cover-letters
description: Cover letter generation, refinement, and PDF export. Load when modifying prompts, style rules, PDF layout, or the refinement chat.
---

# Cover Letters

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
- `GET /api/jobs/{id}/cover-letter/pdf` — download PDF (requires auth, fetches via blob in frontend)

## Standalone / ad-hoc cover letters (no DB)
For jobs not in the DB, a separate stateless flow generates a letter from a
pasted job description. Nothing is persisted — the letter text round-trips
through the request body.
- `POST /api/cover-letter/adhoc` — body `{description, title?, company?}` → `{content}`
- `POST /api/cover-letter/adhoc/refine` — body `{content, message, title?, company?}` → `{content}`
- `POST /api/cover-letter/adhoc/pdf` — body `{content, title?, company?}` → PDF bytes
- `title`/`company` are optional; the "Application for X at Y" PDF line renders
  ONLY when BOTH are present.
- Generation reuses `generate_cover_letter()` (same prompt). Refine uses
  `refine_cover_letter_adhoc()` in `cover_letter.py`. PDF uses
  `generate_pdf_adhoc()` in `pdf_generator.py` (separate from `generate_pdf` so
  the job-based flow is untouched).

## Frontend
- Job-based: `JobDetail.tsx` shows the letter with a refine box + Download PDF.
- Standalone: `CoverLetter.tsx` page (route `/cover-letter`) — title/company/
  description inputs, generate, refine, Download PDF.
- Both refine boxes use the shared `components/RefineBox.tsx` (see frontend skill).

## Ask-about-job chat (separate from cover letters)
Both `JobDetail.tsx` and `CoverLetter.tsx` also have a stateless Q&A chat card
(shared `components/ChatBox.tsx`) for asking questions about the job + CV. This is
NOT the cover-letter refine flow — it's a separate feature backed by
`POST /api/jobs/{id}/chat` and `POST /api/chat`. Nothing is persisted. See the
scoring/frontend skills and `app/services/chat.py` for details.
