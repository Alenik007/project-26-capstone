export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
};

/**
 * Base URL for API calls.
 * - In the browser: if NEXT_PUBLIC_API_URL is an absolute http(s) URL, use it (local dev: http://localhost:8000).
 *   Otherwise use same origin + /api so nginx reverse proxy works without rebuilding for each host/IP.
 * - On server/build: fall back to env or localhost:8000.
 */
export function getApiBaseUrl(): string {
  const env = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

  if (typeof window !== "undefined") {
    if (env.startsWith("http://") || env.startsWith("https://")) {
      return env;
    }
    return `${window.location.origin}/api`;
  }

  return env || "http://localhost:8000";
}

export async function* chatStream(opts: {
  sessionId: string;
  message: string;
}): AsyncGenerator<string> {
  const res = await fetch(`${getApiBaseUrl()}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: opts.sessionId, message: opts.message }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  if (!res.body) {
    throw new Error("Streaming not supported by browser");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames end with \n\n
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);

      const lines = frame.split("\n");
      for (const line of lines) {
        if (line.startsWith("data:")) {
          const data = line.slice(5).trimStart();
          if (data === "[DONE]") return;
          yield data;
        }
      }
    }
  }
}

