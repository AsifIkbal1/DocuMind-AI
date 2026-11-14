"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart3,
  Download,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Target,
  RefreshCw,
  FileSpreadsheet,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area,
} from "recharts";
import { api } from "../../services/api";
import { AnalyticsOverview } from "../../types";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"];

export default function AnalyticsReportsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await api.getAnalytics();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const pieData = data?.file_type_distribution
    ? Object.entries(data.file_type_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const handleDownloadCsv = () => {
    window.open(api.getExportCsvUrl(), "_blank");
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Analytics & Operational Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            System performance benchmarks, model extraction fidelity, and exportable reconciliation datasets.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleDownloadCsv}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Invoices to CSV</span>
          </button>
        </div>
      </div>

      {/* Accuracy & Performance Summary Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase text-slate-500">Extraction Accuracy</span>
          <p className="text-3xl font-extrabold text-emerald-600 mt-2">
            {data?.measured_extraction_accuracy ?? 0}%
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Field-level precision</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase text-slate-500">Average Processing Time</span>
          <p className="text-3xl font-extrabold text-blue-600 mt-2">
            {data?.average_processing_time ?? 0}s
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Per multi-page document</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase text-slate-500">Success Rate</span>
          <p className="text-3xl font-extrabold text-slate-900 mt-2">
            {data && data.total_documents > 0
              ? `${Math.round((data.processed_documents / data.total_documents) * 100)}%`
              : "100%"}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Batch completion rate</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase text-slate-500">Flagged For Review</span>
          <p className="text-3xl font-extrabold text-amber-600 mt-2">
            {data?.documents_awaiting_review ?? 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Deterministic risk flags</p>
        </div>
      </div>

      {/* Ingestion & Processing Trends Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-1">Processing Throughput Trend</h2>
          <p className="text-xs text-slate-500 mb-4">Daily volume of successfully processed documents</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.document_processing_trend || []}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <Tooltip />
                <Area type="monotone" dataKey="processed" stroke="#3b82f6" fill="#93c5fd" fillOpacity={0.4} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-1">Supported Ingestion Formats</h2>
          <p className="text-xs text-slate-500 mb-4">Volume breakdown across PDF, Images, Excel & CSV</p>
          <div className="h-64">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend verticalAlign="bottom" wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No file ingestion stats available.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
