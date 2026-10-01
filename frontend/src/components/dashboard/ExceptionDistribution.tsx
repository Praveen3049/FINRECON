"use client";

import React from "react";
import Link from "next/link";
import { ArrowUpRight, IndianRupee, Clock, Copy, ShieldAlert } from "lucide-react";

interface ExceptionDistributionProps {
  amountDiscrepancies?: number;
  duplicateCount?: number;
  dateDiscrepancies?: number;
  conflictingCount?: number;
  totalExceptions?: number;
  severityCounts?: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
  };
}

export const ExceptionDistribution: React.FC<ExceptionDistributionProps> = ({
  amountDiscrepancies = 105,
  duplicateCount = 30,
  dateDiscrepancies = 0,
  conflictingCount = 0,
  totalExceptions = 135,
  severityCounts = { critical: 1, high: 85, medium: 49, low: 0 },
}) => {
  const safeTotal = Math.max(1, totalExceptions);

  const categories = [
    {
      name: "Amount Discrepancies",
      count: amountDiscrepancies,
      pct: Math.round((amountDiscrepancies / safeTotal) * 100),
      desc: "TDS Sec 194C/194J withholdings & partial tranches",
      color: "bg-[#FFD400]",
      textColor: "text-[#FFD400]",
      icon: IndianRupee,
    },
    {
      name: "Duplicate Transactions",
      count: duplicateCount,
      pct: Math.round((duplicateCount / safeTotal) * 100),
      desc: "Duplicate webhook triggers & duplicate UTR entries",
      color: "bg-[#FFD400]/70",
      textColor: "text-[#FFD400]/90",
      icon: Copy,
    },
    {
      name: "Date Settlement Lags",
      count: dateDiscrepancies,
      pct: Math.round((dateDiscrepancies / safeTotal) * 100),
      desc: "Bank clearing timing within standard T±3 window",
      color: "bg-white",
      textColor: "text-white",
      icon: Clock,
    },
    {
      name: "Conflicting Records",
      count: conflictingCount,
      pct: Math.round((conflictingCount / safeTotal) * 100),
      desc: "Entity tax ID collisions across registered books",
      color: "bg-white/60",
      textColor: "text-white/70",
      icon: ShieldAlert,
    },
  ];

  return (
    <div className="bg-[#0D0D0D] border border-white/10 rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <div>
          <h3 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">Exception Distribution</h3>
          <p className="text-xs text-white/50 mt-0.5 font-mono">
            Automated categorization of detected financial variances
          </p>
        </div>
        <Link
          href="/exceptions"
          className="text-xs font-mono font-semibold text-[#FFD400] hover:text-white flex items-center gap-1 transition-colors"
        >
          <span>Open Workbench</span>
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Categories Horizontal Bar Visualizer */}
      <div className="space-y-3.5">
        {categories.map((cat, idx) => (
          <div key={idx} className="space-y-1.5 font-mono">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-white/90 flex items-center gap-2">
                <cat.icon className={`h-3.5 w-3.5 ${cat.textColor}`} />
                {cat.name}
              </span>
              <div className="flex items-center gap-2 font-mono">
                <span className="font-bold text-white">
                  {cat.count} {cat.count === 1 ? "case" : "cases"}
                </span>
                <span className="text-[10px] text-white/40">({cat.pct}%)</span>
              </div>
            </div>

            {/* Meter Bar */}
            <div className="w-full bg-[#171717] rounded-full h-2 overflow-hidden border border-white/5">
              <div
                className={`h-full rounded-full transition-all duration-700 ${cat.color}`}
                style={{ width: `${Math.max(cat.count > 0 ? 3 : 0, cat.pct)}%` }}
              />
            </div>
            <p className="text-[10px] text-white/40">{cat.desc}</p>
          </div>
        ))}
      </div>

      {/* Severity Breakdown Bar */}
      <div className="pt-3 border-t border-white/10 font-mono">
        <span className="text-[11px] font-semibold text-white/50 uppercase tracking-wider block mb-2">
          Severity Breakdown
        </span>
        <div className="grid grid-cols-4 gap-2 text-center text-xs">
          <div className="p-2 rounded-lg bg-black border border-[#FFD400]/40">
            <span className="text-[10px] font-bold text-[#FFD400] block uppercase">Critical</span>
            <span className="font-bold text-white font-mono text-sm">
              {severityCounts.critical ?? 1}
            </span>
          </div>
          <div className="p-2 rounded-lg bg-black border border-[#FFD400]/25">
            <span className="text-[10px] font-bold text-[#FFD400]/80 block uppercase">High</span>
            <span className="font-bold text-white font-mono text-sm">
              {severityCounts.high ?? 85}
            </span>
          </div>
          <div className="p-2 rounded-lg bg-black border border-white/15">
            <span className="text-[10px] font-bold text-white/80 block uppercase">Medium</span>
            <span className="font-bold text-white font-mono text-sm">
              {severityCounts.medium ?? 49}
            </span>
          </div>
          <div className="p-2 rounded-lg bg-black border border-white/10">
            <span className="text-[10px] font-bold text-white/40 block uppercase">Low</span>
            <span className="font-bold text-white font-mono text-sm">
              {severityCounts.low ?? 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
