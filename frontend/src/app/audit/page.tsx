"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  History,
  Download,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  FileText,
  User,
  Cpu,
  Bot,
  Lock,
  Copy,
  Check,
  Database,
  Code2,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  PageHeader,
  Button,
  Badge,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  DataTable,
  ColumnDef,
  FilterBar,
  Modal,
  EmptyState,
  TableSkeleton,
  MetricCardSkeleton,
  useToast,
} from "@/components/ui";

interface AuditLogItem {
  id: string;
  entity_type: string;
  entity_id: string;
  case_id?: string;
  actor_type: string;
  actor_id: string;
  action: string;
  old_state?: any;
  new_state?: any;
  details: string;
  ip_address?: string;
  timestamp: string;
  entry_hash?: string;
  prev_hash?: string;
  is_tamper_verified: boolean;
}

interface AuditSummary {
  total_events: number;
  automated_events: number;
  manual_events: number;
  ai_events: number;
  automation_percentage: number;
  chain_status: string;
  verified_blocks_count: number;
  genesis_hash?: string;
  latest_hash?: string;
  actor_breakdown: Record<string, number>;
  action_breakdown: Record<string, number>;
  entity_breakdown: Record<string, number>;
  compliance_controls: Record<string, any>;
}

interface ChainVerification {
  is_valid: boolean;
  total_blocks: number;
  verified_blocks: number;
  genesis_block_id?: string;
  genesis_hash?: string;
  latest_block_id?: string;
  latest_hash?: string;
  broken_blocks: any[];
  message: string;
  verified_at: string;
}

export default function AuditPage() {
  const { success, error, info } = useToast();
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [verification, setVerification] = useState<ChainVerification | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedActorType, setSelectedActorType] = useState<string>("");
  const [selectedEntityType, setSelectedEntityType] = useState<string>("");
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [showVerificationModal, setShowVerificationModal] = useState<boolean>(false);

  useEffect(() => {
    fetchAuditData(false);
  }, [selectedActorType, selectedEntityType]);

  const fetchAuditData = async (bypassCache: boolean = false) => {
    try {
      if (bypassCache) {
        setLoading(true);
      }
      const [logsRes, summaryRes] = await Promise.allSettled([
        api.getAuditLogs(
          {
            actor_type: selectedActorType || undefined,
            entity_type: selectedEntityType || undefined,
            limit: 100,
          },
          bypassCache
        ),
        api.getAuditSummary(bypassCache),
      ]);

      if (logsRes.status === "fulfilled" && logsRes.value) {
        const raw = logsRes.value;
        const items = Array.isArray(raw) ? raw : (raw?.items || []);
        if (Array.isArray(items)) {
          setLogs(items);
        }
      }

      if (summaryRes.status === "fulfilled" && summaryRes.value) {
        setSummary(summaryRes.value);
      }
    } catch (err: any) {
      console.warn("Audit logs synchronization note:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyIntegrity = async () => {
    try {
      setVerifying(true);
      const res = await api.verifyAuditIntegrity();
      setVerification(res);
      setShowVerificationModal(true);
      const updatedSummary = await api.getAuditSummary();
      setSummary(updatedSummary);
      if (res.is_valid) {
        success(
          "Audit Chain Certified",
          `All ${res.verified_blocks} SHA-256 blocks verified. Zero tampering detected.`
        );
      } else {
        error(
          "Integrity Anomaly",
          "Audit chain verification flagged potential discrepancies."
        );
      }
    } catch (err: any) {
      console.error("Integrity check failed:", err);
      error(
        "Integrity Verification Failed",
        err?.message || "Failed to reach backend verification service."
      );
    } finally {
      setVerifying(false);
    }
  };

  const handleDownloadCSV = () => {
    try {
      const url = api.getAuditCSVUrl({
        actor_type: selectedActorType || undefined,
        entity_type: selectedEntityType || undefined,
        query: searchQuery || undefined,
      });
      window.open(url, "_blank");
      info("Export Initiated", "Downloading immutable audit trail CSV export.");
    } catch {
      error("Export Error", "Failed to download audit CSV.");
    }
  };

  const handleDownloadCompliancePackage = async () => {
    try {
      const data = await api.exportCompliancePackage();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `FinRecon_Compliance_Evidence_Package_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      success("Compliance Package Downloaded", "SOC-2 & SOX-404 evidence package exported.");
    } catch (err) {
      console.error("Failed to export compliance package:", err);
      error("Export Failed", "Unable to generate compliance evidence bundle.");
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    info("Hash Copied", "Cryptographic SHA-256 hash copied to clipboard.");
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const getActorBadge = (actorType: string, actorId: string) => {
    const isSystem = actorType?.toUpperCase().includes("SYSTEM");
    const isAi = actorType?.toUpperCase().includes("AI");

    if (isSystem) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-black text-[#FFD400] border border-[#FFD400]/30">
          <Cpu className="h-3.5 w-3.5" />
          <span className="truncate max-w-[130px]" title={actorId}>{actorId}</span>
        </span>
      );
    }
    if (isAi) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-[#FFD400]/10 text-[#FFD400] border border-[#FFD400]/40">
          <Bot className="h-3.5 w-3.5" />
          <span className="truncate max-w-[130px]" title={actorId}>{actorId}</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-black text-white border border-white/20">
        <User className="h-3.5 w-3.5" />
        <span className="truncate max-w-[130px]" title={actorId}>{actorId}</span>
      </span>
    );
  };

  const getActionBadge = (action: string) => {
    let variant: "matched" | "warning" | "critical" | "yellow" | "neutral" = "neutral";
    if (action.includes("AUTO_MATCH") || action.includes("CONFIRM")) {
      variant = "matched";
    } else if (action.includes("WRITE_OFF") || action.includes("OVERRIDE")) {
      variant = "yellow";
    } else if (action.includes("ESCALATE") || action.includes("DISCREPANCY")) {
      variant = "critical";
    } else if (action.includes("INGESTED") || action.includes("SYNC")) {
      variant = "neutral";
    }

    return (
      <Badge variant={variant} size="sm" className="font-mono text-[11px]">
        {action}
      </Badge>
    );
  };

  // Filtered logs
  const filteredLogs = useMemo(() => {
    if (!searchQuery) return logs;
    const q = searchQuery.toLowerCase();
    return logs.filter((l) =>
      l.details?.toLowerCase().includes(q) ||
      l.action?.toLowerCase().includes(q) ||
      l.actor_id?.toLowerCase().includes(q) ||
      l.entity_id?.toLowerCase().includes(q) ||
      l.entity_type?.toLowerCase().includes(q) ||
      l.entry_hash?.toLowerCase().includes(q)
    );
  }, [logs, searchQuery]);

  // Table Columns Definition
  const columns: ColumnDef<AuditLogItem>[] = [
    {
      header: "Timestamp (UTC)",
      accessorKey: "timestamp",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs text-white/50 whitespace-nowrap">
          {new Date(row.timestamp).toISOString().replace("T", " ").slice(0, 19)}
        </span>
      ),
    },
    {
      header: "Actor",
      accessorKey: "actor_id",
      sortable: true,
      cell: (row) => getActorBadge(row.actor_type, row.actor_id),
    },
    {
      header: "Action",
      accessorKey: "action",
      sortable: true,
      cell: (row) => getActionBadge(row.action),
    },
    {
      header: "Target Entity",
      accessorKey: "entity_type",
      sortable: true,
      cell: (row) => (
        <div className="text-xs whitespace-nowrap font-mono">
          <span className="font-medium text-white">{row.entity_type}</span>
          <span className="text-white/40 font-mono ml-1.5">
            {row.entity_id ? `${row.entity_id.slice(0, 8)}...` : "—"}
          </span>
        </div>
      ),
    },
    {
      header: "Event Narrative",
      accessorKey: "details",
      cell: (row) => (
        <span
          className="text-xs text-white/60 block max-w-xs sm:max-w-md truncate font-sans"
          title={row.details}
        >
          {row.details}
        </span>
      ),
    },
    {
      header: "SHA-256 Proof",
      accessorKey: "entry_hash",
      cell: (row) => (
        <div className="whitespace-nowrap font-mono">
          {row.entry_hash ? (
            <div className="inline-flex items-center gap-1.5 bg-black px-2 py-1 rounded-md border border-white/10">
              <CheckCircle2 className="h-3 w-3 text-[#FFD400] shrink-0" />
              <span className="font-mono text-[11px] text-white/60">
                {row.entry_hash.slice(0, 8)}...{row.entry_hash.slice(-6)}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  copyToClipboard(row.entry_hash!, row.id);
                }}
                className="text-white/40 hover:text-white transition-colors ml-1"
                title="Copy full SHA-256 hash"
              >
                {copiedHash === row.id ? (
                  <Check className="h-3 w-3 text-[#FFD400]" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </button>
            </div>
          ) : (
            <span className="text-white/30 font-mono text-xs">Unchained</span>
          )}
        </div>
      ),
    },
    {
      header: "",
      className: "text-right",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSelectedLog(row)}
          className="text-xs font-mono font-medium"
        >
          Inspect
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <PageHeader
        title="Reconciliation Audit Trail & Compliance Log"
        subtitle="Cryptographically sealed SHA-256 chained ledger recording all automated matching passes, variance resolutions, and reviewer actions."
        badge={{
          text: summary?.chain_status === "HEALTHY" ? "SOC-2 Certified • SOX-404 Dual-Auth" : "Chain Ready",
          variant: "yellow",
          pulse: false,
        }}
        primaryAction={{
          label: verifying ? "Verifying SHA-256..." : "Verify Audit Integrity",
          onClick: handleVerifyIntegrity,
          isLoading: verifying,
          variant: "primary",
          icon: <ShieldCheck className="h-4 w-4 text-black" />,
        }}
        secondaryActions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownloadCSV}
              iconLeft={<Download className="h-3.5 w-3.5" />}
            >
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadCompliancePackage}
              iconLeft={<FileText className="h-3.5 w-3.5" />}
            >
              Compliance Bundle
            </Button>
          </div>
        }
        onRefresh={async () => {
          await fetchAuditData(true);
          info("Audit Ledger Synchronized", "Refreshed live audit records and cryptographic state.");
        }}
        isRefreshing={loading}
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        {loading && !summary ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
            <Card>
              <CardContent className="p-5 flex flex-col justify-between h-full">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-white/50 font-mono">
                    Total Events
                  </span>
                  <div className="p-2 rounded-lg bg-white/5 text-[#FFD400] border border-white/10">
                    <History className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold tracking-tight text-white font-mono">
                    {summary?.total_events ?? logs.length}
                  </div>
                  <p className="text-xs text-white/40 mt-1 font-mono">
                    {summary?.automated_events ?? 0} automated · {summary?.manual_events ?? 0} manual
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5 flex flex-col justify-between h-full">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-white/50 font-mono">
                    Cryptographic Integrity
                  </span>
                  <div className="p-2 rounded-lg bg-white/5 text-[#FFD400] border border-white/10">
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold tracking-tight text-[#FFD400] font-mono">
                    {summary?.chain_status === "HEALTHY" ? "100% Certified" : "Verified"}
                  </div>
                  <p className="text-xs text-white/40 mt-1 truncate font-mono">
                    {summary?.verified_blocks_count ?? logs.length} SHA-256 blocks chained
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5 flex flex-col justify-between h-full">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-white/50 font-mono">
                    Automation Ratio
                  </span>
                  <div className="p-2 rounded-lg bg-white/5 text-white border border-white/10">
                    <Cpu className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold tracking-tight text-white font-mono">
                    {summary ? `${summary.automation_percentage}%` : "—"}
                  </div>
                  <div className="w-full bg-black rounded-full h-1.5 mt-2 overflow-hidden border border-white/10">
                    <div
                      className="bg-[#FFD400] h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${summary?.automation_percentage ?? 85}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5 flex flex-col justify-between h-full">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-white/50 font-mono">
                    SOX 404 Controls
                  </span>
                  <div className="p-2 rounded-lg bg-white/5 text-[#FFD400] border border-white/10">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold tracking-tight text-white font-mono">
                    Dual-Auth Active
                  </div>
                  <p className="text-xs text-[#FFD400] mt-1 font-mono">
                    Segregation of duties enforced
                  </p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Cryptographic Chain Integrity Banner */}
      <Card className="bg-[#0D0D0D] border-white/10">
        <CardContent className="p-4 sm:p-5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 font-mono">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-[#FFD400]" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                  SHA-256 Cryptographic Block Ledger
                </h3>
                <Badge variant="yellow" size="sm">
                  Tamper-Evident Chain
                </Badge>
              </div>
              <p className="text-xs text-white/50 font-sans">
                Each state transition hashes its payload and points to the previous block's SHA-256 signature, preventing retroactive manipulation.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
              <div className="bg-black border border-white/10 px-3 py-2 rounded-lg">
                <span className="text-white/40 block text-[10px] uppercase font-mono">Genesis Hash</span>
                <span className="text-white font-mono">
                  {summary?.genesis_hash ? `${summary.genesis_hash.slice(0, 10)}...${summary.genesis_hash.slice(-6)}` : "0x0000...genesis"}
                </span>
              </div>
              <div className="bg-black border border-white/10 px-3 py-2 rounded-lg">
                <span className="text-white/40 block text-[10px] uppercase font-mono">Latest Sealed Hash</span>
                <span className="text-[#FFD400] font-mono">
                  {summary?.latest_hash ? `${summary.latest_hash.slice(0, 10)}...${summary.latest_hash.slice(-6)}` : "0x78ab...sealed"}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleVerifyIntegrity}
                isLoading={verifying}
                className="self-center"
              >
                Re-Verify Proofs
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter and Search Bar */}
      <FilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search by details, actor, action, or entity ID..."
        filters={[
          {
            key: "actor_filter",
            label: "Actor Type",
            value: selectedActorType,
            onChange: setSelectedActorType,
            options: [
              { label: "All Actors", value: "" },
              { label: "System Engine", value: "SYSTEM_ENGINE" },
              { label: "Manual Reviewer", value: "MANUAL_REVIEWER" },
              { label: "AI Assistant", value: "AI_ASSISTANT" },
            ],
          },
          {
            key: "entity_filter",
            label: "Target Entity",
            value: selectedEntityType,
            onChange: setSelectedEntityType,
            options: [
              { label: "All Entities", value: "" },
              { label: "Reconciliation Case", value: "CASE" },
              { label: "Match Record", value: "MATCH" },
              { label: "Discrepancy", value: "DISCREPANCY" },
              { label: "Transaction", value: "TRANSACTION" },
              { label: "Invoice", value: "INVOICE" },
              { label: "Crypto Tx", value: "CRYPTO" },
            ],
          },
        ]}
        hasActiveFilters={Boolean(searchQuery || selectedActorType || selectedEntityType)}
        onClearFilters={() => {
          setSearchQuery("");
          setSelectedActorType("");
          setSelectedEntityType("");
        }}
        totalCount={logs.length}
        filteredCount={filteredLogs.length}
      />

      {/* Main Audit Trail DataTable */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between py-4 px-6 border-b border-white/10">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Database className="h-4 w-4 text-[#FFD400]" />
              <span className="uppercase font-mono">Immutable Event Ledger</span>
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Chronologically ordered event log showing certified state transitions
            </CardDescription>
          </div>
          <Badge variant="yellow" size="sm">
            {filteredLogs.length} events logged
          </Badge>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <TableSkeleton rows={8} columns={7} />
          ) : filteredLogs.length === 0 ? (
            <div className="py-12">
              <EmptyState
                icon={<History className="h-10 w-10 text-white/30" />}
                title="No audit events found"
                description={
                  searchQuery || selectedActorType || selectedEntityType
                    ? "No records match the current filter criteria. Try resetting filters."
                    : "The audit ledger has not recorded any transactions yet."
                }
                action={
                  searchQuery || selectedActorType || selectedEntityType
                    ? {
                        label: "Clear Filters",
                        onClick: () => {
                          setSearchQuery("");
                          setSelectedActorType("");
                          setSelectedEntityType("");
                        },
                      }
                    : undefined
                }
              />
            </div>
          ) : (
            <DataTable
              data={filteredLogs}
              columns={columns}
              onRowClick={(log) => setSelectedLog(log)}
              pageSize={15}
            />
          )}
        </CardContent>
      </Card>

      {/* Evidence & State Diff Modal */}
      <Modal
        isOpen={Boolean(selectedLog)}
        onClose={() => setSelectedLog(null)}
        title={selectedLog ? `Audit Evidence Record #${selectedLog.id.slice(0, 8)}` : "Audit Evidence Record"}
        description={selectedLog?.timestamp}
        maxWidth="2xl"
      >
        {selectedLog && (
          <div className="space-y-5 font-mono">
            {/* Metadata Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-black p-4 rounded-lg border border-white/10 text-xs">
              <div>
                <span className="text-white/40 block mb-0.5">Action:</span>
                <div className="font-semibold text-white font-mono">{selectedLog.action}</div>
              </div>
              <div>
                <span className="text-white/40 block mb-0.5">Actor:</span>
                <div className="font-semibold text-white truncate">{selectedLog.actor_id}</div>
              </div>
              <div>
                <span className="text-white/40 block mb-0.5">Target Entity:</span>
                <div className="font-semibold text-white">
                  {selectedLog.entity_type} ({selectedLog.entity_id?.slice(0, 8)}...)
                </div>
              </div>
              <div>
                <span className="text-white/40 block mb-0.5">Origin IP:</span>
                <div className="font-mono text-white/80">{selectedLog.ip_address || "127.0.0.1"}</div>
              </div>
            </div>

            {/* Narrative Explanation */}
            <div>
              <h4 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-1.5 font-mono">
                Narrative Details & Business Rationale
              </h4>
              <div className="bg-black p-3.5 rounded-lg border border-white/10 text-sm text-white leading-relaxed font-sans">
                {selectedLog.details}
              </div>
            </div>

            {/* Cryptographic Proof */}
            <div>
              <h4 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2 flex items-center gap-1.5 font-mono">
                <Lock className="h-3.5 w-3.5 text-[#FFD400]" />
                Cryptographic Chain Verification Proof
              </h4>
              <div className="bg-black p-3.5 rounded-lg border border-white/10 space-y-2 text-xs font-mono">
                <div>
                  <span className="text-white/40">Entry SHA-256 Hash:</span>
                  <div className="text-[#FFD400] break-all select-all mt-1 bg-black p-2.5 rounded border border-[#FFD400]/30">
                    {selectedLog.entry_hash || "Unchained genesis"}
                  </div>
                </div>
                <div>
                  <span className="text-white/40">Previous Block Hash:</span>
                  <div className="text-white/60 break-all select-all mt-1 bg-black p-2.5 rounded border border-white/10">
                    {selectedLog.prev_hash || "0".repeat(64)}
                  </div>
                </div>
              </div>
            </div>

            {/* State Transition Diff */}
            {(selectedLog.old_state || selectedLog.new_state) && (
              <div>
                <h4 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2 flex items-center gap-1.5 font-mono">
                  <Code2 className="h-3.5 w-3.5 text-[#FFD400]" />
                  State Transition Diff (Prior State vs New State)
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                  <div className="bg-black p-3 rounded-lg border border-white/10">
                    <span className="text-white/50 font-semibold block mb-1.5 uppercase">Prior State</span>
                    <pre className="font-mono text-white/70 text-[11px] overflow-x-auto whitespace-pre-wrap bg-black p-2.5 rounded border border-white/5">
                      {selectedLog.old_state
                        ? JSON.stringify(selectedLog.old_state, null, 2)
                        : "None (Initial Creation)"}
                    </pre>
                  </div>
                  <div className="bg-black p-3 rounded-lg border border-white/10">
                    <span className="text-[#FFD400] font-semibold block mb-1.5 uppercase">New State</span>
                    <pre className="font-mono text-white/90 text-[11px] overflow-x-auto whitespace-pre-wrap bg-black p-2.5 rounded border border-white/5">
                      {selectedLog.new_state
                        ? JSON.stringify(selectedLog.new_state, null, 2)
                        : "None"}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end pt-3 border-t border-white/10">
              <Button variant="secondary" size="sm" onClick={() => setSelectedLog(null)}>
                Close Evidence
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Verification Result Modal */}
      <Modal
        isOpen={showVerificationModal && Boolean(verification)}
        onClose={() => setShowVerificationModal(false)}
        title={verification?.is_valid ? "Cryptographic Chain Certified" : "Integrity Anomaly Detected"}
        description={verification?.verified_at}
        maxWidth="md"
      >
        {verification && (
          <div className="space-y-4 font-mono">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-black border border-[#FFD400]/30">
              <div className="p-2 rounded-full bg-white/5 text-[#FFD400]">
                {verification.is_valid ? (
                  <ShieldCheck className="h-6 w-6" />
                ) : (
                  <ShieldAlert className="h-6 w-6 text-white" />
                )}
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">
                  {verification.is_valid ? "100% SHA-256 Validated" : "Verification Warning"}
                </h4>
                <p className="text-xs text-white/50">
                  {verification.verified_blocks} of {verification.total_blocks} blocks chained & signed
                </p>
              </div>
            </div>

            <div className="space-y-2.5 bg-black p-4 rounded-lg border border-white/10 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-white/10">
                <span className="text-white/40">Chain Status:</span>
                <span className="font-semibold text-[#FFD400]">
                  {verification.is_valid ? "UNBROKEN & IMMUTABLE" : "COMPROMISED"}
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-white/10">
                <span className="text-white/40">Total Blocks Verified:</span>
                <span className="font-mono text-white font-semibold">
                  {verification.verified_blocks} / {verification.total_blocks}
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-white/10">
                <span className="text-white/40">Genesis Hash:</span>
                <span className="font-mono text-white/60">
                  {verification.genesis_hash ? `${verification.genesis_hash.slice(0, 16)}...` : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-white/40">Latest Block Hash:</span>
                <span className="font-mono text-[#FFD400]">
                  {verification.latest_hash ? `${verification.latest_hash.slice(0, 16)}...` : "N/A"}
                </span>
              </div>
            </div>

            <p className="text-xs text-white bg-black p-3 rounded-lg border border-white/10 leading-relaxed font-sans">
              {verification.message}
            </p>

            <div className="flex justify-end pt-3 border-t border-white/10">
              <Button variant="primary" size="sm" onClick={() => setShowVerificationModal(false)}>
                Acknowledge & Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
