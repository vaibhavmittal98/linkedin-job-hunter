"""Generate cover letter as a clean PDF."""

from fpdf import FPDF
import io


def _sanitize(text: str) -> str:
    """Replace unicode characters that aren't supported by standard PDF fonts."""
    replacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...", "\u2022": "-",
        "\u00a0": " ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _extract_contact(cv_text: str) -> dict:
    """Extract name and contact info from first lines of CV."""
    lines = [l.strip() for l in cv_text.strip().split("\n") if l.strip()]
    name = lines[0] if lines else "Applicant"
    if name.isupper():
        name = name.title()
    # Try to find email, phone, linkedin in first few lines
    contact_parts = []
    for line in lines[1:5]:
        if "@" in line or "+" in line or "linkedin" in line.lower():
            # Clean separators like ⋄ or other special chars
            cleaned = line.replace("⋄", "|").replace("◆", "|").replace("•", "|")
            for part in cleaned.split("|"):
                part = part.strip()
                if part:
                    # Ensure linkedin URLs have https://
                    if "linkedin.com" in part.lower() and not part.startswith("http"):
                        part = "https://" + part
                    contact_parts.append(part)
    contact = " | ".join(contact_parts) if contact_parts else ""
    return {"name": name, "contact": contact}


def generate_pdf(content: str, job_title: str, company: str, cv_text: str = "") -> bytes:
    """Generate a LaTeX-style PDF from cover letter text."""
    info = _extract_contact(cv_text) if cv_text else {"name": "Applicant", "contact": ""}

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    # Header - name
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _sanitize(info["name"]), ln=True, align="C")

    # Contact info
    if info["contact"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        parts = [p.strip() for p in info["contact"].split("|") if p.strip()]
        linkedin_url = ""
        display_parts = []
        for part in parts:
            if "linkedin.com" in part.lower():
                linkedin_url = part if part.startswith("http") else "https://" + part
            else:
                display_parts.append(part)

        contact_line = " | ".join(display_parts)
        pdf.cell(0, 5, _sanitize(contact_line), ln=True, align="C")

        if linkedin_url:
            pdf.set_text_color(40, 80, 180)
            pdf.cell(0, 5, "LinkedIn Profile", ln=True, align="C", link=linkedin_url)
            pdf.set_text_color(80, 80, 80)

    # Line separator
    pdf.ln(5)
    pdf.set_draw_color(100, 100, 100)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)

    # Application for
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 6, _sanitize(f"Application for {job_title} at {company}"), ln=True)
    pdf.ln(6)

    # Body
    pdf.set_font("Helvetica", "", 11)
    for paragraph in content.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if paragraph.lower().startswith("subject:"):
            continue
        pdf.multi_cell(0, 6, _sanitize(paragraph))
        pdf.ln(4)

    output = io.BytesIO()
    pdf.output(output)
    return output.getvalue()
