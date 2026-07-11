import { useState } from "react";

interface CopyButtonProps {
  /** Text to copy to the clipboard. */
  text: string;
  /** Optional style overrides (e.g. spacing). */
  style?: React.CSSProperties;
}

/**
 * Shared "copy to clipboard" button used by the cover letter views
 * (JobDetail and CoverLetter pages). Shows a brief "Copied!" confirmation
 * and falls back to execCommand when the async Clipboard API is unavailable
 * (e.g. non-HTTPS contexts).
 */
export default function CopyButton({ text, style }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // If copying fails, leave the label unchanged rather than misreport success.
    }
  };

  return (
    <button className="btn" style={style} onClick={handleCopy}>
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}
