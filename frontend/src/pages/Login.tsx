import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch("/api/auth/login", { method: "POST", body: formData });
    if (!res.ok) {
      const data = await res.json();
      setError(data.detail || "Login failed");
      setLoading(false);
      return;
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    navigate("/");
  };

  return (
    <div className="container" style={{ maxWidth: "400px", marginTop: "4rem" }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit} className="card">
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p style={{ color: "red", marginTop: "0.5rem" }}>{error}</p>}
        <button className="btn" type="submit" disabled={loading} style={{ marginTop: "1rem" }}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
      <p style={{ marginTop: "1rem", textAlign: "center" }}>
        No account? <a href="/signup">Sign up</a>
      </p>
    </div>
  );
}
