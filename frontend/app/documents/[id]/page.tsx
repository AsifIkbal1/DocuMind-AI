"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Edit,
  History,
  Layers,
  FileCode,
} from "lucide-react";
import { api } from "../../../services/api";
import { DocumentDetail, ValidationResult } from "../../../types";
import { StatusBadge } from "../../../components/StatusBadge";
import { SeverityBadge } from "../../../components/SeverityBadge";

export default function DocumentDetailPage() {
  const params = useParams();
  const documentId = params.id as string;

  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [validations, setValidations] = useState<ValidationResult[]>([]);
  const [activeTab, setActiveTab] = useState<"invoice" | "pages" | "text" | "validation" | "history">("invoice");
  const [loading, setLoading] = useState(true);

  const loadDoc = async () => {
    try {
      setLoading(true);
      const doc = await api.getDocument(documentId);
      setDocument(doc);
      const vals = await api.getDocumentValidation(documentId);
      setValidations(vals);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (documentId) loadDoc();
  }, [documentId]);

  if (loading) {
    return (
      <div className="py-24 text-center">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
        <p className="text-sm text-slate-500">Loading document details...</p>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="py-24 text-center">
        <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
        <p className="text-base font-semibold text-slate-800">Document not found</p>
        <Link href="/documents" className="text-xs text-blue-600 underline mt-2 inline-block">
          Return to Document Center
        </Link>
      </div>
    );
  }

  const invoice = document.invoice;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Back button & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <Link
            href="/documents"
            className="p-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">{document.original_filename}</h1>
              <StatusBadge status={document.processing_status} />
              <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                {document.document_classification}
              </span>
            </div>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              ID: {document.id} | Hash: {document.file_hash.slice(0, 16)}... | Uploaded: {new Date(document.upload_time).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={api.getFilePreviewUrl(document.id)}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Open Original File</span>
          </a>
          <Link
            href={`/extraction?docId=${document.id}`}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Edit className="w-3.5 h-3.5" />
            <span>Edit Extracted Data</span>
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 flex gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab("invoice")}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeTab === "invoice"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Extracted Invoice Data</span>
        </button>
        <button
          onClick={() => setActiveTab("validation")}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeTab === "validation"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Validation Audit ({validations.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("pages")}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeTab === "pages"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Pages & OCR ({document.pages?.length || 0})</span>
        </button>
        <button
          onClick={() => setActiveTab("text")}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeTab === "text"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          <FileCode className="w-4 h-4" />
          <span>Text Representation</span>
        </button>
      </div>

      {/* TAB CONTENT: INVOICE */}
      {activeTab === "invoice" && (
        <div className="space-y-6">
          {invoice ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <p className="text-[11px] font-semibold uppercase text-slate-400">Invoice Number</p>
                  <p className="text-base font-bold text-slate-900 mt-1">{invoice.invoice_number || "N/A"}</p>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <p className="text-[11px] font-semibold uppercase text-slate-400">Invoice Date</p>
                  <p className="text-base font-bold text-slate-900 mt-1">{invoice.invoice_date || "N/A"}</p>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <p className="text-[11px] font-semibold uppercase text-slate-400">Supplier Name</p>
                  <p className="text-base font-bold text-slate-900 mt-1 truncate">{invoice.supplier_name || "N/A"}</p>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <p className="text-[11px] font-semibold uppercase text-slate-400">Total Amount</p>
                  <p className="text-base font-bold text-blue-600 mt-1">
                    {invoice.total_amount != null ? `${invoice.total_amount.toFixed(2)} ${invoice.currency}` : "N/A"}
                  </p>
                </div>
              </div>

              {/* Financial Totals Breakdown */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div>
                  <span className="text-slate-500">Customer:</span>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">{invoice.customer_name || "Not parsed"}</p>
                </div>
                <div>
                  <span className="text-slate-500">Subtotal:</span>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">
                    {invoice.subtotal != null ? `${invoice.subtotal.toFixed(2)} ${invoice.currency}` : "N/A"}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Tax / VAT:</span>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">
                    {invoice.tax != null ? `${invoice.tax.toFixed(2)} ${invoice.currency}` : "0.00"}
                  </p>
                </div>
              </div>

              {/* Line Items Table */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="py-3 px-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Line Items ({invoice.line_items?.length || 0})
                  </h3>
                  {invoice.is_corrected && (
                    <span className="text-[11px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      Edited by reviewer
                    </span>
                  )}
                </div>
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50/60 border-b border-slate-200 text-slate-500 uppercase text-[10px] font-semibold">
                    <tr>
                      <th className="py-2.5 px-4">#</th>
                      <th className="py-2.5 px-4">Description</th>
                      <th className="py-2.5 px-4 text-right">Quantity</th>
                      <th className="py-2.5 px-4 text-right">Unit Price</th>
                      <th className="py-2.5 px-4 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {invoice.line_items && invoice.line_items.length > 0 ? (
                      invoice.line_items.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50">
                          <td className="py-2.5 px-4 text-slate-400 font-mono">{idx + 1}</td>
                          <td className="py-2.5 px-4 font-medium text-slate-800">{item.description}</td>
                          <td className="py-2.5 px-4 text-right text-slate-600">{item.quantity}</td>
                          <td className="py-2.5 px-4 text-right text-slate-600 font-mono">{item.unit_price.toFixed(2)}</td>
                          <td className="py-2.5 px-4 text-right font-semibold text-slate-900 font-mono">{item.amount.toFixed(2)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-6 text-center text-slate-400">
                          No line items found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="bg-white p-12 text-center rounded-xl border border-slate-200 text-slate-400 text-sm">
              No structured invoice data extracted for this document.
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: VALIDATION */}
      {activeTab === "validation" && (
        <div className="space-y-4">
          {validations.length === 0 ? (
            <div className="bg-white p-12 text-center rounded-xl border border-slate-200">
              <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800">All Validations Passed!</p>
              <p className="text-xs text-slate-500 mt-1">
                Zero mathematical discrepancies, duplicates, or missing essential fields detected.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
              {validations.map((val) => (
                <div key={val.id} className="p-4 flex items-start justify-between gap-4 hover:bg-slate-50/50">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <SeverityBadge severity={val.severity} />
                      <span className="text-xs font-bold text-slate-800">{val.validation_type}</span>
                      <span className="text-xs text-slate-400 font-mono">({val.field_name || "Document"})</span>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">{val.description}</p>
                    <div className="flex gap-4 text-[11px] text-slate-500 pt-1">
                      <span>Expected: <strong className="text-slate-700">{val.expected_value}</strong></span>
                      <span>Actual: <strong className="text-slate-700">{val.actual_value}</strong></span>
                      {val.difference && <span>Variance: <strong className="text-rose-600">{val.difference}</strong></span>}
                    </div>
                  </div>
                  <div className="shrink-0">
                    <Link
                      href={`/extraction?docId=${document.id}`}
                      className="px-2.5 py-1 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded text-xs font-semibold inline-flex items-center gap-1"
                    >
                      <Edit className="w-3 h-3" />
                      Fix
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: PAGES & OCR */}
      {activeTab === "pages" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {document.pages && document.pages.length > 0 ? (
              document.pages.map((page) => (
                <div key={page.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-xs font-bold text-slate-800">Page {page.page_number}</span>
                    <div className="flex items-center gap-2">
                      {page.ocr_applied ? (
                        <span className="text-[10px] bg-purple-50 text-purple-700 font-semibold px-2 py-0.5 rounded border border-purple-200">
                          OCR Applied ({Math.round((page.ocr_confidence || 0.85) * 100)}% conf)
                        </span>
                      ) : (
                        <span className="text-[10px] bg-slate-100 text-slate-600 font-semibold px-2 py-0.5 rounded">
                          Digital Extraction
                        </span>
                      )}
                      {page.is_empty && (
                        <span className="text-[10px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded">Empty</span>
                      )}
                    </div>
                  </div>
                  <pre className="text-[11px] font-mono text-slate-700 bg-slate-50 p-3 rounded-lg max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {page.raw_text || "(No text detected on this page)"}
                  </pre>
                </div>
              ))
            ) : (
              <div className="col-span-2 bg-white p-8 text-center text-xs text-slate-400 rounded-xl border">
                No page chunks stored.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: TEXT */}
      {activeTab === "text" && (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Normalized Full Text</h3>
            <span className="text-xs text-slate-400 font-mono">
              Method: {document.extracted_text?.extraction_method || "standard"}
            </span>
          </div>
          <pre className="text-xs font-mono text-slate-800 bg-slate-50 p-4 rounded-lg whitespace-pre-wrap max-h-96 overflow-y-auto border border-slate-200">
            {document.extracted_text?.normalized_text || "(No text)"}
          </pre>
        </div>
      )}
    </div>
  );
}

