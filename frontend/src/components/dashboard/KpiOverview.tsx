"use client";

import React from "react";
import { Layers, CheckCircle2, AlertTriangle, Building2, ArrowUpRight } from "lucide-react";
import Link from "next/link";

interface KpiOverviewProps {
  totalRecords: number;
  txnCount: number;
  invCount: number;
  exactMatches: number;
  matchRate: string;
  exceptionsCount: number;
  exceptionRate: string;
  entityCount: number;
  isLoading?: boolean;
}

export const KpiOverview: React.FC<KpiOverviewProps> = ({
  totalRecords,
  txnCount,
  invCount,
  exactMatches,
  matchRate,
  exceptionsCount,
  exceptionRate,
  entityCount,
  isLoading = false,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Total Financial Records */}
      <div className="group relative bg-[#0D0D0D] hover:bg-[#111111] border border-white/10 hover:border-[#FFD400]/40 rounded-xl p-5 shadow-sm transition-all duration-200">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-white/50">
            Total Financial Records
          </span>
          <div className="p-2 rounded-lg bg-[#FFD400]/10 text-[#FFD400] border border-[#FFD400]/20 group-hover:scale-105 transition-transform">
            <Layers className="h-4 w-4" />
          </div>
        </div>

        <div className="mt-3">
          <div className="text-2xl font-bold tracking-tight text-white font-mono">
            {isLoading ? "..." : totalRecords.toLocaleString()}
          </div>
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/10 text-xs font-mono">
            <span className="text-white/40 truncate">
              {txnCount.toLocaleString()} Txns + {invCount.toLocaleString()} Invoices
            </span>
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-white/5 text-white/80 border border-white/10 shrink-0">
              Live DB
            </span>
          </div>
        </div>
      </div>

      {/* 2. Reconciled (Exact) */}
      <div className="group relative bg-[#0D0D0D] hover:bg-[#111111] border border-white/10 hover:border-[#FFD400]/40 rounded-xl p-5 shadow-sm transition-all duration-200">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-white/50">
            Reconciled (Exact)
          </span>
          <div className="p-2 rounded-lg bg-[#FFD400]/10 text-[#FFD400] border border-[#FFD400]/20 group-hover:scale-105 transition-transform">
            <CheckCircle2 className="h-4 w-4" />
          </div>
        </div>

        <div className="mt-3">
          <div className="text-2xl font-bold tracking-tight text-white font-mono">
            {isLoading ? "..." : exactMatches.toLocaleString()}
          </div>
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/10 text-xs font-mono">
            <span className="text-[#FFD400] font-medium">
              {matchRate}% match rate
            </span>
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-[#FFD400]/10 text-[#FFD400] border border-[#FFD400]/20 shrink-0">
              100% Conf
            </span>
          </div>
        </div>
      </div>

      {/* 3. Exceptions for Review */}
      <Link href="/exceptions" className="block">
        <div className="group relative bg-[#0D0D0D] hover:bg-[#111111] border border-white/10 hover:border-[#FFD400]/40 rounded-xl p-5 shadow-sm transition-all duration-200 cursor-pointer">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-white/50">
              Exceptions for Review
            </span>
            <div className="p-2 rounded-lg bg-white/5 text-[#FFD400] border border-white/10 group-hover:scale-105 transition-transform">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>

          <div className="mt-3">
            <div className="text-2xl font-bold tracking-tight text-white font-mono flex items-center justify-between">
              <span>{isLoading ? "..." : exceptionsCount.toLocaleString()}</span>
              <ArrowUpRight className="h-3.5 w-3.5 text-white/40 group-hover:text-[#FFD400] transition-colors" />
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/10 text-xs font-mono">
              <span className="text-white/60 font-medium">
                {exceptionRate}% variance rate
              </span>
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-white/5 text-[#FFD400] border border-[#FFD400]/30 shrink-0">
                Action Required
              </span>
            </div>
          </div>
        </div>
      </Link>

      {/* 4. Corporate Entities */}
      <Link href="/entities" className="block">
        <div className="group relative bg-[#0D0D0D] hover:bg-[#111111] border border-white/10 hover:border-[#FFD400]/40 rounded-xl p-5 shadow-sm transition-all duration-200 cursor-pointer">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-white/50">
              Corporate Entities
            </span>
            <div className="p-2 rounded-lg bg-white/5 text-white border border-white/10 group-hover:scale-105 transition-transform">
              <Building2 className="h-4 w-4" />
            </div>
          </div>

          <div className="mt-3">
            <div className="text-2xl font-bold tracking-tight text-white font-mono flex items-center justify-between">
              <span>{isLoading ? "..." : entityCount.toLocaleString()}</span>
              <ArrowUpRight className="h-3.5 w-3.5 text-white/40 group-hover:text-[#FFD400] transition-colors" />
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/10 text-xs font-mono">
              <span className="text-white/40">
                GSTIN / PAN resolved
              </span>
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-white/5 text-white/80 border border-white/10 shrink-0">
                Golden Records
              </span>
            </div>
          </div>
        </div>
      </Link>
    </div>
  );
};
