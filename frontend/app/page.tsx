"use client";

import Chat from "@/components/Chat";
import Sidebar from "@/components/Sidebar";

export default function Page() {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "320px 1fr",
        height: "100vh",
      }}
    >
      <Sidebar />
      <div style={{ padding: 16, overflow: "hidden" }}>
        <Chat />
      </div>
    </div>
  );
}

