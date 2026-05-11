import type { ReactNode } from "react";
import "./globals.css";

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
          background: "#070a12",
          color: "#e7e9ee",
          fontFamily:
            'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif',
        }}
      >
        {children}
      </body>
    </html>
  );
}
