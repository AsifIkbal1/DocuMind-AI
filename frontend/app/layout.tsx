import React from "react";
import "./globals.css";
import { Sidebar } from "../components/Sidebar";
import { Navbar } from "../components/Navbar";

export const metadata = {
  title: "DocuMind AI - Document Intelligence Platform",
  description: "Enterprise-grade AI document processing, extraction, deterministic validation, and reconciliation.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-1 mt-16 p-8 overflow-y-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
