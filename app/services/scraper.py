import httpx
from app.config import settings

ACTOR_ID = "curious_coder~linkedin-jobs-scraper"
BASE_URL = f"https://api.apify.com/v2/actors/{ACTOR_ID}"


def scrape_linkedin_jobs(keywords: str, location: str = "", max_results: int = 10, scrape_all: bool = False, split_by_location: bool = False, split_country: str = "") -> list[dict]:
    """Scrape LinkedIn jobs using curious_coder/linkedin-jobs-scraper on Apify."""
    if not settings.apify_api_token or settings.apify_api_token == "your_apify_token_here":
        return _demo_data(keywords, location, max_results)

    token = settings.apify_api_token
    run_input = {
        "urls": [f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}&f_TPR=r86400"],
        "scrapeCompany": True,
    }
    if not scrape_all:
        run_input["count"] = max(max_results, 10)
    if split_by_location and split_country:
        run_input["splitByLocation"] = True
        run_input["splitCountry"] = split_country

    # Start the actor run
    start_resp = httpx.post(
        f"{BASE_URL}/runs",
        params={"token": token},
        json=run_input,
        timeout=30,
    )
    start_resp.raise_for_status()
    run_data = start_resp.json()["data"]
    run_id = run_data["id"]

    # Poll until finished (no timeout — let it run)
    import time
    while True:
        time.sleep(10)
        status_resp = httpx.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            params={"token": token},
            timeout=10,
        )
        status_resp.raise_for_status()
        status = status_resp.json()["data"]["status"]

        if status == "SUCCEEDED":
            break
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            return []

    # Fetch dataset items
    dataset_id = status_resp.json()["data"]["defaultDatasetId"]
    items_resp = httpx.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        params={"token": token},
        timeout=30,
    )
    items_resp.raise_for_status()
    items = items_resp.json()

    results = []
    for item in items:
        results.append({
            "linkedin_id": item.get("id", ""),
            "title": item.get("title", ""),
            "company": item.get("companyName", ""),
            "company_logo": item.get("companyLogo", ""),
            "company_url": item.get("companyLinkedinUrl", ""),
            "company_website": item.get("companyWebsite", ""),
            "company_description": item.get("companyDescription", ""),
            "company_address": str(item.get("companyAddress", "")),
            "company_employees_count": item.get("companyEmployeesCount"),
            "location": item.get("location", ""),
            "url": item.get("link", ""),
            "apply_url": item.get("applyUrl", ""),
            "description": item.get("descriptionText", ""),
            "description_html": item.get("descriptionHtml", ""),
            "salary": item.get("salary", ""),
            "posted_at": item.get("postedAt", ""),
            "seniority_level": item.get("seniorityLevel", ""),
            "employment_type": item.get("employmentType", ""),
            "job_function": item.get("jobFunction", ""),
            "industries": item.get("industries", ""),
            "applicants_count": item.get("applicantsCount", ""),
            "benefits": str(item.get("benefits", [])),
            "job_poster_name": item.get("jobPosterName", ""),
            "job_poster_profile_url": item.get("jobPosterProfileUrl", ""),
        })

    return results


def abort_run(run_id: str):
    """Abort a running actor to stop credit usage."""
    httpx.post(
        f"https://api.apify.com/v2/actor-runs/{run_id}/abort",
        params={"token": settings.apify_api_token},
        timeout=10,
    )


def _demo_data(keywords: str, location: str, max_results: int) -> list[dict]:
    """Generate sample job data for demo/testing."""
    samples = [
        {
            "title": f"Senior {keywords}",
            "company": "TechCorp",
            "location": location or "Remote",
            "url": "https://linkedin.com/jobs/1",
            "description": f"We are looking for a Senior {keywords} to join our team. Requirements: 5+ years experience, strong problem-solving skills, experience with modern frameworks and cloud infrastructure. You will lead projects, mentor juniors, and collaborate across teams.",
            "salary": "€70,000 - €90,000",
            "posted_at": "2 days ago",
        },
        {
            "title": f"{keywords} - Mid Level",
            "company": "StartupXYZ",
            "location": location or "Amsterdam",
            "url": "https://linkedin.com/jobs/2",
            "description": f"Join our fast-growing startup as a {keywords}. You'll work on greenfield projects with a small, talented team. Requirements: 3+ years experience, passion for clean code, CI/CD knowledge.",
            "salary": "€55,000 - €70,000",
            "posted_at": "1 week ago",
        },
        {
            "title": f"Lead {keywords}",
            "company": "BigBank Inc",
            "location": location or "London",
            "url": "https://linkedin.com/jobs/3",
            "description": f"Lead {keywords} position at a major financial institution. Manage a team of 8, drive architecture decisions, ensure compliance with security standards. 7+ years required.",
            "salary": "€95,000 - €120,000",
            "posted_at": "3 days ago",
        },
        {
            "title": f"Junior {keywords}",
            "company": "LearnTech",
            "location": location or "Berlin",
            "url": "https://linkedin.com/jobs/4",
            "description": f"Great opportunity for a Junior {keywords} to grow. Mentorship provided, modern stack, flexible hours. 0-2 years experience.",
            "salary": "€35,000 - €45,000",
            "posted_at": "5 days ago",
        },
    ]
    return samples[:max_results]
