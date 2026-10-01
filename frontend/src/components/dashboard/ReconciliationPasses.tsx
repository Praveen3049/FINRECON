"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, ArrowRight } from "lucide-react";

interface ReconciliationPassesProps {
  exactMatches?: number;
  underReviewCount?: number;
  entityCount?: number;
  txnCount?: number;
}

export const ReconciliationPasses: React.FC<ReconciliationPassesProps> = ({
  exactMatches = 196,
  underReviewCount = 104,
  entityCount = 53,
  txnCount = 1711,
}) => {
  const passes = [
    {
      name: "1. Deterministic Exact",
      category: "Pass 1 (Ref + Amount + Date)",
      count: `${exactMatches} Cases`,
      confidence: "100% Conf",
      pct: 100,
      color: "bg-[#FFD400]",
      badgeColor: "bg-[#FFD400]/10 text-[#FFD400] border-[#FFD400]/30",
    },
    {
      name: "2. TDS & Partial Matching",
      category: "Pass 2 & 3 (Sec 194C/194J)",
      count: `${underReviewCount} Cases`,
      confidence: "91% Conf",
      pct: 91,
      color: "bg-white",
      badgeColor: "bg-white/10 text-white border-white/20",
    },
    {
      name: "3. Entity Resolution",
      category: "Pass 5 (GSTIN & PAN Master)",
      count: `${entityCount} Entities`,
      confidence: "100% Conf",
      pct: 100,
      color: "bg-[#FFD400]",
      badgeColor: "bg-[#FFD400]/10 text-[#FFD400] border-[#FFD400]/30",
    },
    {
      name: "4. Bank & Payment Correlation",
      category: "Multi-Rail Line Aligner",
      count: `${txnCount.toLocaleString()} Lines`,
      confidence: "98% Conf",
      pct: 98,
      color: "bg-white/70",
      badgeColor: "bg-white/10 text-white/80 border-white/20",
    },
  ];

  return (
    <div className="bg-[#0D0D0D] border border-white/10 rounded-xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div>
            <h3 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">Reconciliation Passes</h3>
            <p className="text-xs text-white/50 mt-0.5 font-mono">
              Deterministic rule execution progression and confidence scores
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-[#FFD400] border border-[#FFD400]/30">
            Multi-Pass Engine
          </span>
        </div>

        {/* Visual Passes */}
        <div className="space-y-4 pt-2 font-mono">
          {passes.map((pass, idx) => (
            <div key={idx} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <div>
                  <span className="font-semibold text-white">{pass.name}</span>
                  <span className="text-[11px] text-white/40 ml-2 hidden sm:inline">
                    ({pass.category})
                  </span>
                </div>
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-white font-bold">{pass.count}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded border font-medium ${pass.badgeColor}`}>
                    {pass.confidence}
                  </span>
                </div>
              </div>

              {/* Progress meter */}
              <div className="w-full bg-[#171717] rounded-full h-2 overflow-hidden border border-white/5">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${pass.color}`}
                  style={{ width: `${pass.pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Explanation CTA Footer */}
      <div className="pt-3 border-t border-white/10 flex items-center justify-between text-xs font-mono">
        <span className="text-white/50 flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-[#FFD400]" />
          <span>Need explanation on variances?</span>
        </span>
        <Link
          href="/ai-assistant"
          className="text-xs font-semibold text-[#FFD400] hover:text-white flex items-center gap-1 transition-colors"
        >
          <span>Ask AI Assistant</span>
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
};
