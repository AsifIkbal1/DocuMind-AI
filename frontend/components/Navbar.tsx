"use client";

import React, { useEffect, useState } from "react";
import { Search, Bell, CheckCircle2, AlertCircle, User } from "lucide-react";
import { api } from "../services/api";

export function Navbar() {
  const [healthStatus, setHealthStatus] = useState<string>("checking");

  useEffect(() => {
    api
      .getHealth()
      .then((res) => {
        setHealthStatus(res.status === "healthy" ? "healthy" : "degraded");
      })
      .catch(() => {
        setHealthStatus("offline");
      });
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 fixed top-0 right-0 left-64 z-30 flex items-center justify-between px-8">
      {/* Search Input */}
      <div className="relative w-96">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search invoices, suppliers, or amounts (Cmd + K)..."
          className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              const val = (e.target as HTMLInputElement).value;
              if (val) window.location.href = `/search?q=${encodeURIComponent(val)}`;
            }
          }}
        />
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* System Health Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border bg-slate-50 border-slate-200">
          {healthStatus === "healthy" ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-slate-700">API & DB Operational</span>
            </>
          ) : healthStatus === "offline" ? (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
              <span className="text-rose-600">Backend Disconnected</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-slate-600">Connecting...</span>
            </>
          )}
        </div>

        {/* Notifications */}
        <button
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors relative"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-600" />
        </button>

        {/* User Info */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-xs">
            PR
          </div>
          <div className="text-left hidden md:block">
            <p className="text-xs font-semibold text-slate-800 leading-tight">Principal Reviewer</p>
            <p className="text-[10px] text-slate-500 leading-tight">admin@documind.ai</p>
          </div>
        </div>
      </div>
    </header>
  );
}
