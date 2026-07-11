import { useEffect, useState } from "react";

export default function Profile() {
  const [username, setUsername] = useState("");
  const [hasCv, setHasCv] = useState(false);
  const [cv, setCv] = useState<File | null>(null);
  const [rescore, setRescore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => {
        setUsername(data.username);
        setHasCv(data.has_cv);
      });
  }, []);

  const handleUpdateCv = async () => {
    if (!cv) return;
    setLoading(true);
    setMessage("");
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("cv", cv);
    formData.append("rescore", String(rescore));
    const res = await fetch("/api/auth/update-cv", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    const data = await res.json();
    if (res.ok) {
      setMessage(data.message);
      setHasCv(true);
    } else {
      setMessage(data.detail || "Upload failed");
    }
    setLoading(false);
    setCv(null);
    setRescore(false);
  };

  return (
    <>
      <h1>Profile</h1>
      <div className="card">
        <p><strong>Username:</strong> {username}</p>
        <p><strong>CV:</strong> {hasCv ? "✓ Uploaded" : "Not uploaded"}</p>
      </div>
      <div className="card">
        <h2>Update CV</h2>
        <p style={{ fontSize: "0.85rem", color: "#666", marginBottom: "0.75rem" }}>
          Upload a new CV to update your profile. Scoring of existing jobs stays
          unchanged unless you opt in to re-scoring below.
        </p>
        <input type="file" accept=".pdf" onChange={(e) => setCv(e.target.files?.[0] || null)} />
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.5rem", fontSize: "0.85rem" }}>
          <input type="checkbox" checked={rescore} onChange={(e) => setRescore(e.target.checked)} />
          Re-score non-applied jobs with the new CV (uses one LLM call per job)
        </label>
        <button className="btn" onClick={handleUpdateCv} disabled={loading || !cv} style={{ marginTop: "0.5rem" }}>
          {loading ? "Updating..." : rescore ? "Update CV & Re-score" : "Update CV"}
        </button>
        {message && <p style={{ marginTop: "0.5rem", color: "green" }}>{message}</p>}
      </div>
    </>
  );
}
