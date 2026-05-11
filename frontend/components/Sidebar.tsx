"use client";

const QUICK_ACTIONS: { label: string; message: string; variant: "primary" | "ghost" }[] = [
  {
    label: "Ссылка на вакансию",
    message: "",
    variant: "ghost",
  },
  {
    label: "Сгенерировать вопросы",
    message: "Сгенерируй вопросы для подготовки к этой вакансии.",
    variant: "primary",
  },
  {
    label: "Начать mock-интервью",
    message: "Начни mock-интервью, пожалуйста.",
    variant: "primary",
  },
  {
    label: "Завершить и отчёт",
    message: "Заверши интервью и дай итоговую обратную связь.",
    variant: "primary",
  },
];

type Props = {
  disabled?: boolean;
  onInsertLinkHint: () => void;
  onQuickSend: (message: string) => void;
};

export default function Sidebar({ disabled, onInsertLinkHint, onQuickSend }: Props) {
  return (
    <aside
      style={{
        borderRight: "1px solid rgba(255,255,255,0.08)",
        padding: "22px 18px",
        background: "rgba(4,6,14,0.85)",
        backdropFilter: "blur(12px)",
        display: "flex",
        flexDirection: "column",
        gap: 18,
        minHeight: 0,
      }}
    >
      <div>
        <div
          style={{
            fontSize: 11,
            textTransform: "uppercase",
            letterSpacing: "0.12em",
            color: "rgba(231,233,238,0.45)",
            marginBottom: 6,
          }}
        >
          AI Interview Coach
        </div>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: "-0.03em" }}>Подготовка</h2>
        <p style={{ margin: "10px 0 0", fontSize: 14, lineHeight: 1.55, color: "rgba(231,233,238,0.7)" }}>
          Вакансия → вопросы → mock → разбор ответов и итоговый отчёт.
        </p>
      </div>

      <div>
        <div style={{ fontSize: 12, fontWeight: 700, color: "rgba(231,233,238,0.55)", marginBottom: 10 }}>
          Быстрые действия
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {QUICK_ACTIONS.map((a) => {
            const isLinkHint = a.label === "Ссылка на вакансию";
            const base = {
              textAlign: "left" as const,
              padding: "12px 14px",
              borderRadius: 12,
              fontSize: 14,
              fontWeight: 600,
              cursor: disabled ? ("not-allowed" as const) : ("pointer" as const),
              border: "1px solid rgba(255,255,255,0.1)",
              opacity: disabled ? 0.55 : 1,
            };
            const primary = {
              ...base,
              background: "linear-gradient(135deg, rgba(99,102,241,0.95), rgba(79,70,229,0.95))",
              color: "#fff",
              border: "1px solid rgba(129,140,248,0.5)",
              boxShadow: "0 6px 20px rgba(79,70,229,0.25)",
            };
            const ghost = {
              ...base,
              background: "rgba(255,255,255,0.04)",
              color: "#e7e9ee",
            };
            return (
              <button
                key={a.label}
                type="button"
                disabled={disabled}
                onClick={() => {
                  if (disabled) return;
                  if (isLinkHint) onInsertLinkHint();
                  else onQuickSend(a.message);
                }}
                style={a.variant === "primary" ? primary : ghost}
              >
                {a.label}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ marginTop: "auto", fontSize: 12, lineHeight: 1.5, color: "rgba(231,233,238,0.5)" }}>
        Поддерживаются ссылки{" "}
        <span style={{ color: "#a5b4fc" }}>hh.ru</span>, <span style={{ color: "#a5b4fc" }}>hh.kz</span> и
        региональные домены (например <code style={{ fontSize: 11 }}>city.hh.kz</code>).
      </div>
    </aside>
  );
}
