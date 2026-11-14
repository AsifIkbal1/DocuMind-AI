import React from "react";

export function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    Completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
    Processing: "bg-blue-50 text-blue-700 border-blue-200 animate-pulse",
    "OCR Processing": "bg-indigo-50 text-indigo-700 border-indigo-200 animate-pulse",
    "AI Extraction": "bg-purple-50 text-purple-700 border-purple-200 animate-pulse",
    Validation: "bg-amber-50 text-amber-700 border-amber-200",
    "Needs Review": "bg-amber-50 text-amber-700 border-amber-200 font-semibold",
    Queued: "bg-slate-100 text-slate-700 border-slate-200",
    Uploaded: "bg-slate-100 text-slate-700 border-slate-200",
    Failed: "bg-rose-50 text-rose-700 border-rose-200 font-semibold",
  };

  const style = styles[status] || "bg-slate-100 text-slate-700 border-slate-200";

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${style}`}>
      <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-current opacity-70" />
      {status}
    </span>
  );
}

