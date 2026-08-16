import { useState } from "react";
import { triggerScrape } from "../api";

export default function Scrape() {
  const [keywords, setKeywords] = useState("");
  const [locations, setLocations] = useState("");
  const [maxResults, setMaxResults] = useState<number | "">(150);
  const [scrapeAll, setScrapeAll] = useState(false);
  const [publishedAt, setPublishedAt] = useState("");
  const [jobType, setJobType] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const handleScrape = async () => {
    setLoading(true);
    setResult(null);
    const kws = keywords.split(",").map(k => k.trim()).filter(Boolean);
    const locs = locations.split(",").map(l => l.trim()).filter(Boolean);
    const res = await triggerScrape(kws, locs, Math.max(1, Number(maxResults) || 1), scrapeAll, publishedAt, jobType);
    setResult(res);
    setLoading(false);
  };

  return (
    <>
      <h1>Scrape LinkedIn Jobs</h1>
      <div className="card">
        <label>Keywords (comma-separated)</label>
        <input
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="Software Engineer, Backend Developer"
        />
        <label>Locations (comma-separated)</label>
        <input
          value={locations}
          onChange={(e) => setLocations(e.target.value)}
          placeholder="Stockholm, Netherlands, Remote"
        />
        <label>Posted within</label>
        <select value={publishedAt} onChange={(e) => setPublishedAt(e.target.value)}>
          <option value="">Any time</option>
          <option value="r86400">Last 24 hours</option>
          <option value="r604800">Last week</option>
          <option value="r2592000">Last month</option>
        </select>
        <label>Job type</label>
        <select value={jobType} onChange={(e) => setJobType(e.target.value)}>
          <option value="">Any type</option>
          <option value="full-time">Full-time</option>
          <option value="part-time">Part-time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
          <option value="temporary">Temporary</option>
        </select>
        <label>Max results</label>
        <input type="number" min={1} value={maxResults} onChange={(e) => setMaxResults(e.target.value === "" ? "" : Number(e.target.value))} disabled={scrapeAll} />
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input type="checkbox" checked={scrapeAll} onChange={(e) => setScrapeAll(e.target.checked)} style={{ width: "auto", marginBottom: 0 }} />
          Scrape all available (up to 1000)
        </label>
        <button className="btn" onClick={handleScrape} disabled={loading || !keywords}>
          {loading ? "Starting..." : "Start Scrape"}
        </button>
      </div>
      {result && (
        <div className="card">
          <p>✓ {result.message}</p>
        </div>
      )}
    </>
  );
}
