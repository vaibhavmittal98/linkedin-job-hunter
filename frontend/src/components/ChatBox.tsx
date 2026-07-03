import { useState } from "react";
import type { ChatMessage } from "../api";

interface ChatBoxProps {
  /**
   * Sends the full conversation so far and returns the assistant's reply.
   * The caller decides the context (job-based vs standalone) via this fn.
   */
  sendFn: (messages: ChatMessage[]) => Promise<{ reply: string }>;
  /** Optional placeholder for the input. */
  placeholder?: string;
}

/**
 * Shared, stateless chat widget used by both the job detail page and the
 * standalone Chat tab. Holds the conversation in component state only —
 * nothing is persisted. Reset clears the conversation (useful after the
 * underlying context, e.g. a pasted job description, changes).
 */
export default function ChatBox({ sendFn, placeholder }: ChatBoxProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const next: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setSending(true);
    try {
      const { reply } = await sendFn(next);
      if (typeof reply === "string") {
        setMessages([...next, { role: "assistant", content: reply }]);
      }
    } catch {
      setMessages([
        ...next,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleReset = () => {
    if (sending) return;
    setMessages([]);
    setInput("");
  };

  return (
    <div className="chat-box">
      {messages.length > 0 && (
        <div className="chat-log">
          {messages.map((m, i) => (
            <div key={i} className={`chat-msg chat-msg-${m.role}`}>
              <span className="chat-role">{m.role === "user" ? "You" : "Assistant"}</span>
              <p style={{ whiteSpace: "pre-wrap", margin: "0.25rem 0 0" }}>{m.content}</p>
            </div>
          ))}
          {sending && <p className="placeholder-text">Thinking...</p>}
        </div>
      )}

      <div className="chat-input" style={{ marginTop: "0.75rem" }}>
        <input
          type="text"
          placeholder={placeholder || "Ask a question about the job or your CV..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && input.trim()) {
              e.preventDefault();
              handleSend();
            }
          }}
          style={{ marginBottom: "0.5rem" }}
        />
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button className="btn" disabled={sending || !input.trim()} onClick={handleSend}>
            {sending ? "Sending..." : "Send"}
          </button>
          {messages.length > 0 && (
            <button className="btn btn-outline" disabled={sending} onClick={handleReset}>
              Reset
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
