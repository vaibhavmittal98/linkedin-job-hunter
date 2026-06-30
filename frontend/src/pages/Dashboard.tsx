import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchJobs, Job } from "../api";

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [minScore, setMinScore] = useState(0);
  const [search, setSearch] = useState("");
  const [seniorityFilter, setSeniorityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [appliedFilter, setAppliedFilter] = useState("not_applied");
  const [timeFilter, setTimeFilter] = useState("");

  useEffect(() => {
    fetchJobs(minScore).then(setJobs);
  }, [minScore]);

  const filtered = jobs.filter((job) => {
    const matchesSearch =
      !search ||
      job.title.toLowerCase().includes(search.toLowerCase()) ||
      job.company.toLowerCase().includes(search.toLowerCase());
    const matchesSeniority =
      !seniorityFilter || job.seniority_level === seniorityFilter;
    const matchesType = !typeFilter || job.employment_type === typeFilter;
    const matchesLocation =
      !locationFilter || (job.location || "").toLowerCase().includes(locationFilter.toLowerCase());
    const matchesApplied =
      !appliedFilter ||
      (appliedFilter === "applied" && job.applied) ||
      (appliedFilter === "not_applied" && !job.applied);
    const matchesTime = (() => {
      if (!timeFilter || !job.posted_at) return true;
      const posted = new Date(job.posted_at);
      const now = new Date();
      const diffDays = (now.getTime() - posted.getTime()) / (1000 * 60 * 60 * 24);
      if (timeFilter === "day") return diffDays <= 1;
      if (timeFilter === "week") return diffDays <= 7;
      if (timeFilter === "month") return diffDays <= 30;
      return true;
    })();
    return matchesSearch && matchesSeniority && matchesType && matchesLocation && matchesApplied && matchesTime;
  });

  const seniorityLevels = [...new Set(jobs.map((j) => j.seniority_level).filter(Boolean))];
  const employmentTypes = [...new Set(jobs.map((j) => j.employment_type).filter(Boolean))];

  return (
    <>
      <h1>Jobs ({filtered.length})</h1>

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
              <option key={s} value={s!}>{s}</option>
            ))}
          </select>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="">All Types</option>
            {employmentTypes.map((t) => (
              <option key={t} value={t!}>{t}</option>
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

      {filtered.length === 0 && <p className="empty">No jobs match your filters.</p>}

      <div className="job-list">
        {[...filtered]
          .sort((a, b) => (b.relevance_score ?? -1) - (a.relevance_score ?? -1))
          .map((job) => (
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
    </>
  );
}
