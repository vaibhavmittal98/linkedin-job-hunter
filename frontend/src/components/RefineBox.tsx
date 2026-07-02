import { useState } from "react";

interface RefineBoxProps {
  /** Called with the user's feedback; returns the refined letter text. */
  refineFn: (message: string) => Promise<{ content: string }>;
  /** Called with the new letter text after a successful refine. */
  onRefined: (content: string) => void;
}

/**
 * Shared refine input + button used by both the job-based cover letter
 * (JobDetail) and the standalone cover letter (CoverLetter) pages, so the
 * button behavior is defined once and stays consistent.
 */
export default function RefineBox({ refineFn, onRefined }: RefineBoxProps) {
  const [message, setMessage] = useState("");
  const [refining, setRefining] = useState(false);

  const handleRefine = async () => {
    if (!message.trim() || refining) return;
    setRefining(true);
    try {
      const result = await refineFn(message);
      if (typeof result.content === "string") onRefined(result.content);
      setMessage("");
    } finally {
      setRefining(false);
    }
  };

  return (
    <div className="refine-chat" style={{ marginTop: "1rem" }}>
      <input
        type="text"
        placeholder="e.g. Make it longer, mention Kubernetes more, less formal..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && message.trim()) {
            e.preventDefault();
            handleRefine();
          }
        }}
        style={{ marginBottom: "0.5rem" }}
      />
      <button className="btn" disabled={refining || !message.trim()} onClick={handleRefine}>
        {refining ? "Refining..." : "Refine"}
      </button>
    </div>
  );
}
