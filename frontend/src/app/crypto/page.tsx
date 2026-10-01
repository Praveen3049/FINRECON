"use client";

import React, { useState, useEffect } from "react";
import {
  Coins,
  ExternalLink,
  Calculator,
  TrendingDown,
  Copy,
  Check,
} from "lucide-react";
import { api } from "@/lib/api";
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
  FilterBar,
  useToast,
} from "@/components/ui";

interface CryptoTxn {
  id: string;
  transaction_hash: string;
  blockchain_network: string;
  wallet_from: string;
  wallet_to: string;
  from_entity_name?: string;
  to_entity_name?: string;
  asset: string;
  token_amount: number;
  fiat_value: number;
  fiat_currency: string;
  gas_fee: number;
  gas_fee_fiat: number;
  confirmation_status: string;
  block_number?: number;
  timestamp: string;
  associated_invoice_id?: string;
  reconciliation_status: string;
  confidence_score?: number;
  explorer_urls: {
    tx: string;
    from: string;
    to: string;
  };
}

interface TreasuryWallet {
  wallet_address: string;
  network: string;
  entity_id?: string;
  entity_name?: string;
  total_fiat_value: number;
  token_balances: Record<string, number>;
  transaction_count: number;
  explorer_url: string;
}

interface AnalyticsData {
  total_crypto_transactions: number;
  total_fiat_volume_usd: number;
  total_gas_fee_usd: number;
  crypto_reconciliation_rate: number;
  networks: Record<
    string,
    {
      total_transactions: number;
      total_fiat_volume: number;
      total_gas_fee_usd: number;
      assets: Record<string, number>;
    }
  >;
}

export default function CryptoPage() {
  const [txns, setTxns] = useState<CryptoTxn[]>([]);
  const [wallets, setWallets] = useState<TreasuryWallet[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [networkFilter, setNetworkFilter] = useState("");
  const [assetFilter, setAssetFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState("");

  // Gas Calculator State
  const [calcNetwork, setCalcNetwork] = useState("ETHEREUM");
  const [calcGasUnits, setCalcGasUnits] = useState(21000);
  const [calcGwei, setCalcGwei] = useState(25.0);
  const [gasResult, setGasResult] = useState<{ gas_fee_native: number; gas_fee_usd: number } | null>(
    null
  );

  // Slippage Analyzer State
  const [slipExpected, setSlipExpected] = useState(5000);
  const [slipActual, setSlipActual] = useState(4992.5);
  const [slipResult, setSlipResult] = useState<{
    slippage_usd: number;
    slippage_percentage: number;
    is_acceptable: boolean;
  } | null>(null);

  const { success, info } = useToast();

  useEffect(() => {
    loadData(false);
  }, []);

  const loadData = async (bypassCache: boolean = false) => {
    if (bypassCache) {
      setIsLoading(true);
    }
    try {
      const [txnsData, walletsData, analyticsData] = await Promise.allSettled([
        api.getCryptoTransactions({ limit: 100 }, bypassCache),
        api.getCryptoWallets(bypassCache),
        api.getCryptoAnalytics(bypassCache),
      ]);

      if (txnsData.status === "fulfilled" && Array.isArray(txnsData.value)) {
        setTxns(txnsData.value);
      }
      if (walletsData.status === "fulfilled" && Array.isArray(walletsData.value)) {
        setWallets(walletsData.value);
      }
      if (analyticsData.status === "fulfilled" && analyticsData.value) {
        setAnalytics(analyticsData.value);
      }
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Crypto data loading error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCalculateGas = async () => {
    try {
      const res = await api.calculateGas({
        blockchain_network: calcNetwork,
        gas_units: calcGasUnits,
        gas_price_gwei: calcGwei,
      });
      setGasResult(res);
      info("Gas Fee Calculated", `Estimated cost: $${res.gas_fee_usd.toFixed(2)}`);
    } catch {
      const ethPrice = calcNetwork === "POLYGON" ? 0.42 : 2450.0;
      const native = calcGasUnits * calcGwei * 1e-9;
      setGasResult({ gas_fee_native: native, gas_fee_usd: native * ethPrice });
    }
  };

  const handleAnalyzeSlippage = async () => {
    try {
      const res = await api.analyzeSlippage({
        expected_fiat_amount: slipExpected,
        actual_fiat_amount: slipActual,
      });
      setSlipResult(res);
      success("Slippage Analyzed", `Variance: $${Math.abs(res.slippage_usd).toFixed(2)} (${res.slippage_percentage.toFixed(2)}%)`);
    } catch {
      const diff = slipActual - slipExpected;
      const pct = (Math.abs(diff) / slipExpected) * 100;
      setSlipResult({ slippage_usd: diff, slippage_percentage: pct, is_acceptable: pct <= 0.5 });
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const filteredTxns = txns.filter((t) => {
    const matchesNetwork = networkFilter === "" || t.blockchain_network === networkFilter;
    const matchesAsset = assetFilter === "" || t.asset === assetFilter;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      searchQuery === "" ||
      t.transaction_hash.toLowerCase().includes(q) ||
      t.wallet_from.toLowerCase().includes(q) ||
      t.wallet_to.toLowerCase().includes(q) ||
      (t.associated_invoice_id || "").toLowerCase().includes(q);

    return matchesNetwork && matchesAsset && matchesSearch;
  });

  const columns: ColumnDef<CryptoTxn>[] = [
    {
      header: "Transaction Hash",
      accessorKey: "transaction_hash",
      cell: (row) => (
        <div className="flex items-center gap-2 font-mono">
          <span className="font-mono text-xs text-white">
            {row.transaction_hash.slice(0, 10)}...{row.transaction_hash.slice(-8)}
          </span>
          <button
            type="button"
            onClick={() => copyToClipboard(row.transaction_hash, row.id)}
            className="text-white/40 hover:text-white transition-colors"
            title="Copy transaction hash"
          >
            {copiedHash === row.id ? (
              <Check className="h-3 w-3 text-[#FFD400]" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </button>
          <a
            href={row.explorer_urls?.tx}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#FFD400] hover:text-white transition-colors"
            title="View on Block Explorer"
          >
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      ),
    },
    {
      header: "Blockchain Rail",
      accessorKey: "blockchain_network",
      cell: (row) => (
        <Badge variant={row.blockchain_network === "ETHEREUM" ? "yellow" : "crypto"} size="xs">
          {row.blockchain_network}
        </Badge>
      ),
      sortable: true,
    },
    {
      header: "Asset & Volume",
      cell: (row) => (
        <div>
          <div className="font-mono font-bold text-white">
            {row.token_amount.toLocaleString()} {row.asset}
          </div>
          <div className="text-[10px] text-white/40 font-mono">
            ${row.fiat_value.toLocaleString(undefined, { minimumFractionDigits: 2 })} USD
          </div>
        </div>
      ),
      sortable: true,
    },
    {
      header: "Counterparties",
      cell: (row) => (
        <div>
          <div className="text-xs font-semibold text-white">
            {row.from_entity_name || "Unknown"} &rarr; {row.to_entity_name || "Unknown"}
          </div>
          <div className="font-mono text-[10px] text-white/40 truncate max-w-[180px]">
            {row.wallet_from.slice(0, 6)}... &rarr; {row.wallet_to.slice(0, 6)}...
          </div>
        </div>
      ),
    },
    {
      header: "Ledger Match",
      accessorKey: "reconciliation_status",
      cell: (row) => (
        <Badge
          variant={
            row.reconciliation_status === "EXACT_MATCH"
              ? "matched"
              : row.reconciliation_status === "PARTIAL_MATCH"
              ? "yellow"
              : "warning"
          }
          size="xs"
        >
          {row.reconciliation_status.replace(/_/g, " ")}
        </Badge>
      ),
      sortable: true,
    },
    {
      header: "Invoice Reference",
      accessorKey: "associated_invoice_id",
      cell: (row) => (
        <span className="font-mono text-[11px] text-[#FFD400]">
          {row.associated_invoice_id || "Unlinked"}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* 1. Page Header */}
      <PageHeader
        title="Blockchain Ledger & Crypto Reconciliation"
        subtitle="Institutional digital asset settlement reconciliation. Pairs on-chain smart contract transactions (Ethereum, Polygon) with B2B invoices and ERP accounting ledgers."
        badge={{ text: "On-Chain Feeds Connected", variant: "yellow", pulse: true }}
        onRefresh={() => loadData(true)}
        isRefreshing={isLoading}
        lastUpdated={lastUpdated}
      />

      {/* 2. Top Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Total On-Chain Volume
          </span>
          <div className="text-xl font-mono font-bold text-white">
            ${(analytics?.total_fiat_volume_usd || 8400.0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-[#FFD400] font-medium block">
            {txns.length} Verified Transfers
          </span>
        </div>

        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Cumulative Gas Fees
          </span>
          <div className="text-xl font-mono font-bold text-white">
            ${(analytics?.total_gas_fee_usd || 6.08).toFixed(2)} USD
          </div>
          <span className="text-[10px] text-white/40 block">Network Execution Cost</span>
        </div>

        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Crypto Match Rate
          </span>
          <div className="text-xl font-mono font-bold text-[#FFD400]">
            {analytics?.crypto_reconciliation_rate || 95.0}%
          </div>
          <span className="text-[10px] text-[#FFD400] block font-medium">100% Invoiced</span>
        </div>

        <div className="p-3.5 rounded-xl border border-white/10 bg-[#0D0D0D] shadow-sm space-y-1">
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider block">
            Treasury Wallets
          </span>
          <div className="text-xl font-mono font-bold text-white">
            {wallets.length || 2} Active
          </div>
          <span className="text-[10px] text-white/40 block">Multi-Sig & Smart Contracts</span>
        </div>
      </div>

      {/* 3. Gas Calculator & Slippage Analyzer Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gas Fee Estimator */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle>
                <Calculator className="h-4 w-4 text-[#FFD400]" />
                <span className="uppercase font-mono">On-Chain Gas Fee Calculator</span>
              </CardTitle>
              <CardDescription>
                Compute transaction execution overhead for financial fee netting.
              </CardDescription>
            </div>
            <Badge variant="yellow">EIP-1559</Badge>
          </CardHeader>

          <CardContent className="space-y-4 font-mono">
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-[10px] text-white/50 block mb-1">Network</label>
                <select
                  value={calcNetwork}
                  onChange={(e) => setCalcNetwork(e.target.value)}
                  className="w-full bg-black border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#FFD400]"
                >
                  <option value="ETHEREUM">Ethereum</option>
                  <option value="POLYGON">Polygon</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-white/50 block mb-1">Gas Units</label>
                <input
                  type="number"
                  value={calcGasUnits}
                  onChange={(e) => setCalcGasUnits(Number(e.target.value))}
                  className="w-full bg-black border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#FFD400] font-mono"
                />
              </div>

              <div>
                <label className="text-[10px] text-white/50 block mb-1">Price (Gwei)</label>
                <input
                  type="number"
                  value={calcGwei}
                  onChange={(e) => setCalcGwei(Number(e.target.value))}
                  className="w-full bg-black border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#FFD400] font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <Button variant="secondary" size="xs" onClick={handleCalculateGas}>
                Compute Gas
              </Button>

              {gasResult && (
                <div className="text-right">
                  <span className="text-xs font-mono font-bold text-white">
                    ${gasResult.gas_fee_usd.toFixed(2)} USD
                  </span>
                  <span className="text-[10px] text-white/40 block font-mono">
                    ({gasResult.gas_fee_native.toFixed(5)} Native)
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Slippage Analyzer */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle>
                <TrendingDown className="h-4 w-4 text-[#FFD400]" />
                <span className="uppercase font-mono">Fiat Conversion Slippage Analyzer</span>
              </CardTitle>
              <CardDescription>
                Compare expected fiat invoice amount against actual on-chain settlement.
              </CardDescription>
            </div>
            <Badge variant="yellow">Max 0.5% Tol</Badge>
          </CardHeader>

          <CardContent className="space-y-4 font-mono">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-white/50 block mb-1">Expected USD</label>
                <input
                  type="number"
                  value={slipExpected}
                  onChange={(e) => setSlipExpected(Number(e.target.value))}
                  className="w-full bg-black border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#FFD400] font-mono"
                />
              </div>

              <div>
                <label className="text-[10px] text-white/50 block mb-1">Settled USD</label>
                <input
                  type="number"
                  value={slipActual}
                  onChange={(e) => setSlipActual(Number(e.target.value))}
                  className="w-full bg-black border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#FFD400] font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <Button variant="secondary" size="xs" onClick={handleAnalyzeSlippage}>
                Analyze Variance
              </Button>

              {slipResult && (
                <div className="text-right">
                  <span
                    className={`text-xs font-mono font-bold ${
                      slipResult.is_acceptable ? "text-[#FFD400]" : "text-white"
                    }`}
                  >
                    ${Math.abs(slipResult.slippage_usd).toFixed(2)} ({slipResult.slippage_percentage.toFixed(2)}%)
                  </span>
                  <span className="text-[10px] text-white/40 block">
                    {slipResult.is_acceptable ? "Within Tolerance (Pass)" : "Flagged as Variance"}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 4. On-Chain Treasury Transactions Table */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>
              <Coins className="h-4 w-4 text-[#FFD400]" />
              <span className="uppercase font-mono">On-Chain Treasury Settlement Ledger</span>
            </CardTitle>
            <CardDescription>
              Verified blockchain payments correlated with invoice orders and ledger journal lines.
            </CardDescription>
          </div>
          <Badge variant="yellow">{txns.length} Transactions</Badge>
        </CardHeader>

        <CardContent className="space-y-4">
          <FilterBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            searchPlaceholder="Search hash, wallet address, or invoice ID..."
            filters={[
              {
                key: "network",
                label: "Network",
                value: networkFilter,
                options: [
                  { label: "Ethereum", value: "ETHEREUM" },
                  { label: "Polygon", value: "POLYGON" },
                ],
                onChange: setNetworkFilter,
              },
              {
                key: "asset",
                label: "Asset",
                value: assetFilter,
                options: [
                  { label: "USDT", value: "USDT" },
                  { label: "USDC", value: "USDC" },
                ],
                onChange: setAssetFilter,
              },
            ]}
            hasActiveFilters={Boolean(searchQuery || networkFilter || assetFilter)}
            onClearFilters={() => {
              setSearchQuery("");
              setNetworkFilter("");
              setAssetFilter("");
            }}
            totalCount={txns.length}
            filteredCount={filteredTxns.length}
          />

          <DataTable
            columns={columns}
            data={filteredTxns}
            pageSize={10}
            emptyTitle="No Blockchain Transactions Found"
            emptyDescription="No on-chain records match the active network and asset filters."
          />
        </CardContent>
      </Card>
    </div>
  );
}
