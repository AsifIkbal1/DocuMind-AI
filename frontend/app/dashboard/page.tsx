"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Files,
  CheckCircle2,
  Clock,
  AlertOctagon,
  Copy,
  AlertTriangle,
  Timer,
  Target,
  ArrowRight,
  Upload,
  RefreshCw,
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
} from "recharts";
import { api } from "../../services/api";
import { AnalyticsOverview } from "../../types";
import { MetricCard } from "../../components/MetricCard";

const PIE_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#64748b"];

export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const pieData = data?.file_type_distribution
    ? Object.entries(data.file_type_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const severityData = data?.validation_error_distribution
    ? Object.entries(data.validation_error_distribution).map(([severity, count]) => ({
        severity,
        count,
      }))
    : [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Executive Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time document ingestion throughput, deterministic validation audits, and cross-reconciliation metrics.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/documents"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload Invoices
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Ingested"
          value={data?.total_documents ?? 0}
          subtitle="Multi-format documents parsed"
          icon={Files}
          variant="default"
        />
        <MetricCard
          title="Processed Successfully"
          value={data?.processed_documents ?? 0}
          subtitle="Ready & validated"
          icon={CheckCircle2}
          variant="success"
        />
        <MetricCard
          title="Awaiting Human Review"
          value={data?.documents_awaiting_review ?? 0}
          subtitle="Flagged by validation engine"
          icon={AlertTriangle}
          variant="warning"
        />
        <MetricCard
          title="Duplicates Detected"
          value={data?.duplicate_invoices_count ?? 0}
          subtitle="Exact & potential duplicates"
          icon={Copy}
          variant="danger"
        />
        <MetricCard
          title="Validation Issues"
          value={data?.validation_errors_count ?? 0}
          subtitle="Pending resolution"
          icon={AlertOctagon}
          variant="warning"
        />
        <MetricCard
          title="Average Latency"
          value={`${data?.average_processing_time ?? 0}s`}
          subtitle="Pipeline execution time"
          icon={Timer}
          variant="info"
        />
        <MetricCard
          title="Extraction Accuracy"
          value={`${data?.measured_extraction_accuracy ?? 0}%`}
          subtitle="Measured benchmark score"
          icon={Target}
          variant="success"
        />
        <MetricCard
          title="Failed Documents"
          value={data?.failed_documents ?? 0}
          subtitle="Corrupted / parse errors"
          icon={Clock}
          variant="danger"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Processing Trend */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Document Processing Velocity</h2>
              <p className="text-xs text-slate-500">Completed vs failed batches over recent runs</p>
            </div>
            <span className="text-xs font-medium px-2 py-1 bg-slate-100 rounded text-slate-600">Daily Runs</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.document_processing_trend || []}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="processed" name="Processed" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="failed" name="Failed" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* File Type Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-1">File Format Ingestion</h2>
          <p className="text-xs text-slate-500 mb-4">Distribution across formats</p>
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
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend verticalAlign="bottom" wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No file distribution data available.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Row: Validation Error Severity & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Validation Breakdown */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Validation Errors by Severity</h2>
              <p className="text-xs text-slate-500">Deterministic arithmetic and structural issue distribution</p>
            </div>
            <Link
              href="/validation"
              className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
            >
              <span>View All Issues</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="h-56">
            {severityData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityData} layout="vertical">
                  <XAxis type="number" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <YAxis type="category" dataKey="severity" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <Tooltip />
                  <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Zero active validation issues detected.
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity Feed */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">System Audit Trail</h2>
              <p className="text-xs text-slate-500">Live ingestion, validation, and correction events</p>
            </div>
            <Link
              href="/jobs"
              className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
            >
              <span>Jobs Log</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="divide-y divide-slate-100 max-h-56 overflow-y-auto">
            {data?.recent_activity && data.recent_activity.length > 0 ? (
              data.recent_activity.map((act) => (
                <div key={act.id} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-slate-800">{act.action}</span>
                    <span className="text-slate-400 ml-2">({act.entity})</span>
                  </div>
                  <span className="text-slate-400 text-[11px]">{act.timestamp}</span>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">No recent activity logged yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
