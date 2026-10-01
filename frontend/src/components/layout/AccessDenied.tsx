"use client";

import React from "react";
import { ShieldAlert, ArrowLeft, Lock, UserCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useAuth, ROUTE_TITLES } from "@/lib/AuthContext";
import { useInstantNav } from "./NavigationContext";

interface AccessDeniedProps {
  attemptedPath: string;
}

export const AccessDenied: React.FC<AccessDeniedProps> = ({ attemptedPath }) => {
  const { user } = useAuth();
  const { navigateTo } = useInstantNav();

  const routeName = ROUTE_TITLES[attemptedPath] || attemptedPath;

  const getRoleBadgeVariant = (role?: string) => {
    switch (role) {
      case "USER":
        return "info";
      case "AUDITOR":
        return "success";
      case "MANAGER":
        return "neutral";
      default:
        return "neutral";
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-card border border-border/80 rounded-2xl p-8 shadow-2xl text-center relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-48 h-48 bg-[#FFD400]/10 rounded-full blur-3xl pointer-events-none" />

        {/* Shield Icon */}
        <div className="h-16 w-16 mx-auto rounded-2xl bg-[#000000] border border-[#FFD400]/40 flex items-center justify-center text-[#FFD400] mb-6 shadow-lg shadow-[#FFD400]/10">
          <ShieldAlert className="h-8 w-8" />
        </div>

        <div className="space-y-2 mb-6">
          <div className="flex items-center justify-center gap-2">
            <span className="font-mono text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded border border-[#FFD400] bg-[#FFD400] text-black">
              HTTP 403
            </span>
            <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
              Role Access Control
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Access Denied
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed">
            You do not have authorization to access the{" "}
            <span className="text-white font-semibold font-mono">{routeName}</span>{" "}
            module.
          </p>
        </div>

        {/* Identity & Role Context Box */}
        {user && (
          <div className="bg-[#111111] border border-white/10 rounded-xl p-4 mb-6 text-left space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground flex items-center gap-1.5">
                <UserCheck className="h-3.5 w-3.5 text-[#FFD400]" />
                Signed In As:
              </span>
              <span className="font-semibold text-white">{user.name}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Active Role:</span>
              <span className="font-mono text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded border border-[#FFD400]/40 bg-[#FFD400]/15 text-[#FFD400]">
                {user.role}
              </span>
            </div>
            <div className="pt-2 border-t border-border/40 text-[11px] text-muted-foreground leading-normal">
              {user.role === "USER" && (
                <span>
                  The <strong>USER</strong> role has access to CSV Data Ingestion, Crypto Ledger, and AI Copilot. Discrepancy Exception Investigation, Multi-Pass Reconciliation, and Entity Resolution require <strong>AUDITOR</strong> or <strong>MANAGER</strong> credentials.
                </span>
              )}
              {user.role === "AUDITOR" && (
                <span>
                  The <strong>AUDITOR</strong> role has access to Reconciliation, Exception Investigation Workbench (evaluating variances, duplicate/missing entries, and resolving or escalating to management), Crypto Ledger, and Cryptographic Audit Trail. Raw file ingestion and entity administration are restricted.
                </span>
              )}
              {user.role === "MANAGER" && (
                <span>
                  The <strong>MANAGER</strong> role possesses unrestricted supervisory access across the entire platform, including task delegation to compliance auditors.
                </span>
              )}
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <Button
            variant="primary"
            className="w-full"
            iconLeft={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigateTo("/")}
          >
            Return to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
};
