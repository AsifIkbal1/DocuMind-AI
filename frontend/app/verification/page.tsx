"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCheck,
  FileText,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  ArrowRight,
  Percent,
} from "lucide-react";
import { api } from "../../services/api";
import { DocumentItem, VerificationReport, VerificationItem } from "../../types";

export default function VerificationCenterPage() {
  const [activeWorkflow, setActiveWorkflow] = useState<"pdf-pdf" | "pdf-excel">("pdf-pdf");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [pdfDocs, setPdfDocs] = useState<DocumentItem[]>([]);
  const [excelDocs, setExcelDocs] = useState<DocumentItem[]>([]);

  // PDF-to-PDF states
  const [sourcePdfId, setSourcePdfId] = useState("");
  const [targetPdfId, setTargetPdfId] = useState("");
  const [pdfPdfReport, setPdfPdfReport] = useState<VerificationReport | null>(null);
  const [pdfPdfLoading, setPdfPdfLoading] = useState(false);

  // PDF-to-Excel states
  const [selectedPdfIds, setSelectedPdfIds] = useState<string[]>([]);
  const [selectedExcelId, setSelectedExcelId] = useState("");
  const [pdfExcelReport, setPdfExcelReport] = useState<VerificationReport | null>(null);
  const [pdfExcelLoading, setPdfExcelLoading] = useState(false);

  // Historical reports
  const [historyReports, setHistoryReports] = useState<VerificationReport[]>([]);

  useEffect(() => {
    api.getDocuments({ limit: 100 }).then((res) => {
      setDocuments(res.documents);
      const pdfs = res.documents.filter((d) => d.file_format === "pdf");
      const excels = res.documents.filter((d) => ["xlsx", "xls", "csv"].includes(d.file_format));
      setPdfDocs(pdfs);
      setExcelDocs(excels);

      if (pdfs.length >= 2) {
        setSourcePdfId(pdfs[0].id);
        setTargetPdfId(pdfs[1].id);
      }
      if (pdfs.length > 0) {
        setSelectedPdfIds(pdfs.slice(0, 3).map((p) => p.id));
      }
      if (excels.length > 0) {
        setSelectedExcelId(excels[0].id);
      }
    });

    api.getVerificationReports().then((reps) => setHistoryReports(reps));
  }, []);

  const handleRunPdfToPdf = async () => {
    if (!sourcePdfId || !targetPdfId) return;
    setPdfPdfLoading(true);
    try {
      const rep = await api.verifyPdfToPdf(sourcePdfId, targetPdfId);
      setPdfPdfReport(rep);
      api.getVerificationReports().then((reps) => setHistoryReports(reps));
    } catch (err: any) {
      alert(err.message || "PDF comparison failed");
    } finally {
      setPdfPdfLoading(false);
    }
  };

  const handleRunPdfToExcel = async () => {
    if (selectedPdfIds.length === 0 || !selectedExcelId) return;
    setPdfExcelLoading(true);
    try {
      const rep = await api.verifyPdfToExcel(selectedPdfIds, selectedExcelId);
      setPdfExcelReport(rep);
      api.getVerificationReports().then((reps) => setHistoryReports(reps));
    } catch (err: any) {
      alert(err.message || "PDF-Excel verification failed");
    } finally {
      setPdfExcelLoading(false);
    }
  };

  const togglePdfSelection = (id: string) => {
    if (selectedPdfIds.includes(id)) {
      setSelectedPdfIds(selectedPdfIds.filter((item) => item !== id));
    } else {
      setSelectedPdfIds([...selectedPdfIds, id]);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="pb-3 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Cross-Verification Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          Perform multi-document comparison across PDF invoices and reconcile ledger records against Excel workbooks.
        </p>
      </div>

      {/* Workflow Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveWorkflow("pdf-pdf")}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeWorkflow === "pdf-pdf"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>PDF-to-PDF Side-by-Side Comparison</span>
        </button>
        <button
          onClick={() => setActiveWorkflow("pdf-excel")}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeWorkflow === "pdf-excel"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>PDF-to-Excel Workbook Reconciliation</span>
        </button>
      </div>

      {/* WORKFLOW 1: PDF TO PDF */}
      {activeWorkflow === "pdf-pdf" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Select PDF Invoices to Compare</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Source PDF Invoice:</label>
                <select
                  value={sourcePdfId}
                  onChange={(e) => setSourcePdfId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {pdfDocs.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename} ({d.document_classification})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Target PDF Invoice (Comparison):</label>
                <select
                  value={targetPdfId}
                  onChange={(e) => setTargetPdfId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {pdfDocs.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename} ({d.document_classification})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={handleRunPdfToPdf}
                disabled={pdfPdfLoading || !sourcePdfId || !targetPdfId}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
              >
                {pdfPdfLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>Execute Side-by-Side Comparison</span>
              </button>
            </div>
          </div>

          {/* Results Comparison Table */}
          {pdfPdfReport && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-5">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Verification Report #{pdfPdfReport.id.slice(0, 8)}</h3>
                  <p className="text-xs text-slate-500">
                    Source: {pdfPdfReport.summary.source_filename} vs Target: {pdfPdfReport.summary.target_filename}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold">Similarity Match</span>
                    <p className="text-lg font-bold text-blue-600">{pdfPdfReport.matching_score}%</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      pdfPdfReport.matching_score >= 90
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}
                  >
                    {pdfPdfReport.status}
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b">
                    <tr>
                      <th className="py-2.5 px-3">Field</th>
                      <th className="py-2.5 px-3">Source PDF Value</th>
                      <th className="py-2.5 px-3">Target PDF Value</th>
                      <th className="py-2.5 px-3 text-center">Match?</th>
                      <th className="py-2.5 px-3">Discrepancy Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {pdfPdfReport.items.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-semibold text-slate-800">{item.field_name}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-700">{item.source_value || "(none)"}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-700">{item.target_value || "(none)"}</td>
                        <td className="py-2.5 px-3 text-center">
                          {item.is_match ? (
                            <CheckCircle className="w-4 h-4 text-emerald-500 mx-auto" />
                          ) : (
                            <XCircle className="w-4 h-4 text-rose-500 mx-auto" />
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 text-[11px]">{item.notes || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* WORKFLOW 2: PDF TO EXCEL */}
      {activeWorkflow === "pdf-excel" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Reconcile PDF Invoices Against Excel Workbook
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Select PDFs */}
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Select PDF Invoices to Reconcile ({selectedPdfIds.length} selected):
                </label>
                <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100">
                  {pdfDocs.map((doc) => (
                    <label
                      key={doc.id}
                      className="flex items-center gap-2.5 p-2 text-xs hover:bg-slate-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPdfIds.includes(doc.id)}
                        onChange={() => togglePdfSelection(doc.id)}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="font-medium text-slate-800">{doc.original_filename}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Select Excel */}
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Target Excel Workbook / Ledger:
                </label>
                <select
                  value={selectedExcelId}
                  onChange={(e) => setSelectedExcelId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {excelDocs.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename} ({d.file_format.toUpperCase()})
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-400 mt-2">
                  The reconciliation engine will automatically inspect all worksheets, map column headers, and flag missing rows or amount discrepancies.
                </p>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={handleRunPdfToExcel}
                disabled={pdfExcelLoading || selectedPdfIds.length === 0 || !selectedExcelId}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
              >
                {pdfExcelLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>Execute Reconciliation Matching</span>
              </button>
            </div>
          </div>

          {/* Results Reconciliation Table */}
          {pdfExcelReport && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-5">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Reconciliation Report #{pdfExcelReport.id.slice(0, 8)}</h3>
                  <p className="text-xs text-slate-500">
                    Reconciled {pdfExcelReport.summary.total_pdf_invoices} PDF invoices against {pdfExcelReport.summary.total_excel_records} spreadsheet records.
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold">Matched Records</span>
                    <p className="text-lg font-bold text-emerald-600">
                      {pdfExcelReport.summary.matched_records} / {pdfExcelReport.summary.total_pdf_invoices} ({pdfExcelReport.matching_score}%)
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      pdfExcelReport.status === "Completed"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}
                  >
                    {pdfExcelReport.status}
                  </span>
                </div>
              </div>

              {/* Duplicate Rows in Excel Warning */}
              {pdfExcelReport.summary.duplicate_excel_rows_count > 0 && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2 text-xs text-amber-800 font-semibold">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>
                    Detected {pdfExcelReport.summary.duplicate_excel_rows_count} duplicate row(s) inside the spreadsheet ledger!
                  </span>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b">
                    <tr>
                      <th className="py-2.5 px-3">Item / Target</th>
                      <th className="py-2.5 px-3">PDF Invoice Source</th>
                      <th className="py-2.5 px-3">Excel Ledger Match</th>
                      <th className="py-2.5 px-3 text-center">Status</th>
                      <th className="py-2.5 px-3">Audit Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {pdfExcelReport.items.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-semibold text-slate-800">{item.field_name}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-700 text-[11px]">{item.source_value || "-"}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-700 text-[11px]">{item.target_value || "-"}</td>
                        <td className="py-2.5 px-3 text-center">
                          {item.is_match ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                              <CheckCircle className="w-3 h-3" />
                              Matched
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                              <XCircle className="w-3 h-3" />
                              Discrepancy
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 text-[11px]">{item.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
