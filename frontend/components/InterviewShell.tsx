"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Message from "@/components/Message";
import Sidebar from "@/components/Sidebar";
import { chatStream, type ChatMessage } from "@/lib/api";

const SESSION_KEY = "ai_interview_coach_session_id";

function getOrCreateSessionId(): string {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const id = (
    globalThis.crypto?.randomUUID?.() ?? `sess_${Date.now()}_${Math.random()}`
  )
    .toString()
    .slice(0, 100);
  localStorage.setItem(SESSION_KEY, id);
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
    /* ignore */
  }
  return [];
}

function saveMessages(sessionId: string, messages: ChatMessage[]) {
  localStorage.setItem(`ai_interview_coach_messages_${sessionId}`, JSON.stringify(messages));
}

export default function InterviewShell() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [hint, setHint] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

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
  }, [messages, isStreaming, hint]);

  const sendWithText = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!sessionId || !text || isStreaming) return;

      setHint(null);
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
                "\n\nПроверьте, что сайт открыт по тому же адресу, что и API (например http://IP), и что `/api/chat` доступен.",
            };
          }
          return copy;
        });
      } finally {
        setIsStreaming(false);
      }
    },
    [sessionId, messages, isStreaming]
  );

  const canSend = useMemo(
    () => Boolean(sessionId) && input.trim().length > 0 && !isStreaming,
    [sessionId, input, isStreaming]
  );

  const onSend = useCallback(async () => {
    const t = input.trim();
    if (!canSend) return;
    setInput("");
    await sendWithText(t);
  }, [canSend, input, sendWithText]);

  const onClear = useCallback(() => {
    if (!sessionId || isStreaming) return;
    localStorage.removeItem(`ai_interview_coach_messages_${sessionId}`);
    setMessages([]);
    setHint(null);
  }, [sessionId, isStreaming]);

  const lastIdx = messages.length - 1;
  const typingOnLast =
    isStreaming &&
    lastIdx >= 0 &&
    messages[lastIdx]?.role === "assistant" &&
    messages[lastIdx]?.content.trim() === "";

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(280px, 340px) 1fr",
        height: "100vh",
        background:
          "radial-gradient(1200px 600px at 10% -10%, rgba(99,102,241,0.35), transparent 55%), radial-gradient(900px 500px at 100% 0%, rgba(34,211,238,0.12), transparent 50%), #070a12",
      }}
    >
      <Sidebar
        disabled={isStreaming}
        onInsertLinkHint={() => {
          setHint(
            "Вставьте ссылку на вакансию в поле справа (hh.ru, hh.kz, например ust-kamenogorsk.hh.kz) и нажмите «Отправить»."
          );
          textareaRef.current?.focus();
        }}
        onQuickSend={(msg) => {
          void sendWithText(msg);
        }}
      />

      <main
        style={{
          display: "flex",
          flexDirection: "column",
          padding: "20px 24px 20px 16px",
          gap: 14,
          minWidth: 0,
        }}
      >
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            flexWrap: "wrap",
          }}
        >
          <div>
            <div style={{ fontSize: 13, color: "rgba(231,233,238,0.55)", letterSpacing: "0.02em" }}>
              Сессия · HeadHunter · mock + feedback
            </div>
            <h1 style={{ margin: "4px 0 0", fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>
              Чат с коучем
            </h1>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            {isStreaming ? (
              <span
                style={{
                  fontSize: 13,
                  color: "#a5b4fc",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <span className="coach-pulse-dot" style={{ width: 8, height: 8, borderRadius: "50%", background: "#818cf8" }} />
                Обрабатываю запрос…
              </span>
            ) : null}
            <button
              type="button"
              onClick={onClear}
              disabled={isStreaming}
              style={{
                padding: "8px 14px",
                borderRadius: 10,
                border: "1px solid rgba(255,255,255,0.14)",
                background: "rgba(255,255,255,0.06)",
                color: "#e7e9ee",
                fontSize: 13,
                cursor: isStreaming ? "not-allowed" : "pointer",
              }}
            >
              Очистить историю
            </button>
          </div>
        </header>

        {hint ? (
          <div
            role="status"
            style={{
              padding: "12px 14px",
              borderRadius: 12,
              border: "1px solid rgba(129,140,248,0.45)",
              background: "rgba(99,102,241,0.12)",
              color: "#c7d2fe",
              fontSize: 14,
              lineHeight: 1.45,
            }}
          >
            {hint}
          </div>
        ) : null}

        <section
          style={{
            flex: 1,
            overflow: "auto",
            borderRadius: 16,
            border: "1px solid rgba(255,255,255,0.08)",
            background: "rgba(6,8,18,0.65)",
            boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
            padding: 18,
            minHeight: 0,
          }}
        >
          {messages.length === 0 ? (
            <div style={{ color: "rgba(231,233,238,0.65)", lineHeight: 1.6, maxWidth: 560, fontSize: 15 }}>
              Вставьте <strong>ссылку</strong> на вакансию (hh.ru, hh.kz и региональные домены) или{" "}
              <strong>полный текст</strong> вакансии. Затем используйте кнопки слева или напишите в чате: сгенерировать
              вопросы, начать mock-интервью, завершить и получить отчёт.
            </div>
          ) : null}
          {messages.map((m, i) => (
            <Message
              key={i}
              msg={m}
              isTyping={typingOnLast && i === lastIdx}
            />
          ))}
          <div ref={bottomRef} />
        </section>

        <footer style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Сообщение… (Shift+Enter — новая строка)"
            rows={3}
            disabled={!sessionId || isStreaming}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void onSend();
              }
            }}
            style={{
              width: "100%",
              resize: "vertical",
              minHeight: 88,
              maxHeight: 220,
              padding: "14px 16px",
              borderRadius: 14,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(0,0,0,0.35)",
              color: "#e7e9ee",
              fontSize: 15,
              lineHeight: 1.45,
              outline: "none",
              fontFamily: "inherit",
            }}
          />
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
            <button
              type="button"
              onClick={() => void onSend()}
              disabled={!canSend}
              style={{
                padding: "12px 22px",
                borderRadius: 12,
                border: "none",
                background: canSend
                  ? "linear-gradient(135deg, #6366f1, #4f46e5)"
                  : "rgba(255,255,255,0.08)",
                color: canSend ? "#fff" : "rgba(231,233,238,0.45)",
                fontWeight: 700,
                fontSize: 15,
                cursor: canSend ? "pointer" : "not-allowed",
                boxShadow: canSend ? "0 8px 24px rgba(79,70,229,0.35)" : "none",
              }}
            >
              Отправить
            </button>
          </div>
        </footer>
      </main>
    </div>
  );
}
