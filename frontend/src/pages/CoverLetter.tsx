import { useState } from "react";
import {
  generateAdhocCoverLetter,
  refineAdhocCoverLetter,
  downloadAdhocCoverLetterPdf,
} from "../api";

export default function CoverLetter() {
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");
  const [letter, setLetter] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refineMsg, setRefineMsg] = useState("");
  const [refining, setRefining] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await generateAdhocCoverLetter(description, title, company);
      if (typeof result.content === "string") {
        setLetter(result.content);
      } else {
        setError("Could not generate a cover letter. Make sure your CV is uploaded on the Profile page.");
      }
    } catch {
      setError("Something went wrong generating the cover letter.");
    }
    setLoading(false);
  };

  const handleRefine = async () => {
    if (!refineMsg.trim() || letter === null) return;
    setRefining(true);
    try {
      const result = await refineAdhocCoverLetter(letter, refineMsg, title, company);
      if (typeof result.content === "string") setLetter(result.content);
      setRefineMsg("");
    } catch {
      setError("Something went wrong refining the cover letter.");
    }
    setRefining(false);
  };

  return (
    <>
      <h1>Cover Letter</h1>
      <p className="placeholder-text">
        Paste a job description to generate a tailored cover letter. Job title and
        company are optional — if you provide both, they appear on the PDF.
      </p>

      <div className="card">
        <div style={{ display: "flex", gap: "1rem", marginBottom: "0.75rem" }}>
          <input
            type="text"
            placeholder="Job title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={{ flex: 1 }}
          />
          <input
            type="text"
            placeholder="Company (optional)"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            style={{ flex: 1 }}
          />
        </div>
        <textarea
          placeholder="Paste the job description here..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={10}
          style={{ width: "100%", marginBottom: "0.75rem" }}
        />
        <button className="btn" onClick={handleGenerate} disabled={loading || !description.trim()}>
          {loading ? "Generating..." : "Generate Cover Letter"}
        </button>
        {error && <p style={{ color: "#dc2626", marginTop: "0.5rem" }}>{error}</p>}
      </div>

      {letter !== null && (
        <div className="card">
          <h2>Generated Cover Letter</h2>
          <p style={{ whiteSpace: "pre-wrap" }}>{letter}</p>

          <div className="refine-chat" style={{ marginTop: "1rem" }}>
            <input
              type="text"
              placeholder="e.g. Make it longer, less formal, mention Kubernetes..."
              value={refineMsg}
              onChange={(e) => setRefineMsg(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && refineMsg.trim()) {
                  e.preventDefault();
                  handleRefine();
                }
              }}
              style={{ marginBottom: "0.5rem" }}
            />
            <button className="btn" disabled={refining || !refineMsg.trim()} onClick={handleRefine}>
              {refining ? "Refining..." : "Refine"}
            </button>
          </div>

          <button
            className="btn"
            style={{ marginTop: "1rem" }}
            onClick={() => downloadAdhocCoverLetterPdf(letter, title, company)}
          >
            Download PDF
          </button>
        </div>
      )}
    </>
  );
}
