"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Cpu, RefreshCw, AlertCircle, CheckCircle2, Clock, RotateCcw } from "lucide-react";
import { api } from "../../services/api";
import { JobItem } from "../../types";
import { StatusBadge } from "../../components/StatusBadge";

export default function ProcessingJobsPage() {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await api.getJobs();
      setJobs(data);
    } catch (err) {
      console.error("Failed to load jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleRetry = async (documentId: string) => {
    try {
      await api.retryProcessing(documentId);
      loadJobs();
    } catch (err: any) {
      alert(err.message || "Retry failed");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Background Processing Jobs</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time monitoring of asynchronous pipeline tasks, Celery worker concurrency, and OCR progress.
          </p>
        </div>
        <button
          onClick={loadJobs}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Jobs
        </button>
      </div>

      {/* Jobs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <tr>
                <th className="py-3 px-4">Job ID</th>
                <th className="py-3 px-4">Document</th>
                <th className="py-3 px-4">Job Type</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Progress</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading && jobs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-slate-400" />
                    Loading background queue jobs...
                  </td>
                </tr>
              ) : jobs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No active or historical processing jobs found.
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-900">{job.id.slice(0, 8)}...</td>
                    <td className="py-3 px-4 font-semibold text-slate-800">
                      <Link href={`/documents/${job.document_id}`} className="hover:text-blue-600 transition-colors">
                        {job.document_name}
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">{job.job_type}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={job.current_status} />
                    </td>
                    <td className="py-3 px-4">
                      <div className="w-28 space-y-1">
                        <div className="flex items-center justify-between text-[10px] text-slate-500">
                          <span>{job.progress}%</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              job.current_status === "Failed"
                                ? "bg-rose-500"
                                : job.progress === 100
                                ? "bg-emerald-500"
                                : "bg-blue-600"
                            }`}
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-600">
                      {job.processing_duration ? `${job.processing_duration}s` : "-"}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(job.creation_time).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {job.current_status === "Failed" ? (
                        <button
                          onClick={() => handleRetry(job.document_id)}
                          className="px-2.5 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded text-xs font-semibold inline-flex items-center gap-1 transition-colors"
                        >
                          <RotateCcw className="w-3 h-3" />
                          Retry
                        </button>
                      ) : (
                        <Link
                          href={`/documents/${job.document_id}`}
                          className="text-blue-600 hover:underline text-xs font-medium"
                        >
                          Inspect
                        </Link>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
