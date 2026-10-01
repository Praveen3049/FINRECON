"use client";

import React, { useEffect, useState } from "react";
import { Landmark, CreditCard, BookOpen, Receipt, Building2, ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { api, DataSourceItem } from "@/lib/api";

interface SourceBadgesProps {
  sources?: DataSourceItem[];
  entitiesCount?: number;
}

export const SourceBadges: React.FC<SourceBadgesProps> = ({ sources: propSources }) => {
  const [sources, setSources] = useState<DataSourceItem[]>(propSources || []);
  const [loading, setLoading] = useState(!propSources || propSources.length === 0);

  useEffect(() => {
    if (propSources && propSources.length > 0) {
      setSources(propSources);
      setLoading(false);
      return;
    }

    const fetchSources = async () => {
      try {
        const data = await api.getDataSources();
        if (Array.isArray(data) && data.length > 0) {
          setSources(data);
        }
      } catch (err) {
        console.error("Failed to load data sources in SourceBadges:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSources();
  }, [propSources]);

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType.toUpperCase()) {
      case "BANK":
        return <Landmark className="h-4 w-4 text-[#FFD400]" />;
      case "PAYMENT_GATEWAY":
        return <CreditCard className="h-4 w-4 text-[#FFD400]" />;
      case "INVOICE":
        return <Receipt className="h-4 w-4 text-white" />;
      case "ACCOUNTING":
        return <BookOpen className="h-4 w-4 text-white/80" />;
      default:
        return <Building2 className="h-4 w-4 text-[#FFD400]" />;
    }
  };

  return (
    <div className="bg-[#0D0D0D] border border-white/10 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">Aczen Nova Books & Feed Ingestion</h3>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono font-medium bg-[#FFD400]/10 text-[#FFD400] border border-[#FFD400]/30 px-2 py-0.5 rounded-full">
              <CheckCircle2 className="h-3 w-3" />
              API Key Live
            </span>
          </div>
          <p className="text-xs text-white/50 mt-0.5 font-mono">
            Active corporate financial ledgers pulled directly from Aczen Nova REST endpoints
          </p>
        </div>
        <Link
          href="/ingestion"
          className="text-xs text-[#FFD400] hover:text-white flex items-center space-x-1 font-mono font-medium"
        >
          <span>Sync & Settings</span>
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-3 font-mono">
        {loading ? (
          <div className="col-span-full py-4 text-center text-xs text-white/40">
            Loading live feeds from Aczen API...
          </div>
        ) : (
          sources.map((source) => (
            <div
              key={source.id || source.source_type}
              className="border border-white/10 bg-black rounded-lg p-3 hover:border-[#FFD400]/40 transition-all hover:scale-[1.01]"
            >
              <div className="flex items-center justify-between">
                {getSourceIcon(source.source_type)}
                <span className="text-[10px] font-mono text-[#FFD400] bg-[#FFD400]/10 px-1.5 py-0.5 rounded border border-[#FFD400]/30">
                  NOVA API
                </span>
              </div>
              <div className="mt-2.5">
                <div className="text-xs font-semibold text-white truncate" title={source.name}>
                  {source.name.replace("Aczen ", "")}
                </div>
                <div className="text-base font-bold text-white mt-0.5 flex items-baseline gap-1">
                  <span>{(source.records_count || 0).toLocaleString()}</span>
                  <span className="text-[10px] font-normal text-white/40">records</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
