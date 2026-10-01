"use client";

import React from "react";
import { cn } from "@/lib/utils";

export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => {
  return (
    <div
      className={cn("shimmer-loading rounded-md bg-secondary/40", className)}
      {...props}
    />
  );
};

export const MetricCardSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-card/75 border border-border/80 rounded-xl p-5 shadow-sm space-y-3"
        >
          <div className="flex items-center justify-between">
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-7 w-7 rounded-lg" />
          </div>
          <Skeleton className="h-8 w-24" />
          <div className="pt-2 border-t border-border/40 flex items-center justify-between">
            <Skeleton className="h-3 w-32" />
            <Skeleton className="h-4 w-12 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
};

export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 5,
}) => {
  return (
    <div className="bg-card/75 border border-border/80 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-border/50 flex items-center justify-between">
        <Skeleton className="h-4 w-36" />
        <Skeleton className="h-8 w-48 rounded-lg" />
      </div>
      <div className="divide-y divide-border/40">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="p-3.5 flex items-center gap-4">
            {Array.from({ length: columns }).map((_, c) => (
              <Skeleton
                key={c}
                className={cn("h-4", c === 0 ? "w-32" : c === 1 ? "w-24" : "flex-1")}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 280 }) => {
  return (
    <div className="bg-card/75 border border-border/80 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-border/40">
        <div className="space-y-1">
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-3 w-56" />
        </div>
        <Skeleton className="h-8 w-40 rounded-lg" />
      </div>
      <div style={{ height }} className="w-full flex items-end gap-3 pt-6 px-4">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="flex-1 flex flex-col justify-end gap-2 h-full">
            <Skeleton
              className="w-full rounded-t-lg"
              style={{ height: `${30 + ((i * 17) % 65)}%` }}
            />
            <Skeleton className="h-3 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
};

export const CardSkeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div
      className={cn(
        "bg-card/75 border border-border/80 rounded-xl p-5 shadow-sm space-y-4",
        className
      )}
    >
      <div className="flex items-center justify-between pb-3 border-b border-border/40">
        <div className="space-y-1">
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-3 w-56" />
        </div>
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      <Skeleton className="h-44 w-full rounded-lg" />
    </div>
  );
};

