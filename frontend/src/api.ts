const API_BASE = "/api";

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(url, { ...options, headers: { ...authHeaders(), ...options.headers } });
  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login";
  }
  return res;
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
  ind_sponsor: boolean | null;
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

export interface JobFilters {
  minScore?: number;
  search?: string;
  seniority?: string;
  employmentType?: string;
  location?: string;
  applied?: string; // "", "applied", "not_applied"
  timePeriod?: string; // "", "day", "week", "month"
  indSponsor?: string; // "", "sponsor", "non_sponsor"
  limit?: number;
  offset?: number;
}

export interface JobListResponse {
  items: Job[];
  total: number;
  limit: number;
  offset: number;
}

export interface FilterOptions {
  seniority_levels: string[];
  employment_types: string[];
}

export async function fetchJobs(filters: JobFilters = {}): Promise<JobListResponse> {
  const params = new URLSearchParams();
  if (filters.minScore) params.set("min_score", String(filters.minScore));
  if (filters.search) params.set("search", filters.search);
  if (filters.seniority) params.set("seniority", filters.seniority);
  if (filters.employmentType) params.set("employment_type", filters.employmentType);
  if (filters.location) params.set("location", filters.location);
  if (filters.applied) params.set("applied", filters.applied);
  if (filters.timePeriod) params.set("time_period", filters.timePeriod);
  if (filters.indSponsor) params.set("ind_sponsor", filters.indSponsor);
  params.set("limit", String(filters.limit ?? 50));
  params.set("offset", String(filters.offset ?? 0));
  const res = await authFetch(`${API_BASE}/jobs?${params.toString()}`);
  return res.json();
}

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const res = await authFetch(`${API_BASE}/jobs/filter-options`);
  return res.json();
}

export async function fetchJob(id: number): Promise<Job> {
  const res = await authFetch(`${API_BASE}/jobs/${id}`);
  return res.json();
}

export async function triggerScrape(keywords: string[], locations: string[], maxResults = 150, scrapeAll = false, publishedAt = "", jobType = "") {
  const res = await authFetch(`${API_BASE}/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keywords, locations, max_results: maxResults, scrape_all: scrapeAll, published_at: publishedAt, job_type: jobType }),
  });
  return res.json();
}

export async function generateCoverLetter(jobId: number): Promise<CoverLetter> {
  const res = await authFetch(`${API_BASE}/jobs/${jobId}/cover-letter`, { method: "POST" });
  return res.json();
}

export async function getCoverLetter(jobId: number): Promise<CoverLetter | null> {
  const res = await authFetch(`${API_BASE}/jobs/${jobId}/cover-letter`);
  if (res.status === 404) return null;
  return res.json();
}

export async function refineCoverLetter(jobId: number, message: string): Promise<{ content: string }> {
  const res = await authFetch(`${API_BASE}/jobs/${jobId}/cover-letter/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return res.json();
}

export async function scoreJob(jobId: number): Promise<{ score: number; reason: string }> {
  const res = await authFetch(`${API_BASE}/jobs/${jobId}/score`, { method: "POST" });
  return res.json();
}

export async function markApplied(jobId: number): Promise<void> {
  await authFetch(`${API_BASE}/jobs/${jobId}/apply`, { method: "POST" });
}

export async function markUnapplied(jobId: number): Promise<void> {
  await authFetch(`${API_BASE}/jobs/${jobId}/unapply`, { method: "POST" });
}

export async function deleteJob(jobId: number): Promise<void> {
  await authFetch(`${API_BASE}/jobs/${jobId}`, { method: "DELETE" });
}


export async function generateAdhocCoverLetter(
  description: string,
  title?: string,
  company?: string
): Promise<{ content: string }> {
  const res = await authFetch(`${API_BASE}/cover-letter/adhoc`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description, title: title || null, company: company || null }),
  });
  return res.json();
}

export async function refineAdhocCoverLetter(
  content: string,
  message: string,
  title?: string,
  company?: string
): Promise<{ content: string }> {
  const res = await authFetch(`${API_BASE}/cover-letter/adhoc/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, message, title: title || null, company: company || null }),
  });
  return res.json();
}

export async function downloadAdhocCoverLetterPdf(
  content: string,
  title?: string,
  company?: string
): Promise<void> {
  const token = localStorage.getItem("token");
  const res = await fetch(`${API_BASE}/cover-letter/adhoc/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ content, title: title || null, company: company || null }),
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = company ? `cover_letter_${company.replace(/ /g, "_")}.pdf` : "cover_letter.pdf";
  a.click();
  URL.revokeObjectURL(url);
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** Chat about a specific job (CV + that job's description as context). */
export async function jobChat(
  jobId: number,
  messages: ChatMessage[]
): Promise<{ reply: string }> {
  const res = await authFetch(`${API_BASE}/jobs/${jobId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  return res.json();
}

/** Standalone chat (CV context + optional pasted job description). */
export async function chat(
  messages: ChatMessage[],
  description?: string,
  title?: string,
  company?: string
): Promise<{ reply: string }> {
  const res = await authFetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      description: description || null,
      title: title || null,
      company: company || null,
    }),
  });
  return res.json();
}
