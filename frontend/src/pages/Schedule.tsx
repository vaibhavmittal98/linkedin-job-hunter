import { useEffect, useState } from "react";

interface Schedule {
  id: string;
  keywords: string;
  location: string;
  hour: number;
  minute: number;
  scrape_all: boolean;
}

interface RunHistory {
  ran_at: string;
  jobs_added: number;
  total_scraped: number;
  status: string;
  error: string | null;
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function SchedulePage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [keywords, setKeywords] = useState("");
  const [location, setLocation] = useState("");
  const [maxResults, setMaxResults] = useState(10);
  const [scrapeAll, setScrapeAll] = useState(false);
  const [hour, setHour] = useState("2");
  const [minute, setMinute] = useState("0");
  const [hourTouched, setHourTouched] = useState(false);
  const [minuteTouched, setMinuteTouched] = useState(false);
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<RunHistory[]>([]);
  const [selectedSchedule, setSelectedSchedule] = useState<string | null>(null);

  const loadSchedules = () => {
    fetch("/api/schedules", { headers: authHeaders() })
      .then((r) => r.json())
      .then(setSchedules);
  };

  useEffect(() => { loadSchedules(); }, []);

  const handleCreate = async () => {
    const res = await fetch("/api/schedules", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ keywords, location, max_results: maxResults, scrape_all: scrapeAll, hour: Number(hour) || 0, minute: Number(minute) || 0 }),
    });
    const data = await res.json();
    if (res.ok) {
      setMessage(`Scheduled: runs daily at ${String(Number(hour) || 0).padStart(2, "0")}:${String(Number(minute) || 0).padStart(2, "0")}`);
      loadSchedules();
    } else {
      setMessage(data.detail || "Failed");
    }
  };

  const handleDelete = async (id: string) => {
    await fetch(`/api/schedules/${id}`, { method: "DELETE", headers: authHeaders() });
    if (selectedSchedule === id) { setSelectedSchedule(null); setHistory([]); }
    loadSchedules();
  };

  const handleShowHistory = async (id: string) => {
    if (selectedSchedule === id) { setSelectedSchedule(null); setHistory([]); return; }
    setSelectedSchedule(id);
    const res = await fetch(`/api/schedules/${id}/history`, { headers: authHeaders() });
    setHistory(await res.json());
  };

  return (
    <>
      <h1>Scheduled Scrapes</h1>
      <p style={{ color: "#666", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
        Schedule automatic daily scrapes. Only jobs posted in the last 24 hours are fetched, and duplicates are skipped automatically.
        New jobs are scored against your CV as they come in.
      </p>

      <div className="card">
        <h2>Create Schedule</h2>
        <label>Keywords</label>
        <input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="e.g. Software Engineer" />
        <label>Location</label>
        <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Stockholm" />
        <label>Max results (min 10)</label>
        <input type="number" min={10} value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value) || 10)} disabled={scrapeAll} />
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input type="checkbox" checked={scrapeAll} onChange={(e) => setScrapeAll(e.target.checked)} style={{ width: "auto", marginBottom: 0 }} />
          Scrape all available
        </label>
        <label>Run at (24h, CET timezone)</label>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input type="text" maxLength={2} value={hour} onChange={(e) => setHour(e.target.value.replace(/\D/g, "").slice(0, 2))} placeholder="6" style={{ width: "60px", textAlign: "center" }} />
          <span style={{ alignSelf: "center" }}>:</span>
          <input type="text" maxLength={2} value={minute} onChange={(e) => setMinute(e.target.value.replace(/\D/g, "").slice(0, 2))} placeholder="0" style={{ width: "60px", textAlign: "center" }} />
        </div>
        <button className="btn" onClick={handleCreate} disabled={!keywords}>Create Schedule</button>
        {message && <p style={{ marginTop: "0.5rem", color: "green" }}>{message}</p>}
      </div>

      <div className="card">
        <h2>Active Schedules</h2>
        {schedules.length === 0 && <p className="placeholder-text">No scheduled scrapes yet.</p>}
        {schedules.map((s) => (
          <div key={s.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid #eee" }}>
              <div style={{ cursor: "pointer" }} onClick={() => handleShowHistory(s.id)}>
                <strong>{s.keywords}</strong> — {s.location || "Any location"}
                <p style={{ fontSize: "0.8rem", color: "#666" }}>
                  Runs daily at {String(s.hour).padStart(2, "0")}:{String(s.minute).padStart(2, "0")} | {s.scrape_all ? "All available" : "Limited"}
                </p>
              </div>
              <button className="btn btn-outline" onClick={() => handleDelete(s.id)} style={{ fontSize: "0.8rem" }}>Delete</button>
            </div>
            {selectedSchedule === s.id && (
              <div style={{ padding: "0.75rem", background: "#f9f9f9", borderRadius: "6px", marginBottom: "0.5rem" }}>
                <strong>Run History</strong>
                {history.length === 0 && <p style={{ fontSize: "0.85rem", color: "#888" }}>No runs yet.</p>}
                {history.map((h, i) => (
                  <div key={i} style={{ fontSize: "0.85rem", padding: "0.25rem 0", borderBottom: "1px solid #eee" }}>
                    <span>{h.ran_at}</span> — <span style={{ color: h.status === "success" ? "green" : "red" }}>{h.status}</span> — Added {h.jobs_added} / Scraped {h.total_scraped}
                    {h.error && <p style={{ color: "red", fontSize: "0.8rem" }}>{h.error}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
