import { useState } from "react";
import { chat } from "../api";
import ChatBox from "../components/ChatBox";

export default function Chat() {
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");

  return (
    <>
      <h1>Chat</h1>
      <p className="placeholder-text">
        Ask questions about your CV and, optionally, a job. Paste a job description
        below to include it as context — leave it empty to chat about your CV alone.
        The description is read fresh on each message; if you change it mid-conversation,
        use Reset to start over.
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
          placeholder="Paste a job description here (optional)..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={8}
          style={{ width: "100%" }}
        />
      </div>

      <div className="card">
        <ChatBox
          sendFn={(messages) => chat(messages, description, title, company)}
        />
      </div>
    </>
  );
}
