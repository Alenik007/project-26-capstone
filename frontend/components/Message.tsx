"use client";

import type { ChatMessage } from "@/lib/api";

export default function Message({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: 10,
      }}
    >
      <div
        style={{
          maxWidth: 760,
          whiteSpace: "pre-wrap",
          padding: "10px 12px",
          borderRadius: 12,
          border: "1px solid rgba(255,255,255,0.12)",
          background: isUser ? "rgba(99,102,241,0.25)" : "rgba(255,255,255,0.06)",
          lineHeight: 1.35,
        }}
      >
        {msg.content}
      </div>
    </div>
  );
}

