import httpx
import time
from app.config import settings

ACTOR_ID = "cheap_scraper~linkedin-job-scraper"
BASE_URL = f"https://api.apify.com/v2/actors/{ACTOR_ID}"


def scrape_linkedin_jobs(linkedin_url: str, max_results: int = 10, scrape_all: bool = False, split_by_location: bool = False, split_country: str = "", last_24h: bool = False) -> list[dict]:
    """Scrape LinkedIn jobs using cheap_scraper/linkedin-job-scraper on Apify."""
    if not settings.apify_api_token or settings.apify_api_token == "your_apify_token_here":
        return _demo_data("", "", max_results)

    token = settings.apify_api_token

    run_input = {
        "startUrls": [{"url": linkedin_url}],
        "saveOnlyUniqueItems": True,
        "enrichCompanyData": False,
    }
    if not scrape_all:
        run_input["maxItems"] = max(max_results, 150)

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

    # Poll until finished (no timeout)
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
        timeout=60,
    )
    items_resp.raise_for_status()
    items = items_resp.json()

    results = []
    for item in items:
        results.append({
            "linkedin_id": item.get("jobId", ""),
            "title": item.get("jobTitle", ""),
            "company": item.get("companyName", ""),
            "company_logo": item.get("companyLogo", ""),
            "company_url": item.get("companyUrl", ""),
            "company_website": "",
            "company_description": "",
            "company_address": "",
            "company_employees_count": None,
            "location": item.get("location", ""),
            "url": item.get("jobUrl", ""),
            "apply_url": item.get("applyUrl", ""),
            "description": item.get("jobDescription", ""),
            "description_html": "",
            "salary": ", ".join(item.get("salaryInfo", [])) if item.get("salaryInfo") else "",
            "posted_at": item.get("publishedAt", ""),
            "seniority_level": item.get("experienceLevel", ""),
            "employment_type": item.get("contractType", ""),
            "job_function": item.get("workType", ""),
            "industries": item.get("sector", ""),
            "applicants_count": item.get("applicationsCount", ""),
            "benefits": "",
            "job_poster_name": item.get("posterFullName", ""),
            "job_poster_profile_url": item.get("posterProfileUrl", ""),
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
            "linkedin_id": "demo1",
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "company_logo": "",
            "company_url": "",
            "company_website": "",
            "company_description": "",
            "company_address": "",
            "company_employees_count": None,
            "location": location or "Remote",
            "url": "https://linkedin.com/jobs/1",
            "apply_url": "",
            "description": "We are looking for a Senior Software Engineer to join our team.",
            "description_html": "",
            "salary": "",
            "posted_at": "2026-06-28",
            "seniority_level": "Mid-Senior level",
            "employment_type": "Full-time",
            "job_function": "Engineering",
            "industries": "Technology",
            "applicants_count": "50",
            "benefits": "",
            "job_poster_name": "",
            "job_poster_profile_url": "",
        },
    ]
    return samples[:max_results]
