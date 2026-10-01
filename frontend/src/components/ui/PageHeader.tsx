"use client";

import React from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

export interface PageHeaderProps {
  title: string;
  subtitle: string;
  badge?: {
    text: string;
    variant?: "success" | "warning" | "info" | "crypto" | "neutral" | "yellow";
    pulse?: boolean;
  };
  primaryAction?: {
    label: string;
    onClick: () => void;
    isLoading?: boolean;
    icon?: React.ReactNode;
    variant?: "primary" | "success" | "destructive";
    disabled?: boolean;
  };
  secondaryActions?: React.ReactNode;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  lastUpdated?: string;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  badge,
  primaryAction,
  secondaryActions,
  onRefresh,
  isRefreshing = false,
  lastUpdated,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border/40",
        className
      )}
    >
      <div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">{title}</h1>
          {badge && (
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border font-mono select-none",
                badge.variant === "warning" || badge.variant === "crypto" || badge.variant === "yellow"
                  ? "bg-[#FFD400]/15 text-[#FFD400] border-[#FFD400]/30"
                  : "bg-white/10 text-white border-white/20"
              )}
            >
              {badge.pulse && (
                <span className="h-1.5 w-1.5 rounded-full bg-[#FFD400] animate-pulse" />
              )}
              {badge.text}
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1 max-w-3xl leading-relaxed">{subtitle}</p>
      </div>

      <div className="flex items-center gap-2.5 self-start sm:self-auto shrink-0 flex-wrap">
        {lastUpdated && (
          <span className="text-[11px] font-mono text-muted-foreground mr-1 hidden lg:inline-block">
            Updated {lastUpdated}
          </span>
        )}

        {onRefresh && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh latest records from backend database"
            iconLeft={<RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin text-[#FFD400]")} />}
          >
            Refresh
          </Button>
        )}

        {secondaryActions}

        {primaryAction && (
          <Button
            variant={primaryAction.variant || "primary"}
            size="sm"
            onClick={primaryAction.onClick}
            isLoading={primaryAction.isLoading}
            disabled={primaryAction.disabled}
            iconLeft={primaryAction.icon}
          >
            {primaryAction.label}
          </Button>
        )}
      </div>
    </div>
  );
};
