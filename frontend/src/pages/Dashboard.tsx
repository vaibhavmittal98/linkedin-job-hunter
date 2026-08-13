import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchJobs, fetchFilterOptions, Job } from "../api";

const PAGE_SIZE = 50;

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);

  const [minScore, setMinScore] = useState(0);
  const [search, setSearch] = useState("");
  const [seniorityFilter, setSeniorityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [appliedFilter, setAppliedFilter] = useState("not_applied");
  const [timeFilter, setTimeFilter] = useState("");
  const [sponsorFilter, setSponsorFilter] = useState("");

  // Debounced copies of the free-text inputs so typing doesn't spam the API.
  const [debouncedSearch, setDebouncedSearch] = useState(search);
  const [debouncedLocation, setDebouncedLocation] = useState(locationFilter);

  const [seniorityLevels, setSeniorityLevels] = useState<string[]>([]);
  const [employmentTypes, setEmploymentTypes] = useState<string[]>([]);

  // Load dropdown options once.
  useEffect(() => {
    fetchFilterOptions().then((opts) => {
      setSeniorityLevels(opts.seniority_levels);
      setEmploymentTypes(opts.employment_types);
    });
  }, []);

  // Debounce text inputs (300ms).
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);
  useEffect(() => {
    const t = setTimeout(() => setDebouncedLocation(locationFilter), 300);
    return () => clearTimeout(t);
  }, [locationFilter]);

  // Reset to first page whenever any filter changes.
  useEffect(() => {
    setPage(0);
  }, [minScore, debouncedSearch, seniorityFilter, typeFilter, debouncedLocation, appliedFilter, timeFilter, sponsorFilter]);

  // Fetch the current page from the server.
  useEffect(() => {
    setLoading(true);
    fetchJobs({
      minScore,
      search: debouncedSearch,
      seniority: seniorityFilter,
      employmentType: typeFilter,
      location: debouncedLocation,
      applied: appliedFilter,
      timePeriod: timeFilter,
      indSponsor: sponsorFilter,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    })
      .then((res) => {
        setJobs(res.items);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  }, [minScore, debouncedSearch, seniorityFilter, typeFilter, debouncedLocation, appliedFilter, timeFilter, sponsorFilter, page]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const from = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const to = Math.min(total, (page + 1) * PAGE_SIZE);

  // Compute a compact list of page numbers to show (with ellipses).
  const pageNumbers = useMemo(() => {
    const pages: (number | "…")[] = [];
    const window = 2; // pages on each side of current
    for (let i = 0; i < totalPages; i++) {
      if (i === 0 || i === totalPages - 1 || (i >= page - window && i <= page + window)) {
        pages.push(i);
      } else if (pages[pages.length - 1] !== "…") {
        pages.push("…");
      }
    }
    return pages;
  }, [totalPages, page]);

  return (
    <>
      <h1>Jobs ({total})</h1>

      <div className="filters">
        <input
          type="text"
          placeholder="Search title or company..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="filter-row">
          <select value={seniorityFilter} onChange={(e) => setSeniorityFilter(e.target.value)}>
            <option value="">All Seniority</option>
            {seniorityLevels.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="">All Types</option>
            {employmentTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Filter by location..."
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            style={{ width: "180px", marginBottom: 0 }}
          />
          <select value={appliedFilter} onChange={(e) => setAppliedFilter(e.target.value)}>
            <option value="">All</option>
            <option value="applied">Applied</option>
            <option value="not_applied">Not Applied</option>
          </select>
          <select value={timeFilter} onChange={(e) => setTimeFilter(e.target.value)}>
            <option value="">Any time</option>
            <option value="day">Last 24 hours</option>
            <option value="week">Last week</option>
            <option value="month">Last month</option>
          </select>
          <select value={sponsorFilter} onChange={(e) => setSponsorFilter(e.target.value)}>
            <option value="">All companies</option>
            <option value="sponsor">IND sponsors only</option>
            <option value="non_sponsor">Non-sponsors</option>
          </select>
          <div className="score-filter">
            <label>Min score: {minScore}</label>
            <input
              type="range"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
            />
          </div>
        </div>
      </div>

      {!loading && total > 0 && (
        <p className="results-summary" style={{ color: "#555", fontSize: "0.9rem" }}>
          Showing {from}–{to} of {total}
        </p>
      )}

      {loading && <p className="empty">Loading…</p>}
      {!loading && total === 0 && <p className="empty">No jobs match your filters.</p>}

      <div className="job-list">
        {jobs.map((job) => (
          <Link to={`/jobs/${job.id}`} key={job.id} className="job-card-link" target="_blank" rel="noopener noreferrer">
            <div className="job-card">
              <div className="job-card-header">
                {job.company_logo && (
                  <img src={job.company_logo} alt={job.company} className="company-logo" />
                )}
                <div>
                  <h3>{job.title}</h3>
                  <p className="company-name">{job.company}</p>
                </div>
              </div>
              <div className="job-card-meta">
                <span>📍 {job.location}</span>
                {job.seniority_level && <span>📊 {job.seniority_level}</span>}
                {job.employment_type && <span>💼 {job.employment_type}</span>}
                {job.posted_at && <span>📅 {(() => {
                  const d = new Date(job.posted_at);
                  if (isNaN(d.getTime())) return job.posted_at;
                  const now = new Date();
                  const diff = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
                  if (diff === 0) return "Today";
                  if (diff === 1) return "Yesterday";
                  if (diff < 7) return `${diff} days ago`;
                  if (diff < 30) { const w = Math.floor(diff / 7); return `${w} ${w === 1 ? "week" : "weeks"} ago`; }
                  return d.toLocaleDateString();
                })()}</span>}
                {job.applicants_count && <span>👥 {job.applicants_count} applicants</span>}
              </div>
              {job.relevance_score !== null && (
                <p className="score">Relevance: {job.relevance_score.toFixed(0)}/100</p>
              )}
            </div>
          </Link>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="pagination" style={{ display: "flex", gap: "0.5rem", alignItems: "center", justifyContent: "center", marginTop: "1.5rem", flexWrap: "wrap" }}>
          <button className="btn btn-outline" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>
            ← Prev
          </button>
          {pageNumbers.map((p, i) =>
            p === "…" ? (
              <span key={`ellipsis-${i}`} style={{ padding: "0 0.25rem" }}>…</span>
            ) : (
              <button
                key={p}
                className={p === page ? "btn" : "btn btn-outline"}
                onClick={() => setPage(p)}
                aria-current={p === page ? "page" : undefined}
              >
                {p + 1}
              </button>
            )
          )}
          <button className="btn btn-outline" disabled={page >= totalPages - 1} onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}>
            Next →
          </button>
        </div>
      )}
    </>
  );
}
