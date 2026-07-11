import { useState } from "react";
import {
  generateAdhocCoverLetter,
  refineAdhocCoverLetter,
  downloadAdhocCoverLetterPdf,
  chat,
} from "../api";
import RefineBox from "../components/RefineBox";
import CopyButton from "../components/CopyButton";
import ChatBox from "../components/ChatBox";

export default function CoverLetter() {
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");
  const [letter, setLetter] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
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

          <RefineBox
            refineFn={(message) => refineAdhocCoverLetter(letter, message, title, company)}
            onRefined={setLetter}
          />

          <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem", flexWrap: "wrap" }}>
            <CopyButton text={letter} />
            <button
              className="btn"
              onClick={() => downloadAdhocCoverLetterPdf(letter, title, company)}
            >
              Download PDF
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Ask about this job</h2>
        <p className="placeholder-text">
          Ask questions about this role and how it fits your CV. Uses your CV and the
          job description above as context — leave the description empty to chat about
          your CV alone. The description is read fresh on each message; if you change it
          mid-conversation, use Reset to start over.
        </p>
        <ChatBox
          sendFn={(messages) => chat(messages, description, title, company)}
          placeholder="e.g. Do I meet the requirements? What should I emphasize?"
        />
      </div>
    </>
  );
}
