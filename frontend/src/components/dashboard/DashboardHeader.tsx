"use client";

import React from "react";
import { Play, RefreshCw } from "lucide-react";

interface DashboardHeaderProps {
  onRefresh: () => void;
  onExecuteReconcile: () => void;
  isLoading: boolean;
  isReconciling: boolean;
  lastUpdated?: string;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  onRefresh,
  onExecuteReconcile,
  isLoading,
  isReconciling,
  lastUpdated,
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-white/10">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-white uppercase font-mono">
            Reconciliation Command Center
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-[#FFD400]/10 text-[#FFD400] border border-[#FFD400]/30">
            <span className="h-1.5 w-1.5 rounded-full bg-[#FFD400] animate-pulse" />
            Aczen Nova Live
          </span>
        </div>
        <p className="text-xs text-white/50 mt-1 max-w-2xl leading-relaxed">
          Deterministic multi-source financial and blockchain reconciliation across Bank Statements, Payment Gateways, Invoices, and ERP Ledgers.
        </p>
      </div>

      <div className="flex items-center gap-2.5 self-start sm:self-auto shrink-0">
        {lastUpdated && (
          <span className="text-[11px] font-mono text-white/40 mr-1 hidden lg:inline-block">
            Updated {lastUpdated}
          </span>
        )}

        <button
          onClick={onRefresh}
          disabled={isLoading || isReconciling}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-mono font-medium bg-[#0D0D0D] hover:bg-[#171717] border border-white/15 text-white/80 hover:text-white transition-all disabled:opacity-50"
          title="Refresh metrics from backend database"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin text-[#FFD400]" : ""}`} />
          <span>Refresh</span>
        </button>

        <button
          onClick={onExecuteReconcile}
          disabled={isReconciling || isLoading}
          className="flex items-center gap-2 bg-[#FFD400] hover:bg-[#ffe14d] text-black px-4 py-2 rounded-lg text-xs font-mono font-bold tracking-wide shadow-md shadow-[#FFD400]/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
        >
          {isReconciling ? (
            <>
              <RefreshCw className="h-3.5 w-3.5 animate-spin text-black" />
              <span>Executing Passes...</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-black text-black" />
              <span>Execute Reconciliation</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
