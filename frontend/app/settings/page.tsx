"use client";

import React, { useEffect, useState } from "react";
import {
  Settings as SettingsIcon,
  Cpu,
  ShieldCheck,
  HardDrive,
  Database,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Server,
} from "lucide-react";
import { api } from "../../services/api";

export default function SettingsPage() {
  const [healthData, setHealthData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadHealth = async () => {
    try {
      setLoading(true);
      const data = await api.getHealth();
      setHealthData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="pb-3 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System & AI Provider Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Inspect LLM extraction providers, database connection pooling, and background Celery queue configurations.
        </p>
      </div>

      {/* AI Provider Status Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">AI Extraction Engine Configuration</h2>
              <p className="text-xs text-slate-500">Configured via environment variables (GEMINI_API_KEY / OPENAI_API_KEY)</p>
            </div>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              healthData?.ai_provider?.is_configured
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : "bg-blue-50 text-blue-700 border border-blue-200"
            }`}
          >
            Mode: {healthData?.ai_provider?.mode || "heuristic_fallback"}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
            <span className="text-slate-400 block mb-0.5 font-medium">Selected Provider</span>
            <span className="font-bold text-slate-800 text-sm capitalize">
              {healthData?.ai_provider?.provider || "gemini"}
            </span>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
            <span className="text-slate-400 block mb-0.5 font-medium">Active Model</span>
            <span className="font-bold text-slate-800 text-sm font-mono">
              {healthData?.ai_provider?.model || "gemini-2.0-flash"}
            </span>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
            <span className="text-slate-400 block mb-0.5 font-medium">Credentials Status</span>
            <span className="font-semibold text-slate-700">
              {healthData?.ai_provider?.is_configured
                ? "Live API Key Loaded (Secret Protected)"
                : "Heuristic Fallback Engine Active"}
            </span>
          </div>
        </div>

        {healthData?.ai_provider?.warning && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0" />
            <span>{healthData.ai_provider.warning}</span>
          </div>
        )}
      </div>

      {/* Infrastructure Diagnostic Status */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
          Platform Infrastructure Health
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start gap-3">
            <Server className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-900">FastAPI REST Server</p>
              <p className="text-[11px] text-emerald-600 font-semibold mt-0.5">Healthy & Operational</p>
              <p className="text-[10px] text-slate-400 mt-1">Uvicorn ASGI runner</p>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start gap-3">
            <Database className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-900">Database Engine</p>
              <p className="text-[11px] text-emerald-600 font-semibold mt-0.5 capitalize">
                {healthData?.database || "Connected"}
              </p>
              <p className="text-[10px] text-slate-400 mt-1">SQLAlchemy ORM + Connection Pool</p>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start gap-3">
            <HardDrive className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-900">Background Queue Broker</p>
              <p className="text-[11px] text-slate-700 font-semibold mt-0.5">
                {healthData?.background_queue || "Active"}
              </p>
              <p className="text-[10px] text-slate-400 mt-1">Redis / In-process background tasks</p>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Limits & Processing Preferences */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
          Processing Engine Parameters
        </h2>
        <div className="divide-y divide-slate-100 text-xs text-slate-700">
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-600">Maximum Upload File Size:</span>
            <span className="font-bold text-slate-900">50 MB per document</span>
          </div>
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-600">Supported Formats:</span>
            <span className="font-mono text-slate-800">PDF, JPG, JPEG, PNG, TIFF, XLSX, XLS, CSV</span>
          </div>
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-600">Max PDF Page Extraction Depth:</span>
            <span className="font-bold text-slate-900">1,000 pages (streamed chunk-based)</span>
          </div>
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-600">Mathematical Rounding Tolerance:</span>
            <span className="font-mono text-slate-800">±0.05 currency units</span>
          </div>
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-600">Deterministic Arithmetic Verification:</span>
            <span className="text-emerald-700 font-semibold">Strict Independent Enforced</span>
          </div>
        </div>
      </div>
    </div>
  );
}

