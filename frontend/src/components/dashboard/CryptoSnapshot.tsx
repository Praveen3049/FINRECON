"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, ShieldCheck, ExternalLink } from "lucide-react";

interface CryptoSnapshotProps {
  cryptoCount?: number;
  totalVolumeUsd?: number;
  networkBreakdown?: Array<{
    network: string;
    transactions: number;
    volumeUsd: number;
    asset: string;
  }>;
}

export const CryptoSnapshot: React.FC<CryptoSnapshotProps> = ({
  cryptoCount = 2,
  totalVolumeUsd = 8400.0,
  networkBreakdown = [
    { network: "ETHEREUM", transactions: 1, volumeUsd: 5000.0, asset: "USDT" },
    { network: "POLYGON", transactions: 1, volumeUsd: 3400.0, asset: "USDC" },
  ],
}) => {
  return (
    <div className="bg-[#0D0D0D] border border-white/10 rounded-xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">Crypto Treasury Snapshot</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-[#FFD400] border border-[#FFD400]/30">
                On-Chain Rail
              </span>
            </div>
            <p className="text-xs text-white/50 mt-0.5 font-mono">
              Enterprise digital asset settlement & treasury reconciliation
            </p>
          </div>

          <Link
            href="/crypto"
            className="text-xs font-mono font-semibold text-[#FFD400] hover:text-white flex items-center gap-1 transition-colors"
          >
            <span>Ledger</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Top KPIs */}
        <div className="grid grid-cols-2 gap-3 pt-2 font-mono">
          <div className="p-3 rounded-lg bg-black border border-white/10">
            <span className="text-[10px] font-medium text-white/50 uppercase block">
              Total On-Chain Volume
            </span>
            <div className="text-lg font-bold text-white font-mono mt-0.5">
              ${totalVolumeUsd.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[10px] text-[#FFD400]">USD Equivalent</span>
          </div>

          <div className="p-3 rounded-lg bg-black border border-white/10">
            <span className="text-[10px] font-medium text-white/50 uppercase block">
              Treasury Txns
            </span>
            <div className="text-lg font-bold text-white font-mono mt-0.5">
              {cryptoCount} On-Chain
            </div>
            <span className="text-[10px] text-white/80 flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-[#FFD400]" />
              100% Invoiced
            </span>
          </div>
        </div>

        {/* Network Breakdown */}
        <div className="space-y-2 pt-3 font-mono">
          <span className="text-[11px] font-semibold text-white/50 uppercase tracking-wider block">
            Blockchain Rail Allocation
          </span>
          <div className="space-y-2 text-xs">
            {networkBreakdown.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded-lg bg-black border border-white/10 hover:border-[#FFD400]/40 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#FFD400]" />
                  <div>
                    <span className="font-semibold text-white">{item.network}</span>
                    <span className="text-white/40 text-[11px] ml-1.5 font-mono">
                      ({item.asset})
                    </span>
                  </div>
                </div>
                <div className="text-right font-mono">
                  <span className="text-white font-medium">
                    ${item.volumeUsd.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-[10px] text-white/40 ml-1.5">
                    ({item.transactions} txn)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer link */}
      <div className="pt-3 border-t border-white/10 flex items-center justify-between text-xs font-mono">
        <span className="text-white/40">Supported: Ethereum &bull; Polygon &bull; Solana</span>
        <Link
          href="/crypto"
          className="text-xs text-[#FFD400] hover:text-white font-medium flex items-center gap-1"
        >
          <span>View On-Chain Wallets</span>
          <ExternalLink className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
};
