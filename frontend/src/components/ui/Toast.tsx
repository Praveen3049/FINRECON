"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "warning" | "error" | "info";

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextValue {
  toast: (item: Omit<ToastItem, "id">) => void;
  success: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    ({ type, title, message, duration = 4000 }: Omit<ToastItem, "id">) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastItem = { id, type, title, message, duration };
      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = useCallback(
    (title: string, message?: string) => toast({ type: "success", title, message }),
    [toast]
  );
  const warning = useCallback(
    (title: string, message?: string) => toast({ type: "warning", title, message }),
    [toast]
  );
  const error = useCallback(
    (title: string, message?: string) => toast({ type: "error", title, message }),
    [toast]
  );
  const info = useCallback(
    (title: string, message?: string) => toast({ type: "info", title, message }),
    [toast]
  );

  return (
    <ToastContext.Provider value={{ toast, success, warning, error, info, removeToast }}>
      {children}
      {/* Toast Render Container */}
      <div
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none"
        aria-live="polite"
      >
        {toasts.map((t) => {
          const config = {
            success: {
              icon: CheckCircle2,
              color: "text-[#FFD400]",
              bg: "bg-[#0D0D0D] border-[#FFD400]/40 text-white",
            },
            warning: {
              icon: AlertTriangle,
              color: "text-[#FFD400]",
              bg: "bg-[#0D0D0D] border-[#FFD400]/50 text-white",
            },
            error: {
              icon: XCircle,
              color: "text-white",
              bg: "bg-[#0D0D0D] border-[#FFD400]/60 text-white",
            },
            info: {
              icon: Info,
              color: "text-white",
              bg: "bg-[#0D0D0D] border-white/20 text-white",
            },
          }[t.type];

          const IconComponent = config.icon;

          return (
            <div
              key={t.id}
              className={cn(
                "pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border bg-card/95 backdrop-blur-md shadow-2xl transition-all duration-200 animate-fade-in",
                config.bg
              )}
            >
              <IconComponent className={cn("h-5 w-5 shrink-0 mt-0.5", config.color)} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-white tracking-tight">{t.title}</p>
                {t.message && (
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
                    {t.message}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={() => removeToast(t.id)}
                className="text-muted-foreground hover:text-white p-1 rounded-md transition-colors"
                aria-label="Dismiss notification"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
