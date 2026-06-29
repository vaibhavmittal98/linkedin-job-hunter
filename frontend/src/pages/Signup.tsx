import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Signup() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [cv, setCv] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cv) { setError("Please upload your CV"); return; }
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    formData.append("cv", cv);

    const res = await fetch("/api/auth/signup", { method: "POST", body: formData });
    if (!res.ok) {
      const data = await res.json();
      setError(data.detail || "Signup failed");
      setLoading(false);
      return;
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    navigate("/");
  };

  return (
    <div className="container" style={{ maxWidth: "400px", marginTop: "4rem" }}>
      <h1>Sign Up</h1>
      <form onSubmit={handleSubmit} className="card">
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <label>Upload CV (PDF)</label>
        <input type="file" accept=".pdf" onChange={(e) => setCv(e.target.files?.[0] || null)} required />
        {error && <p style={{ color: "red", marginTop: "0.5rem" }}>{error}</p>}
        <button className="btn" type="submit" disabled={loading} style={{ marginTop: "1rem" }}>
          {loading ? "Creating account..." : "Sign Up"}
        </button>
      </form>
      <p style={{ marginTop: "1rem", textAlign: "center" }}>
        Already have an account? <a href="/login">Login</a>
      </p>
    </div>
  );
}
