import type { ReactNode } from "react";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata = {
  title: "AI Interview Coach",
  description: "Mock interview + feedback под вакансию",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body
        className={inter.className}
        style={{
          margin: 0,
          background: "#070a12",
          color: "#e7e9ee",
        }}
      >
        {children}
      </body>
    </html>
  );
}

