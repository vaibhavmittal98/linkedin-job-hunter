import { useState } from "react";
import { triggerScrape } from "../api";

export default function Scrape() {
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [maxResults, setMaxResults] = useState(10);
  const [scrapeAll, setScrapeAll] = useState(false);
  const [splitByLocation, setSplitByLocation] = useState(false);
  const [splitCountry, setSplitCountry] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const handleScrape = async () => {
    setLoading(true);
    setResult(null);
    const res = await triggerScrape(linkedinUrl, maxResults, scrapeAll, splitByLocation, splitCountry);
    setResult(res);
    setLoading(false);
  };

  return (
    <>
      <h1>Scrape LinkedIn Jobs</h1>
      <div className="card">
        <label>LinkedIn Search URL</label>
        <p style={{ fontSize: "0.8rem", color: "#666", marginBottom: "0.5rem" }}>
          Go to LinkedIn jobs search in an incognito window, apply your filters (keywords, location, date posted, etc.), then copy the full URL from the address bar.
        </p>
        <input
          value={linkedinUrl}
          onChange={(e) => setLinkedinUrl(e.target.value)}
          placeholder="https://www.linkedin.com/jobs/search?keywords=Software%20Engineer&location=Stockholm&..."
        />
        <label>Max results (min 10)</label>
        <input type="number" min={10} value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value) || 10)} disabled={scrapeAll} />
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input type="checkbox" checked={scrapeAll} onChange={(e) => setScrapeAll(e.target.checked)} style={{ width: "auto", marginBottom: 0 }} />
          Scrape all available {splitByLocation ? "(per city, can be expensive)" : "(up to 1000)"}
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input type="checkbox" checked={splitByLocation} onChange={(e) => setSplitByLocation(e.target.checked)} style={{ width: "auto", marginBottom: 0 }} />
          Split search by cities (bypasses 1000 limit)
        </label>
        {splitByLocation && (
          <>
            <label>Country code (e.g. SE, NL, DE)</label>
            <input value={splitCountry} onChange={(e) => setSplitCountry(e.target.value.toUpperCase())} placeholder="SE" />
          </>
        )}
        <button className="btn" onClick={handleScrape} disabled={loading || !linkedinUrl || (splitByLocation && !splitCountry)}>
          {loading ? "Starting..." : "Start Scrape"}
        </button>
        {splitByLocation && !splitCountry && (
          <p style={{ color: "red", fontSize: "0.85rem", marginTop: "0.5rem" }}>Country code is required when splitting by city.</p>
        )}
      </div>
      {result && (
        <div className="card">
          <p>✓ {result.message}</p>
        </div>
      )}
    </>
  );
}
