"use client";

import React from "react";
import { Search, Filter, X } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

export interface FilterOption {
  label: string;
  value: string;
}

export interface FilterItem {
  key: string;
  label: string;
  value: string;
  options: FilterOption[];
  onChange: (value: string) => void;
}

export interface FilterBarProps {
  searchQuery?: string;
  onSearchChange?: (val: string) => void;
  searchPlaceholder?: string;
  filters?: FilterItem[];
  onClearFilters?: () => void;
  hasActiveFilters?: boolean;
  totalCount?: number;
  filteredCount?: number;
  className?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  searchQuery,
  onSearchChange,
  searchPlaceholder = "Search records, IDs, or references...",
  filters = [],
  onClearFilters,
  hasActiveFilters = false,
  totalCount,
  filteredCount,
  className,
}) => {
  return (
    <div
      className={cn(
        "p-3 rounded-xl bg-card/75 border border-border/80 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm",
        className
      )}
    >
      <div className="flex flex-1 flex-wrap items-center gap-2.5">
        {/* Search input */}
        {onSearchChange && (
          <div className="relative flex-1 min-w-[200px] sm:min-w-[260px]">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              value={searchQuery || ""}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full bg-[#111111] border border-white/10 rounded-lg pl-9 pr-8 py-1.5 text-xs text-white placeholder:text-muted-foreground focus:outline-none focus:border-[#FFD400] transition-colors"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => onSearchChange("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white"
                aria-label="Clear search"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        )}

        {/* Dropdown Filters */}
        {filters.map((f) => (
          <div key={f.key} className="relative">
            <select
              value={f.value}
              onChange={(e) => f.onChange(e.target.value)}
              className={cn(
                "bg-[#111111] border text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-[#FFD400] cursor-pointer appearance-none pr-7 transition-colors",
                f.value
                  ? "border-[#FFD400]/60 text-[#FFD400] font-medium bg-[#FFD400]/10"
                  : "border-white/10 text-slate-300 hover:border-white/20"
              )}
              aria-label={f.label}
            >
              <option value="" className="bg-black text-slate-300">
                All {f.label}s
              </option>
              {f.options.map((opt) => (
                <option
                  key={opt.value}
                  value={opt.value}
                  className="bg-black text-slate-200"
                >
                  {opt.label}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground text-[10px]">
              ▼
            </div>
          </div>
        ))}

        {/* Clear Filters Button */}
        {hasActiveFilters && onClearFilters && (
          <Button
            variant="ghost"
            size="xs"
            onClick={onClearFilters}
            className="text-muted-foreground hover:text-[#FFD400]"
            iconLeft={<X className="h-3 w-3" />}
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Record Counter */}
      {typeof totalCount === "number" && (
        <div className="text-[11px] font-mono text-muted-foreground shrink-0 self-end md:self-center">
          Showing{" "}
          <span className="text-white font-semibold">
            {typeof filteredCount === "number" ? filteredCount.toLocaleString() : totalCount.toLocaleString()}
          </span>{" "}
          of <span className="text-white font-semibold">{totalCount.toLocaleString()}</span> records
        </div>
      )}
    </div>
  );
};
