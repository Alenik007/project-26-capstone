import type { ReactNode } from "react";

export const metadata = {
  title: "AI Interview Coach",
  description: "Mock interview + feedback под вакансию",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body
        style={{
          margin: 0,
          fontFamily:
            'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"',
          background: "#0b1020",
          color: "#e7e9ee",
        }}
      >
        {children}
      </body>
    </html>
  );
}

