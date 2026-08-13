import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { fetchJob, getCoverLetter, generateCoverLetter, markApplied, markUnapplied, scoreJob, refineCoverLetter, deleteJob, jobChat, Job, CoverLetter } from "../api";
import RefineBox from "../components/RefineBox";
import CopyButton from "../components/CopyButton";
import ChatBox from "../components/ChatBox";

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [letter, setLetter] = useState<CoverLetter | null>(null);
  const [loading, setLoading] = useState(false);
  const [scoring, setScoring] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetchJob(Number(id)).then(setJob);
    getCoverLetter(Number(id)).then(setLetter);
  }, [id]);

  const handleGenerate = async () => {
    if (!id) return;
    setLoading(true);
    const result = await generateCoverLetter(Number(id));
    setLetter(result);
    setLoading(false);
  };

  if (!job) return <p>Loading...</p>;

  return (
    <>
      <Link to="/" className="back-link">← Back to jobs</Link>

      <div className="job-detail-header">
        {job.company_logo && <img src={job.company_logo} alt={job.company} className="company-logo-lg" />}
        <div>
          <h1>{job.title}</h1>
          <p className="company-name-lg">
            {job.company}
            {job.ind_sponsor && (
              <span
                title="This company is on the IND public register of recognised sponsors"
                style={{ marginLeft: 8, padding: "2px 8px", borderRadius: 4, background: "#e6f4ea", color: "#1e7e34", fontSize: "0.75em", fontWeight: 600, verticalAlign: "middle" }}
              >
                IND Sponsor
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="job-detail-meta">
        <div className="meta-grid">
          <div><strong>Location:</strong> {job.location || "N/A"}</div>
          <div><strong>Seniority:</strong> {job.seniority_level || "N/A"}</div>
          <div><strong>Type:</strong> {job.employment_type || "N/A"}</div>
          <div><strong>Function:</strong> {job.job_function || "N/A"}</div>
          <div><strong>Industry:</strong> {job.industries || "N/A"}</div>
          <div><strong>Applicants:</strong> {job.applicants_count || "N/A"}</div>
          <div><strong>Posted:</strong> {(() => {
            if (!job.posted_at) return "N/A";
            const d = new Date(job.posted_at);
            if (isNaN(d.getTime())) return job.posted_at;
            const now = new Date();
            const diff = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
            if (diff === 0) return "Today";
            if (diff === 1) return "Yesterday";
            if (diff < 7) return `${diff} days ago`;
            if (diff < 30) { const w = Math.floor(diff / 7); return `${w} ${w === 1 ? "week" : "weeks"} ago`; }
            return d.toLocaleDateString();
          })()}</div>
          <div><strong>Salary:</strong> {job.salary || "Not listed"}</div>
        </div>
        {job.relevance_score !== null && (
          <p className="score">Relevance: {job.relevance_score.toFixed(0)}/100</p>
        )}
        {job.relevance_score === null && (
          <button
            className="btn"
            disabled={scoring}
            onClick={async () => {
              setScoring(true);
              const result = await scoreJob(job.id);
              setJob({ ...job, relevance_score: result.score, score_reason: result.reason });
              setScoring(false);
            }}
          >
            {scoring ? "Scoring..." : "Generate Score"}
          </button>
        )}
        {job.score_reason && (
          <p style={{ marginTop: "0.5rem", fontSize: "0.9rem", color: "#555" }}><strong>Reason:</strong> {job.score_reason}</p>
        )}
      </div>

      <div className="job-detail-actions">
        {job.url && <a href={job.url} target="_blank" rel="noreferrer" className="btn btn-green">Apply on LinkedIn</a>}
        {job.company_website && <a href={job.company_website} target="_blank" rel="noreferrer" className="btn btn-outline">Company Website</a>}
        <button
          className={job.applied ? "btn btn-outline" : "btn btn-green"}
          onClick={async () => {
            if (job.applied) {
              await markUnapplied(job.id);
            } else {
              await markApplied(job.id);
            }
            setJob({ ...job, applied: !job.applied });
          }}
        >
          {job.applied ? "✓ Applied" : "Mark as Applied"}
        </button>
        <button
          className="btn"
          style={{ background: "#dc2626" }}
          onClick={async () => {
            if (confirm("Delete this job?")) {
              await deleteJob(job.id);
              navigate("/");
            }
          }}
        >
          Delete
        </button>
      </div>

      <div className="card">
        <h2>Job Description</h2>
        <p style={{ whiteSpace: "pre-wrap" }}>{job.description}</p>
      </div>

      <div className="card">
        <h2>Cover Letter</h2>
        {letter ? (
          <>
            <p style={{ whiteSpace: "pre-wrap" }}>{letter.content}</p>
            <RefineBox
              refineFn={(message) => refineCoverLetter(Number(id), message)}
              onRefined={(content) => setLetter({ ...letter, content })}
            />
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem", flexWrap: "wrap" }}>
              <CopyButton text={letter.content} />
              <button className="btn" onClick={async () => {
                const token = localStorage.getItem("token");
                const res = await fetch(`/api/jobs/${id}/cover-letter/pdf`, { headers: { Authorization: `Bearer ${token}` } });
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `cover_letter_${job.company.replace(/ /g, "_")}.pdf`;
                a.click();
                URL.revokeObjectURL(url);
              }}>
                Download PDF
              </button>
            </div>
          </>
        ) : (
          <div>
            <p className="placeholder-text">Generate a tailored cover letter for this role.</p>
            <button className="btn" onClick={handleGenerate} disabled={loading}>
              {loading ? "Generating..." : "Generate Cover Letter"}
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Ask about this job</h2>
        <p className="placeholder-text">
          Ask questions about this role and how it fits your CV. Uses your CV and this
          job's description as context.
        </p>
        <ChatBox
          sendFn={(messages) => jobChat(job.id, messages)}
          placeholder="e.g. Do I meet the requirements? What should I emphasize?"
        />
      </div>
    </>
  );
}
