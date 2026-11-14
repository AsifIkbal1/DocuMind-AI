"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  FileSpreadsheet,
  Save,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Plus,
  Trash2,
  HelpCircle,
  History,
} from "lucide-react";
import { api } from "../../services/api";
import { DocumentItem, DocumentDetail, InvoiceData, LineItem } from "../../types";

function ExtractionContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("docId") || "";

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>(initialDocId);
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [savingField, setSavingField] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Form states
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [invoiceDate, setInvoiceDate] = useState("");
  const [supplierName, setSupplierName] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [subtotal, setSubtotal] = useState<number | string>("");
  const [tax, setTax] = useState<number | string>("");
  const [totalAmount, setTotalAmount] = useState<number | string>("");
  const [currency, setCurrency] = useState("USD");
  const [lineItems, setLineItems] = useState<LineItem[]>([]);

  useEffect(() => {
    api.getDocuments({ limit: 100 }).then((res) => {
      setDocuments(res.documents);
      if (!selectedDocId && res.documents.length > 0) {
        setSelectedDocId(res.documents[0].id);
      }
    });
  }, []);

  const loadDocumentDetails = async (id: string) => {
    if (!id) return;
    setLoading(true);
    setSaveSuccess(null);
    try {
      const data = await api.getDocument(id);
      setDocDetail(data);
      if (data.invoice) {
        setInvoiceNumber(data.invoice.invoice_number || "");
        setInvoiceDate(data.invoice.invoice_date || "");
        setSupplierName(data.invoice.supplier_name || "");
        setCustomerName(data.invoice.customer_name || "");
        setSubtotal(data.invoice.subtotal ?? "");
        setTax(data.invoice.tax ?? "");
        setTotalAmount(data.invoice.total_amount ?? "");
        setCurrency(data.invoice.currency || "USD");
        setLineItems(data.invoice.line_items || []);
      } else {
        setInvoiceNumber("");
        setInvoiceDate("");
        setSupplierName("");
        setCustomerName("");
        setSubtotal("");
        setTax("");
        setTotalAmount("");
        setCurrency("USD");
        setLineItems([]);
      }
    } catch (err) {
      console.error("Failed to load invoice:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDocId) {
      loadDocumentDetails(selectedDocId);
    }
  }, [selectedDocId]);

  const handleSaveField = async (fieldName: string, value: any) => {
    if (!selectedDocId) return;
    setSavingField(fieldName);
    setSaveSuccess(null);
    try {
      await api.applyCorrection(selectedDocId, {
        field_name: fieldName,
        corrected_value: value,
        reason: "User manual verification in AI Extraction Center",
        reviewer_name: "Audit Specialist",
      });
      setSaveSuccess(`Updated ${fieldName.replace("_", " ")} successfully.`);
      setTimeout(() => setSaveSuccess(null), 3000);
      loadDocumentDetails(selectedDocId);
    } catch (err: any) {
      alert(err.message || "Correction failed");
    } finally {
      setSavingField(null);
    }
  };

  const handleSaveAll = async () => {
    if (!selectedDocId) return;
    setSavingField("all");
    try {
      await handleSaveField("invoice_number", invoiceNumber);
      await handleSaveField("invoice_date", invoiceDate);
      await handleSaveField("supplier_name", supplierName);
      await handleSaveField("customer_name", customerName);
      await handleSaveField("subtotal", Number(subtotal) || 0.0);
      await handleSaveField("tax", Number(tax) || 0.0);
      await handleSaveField("total_amount", Number(totalAmount) || 0.0);
      await handleSaveField("currency", currency);
      setSaveSuccess("All invoice fields successfully updated and validated!");
    } catch (err: any) {
      alert("Error saving fields: " + err.message);
    } finally {
      setSavingField(null);
    }
  };

  const invoice = docDetail?.invoice;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AI Extraction Center</h1>
          <p className="text-sm text-slate-500 mt-1">
            Review, verify, and non-destructively edit structured AI extractions with complete revision tracking.
          </p>
        </div>

        {/* Document Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Select Document:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename} ({d.document_classification})
              </option>
            ))}
          </select>
        </div>
      </div>

      {saveSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-xs font-semibold text-emerald-800">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <span>{saveSuccess}</span>
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
          <p className="text-sm text-slate-500">Loading extracted data...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Editable Form */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  Extracted Invoice Fields
                </h2>
                <p className="text-xs text-slate-500">Directly edit values below. Changes update downstream validations.</p>
              </div>
              <button
                onClick={handleSaveAll}
                disabled={savingField !== null}
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save All Changes</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Invoice Number */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-700">Invoice Number</label>
                  {invoice?.confidence?.invoice_number && (
                    <span className="text-[10px] text-slate-400">
                      {Math.round(invoice.confidence.invoice_number * 100)}% conf
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={invoiceNumber}
                    onChange={(e) => setInvoiceNumber(e.target.value)}
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSaveField("invoice_number", invoiceNumber)}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                    title="Save this field"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Invoice Date */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-700">Invoice Date</label>
                  {invoice?.confidence?.invoice_date && (
                    <span className="text-[10px] text-slate-400">
                      {Math.round(invoice.confidence.invoice_date * 100)}% conf
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={invoiceDate}
                    onChange={(e) => setInvoiceDate(e.target.value)}
                    placeholder="YYYY-MM-DD"
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSaveField("invoice_date", invoiceDate)}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Supplier Name */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Supplier Name</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={supplierName}
                    onChange={(e) => setSupplierName(e.target.value)}
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSaveField("supplier_name", supplierName)}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Customer Name */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Customer Name</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSaveField("customer_name", customerName)}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Subtotal */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Subtotal</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    step="0.01"
                    value={subtotal}
                    onChange={(e) => setSubtotal(e.target.value)}
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSaveField("subtotal", Number(subtotal))}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Tax */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Tax / VAT</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    step="0.01"
                    value={tax}
                    onChange={(e) => setTax(e.target.value)}
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSaveField("tax", Number(tax))}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Total Amount */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Total Amount</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    step="0.01"
                    value={totalAmount}
                    onChange={(e) => setTotalAmount(e.target.value)}
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-bold text-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSaveField("total_amount", Number(totalAmount))}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Currency */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Currency</label>
                <div className="flex gap-2">
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="BDT">BDT (৳)</option>
                    <option value="INR">INR (₹)</option>
                  </select>
                  <button
                    onClick={() => handleSaveField("currency", currency)}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Line items Section */}
            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
                Extracted Line Items ({lineItems.length})
              </h3>
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
                {lineItems.length > 0 ? (
                  lineItems.map((item, idx) => (
                    <div key={idx} className="p-3 text-xs flex items-center justify-between gap-4 hover:bg-slate-50">
                      <div className="flex-1">
                        <p className="font-semibold text-slate-800">{item.description}</p>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Qty: {item.quantity} × Unit Price: {item.unit_price.toFixed(2)}
                        </p>
                      </div>
                      <div className="text-right font-mono font-bold text-slate-900">
                        {item.amount.toFixed(2)} {currency}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-6 text-center text-xs text-slate-400">No line items extracted.</div>
                )}
              </div>
            </div>
          </div>

          {/* Right Quality Panel & Discrepancies */}
          <div className="space-y-6">
            {/* Review Status Card */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Audit Status</h3>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Document Status:</span>
                  <span className="font-semibold text-slate-800">{docDetail?.processing_status}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Manual Review Flag:</span>
                  <span
                    className={`font-semibold ${
                      invoice?.requires_manual_review ? "text-amber-600" : "text-emerald-600"
                    }`}
                  >
                    {invoice?.requires_manual_review ? "Flagged for Review" : "Validated Clean"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Correction Trail:</span>
                  <span className="font-semibold text-slate-800">
                    {invoice?.is_corrected ? "Modified by reviewer" : "Original AI extract"}
                  </span>
                </div>
              </div>
            </div>

            {/* Missing & Uncertain Fields Alert */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Missing / Uncertain Fields</h3>
              {invoice?.missing_fields && invoice.missing_fields.length > 0 ? (
                <div className="space-y-1.5">
                  {invoice.missing_fields.map((f) => (
                    <div
                      key={f}
                      className="px-2.5 py-1.5 bg-amber-50 border border-amber-200 text-amber-800 rounded-md text-xs font-medium flex items-center justify-between"
                    >
                      <span>Missing: <strong>{f}</strong></span>
                      <span className="text-[10px] bg-amber-200/60 px-1.5 py-0.5 rounded">Action Req</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-emerald-600 flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5" />
                  All mandatory financial fields were identified.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ExtractionCenterPage() {
  return (
    <Suspense fallback={<div className="py-24 text-center text-sm text-slate-500">Loading Extraction Center...</div>}>
      <ExtractionContent />
    </Suspense>
  );
}

