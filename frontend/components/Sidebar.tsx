"use client";

const STARTER_PROMPTS = [
  "Вставить ссылку на вакансию hh.ru",
  "Начать mock-интервью",
  "Сгенерировать 10 вопросов",
  "Завершить интервью и дать обратную связь",
];

export default function Sidebar() {
  return (
    <aside
      style={{
        borderRight: "1px solid rgba(255,255,255,0.12)",
        padding: 16,
        background: "rgba(255,255,255,0.02)",
        overflow: "auto",
      }}
    >
      <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 10 }}>
        AI Interview Coach
      </div>
      <div style={{ opacity: 0.8, fontSize: 13, lineHeight: 1.45 }}>
        Подготовка к собеседованию под конкретную вакансию: вопросы, mock-интервью,
        feedback и итоговый отчёт.
      </div>

      <div style={{ marginTop: 18, fontWeight: 700, marginBottom: 10 }}>
        Starter prompts
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        {STARTER_PROMPTS.map((p) => (
          <button
            key={p}
            onClick={() => {
              // lightweight UX: copy to clipboard, user pastes into input
              navigator.clipboard?.writeText(p).catch(() => {});
              alert("Скопировано в буфер: " + p);
            }}
            style={{
              textAlign: "left",
              padding: "10px 12px",
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.04)",
              color: "#e7e9ee",
              cursor: "pointer",
              lineHeight: 1.3,
            }}
          >
            {p}
          </button>
        ))}
      </div>

      <div style={{ marginTop: 18, opacity: 0.7, fontSize: 12, lineHeight: 1.45 }}>
        Подсказка: вставьте ссылку вида{" "}
        <span style={{ fontFamily: "monospace" }}>https://hh.ru/vacancy/123456</span>
        .
      </div>
    </aside>
  );
}

