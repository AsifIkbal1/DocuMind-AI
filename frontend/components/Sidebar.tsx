"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Files,
  FileSpreadsheet,
  CheckCheck,
  AlertTriangle,
  Search,
  Cpu,
  BarChart3,
  Settings,
  ShieldCheck,
  ExternalLink,
} from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Document Center", href: "/documents", icon: Files },
    { name: "AI Extraction Center", href: "/extraction", icon: FileSpreadsheet },
    { name: "Verification Center", href: "/verification", icon: CheckCheck },
    { name: "Validation Center", href: "/validation", icon: AlertTriangle },
    { name: "Search Center", href: "/search", icon: Search },
    { name: "Processing Jobs", href: "/jobs", icon: Cpu },
    { name: "Analytics & Reports", href: "/analytics", icon: BarChart3 },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-40 text-slate-300">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-md">
          D
        </div>
        <div>
          <h1 className="font-bold text-white text-base tracking-tight leading-none">DocuMind AI</h1>
          <span className="text-[10px] text-blue-400 font-semibold uppercase tracking-wider">Enterprise Intelligence</span>
        </div>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Status Panel */}
      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/70 rounded-lg p-3 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-slate-400 font-medium">Pipeline Status</span>
            <span className="inline-flex items-center text-emerald-400 font-semibold gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Online
            </span>
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between">
            <span>FastAPI REST + OCR</span>
            <span className="text-slate-400">v1.0.0</span>
          </div>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="mt-2.5 pt-2 border-t border-slate-700/60 text-blue-400 hover:text-blue-300 flex items-center justify-between text-[11px] font-medium"
          >
            <span>Swagger API Docs</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </aside>
  );
}
