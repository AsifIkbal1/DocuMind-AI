"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  Upload,
  Search,
  Filter,
  FileText,
  RefreshCw,
  Eye,
  AlertCircle,
  CheckCircle,
  FileSpreadsheet,
  Image as ImageIcon,
  Copy,
} from "lucide-react";
import { api } from "../../services/api";
import { DocumentItem } from "../../types";
import { StatusBadge } from "../../components/StatusBadge";

export default function DocumentCenterPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const res = await api.getDocuments({
        search: search || undefined,
        status: statusFilter || undefined,
        classification: classFilter || undefined,
        limit: 50,
      });
      setDocuments(res.documents);
      setTotal(res.total);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [statusFilter, classFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadDocuments();
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(`Uploading ${files.length} document(s)...`);

    try {
      const fileArray = Array.from(files);
      await api.uploadDocuments(fileArray);
      setUploadProgress("Upload complete! Processing queued in background.");
      setTimeout(() => setUploadProgress(null), 3000);
      loadDocuments();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload files.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRetry = async (docId: string) => {
    try {
      await api.retryProcessing(docId);
      loadDocuments();
    } catch (err: any) {
      alert(err.message || "Retry failed");
    }
  };

  const getFormatIcon = (fmt: string) => {
    if (fmt === "pdf") return <FileText className="w-4 h-4 text-red-500" />;
    if (["xlsx", "xls", "csv"].includes(fmt)) return <FileSpreadsheet className="w-4 h-4 text-emerald-600" />;
    return <ImageIcon className="w-4 h-4 text-blue-500" />;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Document Center</h1>
          <p className="text-sm text-slate-500 mt-1">
            Batch ingest, classify, and track multi-page PDFs, scans, images, and spreadsheets.
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Documents</span>
        </button>
        <input
          type="file"
          ref={fileInputRef}
          multiple
          className="hidden"
          onChange={(e) => handleFileUpload(e.target.files)}
          accept=".pdf,.jpg,.jpeg,.png,.tiff,.xlsx,.xls,.csv"
        />
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFileUpload(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-300 hover:border-blue-500 bg-white hover:bg-blue-50/20 rounded-xl p-8 text-center cursor-pointer transition-colors shadow-sm"
      >
        <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
          <Upload className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800">
          Click or drag & drop files here to upload
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Supports PDF (digital & scanned up to 1,000 pages), JPG, PNG, TIFF, XLSX, XLS, and CSV (max 50 MB)
        </p>
        {uploadProgress && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 text-xs font-medium rounded-lg">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>{uploadProgress}</span>
          </div>
        )}
        {uploadError && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-rose-50 text-rose-700 text-xs font-medium rounded-lg">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Filters & Search Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full md:max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Filter by filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </form>

        <div className="flex items-center gap-2 w-full md:w-auto">
          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Completed">Completed</option>
            <option value="Needs Review">Needs Review</option>
            <option value="Processing">Processing</option>
            <option value="Failed">Failed</option>
            <option value="Queued">Queued</option>
          </select>

          {/* Classification filter */}
          <select
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Classifications</option>
            <option value="Invoice">Invoice</option>
            <option value="Receipt">Receipt</option>
            <option value="Financial Statement">Financial Statement</option>
            <option value="Spreadsheet">Spreadsheet</option>
            <option value="Unknown Document">Unknown</option>
          </select>

          <button
            onClick={loadDocuments}
            className="p-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <tr>
                <th className="py-3 px-4">Document</th>
                <th className="py-3 px-4">Classification</th>
                <th className="py-3 px-4">Size / Pages</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Duplicate?</th>
                <th className="py-3 px-4">Processing Time</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-slate-400" />
                    Loading documents...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No documents found matching the filter criteria.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="p-1.5 rounded bg-slate-100">
                          {getFormatIcon(doc.file_format)}
                        </div>
                        <div>
                          <Link
                            href={`/documents/${doc.id}`}
                            className="font-semibold text-slate-900 hover:text-blue-600 transition-colors"
                          >
                            {doc.original_filename}
                          </Link>
                          <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                            ID: {doc.id.slice(0, 8)}... | {new Date(doc.upload_time).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700 font-medium">
                        {doc.document_classification}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {(doc.file_size / 1024).toFixed(1)} KB
                      <span className="text-slate-400 ml-1.5 font-normal">
                        ({doc.page_count} {doc.page_count === 1 ? "page" : "pages"})
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={doc.processing_status} />
                    </td>
                    <td className="py-3 px-4">
                      {doc.is_duplicate ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded">
                          <Copy className="w-3 h-3" />
                          Duplicate
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px]">Unique</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">
                      {doc.processing_duration ? `${doc.processing_duration}s` : "-"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/documents/${doc.id}`}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-medium flex items-center gap-1 transition-colors"
                        >
                          <Eye className="w-3 h-3" />
                          View
                        </Link>
                        {doc.processing_status === "Failed" && (
                          <button
                            onClick={() => handleRetry(doc.id)}
                            className="px-2.5 py-1 bg-rose-100 hover:bg-rose-200 text-rose-700 rounded text-xs font-medium flex items-center gap-1 transition-colors"
                          >
                            <RefreshCw className="w-3 h-3" />
                            Retry
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="py-3 px-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span>Showing {documents.length} of {total} documents</span>
        </div>
      </div>
    </div>
  );
}
