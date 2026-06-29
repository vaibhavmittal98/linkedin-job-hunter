import { useEffect, useState } from "react";

export default function Profile() {
  const [username, setUsername] = useState("");
  const [hasCv, setHasCv] = useState(false);
  const [cv, setCv] = useState<File | null>(null);
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
          Upload a new CV to re-score all non-applied jobs against your updated profile.
        </p>
        <input type="file" accept=".pdf" onChange={(e) => setCv(e.target.files?.[0] || null)} />
        <button className="btn" onClick={handleUpdateCv} disabled={loading || !cv} style={{ marginTop: "0.5rem" }}>
          {loading ? "Updating..." : "Update CV & Re-score"}
        </button>
        {message && <p style={{ marginTop: "0.5rem", color: "green" }}>{message}</p>}
      </div>
    </>
  );
}
