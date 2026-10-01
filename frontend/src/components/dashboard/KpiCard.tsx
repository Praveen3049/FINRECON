"use client";

import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  change,
  changeType = "neutral",
  subtitle,
  icon: Icon,
  iconColor = "text-[#FFD400]",
  iconBg = "bg-[#FFD400]/10 border border-[#FFD400]/20",
}) => {
  return (
    <div className="bg-[#0D0D0D] border border-white/10 rounded-xl p-5 shadow-sm hover:border-[#FFD400]/40 transition-all">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono uppercase tracking-wider text-white/50">{title}</span>
        <div className={cn("p-2 rounded-lg", iconBg)}>
          <Icon className={cn("h-4 w-4", iconColor)} />
        </div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-white font-mono">{value}</div>
        <div className="flex items-center space-x-2 mt-1">
          {change && (
            <span
              className={cn(
                "text-xs font-mono font-medium",
                changeType === "positive" && "text-[#FFD400]",
                changeType === "negative" && "text-white/70",
                changeType === "neutral" && "text-white/40"
              )}
            >
              {change}
            </span>
          )}
          {subtitle && <span className="text-xs text-white/40">{subtitle}</span>}
        </div>
      </div>
    </div>
  );
};
