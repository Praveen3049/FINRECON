"use client";

import React, { useEffect, useCallback } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  children: React.ReactNode;
  footerActions?: React.ReactNode;
  width?: "md" | "lg" | "xl" | "2xl";
  className?: string;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  badge,
  children,
  footerActions,
  width = "xl",
  className,
}) => {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const widthClass = {
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "2xl": "max-w-2xl",
  }[width];

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Body sliding from right */}
      <div
        className={cn(
          "relative w-full h-screen bg-card border-l border-border/90 shadow-2xl z-10 flex flex-col justify-between overflow-hidden animate-fade-in",
          widthClass,
          className
        )}
      >
        {/* Header */}
        <div className="h-16 px-6 border-b border-border/50 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5 truncate">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-white tracking-tight truncate">
                  {title}
                </h3>
                {badge}
              </div>
              {subtitle && (
                <p className="text-[11px] text-muted-foreground truncate mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-white hover:bg-secondary/60 transition-colors"
            aria-label="Close investigation drawer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">{children}</div>

        {/* Footer */}
        {footerActions && (
          <div className="p-4 px-6 border-t border-border/50 bg-secondary/20 flex items-center justify-between shrink-0">
            {footerActions}
          </div>
        )}
      </div>
    </div>
  );
};
