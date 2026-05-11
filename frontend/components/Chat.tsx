"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Message from "@/components/Message";
import { chatStream, type ChatMessage } from "@/lib/api";

function getOrCreateSessionId(): string {
  const key = "ai_interview_coach_session_id";
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const id =
    (globalThis.crypto?.randomUUID?.() ?? `sess_${Date.now()}_${Math.random()}`)
      .toString()
      .slice(0, 100);
  localStorage.setItem(key, id);
  return id;
}

function loadMessages(sessionId: string): ChatMessage[] {
  const key = `ai_interview_coach_messages_${sessionId}`;
  const raw = localStorage.getItem(key);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as ChatMessage[];
    if (Array.isArray(parsed)) return parsed;
  } catch {
    // ignore
  }
  return [];
}

function saveMessages(sessionId: string, messages: ChatMessage[]) {
  const key = `ai_interview_coach_messages_${sessionId}`;
  localStorage.setItem(key, JSON.stringify(messages));
}

export default function Chat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const id = getOrCreateSessionId();
    setSessionId(id);
    setMessages(loadMessages(id));
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    saveMessages(sessionId, messages);
  }, [messages, sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isStreaming]);

  const canSend = useMemo(
    () => Boolean(sessionId) && input.trim().length > 0 && !isStreaming,
    [sessionId, input, isStreaming]
  );

  async function onSend() {
    if (!sessionId) return;
    const text = input.trim();
    if (!text) return;

    setInput("");
    const next: ChatMessage[] = [
      ...messages,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ];
    setMessages(next);
    setIsStreaming(true);

    try {
      let acc = "";
      for await (const token of chatStream({ sessionId, message: text })) {
        acc += token;
        setMessages((prev) => {
          const copy = prev.slice();
          const lastIdx = copy.length - 1;
          if (lastIdx >= 0 && copy[lastIdx].role === "assistant") {
            copy[lastIdx] = { role: "assistant", content: acc };
          }
          return copy;
        });
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setMessages((prev) => {
        const copy = prev.slice();
        const lastIdx = copy.length - 1;
        if (lastIdx >= 0 && copy[lastIdx].role === "assistant") {
          copy[lastIdx] = {
            role: "assistant",
            content:
              "Ошибка при запросе к backend.\n\n" +
              msg +
              "\n\nПроверьте `NEXT_PUBLIC_API_URL` и доступность /api/chat.",
          };
        }
        return copy;
      });
    } finally {
      setIsStreaming(false);
    }
  }

  function onClear() {
    if (!sessionId) return;
    localStorage.removeItem(`ai_interview_coach_messages_${sessionId}`);
    setMessages([]);
  }

  return (
    <div
      style={{
        height: "100%",
        display: "grid",
        gridTemplateRows: "1fr auto",
        gap: 12,
      }}
    >
      <div
        style={{
          overflow: "auto",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 14,
          padding: 14,
          background: "rgba(255,255,255,0.03)",
        }}
      >
        {messages.length === 0 ? (
          <div style={{ opacity: 0.8, lineHeight: 1.5 }}>
            Вставьте ссылку на вакансию hh.ru или текст вакансии, затем попросите
            сгенерировать вопросы или начать mock-интервью.
          </div>
        ) : null}
        {messages.map((m, i) => (
          <Message key={i} msg={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr auto auto",
          gap: 10,
          alignItems: "center",
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Напишите сообщение…"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          style={{
            width: "100%",
            padding: "12px 12px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.16)",
            background: "rgba(0,0,0,0.25)",
            color: "#e7e9ee",
            outline: "none",
          }}
        />

        <button
          onClick={onSend}
          disabled={!canSend}
          style={{
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.16)",
            background: canSend ? "#6366f1" : "rgba(255,255,255,0.08)",
            color: canSend ? "#0b1020" : "rgba(231,233,238,0.6)",
            fontWeight: 700,
            cursor: canSend ? "pointer" : "not-allowed",
          }}
        >
          Отправить
        </button>

        <button
          onClick={onClear}
          disabled={isStreaming}
          style={{
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.16)",
            background: "rgba(255,255,255,0.06)",
            color: "#e7e9ee",
            cursor: isStreaming ? "not-allowed" : "pointer",
          }}
        >
          Очистить
        </button>
      </div>
    </div>
  );
}

