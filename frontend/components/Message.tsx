"use client";

import type { ChatMessage } from "@/lib/api";

type Props = {
  msg: ChatMessage;
  /** Пустой ответ ассистента во время стрима */
  isTyping?: boolean;
};

export default function Message({ msg, isTyping }: Props) {
  const isUser = msg.role === "user";
  const showTyping = Boolean(isTyping && msg.role === "assistant");

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: 14,
      }}
    >
      <div
        style={{
          maxWidth: "min(720px, 92%)",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          overflowWrap: "anywhere",
          padding: "12px 16px",
          borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
          border: isUser ? "1px solid rgba(129,140,248,0.35)" : "1px solid rgba(255,255,255,0.1)",
          background: isUser ? "rgba(99,102,241,0.22)" : "rgba(255,255,255,0.05)",
          lineHeight: 1.55,
          fontSize: 15,
          color: "#e7e9ee",
          boxShadow: isUser ? "0 4px 18px rgba(79,70,229,0.12)" : "none",
        }}
      >
        {showTyping ? (
          <span style={{ color: "#a5b4fc", fontSize: 14 }}>
            <span className="coach-pulse-dot" style={{ display: "inline-block", width: 7, height: 7, borderRadius: "50%", background: "#818cf8", marginRight: 8, verticalAlign: "middle" }} />
            Думаю…
          </span>
        ) : (
          msg.content
        )}
      </div>
    </div>
  );
}
