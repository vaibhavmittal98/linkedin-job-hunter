import { useEffect, useState } from "react";

interface Schedule {
  id: string;
  keywords: string[];
  locations: string[];
  hour: number;
  minute: number;
  max_results: number;
  scrape_all: boolean;
  published_at: string;
  job_type: string;
  frequency: string;
  day_of_week: string;
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
  const [locations, setLocations] = useState("");
  const [maxResults, setMaxResults] = useState<number | "">(150);
  const [scrapeAll, setScrapeAll] = useState(false);
  const [publishedAt, setPublishedAt] = useState("r86400");
  const [jobType, setJobType] = useState("");
  const [frequency, setFrequency] = useState("daily");
  const [dayOfWeek, setDayOfWeek] = useState("mon");
  const [hour, setHour] = useState("2");
  const [minute, setMinute] = useState("0");
  const [message, setMessage] = useState("");
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [history, setHistory] = useState<RunHistory[]>([]);
  const [selectedSchedule, setSelectedSchedule] = useState<string | null>(null);

  const loadSchedules = () => {
    fetch("/api/schedules", { headers: authHeaders() })
      .then((r) => r.json())
      .then(setSchedules);
  };

  useEffect(() => { loadSchedules(); }, []);

  const resetForm = () => {
    setEditingId(null);
    setKeywords("");
    setLocations("");
    setMaxResults(150);
    setScrapeAll(false);
    setPublishedAt("r86400");
    setJobType("");
    setFrequency("daily");
    setDayOfWeek("mon");
    setHour("2");
    setMinute("0");
  };

  const startEdit = (s: Schedule) => {
    setEditingId(s.id);
    setKeywords(s.keywords.join(", "));
    setLocations(s.locations.join(", "));
    setMaxResults(s.max_results);
    setScrapeAll(s.scrape_all);
    setPublishedAt(s.published_at || "r86400");
    setJobType(s.job_type || "");
    setFrequency(s.frequency || "daily");
    setDayOfWeek(s.day_of_week || "mon");
    setHour(String(s.hour));
    setMinute(String(s.minute));
    setMessage("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCreate = async () => {
    setCreating(true);
    setMessage("");
    try {
      const kws = keywords.split(",").map(k => k.trim()).filter(Boolean);
      const locs = locations.split(",").map(l => l.trim()).filter(Boolean);
      if (kws.length === 0) {
        setMessage("Please enter at least one keyword");
        return;
      }
      const body = JSON.stringify({ keywords: kws, locations: locs, max_results: Math.max(1, Number(maxResults) || 1), scrape_all: scrapeAll, published_at: publishedAt, job_type: jobType, frequency, day_of_week: dayOfWeek, hour: Number(hour) || 0, minute: Number(minute) || 0 });
      const res = await fetch(editingId ? `/api/schedules/${editingId}` : "/api/schedules", {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body,
      });
      const data = await res.json();
      if (res.ok) {
        const freqStr = frequency === "weekly" ? `weekly on ${dayOfWeek}` : "daily";
        setMessage(`${editingId ? "Updated" : "Scheduled"}: runs ${freqStr} at ${String(Number(hour) || 0).padStart(2, "0")}:${String(Number(minute) || 0).padStart(2, "0")}`);
        resetForm();
        loadSchedules();
      } else {
        setMessage(data.detail || `Error: ${res.status}`);
      }
    } catch (err: any) {
      setMessage(err.message || "Network error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    await fetch(`/api/schedules/${id}`, { method: "DELETE", headers: authHeaders() });
    if (selectedSchedule === id) { setSelectedSchedule(null); setHistory([]); }
    if (editingId === id) resetForm();
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
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
        Schedule automatic daily scrapes. Duplicates are skipped automatically. New jobs are scored against your CV as they come in.
      </p>

      <div className="card">
        <h2>{editingId ? "Edit Schedule" : "Create Schedule"}</h2>
        <label>Keywords (comma-separated)</label>
        <input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="Software Engineer, Backend Developer" />
        <label>Locations (comma-separated)</label>
        <input value={locations} onChange={(e) => setLocations(e.target.value)} placeholder="Stockholm, Netherlands" />
        <label>Max results</label>
        <input type="number" min={1} value={maxResults} onChange={(e) => setMaxResults(e.target.value === "" ? "" : Number(e.target.value))} disabled={scrapeAll} />
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input type="checkbox" checked={scrapeAll} onChange={(e) => setScrapeAll(e.target.checked)} style={{ width: "auto", marginBottom: 0 }} />
          Scrape all available
        </label>
        <label>Job type</label>
        <select value={jobType} onChange={(e) => setJobType(e.target.value)} style={{ marginBottom: "0.75rem" }}>
          <option value="">Any type</option>
          <option value="full-time">Full-time</option>
          <option value="part-time">Part-time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
          <option value="temporary">Temporary</option>
        </select>
        <label>Frequency</label>
        <select value={frequency} onChange={(e) => { setFrequency(e.target.value); setPublishedAt(e.target.value === "weekly" ? "r604800" : "r86400"); }} style={{ marginBottom: "0.75rem" }}>
          <option value="daily">Daily (scrapes last 24h)</option>
          <option value="weekly">Weekly (scrapes last week)</option>
        </select>
        {frequency === "weekly" && (
          <>
            <label>Day of week</label>
            <select value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value)} style={{ marginBottom: "0.75rem" }}>
              <option value="mon">Monday</option>
              <option value="tue">Tuesday</option>
              <option value="wed">Wednesday</option>
              <option value="thu">Thursday</option>
              <option value="fri">Friday</option>
              <option value="sat">Saturday</option>
              <option value="sun">Sunday</option>
            </select>
          </>
        )}
        <label>Run at (24h, CET timezone)</label>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input type="text" maxLength={2} value={hour} onChange={(e) => setHour(e.target.value.replace(/\D/g, "").slice(0, 2))} placeholder="2" style={{ width: "60px", textAlign: "center" }} />
          <span style={{ alignSelf: "center" }}>:</span>
          <input type="text" maxLength={2} value={minute} onChange={(e) => setMinute(e.target.value.replace(/\D/g, "").slice(0, 2))} placeholder="0" style={{ width: "60px", textAlign: "center" }} />
        </div>
        <button className="btn" onClick={handleCreate} disabled={!keywords || creating}>{creating ? (editingId ? "Saving..." : "Creating...") : (editingId ? "Save Changes" : "Create Schedule")}</button>
        {editingId && <button className="btn btn-outline" onClick={resetForm} disabled={creating} style={{ marginLeft: "0.5rem" }}>Cancel</button>}
        {message && <p style={{ marginTop: "0.5rem", color: message.startsWith("Scheduled") || message.startsWith("Updated") ? "green" : "red" }}>{message}</p>}
      </div>

      <div className="card">
        <h2>Active Schedules</h2>
        {schedules.length === 0 && <p className="placeholder-text">No scheduled scrapes yet.</p>}
        {schedules.map((s) => (
          <div key={s.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
              <div style={{ cursor: "pointer" }} onClick={() => handleShowHistory(s.id)}>
                <strong>{s.keywords.join(", ")}</strong> — {s.locations.join(", ") || "Any location"}
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Runs {s.frequency === "weekly" ? `weekly on ${s.day_of_week}` : "daily"} at {String(s.hour).padStart(2, "0")}:{String(s.minute).padStart(2, "0")} | {s.scrape_all ? "All available" : "Limited"} | {s.published_at === "r86400" ? "Last 24h" : s.published_at === "r604800" ? "Last week" : s.published_at === "r2592000" ? "Last month" : "Any time"}{s.job_type ? ` | ${s.job_type.charAt(0).toUpperCase()}${s.job_type.slice(1)}` : ""}
                </p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn btn-outline" onClick={() => startEdit(s)} style={{ fontSize: "0.8rem" }}>Edit</button>
                <button className="btn btn-outline" onClick={() => handleDelete(s.id)} style={{ fontSize: "0.8rem" }}>Delete</button>
              </div>
            </div>
            {selectedSchedule === s.id && (
              <div style={{ padding: "0.75rem", background: "var(--surface-2)", borderRadius: "6px", marginBottom: "0.5rem" }}>
                <strong>Run History</strong>
                {history.length === 0 && <p style={{ fontSize: "0.85rem", color: "var(--text-dim)" }}>No runs yet.</p>}
                {history.map((h, i) => (
                  <div key={i} style={{ fontSize: "0.85rem", padding: "0.25rem 0", borderBottom: "1px solid var(--border)" }}>
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
