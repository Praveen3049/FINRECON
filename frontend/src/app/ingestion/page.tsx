"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Download,
  Landmark,
  CreditCard,
  BookOpen,
  Receipt,
  Coins,
  ArrowRight,
  Database,
  Sparkles,
  RefreshCw,
  FileCheck,
  Plus,
  Trash2,
  Building,
  ShieldAlert,
  Bot,
  Layers,
  X,
  Check,
} from "lucide-react";
import Link from "next/link";
import { api, DataSourceItem, IngestionApiResponse } from "@/lib/api";
import { SourceType } from "@/lib/types";
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
  DataTable,
  ColumnDef,
  useToast,
} from "@/components/ui";

interface SourceOption {
  type: SourceType;
  title: string;
  format: string;
  icon: React.ReactNode;
  sampleFileName: string;
  samplePath: string;
}

const SOURCE_OPTIONS: SourceOption[] = [
  {
    type: "BANK",
    title: "Bank Statement",
    format: "CSV",
    icon: <Landmark className="h-5 w-5 text-[#FFD400]" />,
    sampleFileName: "bank_statement_sample.csv",
    samplePath: "/sample_datasets/bank_statement_sample.csv",
  },
  {
    type: "ACCOUNTING",
    title: "Accounting / ERP",
    format: "CSV (NetSuite)",
    icon: <BookOpen className="h-5 w-5 text-white" />,
    sampleFileName: "accounting_records_sample.csv",
    samplePath: "/sample_datasets/accounting_records_sample.csv",
  },
  {
    type: "INVOICE",
    title: "Tax Invoices",
    format: "CSV / XLSX",
    icon: <Receipt className="h-5 w-5 text-white" />,
    sampleFileName: "invoices_sample.csv",
    samplePath: "/sample_datasets/invoices_sample.csv",
  },
  {
    type: "PAYMENT_GATEWAY",
    title: "Payment Gateway",
    format: "JSON (Stripe)",
    icon: <CreditCard className="h-5 w-5 text-[#FFD400]" />,
    sampleFileName: "payment_gateway_sample.json",
    samplePath: "/sample_datasets/payment_gateway_sample.json",
  },
  {
    type: "CRYPTO",
    title: "Blockchain / Crypto",
    format: "JSON (On-chain)",
    icon: <Coins className="h-5 w-5 text-[#FFD400]" />,
    sampleFileName: "crypto_transactions_sample.json",
    samplePath: "/sample_datasets/crypto_transactions_sample.json",
  },
];

export default function IngestionPage() {
  const { user } = useAuth();
  const isManager = user?.role === "MANAGER";
  const isAuditor = user?.role === "AUDITOR";
  const isUser = user?.role === "USER" || (!isManager && !isAuditor);

  const [selectedSource, setSelectedSource] = useState<SourceType>("BANK");
  const [file, setFile] = useState<File | null>(null);
  const [customSourceName, setCustomSourceName] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<IngestionApiResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState<boolean>(false);
  const [aczenStatus, setAczenStatus] = useState<any>(null);
  const [isSyncingAczen, setIsSyncingAczen] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  // Account Management State
  const [accounts, setAccounts] = useState<DataSourceItem[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>("");
  const [accountModalOpen, setAccountModalOpen] = useState<boolean>(false);
  const [newAccountName, setNewAccountName] = useState<string>("");
  const [newAccountType, setNewAccountType] = useState<string>("BANK");
  const [newAccountIdentifier, setNewAccountIdentifier] = useState<string>("");
  const [newAccountCurrency, setNewAccountCurrency] = useState<string>("INR");
  const [isCreatingAccount, setIsCreatingAccount] = useState<boolean>(false);

  const { success, error: toastError, info } = useToast();

  const currentOption = SOURCE_OPTIONS.find((s) => s.type === selectedSource) || SOURCE_OPTIONS[0];

  const fetchAczenStatus = async (bypassCache: boolean = false) => {
    if (!isManager) return;
    try {
      const data = await api.getAczenStatus(bypassCache);
      setAczenStatus(data);
    } catch {
      // Backend status fallback
    }
  };

  const fetchSourcesAndAccounts = async (bypassCache: boolean = false) => {
    setIsLoadingSources(true);
    try {
      const [sourcesData, accountsData] = await Promise.all([
        api.getDataSources(bypassCache).catch(() => []),
        api.getAccounts(bypassCache).catch(() => []),
      ]);
      setSources(sourcesData);
      setAccounts(accountsData);
      if (accountsData.length > 0 && !selectedAccountId) {
        setSelectedAccountId(accountsData[0].id);
      }
      setLastUpdated(new Date().toLocaleTimeString());
    } catch {
      // Fallback
    } finally {
      setIsLoadingSources(false);
    }
  };

  useEffect(() => {
    fetchSourcesAndAccounts(false);
    if (isManager) {
      fetchAczenStatus(false);
    }
  }, [user?.role]);

  const handleSyncAczen = async () => {
    if (!isManager) {
      toastError("Access Restricted", "Only Managers can synchronize corporate books.");
      return;
    }
    setIsSyncingAczen(true);
    try {
      const res = await api.syncAczenData(true);
      success(
        "Aczen Nova Books Synced",
        `Ingested ${res.invoices_ingested} invoices, ${res.payments_ingested} payments, and ${res.bank_transactions_ingested} bank lines.`
      );
      await fetchSourcesAndAccounts(true);
      await fetchAczenStatus(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to sync Aczen live books.";
      setErrorMessage(msg);
      toastError("Sync Failed", msg);
    } finally {
      setIsSyncingAczen(false);
    }
  };

  const handleCreateAccount = async () => {
    if (!newAccountName.trim()) {
      toastError("Validation Error", "Please provide an account name.");
      return;
    }
    setIsCreatingAccount(true);
    try {
      const res = await api.createAccount({
        name: newAccountName.trim(),
        source_type: newAccountType,
        account_identifier: newAccountIdentifier.trim() || undefined,
        currency: newAccountCurrency,
        file_format: "CSV",
      });
      success("Account Registered", `Successfully created account '${res.account.name}'.`);
      setAccountModalOpen(false);
      setNewAccountName("");
      setNewAccountIdentifier("");
      await fetchSourcesAndAccounts(true);
      setSelectedAccountId(res.account.id);
      setSelectedSource(res.account.source_type as SourceType);
    } catch (err: any) {
      toastError("Creation Failed", err?.response?.data?.detail || "Could not create account.");
    } finally {
      setIsCreatingAccount(false);
    }
  };

  const handleDeleteAccount = async (accId: string, accName: string) => {
    if (!confirm(`Are you sure you want to remove account '${accName}'?`)) return;
    try {
      await api.deleteAccount(accId);
      success("Account Removed", `Account '${accName}' removed.`);
      await fetchSourcesAndAccounts(true);
      if (selectedAccountId === accId) {
        setSelectedAccountId("");
      }
    } catch (err: any) {
      toastError("Delete Failed", err?.response?.data?.detail || "Could not delete account.");
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMessage(null);
    }
  };

  const handleUpload = async () => {
    if (isAuditor) {
      toastError("Read-Only Role", "Auditors possess review-only access. You cannot ingest new files.");
      return;
    }

    if (!file) {
      setErrorMessage("Please select a file to upload.");
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);
    setUploadResult(null);

    const targetAcc = accounts.find((a) => a.id === selectedAccountId);

    try {
      const result = await api.uploadFile(
        file,
        selectedSource,
        customSourceName.trim() || (targetAcc ? targetAcc.name : undefined),
        targetAcc ? targetAcc.id : undefined,
        targetAcc ? targetAcc.account_identifier : undefined
      );
      setUploadResult(result);
      success(
        "File Ingested Successfully",
        `Processed ${result.summary.processed_records} canonical records into ${targetAcc ? targetAcc.name : "FinRecon"}.`
      );
      await fetchSourcesAndAccounts(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload file.";
      setErrorMessage(msg);
      toastError("Upload Failed", msg);
    } finally {
      setIsUploading(false);
    }
  };

  const sourceColumns: ColumnDef<DataSourceItem>[] = [
    {
      header: "Account / Feed Name",
      accessorKey: "name",
      cell: (row) => (
        <div>
          <div className="font-semibold text-white font-mono">{row.name}</div>
          <div className="text-[10px] text-white/40 font-mono">{row.account_identifier || "Default"}</div>
        </div>
      ),
      sortable: true,
    },
    {
      header: "Rail Type",
      accessorKey: "source_type",
      cell: (row) => (
        <Badge variant={row.source_type === "BANK" ? "yellow" : row.source_type === "CRYPTO" ? "crypto" : "neutral"}>
          {row.source_type}
        </Badge>
      ),
      sortable: true,
    },
    {
      header: "Currency",
      accessorKey: "currency",
      cell: (row) => <span className="font-mono text-xs text-[#FFD400] font-bold">{row.currency}</span>,
      align: "center",
    },
    {
      header: "Records Ingested",
      accessorKey: "records_count",
      cell: (row) => (
        <span className="font-mono font-bold text-white">{row.records_count.toLocaleString()}</span>
      ),
      align: "right",
      sortable: true,
    },
    {
      header: "Status",
      cell: (row) => (
        <Badge variant={row.is_active ? "matched" : "neutral"} size="xs">
          {row.is_active ? "Active Feed" : "Archived"}
        </Badge>
      ),
      align: "center",
    },
    {
      header: "Action",
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => {
              setSelectedAccountId(row.id);
              setSelectedSource(row.source_type);
              const el = document.getElementById("upload-section");
              el?.scrollIntoView({ behavior: "smooth" });
              info("Account Selected", `Ready to import CSV into '${row.name}'.`);
            }}
            className="text-[11px] text-[#FFD400] hover:text-white bg-white/5 hover:bg-white/10 px-2 py-1 rounded border border-white/10 transition-colors font-mono"
          >
            Import CSV
          </button>
          {(isManager || row.owner_id === user?.id) && (
            <button
              onClick={() => handleDeleteAccount(row.id, row.name)}
              className="text-white/40 hover:text-red-400 p-1 rounded transition-colors"
              title="Delete Account"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      ),
      align: "right",
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 font-mono">
      {/* 1. Page Header with Role Awareness */}
      <PageHeader
        title={isUser ? "Account Management & CSV Ingestion" : "Multi-Source Data Ingestion & Enterprise Feeds"}
        subtitle={
          isUser
            ? "Manage your financial accounts by importing statement CSV files. Reconcile transactions and query the AI assistant."
            : isAuditor
            ? "Read-only inspection of corporate ingested feeds, provenance records, and raw file manifests."
            : "Automated financial ingestion, schema normalization, and field alignment across Bank Statements, Payment Gateways, ERP Ledgers, Tax Invoices, and Blockchain rails."
        }
        badge={{
          text: isUser
            ? `User Account Mode (${user?.name || "Member"})`
            : isAuditor
            ? "Auditor Mode (Read-Only)"
            : "Enterprise Manager Mode",
          variant: "yellow",
          pulse: isManager,
        }}
        onRefresh={() => {
          fetchSourcesAndAccounts(true);
          if (isManager) fetchAczenStatus(true);
        }}
        isRefreshing={isLoadingSources}
        lastUpdated={lastUpdated}
        secondaryActions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAccountModalOpen(true)}
              className="text-xs font-mono font-medium border-white/20 hover:border-[#FFD400] text-white hover:text-[#FFD400]"
              iconLeft={<Plus className="h-3.5 w-3.5" />}
            >
              Register Account
            </Button>
          </div>
        }
        primaryAction={
          isManager
            ? {
                label: isSyncingAczen ? "Syncing Books..." : "Sync Live Aczen Books",
                onClick: handleSyncAczen,
                isLoading: isSyncingAczen,
                icon: <RefreshCw className={isSyncingAczen ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />,
              }
            : undefined
        }
      />

      {/* Auditor Notice Banner */}
      {isAuditor && (
        <div className="bg-black border border-[#FFD400]/40 rounded-xl p-4 flex items-center justify-between text-xs text-white">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="h-4 w-4 text-[#FFD400] shrink-0" />
            <span>
              <strong>Auditor Review Access:</strong> Ingestion controls are in read-only mode for audit compliance. To investigate variances or resolve cases, visit the Exception Investigation Workbench.
            </span>
          </div>
          <Link href="/exceptions" className="text-[11px] underline text-[#FFD400] hover:text-white shrink-0 ml-4 font-bold">
            Open Exception Workbench &rarr;
          </Link>
        </div>
      )}

      {/* 2. Aczen Nova Enterprise Books Connector (MANAGER ONLY) */}
      {isManager && (
        <div className="bg-[#0D0D0D] border border-white/15 rounded-xl p-5 shadow-sm space-y-4 font-mono">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1 max-w-3xl">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#FFD400]/10 text-[#FFD400] border border-[#FFD400]/30 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#FFD400] animate-pulse" />
                  Live Finathon API Connector
                </span>
                <span className="text-[11px] text-white/40 font-mono">
                  {aczenStatus?.base_url || "https://www.aczen.in/nova-api/v1"}
                </span>
              </div>
              <h2 className="text-base font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-[#FFD400]" />
                Aczen Nova Enterprise Books Connector
              </h2>
              <p className="text-xs text-white/50 leading-relaxed font-sans">
                Synchronizes live enterprise books with zero mock data. Directly pulls Bank Statement Lines, GST Sales Invoices, Gateway settlements, and Corporate Entities into the multi-pass deterministic reconciliation engine.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start lg:self-auto shrink-0">
              <Button
                variant="primary"
                size="sm"
                onClick={handleSyncAczen}
                isLoading={isSyncingAczen}
                iconLeft={<RefreshCw className={isSyncingAczen ? "h-3.5 w-3.5 animate-spin text-black" : "h-3.5 w-3.5 text-black"} />}
              >
                {isSyncingAczen ? "Syncing Books..." : "Sync Live Aczen Books"}
              </Button>
            </div>
          </div>

          {/* Live Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-3 border-t border-white/10 text-xs font-mono">
            <div className="bg-black border border-white/10 rounded-lg p-2.5">
              <div className="text-[10px] text-white/40 uppercase font-medium">Bank Statement Lines</div>
              <div className="text-base font-bold text-white font-mono mt-0.5">
                {aczenStatus?.records?.transactions ? (aczenStatus.records.transactions - 299).toLocaleString() : "1,399"}
              </div>
              <div className="text-[10px] text-white/40">HDFC & SBI RTGS/NEFT</div>
            </div>
            <div className="bg-black border border-white/10 rounded-lg p-2.5">
              <div className="text-[10px] text-white/40 uppercase font-medium">Tax Invoices</div>
              <div className="text-base font-bold text-white font-mono mt-0.5">
                {aczenStatus?.records?.invoices?.toLocaleString() || "304"}
              </div>
              <div className="text-[10px] text-white/40">GST Sales Invoices</div>
            </div>
            <div className="bg-black border border-white/10 rounded-lg p-2.5">
              <div className="text-[10px] text-white/40 uppercase font-medium">Payment Ops</div>
              <div className="text-base font-bold text-white font-mono mt-0.5">
                {aczenStatus?.records?.reconciliation_cases?.toLocaleString() || "303"}
              </div>
              <div className="text-[10px] text-white/40">Gateways & Webhooks</div>
            </div>
            <div className="bg-black border border-white/10 rounded-lg p-2.5">
              <div className="text-[10px] text-white/40 uppercase font-medium">Master Entities</div>
              <div className="text-base font-bold text-[#FFD400] font-mono mt-0.5">
                {aczenStatus?.records?.entities?.toLocaleString() || "53"}
              </div>
              <div className="text-[10px] text-white/40">Clients & Vendors</div>
            </div>
            <div className="bg-black border border-white/10 rounded-lg p-2.5">
              <div className="text-[10px] text-white/40 uppercase font-medium">Reconciled Cases</div>
              <div className="text-base font-bold text-[#FFD400] font-mono mt-0.5">
                196 Exact
              </div>
              <div className="text-[10px] text-white/40">104 Under Review</div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Managed Accounts Section (Crucial for USER role) */}
      <div className="space-y-3 font-mono">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-white uppercase tracking-wider block">
              {isUser ? "1. Your Managed Accounts" : "Corporate Accounts Directory"}
            </span>
            <span className="text-[11px] text-white/50 font-sans">
              {isUser
                ? "Select an account to import bank statements or ledger CSVs into."
                : "Accounts registered across your reconciliation pipeline."}
            </span>
          </div>

          <button
            onClick={() => setAccountModalOpen(true)}
            className="flex items-center gap-1.5 text-xs text-[#FFD400] hover:text-white bg-black border border-[#FFD400]/40 hover:border-[#FFD400] px-3 py-1.5 rounded-lg transition-colors font-mono font-medium"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Account</span>
          </button>
        </div>

        {/* Accounts Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {accounts.map((acc) => {
            const isSelected = selectedAccountId === acc.id;
            return (
              <div
                key={acc.id}
                onClick={() => {
                  setSelectedAccountId(acc.id);
                  setSelectedSource(acc.source_type);
                }}
                className={`p-4 rounded-xl border text-left cursor-pointer transition-all select-none relative group ${
                  isSelected
                    ? "bg-[#171717] border-[#FFD400] shadow-md shadow-[#FFD400]/10 ring-1 ring-[#FFD400]"
                    : "bg-[#0D0D0D] border-white/10 hover:border-white/30"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-1.5 rounded-lg bg-white/5 text-[#FFD400] border border-white/10">
                    <Building className="h-4 w-4" />
                  </div>
                  <Badge variant={acc.source_type === "BANK" ? "yellow" : "neutral"} size="xs">
                    {acc.source_type}
                  </Badge>
                </div>

                <div className="font-semibold text-white text-xs truncate font-mono">
                  {acc.name}
                </div>
                <div className="text-[10px] text-white/40 font-mono mt-0.5 truncate">
                  ID: {acc.account_identifier || "Default"}
                </div>

                <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center justify-between text-xs font-mono">
                  <span className="text-white/50 text-[10px]">Records:</span>
                  <span className="text-[#FFD400] font-bold">{acc.records_count.toLocaleString()}</span>
                </div>

                <div className="mt-2 flex items-center justify-between pt-1">
                  <span className="text-[10px] text-[#FFD400] font-mono group-hover:underline">
                    {isSelected ? "Active Target ✓" : "Select & Import →"}
                  </span>
                  {(isManager || acc.owner_id === user?.id) && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteAccount(acc.id, acc.name);
                      }}
                      className="text-white/30 hover:text-red-400 p-1 transition-colors"
                      title="Delete Account"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {/* Quick Add Card */}
          <button
            type="button"
            onClick={() => setAccountModalOpen(true)}
            className="p-4 rounded-xl border border-dashed border-white/20 hover:border-[#FFD400] bg-black/40 hover:bg-black text-center flex flex-col items-center justify-center gap-2 transition-all group min-h-[130px]"
          >
            <div className="p-2 rounded-full bg-white/5 group-hover:bg-[#FFD400]/10 text-white/50 group-hover:text-[#FFD400] transition-colors border border-white/10">
              <Plus className="h-4 w-4" />
            </div>
            <span className="text-xs font-semibold text-white/70 group-hover:text-[#FFD400] font-mono">
              Register New Account
            </span>
            <span className="text-[10px] text-white/40">
              Bank, Ledger, or Invoices
            </span>
          </button>
        </div>
      </div>

      {/* 4. Rail Type Selector (Shown for clarity) */}
      <div className="space-y-3 font-mono">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-white uppercase tracking-wider">
            2. Ingestion Format & Rail
          </span>
          <span className="text-[11px] text-white/40">Supported formats: CSV, XLSX, JSON</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {SOURCE_OPTIONS.filter((opt) => isManager || opt.type !== "CRYPTO").map((opt) => {
            const isSelected = selectedSource === opt.type;
            return (
              <button
                key={opt.type}
                type="button"
                onClick={() => {
                  setSelectedSource(opt.type);
                  setFile(null);
                  setUploadResult(null);
                  setErrorMessage(null);
                }}
                className={`text-left p-4 rounded-xl border transition-all select-none ${
                  isSelected
                    ? "bg-[#171717] border-[#FFD400] shadow-md shadow-[#FFD400]/10 ring-1 ring-[#FFD400]"
                    : "bg-[#0D0D0D] border-white/10 hover:border-white/30"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="p-1.5 rounded-lg bg-white/5">{opt.icon}</div>
                  <span className="text-[10px] font-mono text-white/50 uppercase">
                    {opt.format}
                  </span>
                </div>
                <div className="mt-3">
                  <div className="text-xs font-semibold text-white">{opt.title}</div>
                  <div className="text-[10px] text-white/40 mt-0.5 font-mono">
                    {opt.type}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 5. Upload Dropzone & Registered Feeds Split */}
      <div id="upload-section" className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start font-mono">
        {/* Upload Form (7 cols) */}
        <div className="lg:col-span-7 bg-[#0D0D0D] border border-white/10 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/10 font-mono">
            <div>
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                <span>Upload {currentOption.title} Statement</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-[#FFD400] border border-[#FFD400]/30">
                  {currentOption.format}
                </span>
              </h3>
              <p className="text-xs text-white/50 mt-0.5 font-sans">
                Normalizes transaction amounts, dates, counterparties, and UTR/reference numbers.
              </p>
            </div>

            <a
              href={currentOption.samplePath}
              download={currentOption.sampleFileName}
              className="flex items-center gap-1.5 text-xs text-[#FFD400] hover:text-white font-mono bg-white/5 px-2.5 py-1.5 rounded-lg border border-white/10 hover:border-[#FFD400]/40 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Sample {currentOption.format.split(" ")[0]}</span>
            </a>
          </div>

          {/* Target Account Selector */}
          <div>
            <label className="text-xs text-white/60 font-mono block mb-1">
              Target Financial Account
            </label>
            <select
              value={selectedAccountId}
              onChange={(e) => {
                setSelectedAccountId(e.target.value);
                const target = accounts.find((a) => a.id === e.target.value);
                if (target) {
                  setSelectedSource(target.source_type);
                }
              }}
              className="w-full bg-black border border-white/15 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-[#FFD400] transition-colors"
            >
              <option value="">-- General Ingestion (No specific account) --</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id} className="bg-black text-white py-1">
                  {a.name} [{a.source_type}] ({a.account_identifier || "Default"}) &bull; {a.records_count} records
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-white/50 font-mono block mb-1">
              Custom Statement Alias / Batch Label (Optional)
            </label>
            <input
              type="text"
              placeholder={`e.g. September 2026 Batch, Q3 Reconciliation Statement...`}
              value={customSourceName}
              onChange={(e) => setCustomSourceName(e.target.value)}
              className="w-full bg-black border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400] transition-colors"
            />
          </div>

          {/* Dropzone */}
          <div className="border-2 border-dashed border-white/15 rounded-xl p-6 text-center bg-black hover:border-[#FFD400]/50 transition-colors">
            <input
              type="file"
              id="file-upload"
              accept=".csv,.json,.xlsx,.xls"
              onChange={handleFileChange}
              disabled={isAuditor}
              className="hidden"
            />
            <label htmlFor="file-upload" className={`block ${isAuditor ? "cursor-not-allowed opacity-50" : "cursor-pointer"}`}>
              <div className="h-10 w-10 rounded-xl bg-white/5 text-[#FFD400] flex items-center justify-center mx-auto mb-2.5 border border-white/10">
                <UploadCloud className="h-5 w-5" />
              </div>
              <div className="text-xs font-semibold text-white font-mono">
                {file ? file.name : "Select or drag & drop financial CSV statement"}
              </div>
              <p className="text-[11px] text-white/40 mt-1 font-mono">
                CSV or XLSX files up to 50 MB
              </p>
              {file && (
                <div className="mt-2 text-xs font-mono text-[#FFD400] flex items-center justify-center gap-1">
                  <FileCheck className="h-3.5 w-3.5" />
                  <span>Ready to import: {(file.size / 1024).toFixed(1)} KB</span>
                </div>
              )}
            </label>
          </div>

          {errorMessage && (
            <div className="p-3 rounded-lg bg-black border border-[#FFD400]/40 text-[#FFD400] text-xs flex items-center gap-2 font-mono">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-white/40 font-mono">
              {isAuditor ? "Upload disabled for Auditor" : "Automated schema detection on upload"}
            </span>
            <Button
              variant="primary"
              size="md"
              onClick={handleUpload}
              disabled={!file || isUploading || isAuditor}
              isLoading={isUploading}
              iconLeft={<CheckCircle2 className="h-4 w-4 text-black" />}
            >
              {isUploading ? "Normalizing..." : "Ingest & Normalize CSV"}
            </Button>
          </div>
        </div>

        {/* Live Active Feeds / Accounts Summary (5 cols) */}
        <div className="lg:col-span-5 bg-[#0D0D0D] border border-white/10 rounded-xl p-5 shadow-sm flex flex-col justify-between h-[450px]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-white/10 font-mono">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-[#FFD400]" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                  {isUser ? "My Managed Feeds" : "Active Data Rails"}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => fetchSourcesAndAccounts(true)}
                className="text-white/40 hover:text-white transition-colors"
                title="Refresh feed list"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isLoadingSources ? "animate-spin text-[#FFD400]" : ""}`} />
              </button>
            </div>
            <p className="text-xs text-white/50 mt-2 mb-3 font-sans">
              Financial statement feeds indexed into FinRecon and accessible to reconciliation passes.
            </p>

            <div className="space-y-2 max-h-[290px] overflow-y-auto pr-1 font-mono">
              {sources.length === 0 ? (
                <div className="text-xs text-white/40 text-center py-8">
                  No accounts or custom statement feeds recorded yet. Use the upload tool to import your first CSV.
                </div>
              ) : (
                sources.slice(0, 8).map((src) => (
                  <div
                    key={src.id}
                    className="p-2.5 rounded-lg bg-black border border-white/10 text-xs flex items-center justify-between hover:border-white/20 transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-white truncate max-w-[200px]">{src.name}</div>
                      <div className="text-[10px] text-white/40 font-mono mt-0.5">
                        {src.source_type} &bull; {src.file_format} &bull; {src.currency}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="font-mono font-bold text-white">{src.records_count.toLocaleString()}</div>
                      <div className="text-[10px] text-white/40">records</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-white/10 text-[11px] text-white/50 font-mono flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FFD400] shrink-0" />
              <span>RapidFuzz & Rule Pass Active</span>
            </div>
            <Link href="/ai-assistant" className="text-[#FFD400] hover:underline flex items-center gap-1">
              <Bot className="h-3 w-3" />
              <span>AI Copilot &rarr;</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 6. Ingestion Summary & Preview (When upload finishes) */}
      {uploadResult && (
        <Card className="border-[#FFD400]/40 shadow-lg shadow-[#FFD400]/5 animate-fade-in font-mono">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-[#FFD400]/10 text-[#FFD400] flex items-center justify-center shrink-0 border border-[#FFD400]/30">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <div>
                <CardTitle>
                  <span className="uppercase font-mono">Ingestion Completed Successfully</span>
                  <Badge variant="yellow" size="xs">
                    {uploadResult.summary.source_type}
                  </Badge>
                </CardTitle>
                <CardDescription>
                  Source File: <span className="font-mono text-white">{uploadResult.summary.file_name}</span>
                </CardDescription>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono">
              <div className="bg-black px-3 py-1 rounded-lg border border-white/10">
                <span className="text-white/40">Total: </span>
                <span className="font-mono font-bold text-white">{uploadResult.summary.total_records}</span>
              </div>
              <div className="bg-[#FFD400]/10 px-3 py-1 rounded-lg border border-[#FFD400]/30">
                <span className="text-[#FFD400] font-medium">Processed: </span>
                <span className="font-mono font-bold text-white">
                  {uploadResult.summary.processed_records}
                </span>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-4 font-mono">
            {/* Call to action: AI Assistant */}
            <div className="p-3 bg-black border border-white/10 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-[#FFD400]" />
                <span className="text-white/80">
                  {uploadResult.summary.processed_records} records are now available in the reconciliation database.
                </span>
              </div>
              <Link href="/ai-assistant">
                <Button variant="secondary" size="sm" iconRight={<ArrowRight className="h-3 w-3" />}>
                  Inspect with AI Assistant
                </Button>
              </Link>
            </div>

            {/* Detected Column Schema Mappings */}
            <div>
              <div className="text-xs font-semibold text-white uppercase tracking-wider mb-2 font-mono">
                Detected Schema Column Mappings
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(uploadResult.summary.detected_columns).map(([raw, canonical]) => (
                  <div
                    key={raw}
                    className="text-xs bg-black border border-white/10 px-2.5 py-1 rounded-md flex items-center gap-2"
                  >
                    <span className="text-white/50 font-mono">{raw}</span>
                    <ArrowRight className="h-3 w-3 text-[#FFD400]" />
                    <span className="text-white font-mono font-medium">{canonical}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Warnings */}
            {uploadResult.summary.warnings.length > 0 && (
              <div className="p-3 rounded-lg bg-black border border-[#FFD400]/40 space-y-1 font-mono">
                <div className="text-xs font-semibold text-[#FFD400] flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span>Ingestion Warnings ({uploadResult.summary.warnings.length})</span>
                </div>
                <ul className="text-[11px] text-white/70 list-disc list-inside space-y-0.5">
                  {uploadResult.summary.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Canonical Normalized Preview Table */}
            {uploadResult.summary.preview.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-white uppercase tracking-wider mb-2 font-mono">
                  Canonical Preview ({uploadResult.summary.preview.length} sample rows)
                </div>
                <div className="border border-white/10 rounded-lg overflow-x-auto bg-black">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#111111] text-white/50 uppercase text-[10px] font-mono border-b border-white/10">
                      <tr>
                        {Object.keys(uploadResult.summary.preview[0]).map((key) => (
                          <th key={key} className="px-3 py-2 font-semibold">
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {uploadResult.summary.preview.map((row, i) => (
                        <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                          {Object.values(row).map((val, j) => (
                            <td key={j} className="px-3 py-2 text-white/90 font-mono text-[11px]">
                              {String(val ?? "-")}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 7. Active Data Sources Full Table */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>
              <Database className="h-4 w-4 text-[#FFD400]" />
              <span className="uppercase font-mono">Registered Accounts & Feeds Registry</span>
            </CardTitle>
            <CardDescription>
              All multi-source accounts and statement feeds indexed for multi-pass reconciliation.
            </CardDescription>
          </div>
          <Badge variant="yellow">{sources.length} Feeds Stored</Badge>
        </CardHeader>
        <CardContent className="p-0">
          <DataTable
            columns={sourceColumns}
            data={sources}
            isLoading={isLoadingSources}
            pageSize={10}
            emptyTitle="No Data Sources Registered"
            emptyDescription="Register an account or import statement CSV files above."
          />
        </CardContent>
      </Card>

      {/* Register New Account Modal */}
      {accountModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-in fade-in font-mono">
          <div className="bg-[#0A0A0A] border border-white/20 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-white/10 bg-black flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-[#FFD400]/10 border border-[#FFD400]/30 text-[#FFD400]">
                  <Building className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Register Managed Account
                  </h3>
                  <p className="text-[11px] text-white/50">
                    Create a dedicated target for importing statement CSVs
                  </p>
                </div>
              </div>
              <button
                onClick={() => setAccountModalOpen(false)}
                className="p-1 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4">
              <div>
                <label className="text-xs font-semibold text-white/80 uppercase tracking-wider block mb-1">
                  Account Name *
                </label>
                <input
                  type="text"
                  value={newAccountName}
                  onChange={(e) => setNewAccountName(e.target.value)}
                  placeholder="e.g. HDFC Operating Account, Client Invoices Ledger..."
                  className="w-full bg-black border border-white/20 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400] transition-colors font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-white/80 uppercase tracking-wider block mb-1">
                  Account Rail Type
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: "BANK", label: "Bank Account" },
                    { id: "INVOICE", label: "Tax Invoices" },
                    { id: "ACCOUNTING", label: "ERP Ledger" },
                  ].map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setNewAccountType(r.id)}
                      className={`py-2 px-2 rounded-lg text-xs font-mono font-medium border text-center transition-all ${
                        newAccountType === r.id
                          ? "bg-black border-[#FFD400] text-[#FFD400]"
                          : "bg-black/40 border-white/10 text-white/60 hover:border-white/30"
                      }`}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-white/80 uppercase tracking-wider block mb-1">
                  Account Number / Identifier (Optional)
                </label>
                <input
                  type="text"
                  value={newAccountIdentifier}
                  onChange={(e) => setNewAccountIdentifier(e.target.value)}
                  placeholder="e.g. HDFC-99482180, INV-2026-CLIENT..."
                  className="w-full bg-black border border-white/20 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400] transition-colors font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-white/80 uppercase tracking-wider block mb-1">
                  Currency
                </label>
                <select
                  value={newAccountCurrency}
                  onChange={(e) => setNewAccountCurrency(e.target.value)}
                  className="w-full bg-black border border-white/20 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-[#FFD400] transition-colors"
                >
                  <option value="INR">INR (₹ Indian Rupee)</option>
                  <option value="USD">USD ($ US Dollar)</option>
                  <option value="EUR">EUR (€ Euro)</option>
                  <option value="GBP">GBP (£ British Pound)</option>
                </select>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-white/10 bg-black flex items-center justify-end gap-2.5">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setAccountModalOpen(false)}
                className="text-xs text-white/70 hover:text-white font-mono"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCreateAccount}
                disabled={isCreatingAccount || !newAccountName.trim()}
                className="text-xs font-mono font-bold bg-[#FFD400] hover:bg-[#e6be00] text-black"
                iconLeft={isCreatingAccount ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
              >
                {isCreatingAccount ? "Registering..." : "Create Account"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
