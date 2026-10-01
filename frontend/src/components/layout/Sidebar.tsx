"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UploadCloud,
  FileSpreadsheet,
  AlertTriangle,
  Coins,
  History,
  Bot,
  Building2,
  Activity,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useInstantNav } from "./NavigationContext";
import { useAuth } from "@/lib/AuthContext";

const NAV_ITEMS = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
    badge: null,
  },
  {
    name: "Data Ingestion",
    href: "/ingestion",
    icon: UploadCloud,
    badge: "",
  },
  {
    name: "Entity Resolution",
    href: "/entities",
    icon: Building2,
    badge: "",
  },
  {
    name: "Reconciliation",
    href: "/reconciliation",
    icon: FileSpreadsheet,
    badge: null,
  },
  {
    name: "Exception Workbench",
    href: "/exceptions",
    icon: AlertTriangle,
    badge: "",
  },
  {
    name: "Crypto Ledger",
    href: "/crypto",
    icon: Coins,
    badge: "",
  },
  {
    name: "Audit Trail",
    href: "/audit",
    icon: History,
    badge: null,
  },
  {
    name: "AI Assistant",
    href: "/ai-assistant",
    icon: Bot,
    badge: "",
  },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen = false, onCloseMobile }) => {
  const pathname = usePathname();
  const { currentPath, navigateTo } = useInstantNav();
  const { user, canAccessRoute } = useAuth();
  const activeRoute = currentPath || pathname;

  const visibleNavItems = React.useMemo(() => {
    return NAV_ITEMS.filter((item) => canAccessRoute(item.href));
  }, [canAccessRoute]);

  const sidebarContent = (
    <aside
      className={cn(
        "w-64 h-screen border-r border-white/10 bg-[#080808] text-white flex flex-col justify-between shrink-0 overflow-hidden select-none",
        mobileOpen
          ? "fixed inset-y-0 left-0 z-50 shadow-2xl bg-[#080808] transition-transform duration-200"
          : "hidden md:flex static z-auto"
      )}
    >
      {/* 1. Header / Brand Top Bar */}
      <div className="h-16 border-b border-white/10 px-5 flex items-center justify-between shrink-0 bg-[#000000]">
        <Link
          href="/"
          className="flex items-center space-x-3 group"
          onClick={(e) => {
            e.preventDefault();
            if (onCloseMobile) onCloseMobile();
            navigateTo("/");
          }}
        >
          <div className="h-9 w-9 rounded-lg bg-black border border-[#FFD400]/40 flex items-center justify-center shrink-0 shadow-sm transition-transform group-hover:scale-105">
            <Activity className="h-5 w-5 text-[#FFD400]" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight text-white">
              FinRecon
            </span>
          </div>
        </Link>

        {/* Mobile close button */}
        {onCloseMobile && (
          <button
            type="button"
            onClick={onCloseMobile}
            className="md:hidden p-1.5 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* 2. Scrollable Navigation List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold text-white/40 uppercase tracking-widest font-mono">
          Reconciliation Core
        </div>
        <nav className="space-y-1">
          {visibleNavItems.map((item) => {
            const isActive = activeRoute === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                prefetch={true}
                onClick={(e) => {
                  e.preventDefault();
                  if (onCloseMobile) onCloseMobile();
                  navigateTo(item.href);
                }}
                className={cn(
                  "flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group",
                  isActive
                    ? "bg-white/[0.08] text-white border-l-2 border-[#FFD400] pl-2.5 font-semibold"
                    : "text-white/60 hover:bg-white/[0.04] hover:text-white"
                )}
              >
                <div className="flex items-center space-x-3">
                  <item.icon
                    className={cn(
                      "h-4 w-4 transition-colors",
                      isActive
                        ? "text-[#FFD400]"
                        : "text-white/40 group-hover:text-white"
                    )}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded border font-mono select-none",
                      isActive
                        ? "bg-[#FFD400]/20 text-[#FFD400] border-[#FFD400]/30 font-semibold"
                        : "bg-white/5 text-white/60 border-white/10"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* 3. Stationary Bottom Status / Role Card */}
      <div className="p-3 border-t border-white/10 shrink-0 bg-[#000000]">
        <div className="bg-[#0D0D0D] rounded-xl p-3 border border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-white">
              <span className="h-2 w-2 rounded-full bg-[#FFD400] animate-pulse"></span>
              <span>
                {user?.role === "AUDITOR"
                  ? "Audit Read-Only"
                  : user?.role === "MANAGER"
                  ? "Executive Oversight"
                  : "Deterministic Engine"}
              </span>
            </div>
            {user && (
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#FFD400]/15 text-[#FFD400] border border-[#FFD400]/30 font-semibold">
                {user.role}
              </span>
            )}
          </div>
          <p className="text-[11px] text-white/50 mt-1 font-mono leading-relaxed">
            {user?.role === "AUDITOR"
              ? "Read-only verification & SHA-256 chain inspection active."
              : user?.role === "MANAGER"
              ? "Reconciliation metrics, variance oversight, and audit logs."
              : "Zero-drift 7-pass rule matcher active."}
          </p>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 md:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}
      {sidebarContent}
    </>
  );
};
