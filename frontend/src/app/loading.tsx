"use client";

import React from "react";
import { Skeleton, MetricCardSkeleton, TableSkeleton } from "@/components/ui/SkeletonLoader";

export default function Loading() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-8 animate-fadeIn">
      {/* 1. Page Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border/40">
        <div className="space-y-2">
          <div className="flex items-center gap-2.5">
            <Skeleton className="h-7 w-56 sm:w-72" />
            <Skeleton className="h-5 w-24 rounded-full" />
          </div>
          <Skeleton className="h-4 w-80 sm:w-96 max-w-full" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-9 w-28 rounded-lg" />
          <Skeleton className="h-9 w-32 rounded-lg" />
        </div>
      </div>

      {/* 2. Top Metric KPI Cards Skeleton */}
      <MetricCardSkeleton count={4} />

      {/* 3. Main Content Skeleton */}
      <TableSkeleton rows={8} columns={6} />
    </div>
  );
}
