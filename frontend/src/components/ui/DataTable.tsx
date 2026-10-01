"use client";

import React, { useState, useMemo } from "react";
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, ChevronsUpDown } from "lucide-react";
import { EmptyState } from "./EmptyState";
import { cn } from "@/lib/utils";

export interface ColumnDef<T> {
  header: string | React.ReactNode;
  accessorKey?: keyof T;
  cell?: (row: T, index: number) => React.ReactNode;
  className?: string;
  align?: "left" | "center" | "right";
  sortable?: boolean;
}

export interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  keyExtractor?: (item: T, index: number) => string | number;
  onRowClick?: (item: T) => void;
  selectedItemId?: string | number;
  pageSize?: number;
  emptyTitle?: string;
  emptyDescription?: string;
  isLoading?: boolean;
  className?: string;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data = [],
  keyExtractor,
  onRowClick,
  selectedItemId,
  pageSize = 10,
  emptyTitle = "No records found",
  emptyDescription = "There are no financial records matching the current criteria.",
  isLoading = false,
  className,
}: DataTableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState<{
    key: keyof T | null;
    direction: "asc" | "desc";
  }>({
    key: null,
    direction: "asc",
  });

  const handleSort = (key?: keyof T) => {
    if (!key) return;
    setSortConfig((prev) => {
      if (prev.key === key) {
        return {
          key,
          direction: prev.direction === "asc" ? "desc" : "asc",
        };
      }
      return { key, direction: "asc" };
    });
  };

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;
    const sorted = [...data].sort((a, b) => {
      const aVal = a[sortConfig.key as keyof T];
      const bVal = b[sortConfig.key as keyof T];
      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortConfig.direction === "asc" ? aVal - bVal : bVal - aVal;
      }
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      return sortConfig.direction === "asc"
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr);
    });
    return sorted;
  }, [data, sortConfig]);

  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  return (
    <div
      className={cn(
        "bg-card/75 border border-border/80 rounded-xl overflow-hidden shadow-sm flex flex-col",
        className
      )}
    >
      <div className="overflow-x-auto min-w-full">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-border/60 bg-secondary/30 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              {columns.map((col, idx) => {
                const isSortable = !!col.sortable && !!col.accessorKey;
                const isSorted = sortConfig.key === col.accessorKey;

                return (
                  <th
                    key={idx}
                    scope="col"
                    onClick={() => isSortable && handleSort(col.accessorKey)}
                    className={cn(
                      "p-3.5 select-none font-semibold",
                      isSortable && "cursor-pointer hover:text-white transition-colors",
                      col.align === "right" && "text-right",
                      col.align === "center" && "text-center",
                      col.className
                    )}
                  >
                    <div
                      className={cn(
                        "inline-flex items-center gap-1.5",
                        col.align === "right" && "justify-end",
                        col.align === "center" && "justify-center"
                      )}
                    >
                      <span>{col.header}</span>
                      {isSortable && (
                        <span className="text-muted-foreground shrink-0">
                          {isSorted ? (
                            sortConfig.direction === "asc" ? (
                              <ChevronUp className="h-3 w-3 text-[#FFD400]" />
                            ) : (
                              <ChevronDown className="h-3 w-3 text-[#FFD400]" />
                            )
                          ) : (
                            <ChevronsUpDown className="h-3 w-3 opacity-40 hover:opacity-100" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody className="divide-y divide-border/40">
            {isLoading ? (
              Array.from({ length: pageSize > 6 ? 6 : pageSize }).map((_, rIdx) => (
                <tr key={`skel-${rIdx}`}>
                  {columns.map((_, cIdx) => (
                    <td key={`skel-c-${cIdx}`} className="p-3.5">
                      <div className="h-4 bg-secondary/50 rounded shimmer-loading" />
                    </td>
                  ))}
                </tr>
              ))
            ) : paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="p-0">
                  <EmptyState title={emptyTitle} description={emptyDescription} />
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIdx) => {
                const key = keyExtractor ? keyExtractor(row, rowIdx) : row.id || rowIdx;
                const isSelected = selectedItemId !== undefined && selectedItemId === key;

                return (
                  <tr
                    key={key}
                    onClick={() => onRowClick && onRowClick(row)}
                    className={cn(
                      "transition-colors duration-150",
                      onRowClick && "cursor-pointer hover:bg-white/5",
                      isSelected
                        ? "bg-[#FFD400]/10 border-l-2 border-[#FFD400]"
                        : "hover:bg-white/[0.03]"
                    )}
                  >
                    {columns.map((col, colIdx) => (
                      <td
                        key={colIdx}
                        className={cn(
                          "p-3.5 text-slate-200 text-xs align-middle",
                          col.align === "right" && "text-right",
                          col.align === "center" && "text-center",
                          col.className
                        )}
                      >
                        {col.cell
                          ? col.cell(row, rowIdx)
                          : col.accessorKey
                          ? String(row[col.accessorKey] ?? "-")
                          : null}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {!isLoading && sortedData.length > pageSize && (
        <div className="p-3.5 border-t border-border/50 bg-secondary/15 flex items-center justify-between text-xs text-muted-foreground select-none">
          <span className="font-mono text-[11px]">
            Page <span className="text-white font-semibold">{currentPage}</span> of{" "}
            <span className="text-white font-semibold">{totalPages}</span> (
            {sortedData.length.toLocaleString()} items)
          </span>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded-lg border border-border/80 bg-secondary/40 hover:bg-secondary text-slate-300 hover:text-white disabled:opacity-40 disabled:pointer-events-none transition-colors"
              aria-label="Previous page"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="p-1.5 rounded-lg border border-border/80 bg-secondary/40 hover:bg-secondary text-slate-300 hover:text-white disabled:opacity-40 disabled:pointer-events-none transition-colors"
              aria-label="Next page"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
