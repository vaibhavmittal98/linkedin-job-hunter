import httpx
import time
from app.config import settings

ACTOR_ID = "cheap_scraper~linkedin-job-scraper"
BASE_URL = f"https://api.apify.com/v2/actors/{ACTOR_ID}"

BRIGHTDATA_BASE = "https://api.brightdata.com/datasets/v3"


def scrape_linkedin_jobs(keywords: list[str], locations: list[str] = [], max_results: int = 150, scrape_all: bool = False, published_at: str = "") -> list[dict]:
    """Dispatch to the configured scraper backend.

    Switch backends via SCRAPER_PROVIDER in .env ("apify" | "brightdata").
    Both backends return the same list-of-dicts shape, so callers
    (`_run_scrape`) need no changes.
    """
    provider = (settings.scraper_provider or "apify").strip().lower()
    if provider == "brightdata":
        if not settings.brightdata_api_token or settings.brightdata_api_token == "your_brightdata_token_here":
            return _demo_data(keywords, locations, max_results)
        return _scrape_brightdata(keywords, locations, max_results, scrape_all, published_at)
    return _scrape_apify(keywords, locations, max_results, scrape_all, published_at)


def _scrape_apify(keywords: list[str], locations: list[str] = [], max_results: int = 150, scrape_all: bool = False, published_at: str = "") -> list[dict]:
    """Scrape LinkedIn jobs using cheap_scraper/linkedin-job-scraper on Apify."""
    if not settings.apify_api_token or settings.apify_api_token == "your_apify_token_here":
        return _demo_data(keywords, locations, max_results)

    token = settings.apify_api_token

    run_input = {
        "keyword": keywords,
        "locations": locations,
        "saveOnlyUniqueItems": True,
        "enrichCompanyData": False,
    }
    if not scrape_all:
        run_input["maxItems"] = max(max_results, 150)
    if published_at:
        run_input["publishedAt"] = published_at

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


# Map Apify's publishedAt codes -> Bright Data time_range labels.
_BRIGHTDATA_TIME_RANGE = {
    "r86400": "Past 24 hours",
    "r604800": "Past week",
    "r2592000": "Past month",
}


def _scrape_brightdata(keywords: list[str], locations: list[str] = [], max_results: int = 150, scrape_all: bool = False, published_at: str = "") -> list[dict]:
    """Scrape LinkedIn jobs via Bright Data's LinkedIn-jobs dataset.

    Flow: trigger (discover_new by keyword) -> poll progress -> download snapshot.
    Returns the same dict shape as the Apify path so callers are unaffected.
    Only core fields are populated; extras (salary, company detail, poster,
    benefits) are intentionally skipped for this temporary switch.
    """
    token = settings.brightdata_api_token
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    time_range = _BRIGHTDATA_TIME_RANGE.get(published_at, "")

    # One input row per keyword x location combination.
    locs = locations or [""]
    inputs = []
    for kw in keywords:
        for loc in locs:
            inputs.append({
                "location": loc,
                "keyword": kw,
                "country": settings.brightdata_country,
                "time_range": time_range,
                "job_type": "",
                "experience_level": "",
                "remote": "",
                "company": "",
                "location_radius": "",
            })

    params = {
        "dataset_id": settings.brightdata_dataset_id,
        "notify": "false",
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword",
    }
    # Bright Data has a per-run minimum; keep parity with Apify's floor.
    if not scrape_all:
        params["limit_per_input"] = max(max_results, 1)

    trigger = httpx.post(
        f"{BRIGHTDATA_BASE}/trigger",
        headers=headers,
        params=params,
        json=inputs,
        timeout=60,
    )
    trigger.raise_for_status()
    snapshot_id = trigger.json().get("snapshot_id")
    if not snapshot_id:
        return []

    # Poll until the snapshot is ready (no hard timeout, mirrors Apify path).
    while True:
        time.sleep(10)
        prog = httpx.get(
            f"{BRIGHTDATA_BASE}/progress/{snapshot_id}",
            headers=headers,
            timeout=30,
        )
        prog.raise_for_status()
        status = prog.json().get("status")
        if status == "ready":
            break
        if status in ("failed", "error", "canceled"):
            return []

    # Download results.
    snap = httpx.get(
        f"{BRIGHTDATA_BASE}/snapshot/{snapshot_id}",
        headers=headers,
        params={"format": "json"},
        timeout=120,
    )
    snap.raise_for_status()
    items = snap.json()
    if not isinstance(items, list):
        return []

    results = []
    for item in items:
        # job_poster can be None (not just an empty dict) — skip it anyway.
        results.append({
            "linkedin_id": str(item.get("job_posting_id") or ""),
            "title": item.get("job_title") or "",
            "company": item.get("company_name") or "",
            "company_logo": item.get("company_logo") or "",
            "company_url": item.get("company_url") or "",
            "company_website": "",
            "company_description": "",
            "company_address": "",
            "company_employees_count": None,
            "location": item.get("job_location") or "",
            "url": item.get("url") or "",
            "apply_url": item.get("apply_link") or "",
            "description": item.get("job_summary") or "",
            "description_html": item.get("job_description_formatted") or "",
            "salary": "",
            "posted_at": item.get("job_posted_date") or "",
            "seniority_level": item.get("job_seniority_level") or "",
            "employment_type": item.get("job_employment_type") or "",
            "job_function": item.get("job_function") or "",
            "industries": item.get("job_industries") or "",
            "applicants_count": str(item.get("job_num_applicants")) if item.get("job_num_applicants") is not None else "",
            "benefits": "",
            "job_poster_name": "",
            "job_poster_profile_url": "",
        })

    return results


def abort_run(run_id: str):
    """Abort a running actor to stop credit usage."""
    httpx.post(
        f"https://api.apify.com/v2/actor-runs/{run_id}/abort",
        params={"token": settings.apify_api_token},
        timeout=10,
    )


def _demo_data(keywords: list[str], locations: list[str], max_results: int) -> list[dict]:
    """Generate sample job data for demo/testing."""
    kw = keywords[0] if keywords else "Software Engineer"
    loc = locations[0] if locations else "Remote"
    samples = [
        {
            "linkedin_id": "demo1",
            "title": f"Senior {kw}",
            "company": "TechCorp",
            "company_logo": "",
            "company_url": "",
            "company_website": "",
            "company_description": "",
            "company_address": "",
            "company_employees_count": None,
            "location": loc,
            "url": "https://linkedin.com/jobs/1",
            "apply_url": "",
            "description": f"We are looking for a Senior {kw} to join our team.",
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
