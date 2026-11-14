"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Search as SearchIcon,
  Sparkles,
  Filter,
  FileText,
  DollarSign,
  Building,
  Calendar,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { api } from "../../services/api";
import { SearchResultItem } from "../../types";

const EXAMPLE_QUERIES = [
  "Find invoices from ABC Technologies",
  "Show invoices with a total amount greater than 50,000 BDT",
  "Find invoices containing software development services",
  "Find documents with inconsistent tax amounts",
  "Cloud hosting and database cluster invoices",
];

function SearchContent() {
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQ);
  const [searchType, setSearchType] = useState<"all" | "keyword" | "semantic">("all");
  const [supplier, setSupplier] = useState("");
  const [minAmount, setMinAmount] = useState<number | string>("");
  const [maxAmount, setMaxAmount] = useState<number | string>("");
  const [docType, setDocType] = useState("");

  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const executeSearch = async (overrideQ?: string) => {
    const qToUse = overrideQ !== undefined ? overrideQ : query;
    setLoading(true);
    setSearched(true);
    try {
      const res = await api.search(qToUse, searchType, {
        supplier: supplier || undefined,
        min_amount: minAmount ? Number(minAmount) : undefined,
        max_amount: maxAmount ? Number(maxAmount) : undefined,
        doc_type: docType || undefined,
      });
      setResults(res.results);
      setTotal(res.total_results);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQ) executeSearch(initialQ);
  }, [initialQ]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch();
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    executeSearch(example);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="pb-3 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Hybrid & Semantic Search Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          Search across unstructured document text, parsed financial line items, and vector semantic similarity.
        </p>
      </div>

      {/* Search Input Box */}
      <form onSubmit={handleFormSubmit} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="relative">
          <SearchIcon className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by keywords, vendor names, or ask in natural language (e.g. 'Show invoices over $5,000')..."
            className="w-full pl-12 pr-28 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <SearchIcon className="w-3.5 h-3.5" />}
            <span>Search</span>
          </button>
        </div>

        {/* Mode Toggle & Filter Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2 text-xs">
          {/* Mode */}
          <div>
            <label className="font-semibold text-slate-600 block mb-1">Search Engine Mode:</label>
            <div className="flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
              <button
                type="button"
                onClick={() => setSearchType("all")}
                className={`flex-1 py-1 rounded text-center font-medium ${
                  searchType === "all" ? "bg-white text-blue-600 shadow-xs font-bold" : "text-slate-600"
                }`}
              >
                Hybrid
              </button>
              <button
                type="button"
                onClick={() => setSearchType("semantic")}
                className={`flex-1 py-1 rounded text-center font-medium flex items-center justify-center gap-1 ${
                  searchType === "semantic" ? "bg-white text-blue-600 shadow-xs font-bold" : "text-slate-600"
                }`}
              >
                <Sparkles className="w-3 h-3 text-purple-600" />
                Semantic
              </button>
              <button
                type="button"
                onClick={() => setSearchType("keyword")}
                className={`flex-1 py-1 rounded text-center font-medium ${
                  searchType === "keyword" ? "bg-white text-blue-600 shadow-xs font-bold" : "text-slate-600"
                }`}
              >
                Keyword
              </button>
            </div>
          </div>

          {/* Supplier filter */}
          <div>
            <label className="font-semibold text-slate-600 block mb-1">Filter by Supplier:</label>
            <input
              type="text"
              placeholder="e.g. ABC Technologies"
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800"
            />
          </div>

          {/* Min Amount */}
          <div>
            <label className="font-semibold text-slate-600 block mb-1">Min Total Amount:</label>
            <input
              type="number"
              placeholder="0.00"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800"
            />
          </div>

          {/* Doc Type */}
          <div>
            <label className="font-semibold text-slate-600 block mb-1">Document Classification:</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800"
            >
              <option value="">All Document Types</option>
              <option value="Invoice">Invoice</option>
              <option value="Receipt">Receipt</option>
              <option value="Financial Statement">Financial Statement</option>
              <option value="Spreadsheet">Spreadsheet</option>
            </select>
          </div>
        </div>

        {/* Natural Language Example Pills */}
        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-semibold text-slate-400">Natural Language Suggestions:</span>
          {EXAMPLE_QUERIES.map((eg, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleExampleClick(eg)}
              className="px-2.5 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-600 text-slate-600 rounded-md text-[11px] transition-colors"
            >
              {eg}
            </button>
          ))}
        </div>
      </form>

      {/* Results Section */}
      <div className="space-y-4">
        {searched && (
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>Found <strong>{total}</strong> relevant document(s)</span>
            <span className="capitalize">Search Mode: {searchType}</span>
          </div>
        )}

        {loading ? (
          <div className="py-20 text-center bg-white rounded-xl border border-slate-200">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
            <p className="text-xs text-slate-500">Executing semantic vector retrieval and ranking...</p>
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-3">
            {results.map((res) => (
              <div
                key={res.document_id}
                className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-300 transition-all space-y-3"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-slate-900">{res.filename}</h3>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">
                        {res.document_type}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                          res.matched_by === "semantic"
                            ? "bg-purple-50 text-purple-700 border border-purple-200"
                            : "bg-blue-50 text-blue-700 border border-blue-200"
                        }`}
                      >
                        {res.matched_by === "semantic" ? "Semantic Match" : "Keyword Match"}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                      Doc ID: {res.document_id} | Ingested: {new Date(res.upload_time).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-[10px] uppercase font-semibold text-slate-400">Relevance</span>
                    <p className="text-base font-extrabold text-blue-600">
                      {Math.round(res.relevance_score * 100)}%
                    </p>
                  </div>
                </div>

                {/* Highlighted snippet */}
                <div className="p-3 bg-slate-50 rounded-lg text-xs font-mono text-slate-700 border border-slate-200/60 leading-relaxed">
                  {res.snippet}
                </div>

                {/* Extracted Details pill row */}
                {res.invoice_details && (
                  <div className="flex flex-wrap items-center gap-4 text-xs pt-1 border-t border-slate-100 text-slate-600">
                    {res.invoice_details.invoice_number && (
                      <span>Invoice: <strong className="text-slate-800">{res.invoice_details.invoice_number}</strong></span>
                    )}
                    {res.invoice_details.supplier_name && (
                      <span>Supplier: <strong className="text-slate-800">{res.invoice_details.supplier_name}</strong></span>
                    )}
                    {res.invoice_details.total_amount && (
                      <span>Total: <strong className="text-blue-600 font-bold">{res.invoice_details.total_amount} {res.invoice_details.currency}</strong></span>
                    )}
                    <Link
                      href={`/documents/${res.document_id}`}
                      className="ml-auto text-blue-600 hover:underline font-semibold flex items-center gap-1 text-xs"
                    >
                      <span>Inspect Document</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : searched ? (
          <div className="py-20 text-center bg-white rounded-xl border border-slate-200 text-slate-400 text-xs">
            No matching documents found. Try broadening keywords or adjusting amount filters.
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function SearchCenterPage() {
  return (
    <Suspense fallback={<div className="py-24 text-center text-sm text-slate-500">Loading Search Center...</div>}>
      <SearchContent />
    </Suspense>
  );
}

