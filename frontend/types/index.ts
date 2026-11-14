export interface DocumentItem {
  id: string;
  original_filename: string;
  file_format: string;
  file_size: number;
  file_hash: string;
  upload_time: string;
  processing_status: string;
  document_classification: string;
  page_count: number;
  processing_duration: number;
  error_information: string | null;
  is_duplicate: boolean;
  duplicate_of_id: string | null;
}

export interface LineItem {
  id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax: number | null;
  amount: number;
  confidence?: number;
  source_page?: number;
}

export interface InvoiceData {
  id: string;
  document_id: string;
  invoice_number: string | null;
  invoice_date: string | null;
  supplier_name: string | null;
  customer_name: string | null;
  subtotal: number | null;
  tax: number | null;
  total_amount: number | null;
  currency: string | null;
  line_items: LineItem[];
  missing_fields: string[];
  uncertain_fields: string[];
  confidence: Record<string, number>;
  source_references: Array<{ field: string; page: number; snippet: string }>;
  requires_manual_review: boolean;
  is_corrected: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentPage {
  id: string;
  page_number: number;
  raw_text: string | null;
  ocr_applied: boolean;
  ocr_confidence: number | null;
  is_empty: boolean;
}

export interface ExtractedText {
  raw_text: string;
  normalized_text: string;
  page_count: number;
  extraction_method: string;
}

export interface DocumentDetail extends DocumentItem {
  pages: DocumentPage[];
  extracted_text: ExtractedText | null;
  invoice: InvoiceData | null;
  validation_issues_count: number;
}

export interface ValidationResult {
  id: string;
  document_id: string;
  invoice_id: string | null;
  validation_type: string;
  field_name: string | null;
  expected_value: string | null;
  actual_value: string | null;
  difference: string | null;
  severity: "Critical" | "High" | "Medium" | "Low";
  description: string;
  status: "Pending" | "Resolved" | "Ignored";
  created_timestamp: string;
}

export interface VerificationItem {
  id: string;
  field_name: string;
  source_value: string | null;
  target_value: string | null;
  is_match: boolean;
  discrepancy_type: string | null;
  severity: string;
  notes: string | null;
}

export interface VerificationReport {
  id: string;
  report_type: "PDF_PDF" | "PDF_EXCEL";
  source_document_id: string | null;
  target_document_id: string | null;
  matching_score: number;
  status: string;
  summary: Record<string, any>;
  items: VerificationItem[];
  created_at: string;
}

export interface JobItem {
  id: string;
  document_id: string;
  document_name: string;
  job_type: string;
  current_status: string;
  progress: number;
  creation_time: string;
  processing_duration: number;
  error_message: string | null;
}

export interface SearchResultItem {
  document_id: string;
  filename: string;
  document_type: string;
  file_format: string;
  upload_time: string;
  relevance_score: number;
  matched_by: string;
  snippet: string;
  invoice_details: Record<string, any> | null;
}

export interface AnalyticsOverview {
  total_documents: number;
  processed_documents: number;
  pending_documents: number;
  failed_documents: number;
  validation_errors_count: number;
  duplicate_invoices_count: number;
  documents_awaiting_review: number;
  average_processing_time: number;
  measured_extraction_accuracy: number;
  file_type_distribution: Record<string, number>;
  document_processing_trend: Array<{ date: string; processed: number; failed: number }>;
  validation_error_distribution: Record<string, number>;
  recent_activity: Array<{ id: string; action: string; entity: string; timestamp: string; details: any }>;
}
