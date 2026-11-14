"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Filter,
  RefreshCw,
  Edit,
  ExternalLink,
} from "lucide-react";
import { api } from "../../services/api";
import { DocumentItem, ValidationResult } from "../../types";
import { SeverityBadge } from "../../components/SeverityBadge";

export default function ValidationCenterPage() {
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("Pending");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [allValidations, setAllValidations] = useState<Array<ValidationResult & { document_name: string }>>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const docsRes = await api.getDocuments({ limit: 100 });
      setDocuments(docsRes.documents);

      // Collect validations across all documents
      const collected: Array<ValidationResult & { document_name: string }> = [];
      for (const d of docsRes.documents) {
        try {
          const vals = await api.getDocumentValidation(d.id, severityFilter || undefined, statusFilter || undefined);
          vals.forEach((v) => {
            collected.push({ ...v, document_name: d.original_filename });
          });
        } catch {}
      }
      setAllValidations(collected);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [severityFilter, statusFilter]);

  const criticalCount = allValidations.filter((v) => v.severity === "Critical").length;
  const highCount = allValidations.filter((v) => v.severity === "High").length;
  const mediumCount = allValidations.filter((v) => v.severity === "Medium").length;
  const lowCount = allValidations.filter((v) => v.severity === "Low").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Validation Audit Center</h1>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic mathematical verification, tax reconciliation, and duplicate invoice anomaly detection.
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Validations
        </button>
      </div>

      {/* Severity Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <button
          onClick={() => setSeverityFilter(severityFilter === "Critical" ? "" : "Critical")}
          className={`p-4 rounded-xl border text-left transition-all ${
            severityFilter === "Critical"
              ? "bg-red-50 border-red-300 ring-2 ring-red-400"
              : "bg-white border-slate-200 hover:border-red-200"
          }`}
        >
          <p className="text-[11px] font-bold uppercase text-red-600">Critical Issues</p>
          <p className="text-2xl font-black text-red-700 mt-1">{criticalCount}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Math errors & duplicates</p>
        </button>

        <button
          onClick={() => setSeverityFilter(severityFilter === "High" ? "" : "High")}
          className={`p-4 rounded-xl border text-left transition-all ${
            severityFilter === "High"
              ? "bg-orange-50 border-orange-300 ring-2 ring-orange-400"
              : "bg-white border-slate-200 hover:border-orange-200"
          }`}
        >
          <p className="text-[11px] font-bold uppercase text-orange-600">High Severity</p>
          <p className="text-2xl font-black text-orange-700 mt-1">{highCount}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Missing dates / tax variance</p>
        </button>

        <button
          onClick={() => setSeverityFilter(severityFilter === "Medium" ? "" : "Medium")}
          className={`p-4 rounded-xl border text-left transition-all ${
            severityFilter === "Medium"
              ? "bg-amber-50 border-amber-300 ring-2 ring-amber-400"
              : "bg-white border-slate-200 hover:border-amber-200"
          }`}
        >
          <p className="text-[11px] font-bold uppercase text-amber-600">Medium Severity</p>
          <p className="text-2xl font-black text-amber-700 mt-1">{mediumCount}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Line item variances</p>
        </button>

        <button
          onClick={() => setSeverityFilter(severityFilter === "Low" ? "" : "Low")}
          className={`p-4 rounded-xl border text-left transition-all ${
            severityFilter === "Low"
              ? "bg-blue-50 border-blue-300 ring-2 ring-blue-400"
              : "bg-white border-slate-200 hover:border-blue-200"
          }`}
        >
          <p className="text-[11px] font-bold uppercase text-blue-600">Low Severity</p>
          <p className="text-2xl font-black text-blue-700 mt-1">{lowCount}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Minor formatting / currency</p>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-slate-600">Status Filter:</span>
          <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
            <button
              onClick={() => setStatusFilter("Pending")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                statusFilter === "Pending" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Pending ({allValidations.length})
            </button>
            <button
              onClick={() => setStatusFilter("Resolved")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                statusFilter === "Resolved" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Resolved
            </button>
          </div>
        </div>

        {severityFilter && (
          <button
            onClick={() => setSeverityFilter("")}
            className="text-xs text-blue-600 hover:underline font-medium"
          >
            Clear Severity Filter ({severityFilter})
          </button>
        )}
      </div>

      {/* Issue Cards */}
      <div className="space-y-3">
        {loading ? (
          <div className="py-20 text-center bg-white rounded-xl border border-slate-200">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
            <p className="text-xs text-slate-500">Scanning document validations...</p>
          </div>
        ) : allValidations.length === 0 ? (
          <div className="py-20 text-center bg-white rounded-xl border border-slate-200">
            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-slate-800">No Validation Issues Found</h3>
            <p className="text-xs text-slate-500 mt-1">
              All documents in this filter view satisfy deterministic mathematical integrity.
            </p>
          </div>
        ) : (
          allValidations.map((issue) => (
            <div
              key={issue.id}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2.5">
                  <SeverityBadge severity={issue.severity} />
                  <span className="font-bold text-slate-900 text-xs">{issue.validation_type}</span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Document: {issue.document_name}
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">{issue.description}</p>
                <div className="flex flex-wrap gap-4 text-[11px] text-slate-500 pt-1">
                  <span>Field: <strong className="text-slate-700">{issue.field_name || "Invoice"}</strong></span>
                  <span>Expected: <strong className="text-slate-700">{issue.expected_value}</strong></span>
                  <span>Actual: <strong className="text-slate-700">{issue.actual_value}</strong></span>
                  {issue.difference && (
                    <span>Discrepancy: <strong className="text-rose-600">{issue.difference}</strong></span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Link
                  href={`/extraction?docId=${issue.document_id}`}
                  className="px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Edit className="w-3.5 h-3.5" />
                  <span>Correct Extracted Value</span>
                </Link>
                <Link
                  href={`/documents/${issue.document_id}`}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>View Doc</span>
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

