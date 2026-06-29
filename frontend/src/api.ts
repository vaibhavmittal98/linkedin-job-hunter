const API_BASE = "/api";

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface Job {
  id: number;
  linkedin_id: string | null;
  title: string;
  company: string;
  company_logo: string | null;
  company_url: string | null;
  company_website: string | null;
  location: string | null;
  url: string | null;
  apply_url: string | null;
  description: string | null;
  salary: string | null;
  posted_at: string | null;
  seniority_level: string | null;
  employment_type: string | null;
  job_function: string | null;
  industries: string | null;
  applicants_count: string | null;
  applied: boolean;
  relevance_score: number | null;
  score_reason: string | null;
  scraped_at: string | null;
}

export interface CoverLetter {
  id: number;
  job_id: number;
  content: string;
  created_at: string | null;
}

export interface UserProfile {
  id?: number;
  name: string;
  title: string;
  summary: string;
  skills: string[];
  experience: string[];
  preferences: Record<string, unknown>;
}

export async function fetchJobs(minScore = 0): Promise<Job[]> {
  const res = await fetch(`${API_BASE}/jobs?min_score=${minScore}`, { headers: authHeaders() });
  return res.json();
}

export async function fetchJob(id: number): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${id}`, { headers: authHeaders() });
  return res.json();
}

export async function triggerScrape(linkedinUrl: string, maxResults = 10, scrapeAll = false, splitByLocation = false, splitCountry = "") {
  const res = await fetch(`${API_BASE}/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ linkedin_url: linkedinUrl, max_results: maxResults, scrape_all: scrapeAll, split_by_location: splitByLocation, split_country: splitCountry }),
  });
  return res.json();
}

export async function generateCoverLetter(jobId: number): Promise<CoverLetter> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/cover-letter`, { method: "POST", headers: authHeaders() });
  return res.json();
}

export async function getCoverLetter(jobId: number): Promise<CoverLetter | null> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/cover-letter`, { headers: authHeaders() });
  if (res.status === 404) return null;
  return res.json();
}

export async function refineCoverLetter(jobId: number, message: string): Promise<{ content: string }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/cover-letter/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ message }),
  });
  return res.json();
}

export async function scoreJob(jobId: number): Promise<{ score: number; reason: string }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/score`, { method: "POST", headers: authHeaders() });
  return res.json();
}

export async function markApplied(jobId: number): Promise<void> {
  await fetch(`${API_BASE}/jobs/${jobId}/apply`, { method: "POST", headers: authHeaders() });
}

export async function markUnapplied(jobId: number): Promise<void> {
  await fetch(`${API_BASE}/jobs/${jobId}/unapply`, { method: "POST", headers: authHeaders() });
}
