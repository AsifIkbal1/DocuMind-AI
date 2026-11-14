import React from "react";

export function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    Critical: "bg-red-50 text-red-700 border-red-200 font-bold",
    High: "bg-orange-50 text-orange-700 border-orange-200 font-semibold",
    Medium: "bg-amber-50 text-amber-700 border-amber-200",
    Low: "bg-blue-50 text-blue-700 border-blue-200",
  };

  const style = styles[severity] || "bg-slate-100 text-slate-700 border-slate-200";

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs border ${style}`}>
      {severity}
    </span>
  );
}

