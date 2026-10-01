"use client";

import React, { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { KpiOverview } from "@/components/dashboard/KpiOverview";
import { CardSkeleton, ChartSkeleton } from "@/components/ui/SkeletonLoader";
import { api, DataSourceItem } from "@/lib/api";

// Dynamically import heavy Recharts components to avoid blocking initial route transition
const ReconciliationAnalytics = dynamic(
  () =>
    import("@/components/dashboard/ReconciliationAnalytics").then(
      (m) => m.ReconciliationAnalytics
    ),
  {
    ssr: false,
    loading: () => <ChartSkeleton height={320} />,
  }
);

const MatchRateChart = dynamic(
  () => import("@/components/dashboard/MatchRateChart").then((m) => m.MatchRateChart),
  {
    ssr: false,
    loading: () => <CardSkeleton className="h-[380px]" />,
  }
);

const ExceptionDistribution = dynamic(
  () =>
    import("@/components/dashboard/ExceptionDistribution").then(
      (m) => m.ExceptionDistribution
    ),
  {
    ssr: false,
    loading: () => <CardSkeleton className="h-[340px]" />,
  }
);

const ReconciliationPasses = dynamic(
  () =>
    import("@/components/dashboard/ReconciliationPasses").then(
      (m) => m.ReconciliationPasses
    ),
  {
    ssr: false,
    loading: () => <CardSkeleton className="h-[340px]" />,
  }
);

const SourceAnalytics = dynamic(
  () => import("@/components/dashboard/SourceAnalytics").then((m) => m.SourceAnalytics),
  {
    ssr: false,
    loading: () => <CardSkeleton className="h-[300px]" />,
  }
);

const CryptoSnapshot = dynamic(
  () => import("@/components/dashboard/CryptoSnapshot").then((m) => m.CryptoSnapshot),
  {
    ssr: false,
    loading: () => <CardSkeleton className="h-[300px]" />,
  }
);

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null);
  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [exceptionsSummary, setExceptionsSummary] = useState<any>(null);
  const [cryptoAnalytics, setCryptoAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [isReconciling, setIsReconciling] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const loadData = useCallback(async (bypassCache: boolean = false) => {
    try {
      // Only set loading if no cached data exists to prevent UI flickering
      if (!summary) {
        setLoading(true);
      }
      const [sumRes, srcRes, excRes, crypRes] = await Promise.allSettled([
        api.getDatabaseSummary(bypassCache),
        api.getDataSources(bypassCache),
        api.getExceptionsSummary(bypassCache),
        api.getCryptoAnalytics(bypassCache),
      ]);

      if (sumRes.status === "fulfilled" && sumRes.value) {
        setSummary(sumRes.value);
      }
      if (srcRes.status === "fulfilled" && Array.isArray(srcRes.value)) {
        setSources(srcRes.value);
      }
      if (excRes.status === "fulfilled" && excRes.value) {
        setExceptionsSummary(excRes.value);
      }
      if (crypRes.status === "fulfilled" && crypRes.value) {
        setCryptoAnalytics(crypRes.value);
      }

      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, [summary]);

  useEffect(() => {
    loadData(false);
  }, []);

  const handleRunRecon = async () => {
    setIsReconciling(true);
    try {
      await api.runReconciliation({
        case_title: `Reconciliation Run ${new Date().toLocaleDateString()}`,
        amount_tolerance: 0.05,
        date_tolerance_days: 3,
      });
      await loadData(true);
    } catch (err) {
      console.error("Reconciliation run failed:", err);
    } finally {
      setIsReconciling(false);
    }
  };

  // Derive genuine metrics bound directly to existing DB records
  const txnCount = summary?.table_counts?.transactions ?? 0;
  const invCount = summary?.table_counts?.invoices ?? 0;
  const totalFinancialRecords = txnCount + invCount;
  const entityCount = summary?.table_counts?.entities ?? 0;

  // Case distribution (from database_summary or fallback to known case totals)
  const reconciledCases = summary?.case_distribution?.RECONCILED ?? 0;
  const underReviewCases = summary?.case_distribution?.UNDER_REVIEW ?? 0;
  const totalCases = summary?.table_counts?.reconciliation_cases ?? (reconciledCases + underReviewCases);

  // Match and discrepancy totals
  const totalMatches = summary?.table_counts?.reconciliation_matches ?? 0;
  const exactMatches = summary?.match_distribution?.EXACT_MATCH ?? 0;

  // Genuine Exceptions count from exceptionsSummary or DB discrepancy records
  const exceptionsCount =
    exceptionsSummary?.total_open ??
    summary?.discrepancy_status_distribution?.OPEN ??
    summary?.table_counts?.discrepancy_records ??
    0;

  // Exact Match Rate on Transactions
  const matchRate = txnCount > 0 ? ((exactMatches / txnCount) * 100).toFixed(1) : "0.0";

  // Exception Rate across total evaluated records
  const exceptionRate = totalMatches > 0 ? ((exceptionsCount / totalMatches) * 100).toFixed(1) : "0.0";

  // Exception categories from summary or DB distribution
  const amountDiscrepancies =
    exceptionsSummary?.by_discrepancy_type?.AMOUNT ??
    summary?.discrepancy_distribution?.AMOUNT ??
    0;
  const duplicateCount =
    exceptionsSummary?.by_discrepancy_type?.DUPLICATE_ENTRY ??
    summary?.discrepancy_distribution?.DUPLICATE_ENTRY ??
    0;
  const dateDiscrepancies =
    exceptionsSummary?.by_discrepancy_type?.DATE ??
    summary?.discrepancy_distribution?.DATE ??
    0;
  const missingCount =
    exceptionsSummary?.by_discrepancy_type?.MISSING_ENTRY ??
    summary?.discrepancy_distribution?.MISSING_ENTRY ??
    0;
  const totalDiscrepancies = amountDiscrepancies + duplicateCount + dateDiscrepancies + missingCount;

  const severityCounts = {
    critical: exceptionsSummary?.critical_count ?? 0,
    high: exceptionsSummary?.high_count ?? 0,
    medium: exceptionsSummary?.medium_count ?? 0,
    low: exceptionsSummary?.low_count ?? 0,
  };

  // Crypto metrics from cryptoAnalytics
  const cryptoTxnCount = cryptoAnalytics?.total_crypto_transactions ?? 0;
  const cryptoVolumeUsd = cryptoAnalytics?.total_fiat_volume_usd ?? 0.0;
  const cryptoNetworks = cryptoAnalytics?.networks
    ? Object.entries(cryptoAnalytics.networks).map(([net, data]: [string, any]) => ({
        network: net,
        transactions: data.total_transactions || 0,
        volumeUsd: data.total_fiat_volume || 0.0,
        asset: Object.keys(data.assets || {})[0] || "",
      }))
    : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-8">
      {/* 1. Header with clean hierarchy & primary CTA */}
      <DashboardHeader
        onRefresh={() => loadData(true)}
        onExecuteReconcile={handleRunRecon}
        isLoading={loading}
        isReconciling={isReconciling}
        lastUpdated={lastUpdated}
      />

      {/* 2. Visual KPI Cards */}
      <KpiOverview
        totalRecords={totalFinancialRecords}
        txnCount={txnCount}
        invCount={invCount}
        exactMatches={exactMatches}
        matchRate={matchRate}
        exceptionsCount={exceptionsCount}
        exceptionRate={exceptionRate}
        entityCount={entityCount}
        isLoading={loading && !summary}
      />

      {/* 3. Middle Section: Large Analytics Graph (8 cols) + Circular Donut Gauges (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <ReconciliationAnalytics
            totalRecords={totalFinancialRecords}
            txnCount={txnCount}
            invCount={invCount}
            exactMatches={exactMatches}
            underReviewCount={exceptionsCount}
            sourcesBreakdown={summary?.transactions_by_source}
            recentCases={summary?.recent_cases}
          />
        </div>

        <div className="lg:col-span-4">
          <MatchRateChart
            exactMatches={reconciledCases}
            totalCases={totalCases}
            exceptionsCount={underReviewCases}
            entityCount={entityCount}
            txnCount={txnCount}
          />
        </div>
      </div>

      {/* 4. Secondary Analytics: Exception Distribution (6 cols) + Reconciliation Passes (6 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <ExceptionDistribution
            amountDiscrepancies={amountDiscrepancies}
            duplicateCount={duplicateCount}
            dateDiscrepancies={dateDiscrepancies}
            conflictingCount={0}
            totalExceptions={totalDiscrepancies}
            severityCounts={severityCounts}
          />
        </div>

        <div className="lg:col-span-6">
          <ReconciliationPasses
            exactMatches={reconciledCases}
            underReviewCount={underReviewCases}
            entityCount={entityCount}
            txnCount={txnCount}
          />
        </div>
      </div>

      {/* 5. Ingestion Feeds (7 cols) + Crypto Snapshot (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <SourceAnalytics
            sources={sources}
            txnCount={txnCount}
            invCount={invCount}
          />
        </div>

        <div className="lg:col-span-5">
          <CryptoSnapshot
            cryptoCount={cryptoTxnCount}
            totalVolumeUsd={cryptoVolumeUsd}
            networkBreakdown={cryptoNetworks}
          />
        </div>
      </div>
    </div>
  );
}
