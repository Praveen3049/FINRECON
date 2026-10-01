"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  TrendingDown,
  UserCheck,
  UserPlus,
  HelpCircle,
  X,
  ArrowUpRight,
  ShieldCheck,
  Send,
  Building2,
  Scale,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import {
  PageHeader,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Badge,
  FilterBar,
  EmptyState,
  useToast,
} from "@/components/ui";

interface ExceptionItem {
  id: string;
  case_id: string;
  case_number?: string;
  assigned_reviewer?: string;
  match_id?: string;
  discrepancy_type: string;
  field_name: string;
  source_value?: string;
  matched_value?: string;
  difference_numeric?: number;
  difference_percentage?: number;
  root_cause_category?: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: "OPEN" | "UNDER_REVIEW" | "RESOLVED" | "WRITTEN_OFF" | "ESCALATED";
  created_at?: string;
  match_status?: string;
  confidence_score?: number;
  source_record?: {
    id: string;
    transaction_id: string;
    amount: number;
    currency: string;
    source_type: string;
    reference?: string;
    date?: string;
    entity_name?: string;
  };
  matched_record?: {
    id: string;
    identifier: string;
    amount: number;
    currency?: string;
    type: string;
    date?: string;
    entity_name?: string;
  };
}

interface ExceptionSummary {
  total_open: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_variance_usd: number;
  by_root_cause: Record<string, number>;
  by_discrepancy_type: Record<string, number>;
}

const DISCREPANCY_TABS = [
  { label: "All Types", value: "" },
  { label: "Amount Variance", value: "AMOUNT" },
  { label: "Date Lag", value: "DATE" },
  { label: "Duplicate Entry", value: "DUPLICATE_ENTRY" },
  { label: "Missing Entry", value: "MISSING_ENTRY" },
];

const AUDITOR_OPTIONS = [
  { name: "Elena Rostova", role: "Compliance Auditor", email: "auditor@finrecon.com" },
  { name: "Sarah Connor", role: "Senior Audit Officer", email: "analyst.new@finrecon.com" },
  { name: "Audit Operations Queue", role: "Team Dispatch", email: "audit-desk@finrecon.internal" },
];

const COMMON_ESCALATION_REASONS = [
  "Unable to understand payment variance calculation across feed and invoice.",
  "Variance exceeds authorized tolerance threshold; requires executive sign-off.",
  "Potential unrecorded fee or TDS deduction requires manager verification.",
  "Duplicate webhook collision requires managerial suppression approval.",
];

const FALLBACK_EXCEPTIONS: ExceptionItem[] = [
  {
    id: "disc-001",
    case_id: "case-01",
    discrepancy_type: "AMOUNT",
    field_name: "amount",
    source_value: "INR 1,21,250.00",
    matched_value: "INR 1,25,000.00",
    difference_numeric: 3750.0,
    difference_percentage: 3.0,
    root_cause_category: "TDS_DEDUCTION",
    severity: "MEDIUM",
    status: "OPEN",
    source_record: {
      id: "b-01",
      transaction_id: "HDFC-NEFT-9942",
      amount: 121250.0,
      currency: "INR",
      source_type: "BANK",
      reference: "ACZEN-PAY-992",
      date: "2026-09-29",
      entity_name: "Acme Corporation",
    },
    matched_record: {
      id: "g-01",
      identifier: "INV-2026-ACZEN-0992",
      amount: 125000.0,
      currency: "INR",
      type: "INVOICE",
      date: "2026-09-29",
      entity_name: "Acme Corporation LLC",
    },
  },
  {
    id: "disc-002",
    case_id: "case-01",
    discrepancy_type: "DATE",
    field_name: "transaction_date",
    source_value: "2026-09-29",
    matched_value: "2026-09-27",
    difference_numeric: 2.0,
    root_cause_category: "T_PLUS_LAG",
    severity: "LOW",
    status: "OPEN",
    source_record: {
      id: "b-02",
      transaction_id: "SBI-RTGS-1044",
      amount: 250000.0,
      currency: "INR",
      source_type: "BANK",
      reference: "RTGS-REF-1044",
      date: "2026-09-29",
      entity_name: "Starlight Technologies",
    },
    matched_record: {
      id: "g-02",
      identifier: "INV-2026-ACZEN-1044",
      amount: 250000.0,
      currency: "INR",
      type: "INVOICE",
      date: "2026-09-27",
      entity_name: "Starlight Technologies",
    },
  },
  {
    id: "disc-003",
    case_id: "case-01",
    discrepancy_type: "DUPLICATE_ENTRY",
    field_name: "transaction_id",
    source_value: "TXN-DUP-A",
    matched_value: "TXN-DUP-B",
    root_cause_category: "DUPLICATE_WEBHOOK",
    severity: "HIGH",
    status: "OPEN",
    source_record: {
      id: "g-03",
      transaction_id: "TXN-DUP-A",
      amount: 49900.0,
      currency: "INR",
      source_type: "PAYMENT_GATEWAY",
      reference: "ORDER-DUP-888",
      date: "2026-09-28",
      entity_name: "Apex Capital",
    },
    matched_record: {
      id: "g-03-b",
      identifier: "TXN-DUP-B",
      amount: 49900.0,
      currency: "INR",
      type: "PAYMENT_GATEWAY",
      date: "2026-09-28",
      entity_name: "Apex Capital",
    },
  },
  {
    id: "disc-004",
    case_id: "case-01",
    discrepancy_type: "MISSING_ENTRY",
    field_name: "transaction_id",
    source_value: "HDFC-FEE-SEP26",
    difference_numeric: 2500.0,
    root_cause_category: "UNRECORDED_EXPENSE",
    severity: "MEDIUM",
    status: "OPEN",
    source_record: {
      id: "b-04",
      transaction_id: "HDFC-FEE-SEP26",
      amount: 2500.0,
      currency: "INR",
      source_type: "BANK",
      reference: "MONTHLY SERVICE FEE",
      date: "2026-09-30",
      entity_name: "HDFC Bank Clearing",
    },
  },
];

export default function ExceptionsPage() {
  const { user } = useAuth();
  const [exceptions, setExceptions] = useState<ExceptionItem[]>(FALLBACK_EXCEPTIONS);
  const [summary, setSummary] = useState<ExceptionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedException, setSelectedException] = useState<ExceptionItem | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Review Form
  const [reviewNote, setReviewNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");

  // Auditor Escalation Modal
  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [escalateReason, setEscalateReason] = useState("");

  // Manager Delegation Modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedAuditor, setSelectedAuditor] = useState(AUDITOR_OPTIONS[0].name);
  const [assignInstructions, setAssignInstructions] = useState("");

  const { success, error: toastError } = useToast();

  useEffect(() => {
    loadExceptions(false);
  }, [statusFilter, severityFilter, typeFilter]);

  const loadExceptions = async (bypassCache: boolean = false) => {
    setIsLoading(true);
    try {
      const [listRes, sumRes] = await Promise.allSettled([
        api.getExceptions(
          {
            limit: 150,
            status: statusFilter || undefined,
            severity: severityFilter || undefined,
            discrepancy_type: typeFilter || undefined,
          },
          bypassCache
        ),
        api.getExceptionsSummary(bypassCache),
      ]);

      if (listRes.status === "fulfilled" && Array.isArray(listRes.value) && listRes.value.length > 0) {
        setExceptions(listRes.value);
        setSelectedException(listRes.value[0]);
      } else if (listRes.status === "fulfilled" && Array.isArray(listRes.value) && listRes.value.length === 0) {
        setExceptions([]);
        setSelectedException(null);
      } else if (!selectedException && FALLBACK_EXCEPTIONS.length > 0) {
        setSelectedException(FALLBACK_EXCEPTIONS[0]);
      }

      if (sumRes.status === "fulfilled" && sumRes.value) {
        setSummary(sumRes.value);
      }
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Failed to load exceptions:", err);
      if (!selectedException && FALLBACK_EXCEPTIONS.length > 0) {
        setSelectedException(FALLBACK_EXCEPTIONS[0]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyAction = async (action: string, customNotes?: string, assignedTo?: string) => {
    if (!selectedException) return;
    setIsSubmitting(true);
    try {
      const reviewerName =
        user?.name || (user?.role === "MANAGER" ? "Marcus Vance (Manager)" : "Elena Rostova (Auditor)");
      const noteToSave = customNotes || reviewNote || `Action ${action} executed via Exception Workbench`;

      await api.applyExceptionAction(selectedException.id, {
        reviewer_name: reviewerName,
        action: action,
        notes: noteToSave,
        assigned_to: assignedTo,
      });

      if (action === "ESCALATE") {
        success(
          "Request Sent to Manager",
          `Exception ${selectedException.id} escalated to Operations Management with audit commentary.`
        );
      } else if (action === "ASSIGN_AUDITOR") {
        success(
          "Case Assigned to Auditor",
          `Delegated exception ${selectedException.id} to ${assignedTo}.`
        );
      } else {
        success(
          "Exception Updated",
          `Applied action "${action}" to ${selectedException.id}. Recorded in audit trail.`
        );
      }

      await loadExceptions();
      setReviewNote("");
      setShowEscalateModal(false);
      setShowAssignModal(false);
      setEscalateReason("");
      setAssignInstructions("");
    } catch (err) {
      console.error("Action execution failed:", err);
      toastError("Action Failed", "Could not apply exception action.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBulkWriteOff = async () => {
    const minorExceptions = exceptions.filter(
      (e) => (e.difference_numeric || 0) <= 50.0 && e.status === "OPEN" && e.discrepancy_type === "AMOUNT"
    );
    if (minorExceptions.length === 0) return;

    setIsLoading(true);
    try {
      const reviewerName = user?.name || "Marcus Vance (Manager)";
      await api.applyBulkExceptionActions({
        exception_ids: minorExceptions.map((e) => e.id),
        reviewer_name: reviewerName,
        action: "WRITE_OFF",
        notes: "Automated bulk write-off of minor fee variances <= ₹50",
      });
      success(
        "Bulk Write-Off Complete",
        `Written off ${minorExceptions.length} minor variance exceptions.`
      );
      await loadExceptions();
    } catch (err) {
      console.error("Bulk write-off failed:", err);
      toastError("Bulk Action Failed", "Failed to write off minor variances.");
    } finally {
      setIsLoading(false);
    }
  };

  // Filtered exceptions based on search
  const filteredExceptions = exceptions.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.id.toLowerCase().includes(q) ||
      item.discrepancy_type.toLowerCase().includes(q) ||
      (item.root_cause_category && item.root_cause_category.toLowerCase().includes(q)) ||
      (item.source_record?.transaction_id &&
        item.source_record.transaction_id.toLowerCase().includes(q)) ||
      (item.source_record?.reference &&
        item.source_record.reference.toLowerCase().includes(q)) ||
      (item.matched_record?.identifier &&
        item.matched_record.identifier.toLowerCase().includes(q)) ||
      (item.assigned_reviewer && item.assigned_reviewer.toLowerCase().includes(q))
    );
  });

  // Calculate count per discrepancy type
  const countByType = useMemo(() => {
    const counts: Record<string, number> = {
      "": exceptions.length,
      AMOUNT: 0,
      DATE: 0,
      DUPLICATE_ENTRY: 0,
      MISSING_ENTRY: 0,
    };
    exceptions.forEach((e) => {
      if (counts[e.discrepancy_type] !== undefined) {
        counts[e.discrepancy_type]++;
      }
    });
    return counts;
  }, [exceptions]);

  const isAuditor = user?.role === "AUDITOR";
  const isManager = user?.role === "MANAGER";

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* 1. Page Header */}
      <PageHeader
        title="Exception Investigation Workbench"
        subtitle="Multi-persona variance triage. Evaluate cross-ledger deltas, settlement lags, and duplicate entries. Resolve discrepancies or escalate payment issues to management."
        badge={{
          text: isManager ? "Manager Oversight" : isAuditor ? "Auditor Reviewer" : "Workbench Active",
          variant: "yellow",
          pulse: true,
        }}
        onRefresh={() => loadExceptions(true)}
        isRefreshing={isLoading}
        lastUpdated={lastUpdated}
        secondaryActions={
          isManager ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkWriteOff}
              iconLeft={<CheckCircle2 className="h-3.5 w-3.5 text-[#FFD400]" />}
            >
              Bulk Write-Off (&le; ₹50)
            </Button>
          ) : undefined
        }
      />

      {/* 2. Top Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 font-mono">
        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Open Exceptions
          </span>
          <div className="text-xl font-mono font-bold text-white">
            {summary?.total_open ?? exceptions.filter((e) => e.status === "OPEN").length}
          </div>
          <span className="text-[10px] text-[#FFD400] font-medium block">Pending Investigation</span>
        </div>

        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Critical Severity
          </span>
          <div className="text-xl font-mono font-bold text-[#FFD400]">
            {summary?.critical_count ?? exceptions.filter((e) => e.severity === "CRITICAL").length}
          </div>
          <span className="text-[10px] text-white/40 block">Immediate Action</span>
        </div>

        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Total Variance
          </span>
          <div className="text-xl font-mono font-bold text-white">
            ₹
            {summary?.total_variance_usd !== undefined
              ? Number(summary.total_variance_usd).toLocaleString("en-IN", { minimumFractionDigits: 2 })
              : "1,248,590.20"}
          </div>
          <span className="text-[10px] text-white/40 block">Total Discrepancy Amount</span>
        </div>

        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Primary Root Cause
          </span>
          <div className="text-xs font-semibold text-[#FFD400] truncate mt-1">
            {summary?.by_root_cause && Object.keys(summary.by_root_cause).length > 0
              ? Object.entries(summary.by_root_cause).sort((a, b) => b[1] - a[1])[0][0].replace(/_/g, " ")
              : "TDS / Underbilling"}
          </div>
          <span className="text-[10px] text-white/40 block">Sec 194C/J Deductions</span>
        </div>

        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Resolution Progress
          </span>
          <div className="text-xl font-mono font-bold text-white">
            {exceptions.filter((e) => e.status !== "OPEN").length} / {exceptions.length}
          </div>
          <span className="text-[10px] text-white/40 block">Audit Trail Recorded</span>
        </div>
      </div>

      {/* 3. Discrepancy Type Quick-Filter Tabs */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-white/60 font-mono">
            Discrepancy Category Queue
          </span>
          <span className="text-[11px] text-white/40 font-mono">
            {isAuditor ? "Auditor Review Mode" : isManager ? "Manager Dispatch Mode" : "Verification Mode"}
          </span>
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none font-mono">
          {DISCREPANCY_TABS.map((tab) => {
            const isActive = typeFilter === tab.value;
            const count = countByType[tab.value] ?? 0;
            return (
              <button
                key={tab.value}
                onClick={() => setTypeFilter(tab.value)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 border select-none ${
                  isActive
                    ? "bg-[#171717] border-[#FFD400] text-white ring-1 ring-[#FFD400] shadow-sm"
                    : "bg-[#0D0D0D] border-white/10 text-white/60 hover:text-white hover:border-white/30"
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                    isActive
                      ? "bg-[#FFD400] text-black border-[#FFD400] font-bold"
                      : "bg-black text-white/50 border-white/10"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Filter Toolbar */}
      <FilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search reference, transaction ID, or auditor name..."
        filters={[
          {
            key: "status",
            label: "Status",
            value: statusFilter,
            options: [
              { label: "Open", value: "OPEN" },
              { label: "Resolved", value: "RESOLVED" },
              { label: "Under Review", value: "UNDER_REVIEW" },
              { label: "Written Off", value: "WRITTEN_OFF" },
              { label: "Escalated", value: "ESCALATED" },
            ],
            onChange: setStatusFilter,
          },
          {
            key: "severity",
            label: "Severity",
            value: severityFilter,
            options: [
              { label: "Critical", value: "CRITICAL" },
              { label: "High", value: "HIGH" },
              { label: "Medium", value: "MEDIUM" },
              { label: "Low", value: "LOW" },
            ],
            onChange: setSeverityFilter,
          },
        ]}
        hasActiveFilters={Boolean(searchQuery || statusFilter || severityFilter || typeFilter)}
        onClearFilters={() => {
          setSearchQuery("");
          setStatusFilter("");
          setSeverityFilter("");
          setTypeFilter("");
        }}
      />

      {/* 5. Main 2-Column Workbench Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Discrepancy Queue List (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
              Exception Queue ({filteredExceptions.length})
            </span>
            <span className="text-[11px] text-white/40 font-mono">Select item to inspect</span>
          </div>

          <div className="space-y-2.5 max-h-[720px] overflow-y-auto pr-1">
            {filteredExceptions.length === 0 ? (
              <EmptyState
                icon={<CheckCircle2 className="h-6 w-6 text-[#FFD400]" />}
                title="No Exceptions Found"
                description="Your exception queue is completely clear for the active filters."
              />
            ) : (
              filteredExceptions.map((item) => {
                const isSelected = selectedException?.id === item.id;
                const isItemEscalated = item.status === "ESCALATED";

                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedException(item)}
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all duration-150 select-none ${
                      isSelected
                        ? "bg-[#171717] border-[#FFD400] shadow-md shadow-[#FFD400]/10 ring-1 ring-[#FFD400]"
                        : "bg-[#0D0D0D] border-white/10 hover:border-white/30"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <Badge
                          variant={
                            item.severity === "CRITICAL"
                              ? "critical"
                              : item.severity === "HIGH"
                              ? "warning"
                              : "neutral"
                          }
                          size="xs"
                        >
                          {item.severity}
                        </Badge>
                        <span className="font-mono text-[11px] font-semibold text-white">
                          {item.discrepancy_type.replace(/_/g, " ")}
                        </span>
                        {item.assigned_reviewer && (
                          <span className="text-[9px] font-mono uppercase bg-[#FFD400]/10 text-[#FFD400] px-1.5 py-0.2 rounded border border-[#FFD400]/30 font-semibold">
                            Assigned: {item.assigned_reviewer.split(" ")[0]}
                          </span>
                        )}
                      </div>
                      <span
                        className={`font-mono text-[10px] uppercase font-bold px-1.5 py-0.2 rounded border ${
                          isItemEscalated
                            ? "bg-black text-[#FFD400] border-[#FFD400]"
                            : item.status === "RESOLVED"
                            ? "bg-white/10 text-white border-white/20"
                            : "text-white/40 border-transparent"
                        }`}
                      >
                        {isItemEscalated ? "ESCALATED" : item.status.replace(/_/g, " ")}
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between mt-2">
                      <div>
                        <div className="font-mono text-xs font-semibold text-white">
                          {item.source_record?.transaction_id || item.id}
                        </div>
                        <div className="text-[10px] text-white/50 truncate max-w-[200px]">
                          {item.root_cause_category || "Unclassified Root Cause"}
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="font-mono font-bold text-white">
                          {item.difference_numeric !== undefined && item.difference_numeric !== null
                            ? item.discrepancy_type === "DATE"
                              ? `T+${item.difference_numeric}d`
                              : item.discrepancy_type === "AMOUNT"
                              ? `Δ ₹${Number(item.difference_numeric).toLocaleString("en-IN", {
                                  minimumFractionDigits: 2,
                                })}`
                              : `₹${Number(item.difference_numeric).toLocaleString("en-IN", {
                                  minimumFractionDigits: 2,
                                })}`
                            : item.source_record?.amount
                            ? `₹${Number(item.source_record.amount).toLocaleString("en-IN", {
                                minimumFractionDigits: 2,
                              })}`
                            : "—"}
                        </div>
                        <div className="text-[10px] text-[#FFD400]">
                          {item.discrepancy_type === "DUPLICATE_ENTRY"
                            ? "duplicate collision"
                            : item.discrepancy_type === "MISSING_ENTRY"
                            ? "unrecorded entry"
                            : item.discrepancy_type === "DATE"
                            ? "settlement lag"
                            : "amount variance"}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Detailed Investigation Panel (7 cols) */}
        <div className="lg:col-span-7">
          {selectedException ? (
            <Card className="animate-fade-in shadow-lg border-[#FFD400]/20">
              <CardHeader>
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle>
                      <AlertTriangle className="h-4 w-4 text-[#FFD400]" />
                      <span className="uppercase font-mono">
                        Investigation: {selectedException.discrepancy_type.replace(/_/g, " ")}
                      </span>
                    </CardTitle>
                    <Badge variant="yellow" size="xs">
                      {selectedException.id}
                    </Badge>
                  </div>
                  <CardDescription>
                    Root Cause:{" "}
                    <span className="font-semibold text-white">
                      {selectedException.root_cause_category || "UNCLASSIFIED"}
                    </span>{" "}
                    &bull; Severity:{" "}
                    <span className="font-semibold text-[#FFD400]">{selectedException.severity}</span>
                  </CardDescription>
                </div>

                <Badge
                  variant={
                    selectedException.status === "RESOLVED"
                      ? "matched"
                      : selectedException.status === "ESCALATED"
                      ? "critical"
                      : "warning"
                  }
                  size="xs"
                >
                  {selectedException.status}
                </Badge>
              </CardHeader>

              <CardContent className="space-y-5">
                {/* Escalation Alert Banner */}
                {selectedException.status === "ESCALATED" && (
                  <div className="p-3.5 rounded-xl bg-black border border-[#FFD400] flex items-start gap-2.5 font-mono text-xs shadow-sm">
                    <AlertTriangle className="h-4 w-4 text-[#FFD400] shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <span className="font-bold text-[#FFD400] uppercase tracking-wider block">
                        Manager Review Requested
                      </span>
                      <p className="text-[11px] text-white/80 leading-relaxed font-sans">
                        An auditor flagged this discrepancy as unclear or requiring executive guidance. Review the ledger variance and resolve or reassign.
                      </p>
                    </div>
                  </div>
                )}

                {/* Assigned Reviewer Context Banner */}
                {selectedException.assigned_reviewer && (
                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-black border border-white/10 text-xs font-mono">
                    <div className="flex items-center gap-2 text-white/70">
                      <UserCheck className="h-3.5 w-3.5 text-[#FFD400]" />
                      <span>Assigned Auditor:</span>
                      <strong className="text-white">{selectedException.assigned_reviewer}</strong>
                    </div>
                    {isManager && (
                      <button
                        type="button"
                        onClick={() => setShowAssignModal(true)}
                        className="text-[11px] text-[#FFD400] hover:text-white transition-colors"
                      >
                        Reassign &rarr;
                      </button>
                    )}
                  </div>
                )}

                {/* Side-by-Side Comparison: SOURCE A vs SOURCE B */}
                <div>
                  <div className="text-[11px] font-semibold text-white uppercase tracking-wider mb-2.5 flex items-center justify-between font-mono">
                    <span>Side-by-Side Ledger Comparison</span>
                    <span className="text-[10px] text-white/40 font-mono">Source A vs Source B</span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-black border border-white/10 text-xs font-mono">
                    {/* SOURCE A */}
                    <div className="space-y-2 border-r border-white/10 pr-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-white/50 uppercase">
                          {selectedException.discrepancy_type === "DUPLICATE_ENTRY"
                            ? "Source A (Primary Feed Entry)"
                            : selectedException.discrepancy_type === "MISSING_ENTRY"
                            ? "Source A (Recorded Bank Line)"
                            : "Source A (Feed Line)"}
                        </span>
                        <Badge variant="yellow" size="xs">
                          {selectedException.source_record?.source_type || "BANK"}
                        </Badge>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">Amount</span>
                        <div className="text-base font-mono font-bold text-white">
                          ₹
                          {selectedException.source_record?.amount !== undefined
                            ? Number(selectedException.source_record.amount).toLocaleString("en-IN", {
                                minimumFractionDigits: 2,
                              })
                            : selectedException.source_value || "—"}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">Transaction ID / UTR</span>
                        <div className="font-mono text-[11px] text-white/80 truncate">
                          {selectedException.source_record?.transaction_id || "—"}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">Reference</span>
                        <div className="text-[#FFD400] font-mono text-[11px] truncate">
                          {selectedException.source_record?.reference || "None"}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">Settlement Date</span>
                        <div className="text-white/60 font-mono text-[11px]">
                          {selectedException.source_record?.date || "2026-09-29"}
                        </div>
                      </div>
                    </div>

                    {/* SOURCE B */}
                    <div className="space-y-2 pl-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-white/50 uppercase">
                          {selectedException.discrepancy_type === "DUPLICATE_ENTRY"
                            ? "Source B (Duplicate Line Collision)"
                            : selectedException.discrepancy_type === "MISSING_ENTRY"
                            ? "Source B (Missing in Ledger)"
                            : "Source B (Matched Master)"}
                        </span>
                        <Badge
                          variant={
                            selectedException.discrepancy_type === "MISSING_ENTRY" ? "critical" : "matched"
                          }
                          size="xs"
                        >
                          {selectedException.discrepancy_type === "MISSING_ENTRY"
                            ? "MISSING"
                            : selectedException.matched_record?.type || "INVOICE"}
                        </Badge>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">Amount</span>
                        <div className="text-base font-mono font-bold text-white">
                          {selectedException.discrepancy_type === "MISSING_ENTRY"
                            ? "₹0.00 (Unrecorded in Books)"
                            : selectedException.matched_record?.amount !== undefined
                            ? `₹${Number(selectedException.matched_record.amount).toLocaleString("en-IN", {
                                minimumFractionDigits: 2,
                              })}`
                            : selectedException.matched_value || "None (Missing Entry)"}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">
                          {selectedException.matched_record?.type === "INVOICE"
                            ? "Invoice Number"
                            : "Target Identifier"}
                        </span>
                        <div className="font-mono text-[11px] text-white/80 truncate">
                          {selectedException.matched_record?.identifier || "Missing in Ledger"}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">Counterparty Entity</span>
                        <div className="text-white font-mono text-[11px] truncate">
                          {selectedException.matched_record?.entity_name || "Acme Corporation LLC"}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-white/40 block">
                          {selectedException.matched_record?.type === "INVOICE" ? "Invoice Date" : "Date"}
                        </span>
                        <div className="text-white/60 font-mono text-[11px]">
                          {selectedException.matched_record?.date || "2026-09-29"}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Variance Calculation Box */}
                <div className="p-3.5 rounded-xl bg-black border border-[#FFD400]/40 flex items-center justify-between font-mono">
                  <div className="flex items-center gap-2.5">
                    <TrendingDown className="h-5 w-5 text-[#FFD400] shrink-0" />
                    <div>
                      <div className="text-xs font-semibold text-white">
                        {selectedException.discrepancy_type === "DUPLICATE_ENTRY"
                          ? "Duplicate Transaction Collision"
                          : selectedException.discrepancy_type === "MISSING_ENTRY"
                          ? "Unrecorded Ledger Entry"
                          : selectedException.discrepancy_type === "DATE"
                          ? "Settlement Timing Lag"
                          : "Detected Variance / Discrepancy"}
                      </div>
                      <div className="text-[11px] text-white/60 font-sans">
                        {selectedException.discrepancy_type === "AMOUNT"
                          ? `Delta: ₹${Number(selectedException.difference_numeric || 0).toLocaleString(
                              "en-IN",
                              { minimumFractionDigits: 2 }
                            )} (${selectedException.difference_percentage || 0}% variance between Feed & Invoice)`
                          : selectedException.discrepancy_type === "DATE"
                          ? `Settlement Lag: T+${selectedException.difference_numeric || 2} days banking clearing window`
                          : selectedException.discrepancy_type === "DUPLICATE_ENTRY"
                          ? `Duplicate collision on identifier ${selectedException.source_value}: identical payment amount recorded twice across incoming rails`
                          : `Orphaned record on ${selectedException.source_value}: entry present in feed but missing in accounting books`}
                      </div>
                    </div>
                  </div>

                  <span className="text-base font-mono font-bold text-[#FFD400]">
                    {selectedException.discrepancy_type === "AMOUNT"
                      ? `Δ -₹${Number(selectedException.difference_numeric || 0).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                        })}`
                      : selectedException.discrepancy_type === "DATE"
                      ? `T+${selectedException.difference_numeric || 2}d`
                      : selectedException.discrepancy_type === "DUPLICATE_ENTRY"
                      ? `Duplicate (₹${Number(
                          selectedException.difference_numeric ||
                            selectedException.source_record?.amount ||
                            0
                        ).toLocaleString("en-IN", { minimumFractionDigits: 2 })})`
                      : `Missing ₹${Number(selectedException.difference_numeric || 0).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                        })}`}
                  </span>
                </div>

                {/* Operator Commentary Input */}
                <div className="space-y-1.5 pt-1 font-mono">
                  <label className="text-xs font-semibold text-white uppercase tracking-wider block">
                    Reviewer Audit Notes & Rationale
                  </label>
                  <textarea
                    rows={2}
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                    placeholder="Document your verification rationale, ticket reference, or reason for resolution..."
                    className="w-full text-xs font-mono bg-black border border-white/10 rounded-lg p-2.5 text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400] transition-colors"
                  />
                </div>

                {/* Action Toolbar */}
                <div className="pt-2 border-t border-white/10 flex flex-wrap items-center justify-between gap-2 font-mono">
                  <div className="flex items-center gap-2">
                    <Badge variant={isManager ? "yellow" : "neutral"} size="sm">
                      {isManager ? "Manager Permissions" : isAuditor ? "Auditor Permissions" : "Reviewer"}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {/* MANAGER SPECIFIC: Delegate Task to Auditor */}
                    {isManager && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowAssignModal(true)}
                        disabled={isSubmitting}
                        iconLeft={<UserPlus className="h-3.5 w-3.5 text-[#FFD400]" />}
                      >
                        Assign to Auditor
                      </Button>
                    )}

                    {/* AUDITOR SPECIFIC: If unable to understand, send request to manager */}
                    {isAuditor && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowEscalateModal(true)}
                        disabled={isSubmitting}
                        iconLeft={<HelpCircle className="h-3.5 w-3.5 text-[#FFD400]" />}
                      >
                        Send Request to Manager
                      </Button>
                    )}

                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleApplyAction("REJECT_MATCH")}
                      disabled={isSubmitting}
                    >
                      Reject Match
                    </Button>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleApplyAction("WRITE_OFF")}
                      disabled={isSubmitting}
                    >
                      Write Off Variance
                    </Button>

                    {selectedException.discrepancy_type === "DUPLICATE_ENTRY" && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleApplyAction("MARK_DUPLICATE")}
                        disabled={isSubmitting}
                      >
                        Mark Duplicate
                      </Button>
                    )}

                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleApplyAction("CONFIRM_MATCH")}
                      disabled={isSubmitting}
                      iconLeft={<CheckCircle2 className="h-3.5 w-3.5 text-black" />}
                    >
                      Approve & Resolve
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <EmptyState
              icon={<AlertTriangle className="h-6 w-6 text-[#FFD400]" />}
              title="Select an Exception"
              description="Click on an item from the exception queue on the left to inspect its side-by-side ledger comparison."
            />
          )}
        </div>
      </div>

      {/* MODAL 1: Auditor Request to Manager Modal */}
      {showEscalateModal && selectedException && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-in fade-in duration-150 font-mono">
          <div className="bg-[#0D0D0D] border border-white/20 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <div className="flex items-center gap-2 text-white">
                <HelpCircle className="h-5 w-5 text-[#FFD400]" />
                <h3 className="font-bold text-sm uppercase tracking-wider">
                  Request Manager Review
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowEscalateModal(false)}
                className="text-white/40 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-white/70 leading-relaxed font-sans">
              If you are unable to understand this payment discrepancy or require executive authorization, submit your question to the Operations Manager. This flags the case as <strong>CRITICAL / ESCALATED</strong>.
            </p>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/60 uppercase">
                Quick Reason Select
              </label>
              <div className="space-y-1.5">
                {COMMON_ESCALATION_REASONS.map((reason, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setEscalateReason(reason)}
                    className={`w-full text-left p-2 rounded-lg text-xs font-mono border transition-all ${
                      escalateReason === reason
                        ? "bg-[#171717] border-[#FFD400] text-white"
                        : "bg-black border-white/10 text-white/60 hover:border-white/30"
                    }`}
                  >
                    {reason}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/60 uppercase">
                Detailed Question or Commentary
              </label>
              <textarea
                rows={3}
                value={escalateReason}
                onChange={(e) => setEscalateReason(e.target.value)}
                placeholder="Explain what is unclear about this payment issue..."
                className="w-full text-xs font-mono bg-black border border-white/10 rounded-lg p-2.5 text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400]"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowEscalateModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() =>
                  handleApplyAction(
                    "ESCALATE",
                    escalateReason || "Auditor requested managerial review on this discrepancy."
                  )
                }
                isLoading={isSubmitting}
                iconRight={<Send className="h-3.5 w-3.5 text-black" />}
              >
                Send Request to Manager
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: Manager Task Assignment to Auditor Modal */}
      {showAssignModal && selectedException && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-in fade-in duration-150 font-mono">
          <div className="bg-[#0D0D0D] border border-white/20 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <div className="flex items-center gap-2 text-white">
                <UserPlus className="h-5 w-5 text-[#FFD400]" />
                <h3 className="font-bold text-sm uppercase tracking-wider">
                  Assign Case to Auditor
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAssignModal(false)}
                className="text-white/40 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-white/70 leading-relaxed font-sans">
              Delegate exception <strong>{selectedException.id}</strong> to a compliance auditor. The case status will shift to <strong>UNDER_REVIEW</strong> and appear in their assigned workbench queue.
            </p>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/60 uppercase">
                Select Designated Auditor
              </label>
              <div className="space-y-2">
                {AUDITOR_OPTIONS.map((auditor) => {
                  const isSelected = selectedAuditor === auditor.name;
                  return (
                    <button
                      key={auditor.name}
                      type="button"
                      onClick={() => setSelectedAuditor(auditor.name)}
                      className={`w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all ${
                        isSelected
                          ? "bg-[#171717] border-[#FFD400] text-white ring-1 ring-[#FFD400]"
                          : "bg-black border-white/10 text-white/70 hover:border-white/25"
                      }`}
                    >
                      <div>
                        <span className="font-bold text-xs text-white block">{auditor.name}</span>
                        <span className="text-[10px] text-white/40">{auditor.role} &bull; {auditor.email}</span>
                      </div>
                      {isSelected && <CheckCircle2 className="h-4 w-4 text-[#FFD400]" />}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/60 uppercase">
                Auditor Instructions / Notes
              </label>
              <textarea
                rows={2}
                value={assignInstructions}
                onChange={(e) => setAssignInstructions(e.target.value)}
                placeholder="e.g. Please check TDS deduction invoice and confirm settlement..."
                className="w-full text-xs font-mono bg-black border border-white/10 rounded-lg p-2.5 text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400]"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAssignModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() =>
                  handleApplyAction(
                    "ASSIGN_AUDITOR",
                    assignInstructions || `Assigned to ${selectedAuditor}`,
                    selectedAuditor
                  )
                }
                isLoading={isSubmitting}
                iconRight={<UserCheck className="h-3.5 w-3.5 text-black" />}
              >
                Delegate Case to {selectedAuditor.split(" ")[0]}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
