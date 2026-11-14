import {
  DocumentItem,
  DocumentDetail,
  InvoiceData,
  ValidationResult,
  VerificationReport,
  JobItem,
  SearchResultItem,
  AnalyticsOverview,
} from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errMessage = `API Error: ${res.status} ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData.detail) errMessage = errData.detail;
      else if (errData.message) errMessage = errData.message;
    } catch {}
    throw new Error(errMessage);
  }
  return res.json();
}

export const api = {
  // Health
  getHealth: () => fetchJson<{ status: string; backend: string; database: string; background_queue: string; ai_provider: any }>(`${API_BASE}/health`),

  // Documents
  getDocuments: (params?: { status?: string; classification?: string; search?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.append("status", params.status);
    if (params?.classification) q.append("classification", params.classification);
    if (params?.search) q.append("search", params.search);
    if (params?.limit) q.append("limit", params.limit.toString());
    if (params?.offset) q.append("offset", params.offset.toString());
    return fetchJson<{ total: number; limit: number; offset: number; documents: DocumentItem[] }>(`${API_BASE}/documents?${q.toString()}`);
  },

  getDocument: (id: string) => fetchJson<DocumentDetail>(`${API_BASE}/documents/${id}`),

  uploadDocuments: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json() as Promise<DocumentItem[]>;
  },

  getDocumentStatus: (id: string) => fetchJson<{ document_id: string; filename: string; processing_status: string; job_progress: number; duration_seconds: number }>(`${API_BASE}/documents/${id}/status`),

  getDocumentResults: (id: string) => fetchJson<InvoiceData | null>(`${API_BASE}/documents/${id}/results`),

  getDocumentValidation: (id: string, severity?: string, statusFilter?: string) => {
    const q = new URLSearchParams();
    if (severity) q.append("severity", severity);
    if (statusFilter) q.append("status_filter", statusFilter);
    return fetchJson<ValidationResult[]>(`${API_BASE}/documents/${id}/validation?${q.toString()}`);
  },

  applyCorrection: (
    documentId: string,
    data: { field_name: string; corrected_value: any; reason?: string; reviewer_name?: string }
  ) =>
    fetchJson<{ status: string; message: string; field_name: string; corrected_value: any; document_status: string; active_validation_issues_count: number }>(
      `${API_BASE}/documents/${documentId}/corrections`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    ),

  retryProcessing: (documentId: string) =>
    fetchJson<{ status: string; message: string }>(`${API_BASE}/documents/${documentId}/retry`, {
      method: "POST",
    }),

  // Verification
  verifyPdfToPdf: (sourceId: string, targetId: string) =>
    fetchJson<VerificationReport>(`${API_BASE}/verification/pdf-pdf`, {
      method: "POST",
      body: JSON.stringify({ source_document_id: sourceId, target_document_id: targetId }),
    }),

  verifyPdfToExcel: (pdfIds: string[], excelId: string) =>
    fetchJson<VerificationReport>(`${API_BASE}/verification/pdf-excel`, {
      method: "POST",
      body: JSON.stringify({ pdf_document_ids: pdfIds, excel_document_id: excelId }),
    }),

  getVerificationReports: () => fetchJson<VerificationReport[]>(`${API_BASE}/verification`),

  getVerificationReport: (id: string) => fetchJson<VerificationReport>(`${API_BASE}/verification/${id}`),

  // Search
  search: (query: string, searchType = "all", filters?: { supplier?: string; min_amount?: number; max_amount?: number; doc_type?: string }) => {
    const q = new URLSearchParams();
    q.append("q", query);
    q.append("type", searchType);
    if (filters?.supplier) q.append("supplier", filters.supplier);
    if (filters?.min_amount) q.append("min_amount", filters.min_amount.toString());
    if (filters?.max_amount) q.append("max_amount", filters.max_amount.toString());
    if (filters?.doc_type) q.append("doc_type", filters.doc_type);
    return fetchJson<{ query: string; search_type: string; total_results: number; results: SearchResultItem[] }>(`${API_BASE}/search?${q.toString()}`);
  },

  // Jobs
  getJobs: () => fetchJson<JobItem[]>(`${API_BASE}/jobs`),

  // Analytics
  getAnalytics: () => fetchJson<AnalyticsOverview>(`${API_BASE}/analytics/overview`),

  getExportCsvUrl: () => `${API_BASE}/analytics/export/csv`,

  getFilePreviewUrl: (documentId: string) => `${API_BASE}/documents/${documentId}/file`,
};
