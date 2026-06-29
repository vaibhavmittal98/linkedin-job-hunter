import { useState } from "react";
import { triggerScrape } from "../api";

export default function Scrape() {
  const [keywords, setKeywords] = useState("");
  const [location, setLocation] = useState("");
  const [maxResults, setMaxResults] = useState(10);
  const [scrapeAll, setScrapeAll] = useState(false);
  const [splitByLocation, setSplitByLocation] = useState(false);
  const [splitCountry, setSplitCountry] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const handleScrape = async () => {
    setLoading(true);
    setResult(null);
    const res = await triggerScrape(keywords, location, maxResults, scrapeAll, splitByLocation, splitCountry);
    setResult(res);
    setLoading(false);
  };

  return (
    <>
      <h1>Scrape LinkedIn Jobs</h1>
      <div className="card">
        <label>Keywords</label>
        <input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="e.g. Python Developer" />
        <label>Location {splitByLocation && <span style={{ fontSize: "0.8rem", color: "#888" }}>(overridden by country split)</span>}</label>
        <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Amsterdam" disabled={splitByLocation} />
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
            <label>Country code (e.g. SE, US, DE)</label>
            <input value={splitCountry} onChange={(e) => setSplitCountry(e.target.value.toUpperCase())} placeholder="SE" />
          </>
        )}
        <button className="btn" onClick={handleScrape} disabled={loading || !keywords || (splitByLocation && !splitCountry)}>
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
