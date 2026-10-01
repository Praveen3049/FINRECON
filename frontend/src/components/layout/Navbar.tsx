"use client";

import React from "react";
import { Activity, Menu, LogOut, User as UserIcon } from "lucide-react";
import { useAuth } from "@/lib/AuthContext";
import { useInstantNav } from "./NavigationContext";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

interface NavbarProps {
  onToggleMobileSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobileSidebar }) => {
  const { user, logout } = useAuth();
  const { navigateTo } = useInstantNav();
  const { info } = useToast();

  const handleLogout = async () => {
    await logout();
    info("Signed Out", "Your session has been terminated.");
    navigateTo("/login");
  };

  return (
    <header className="h-16 border-b border-white/10 bg-[#000000] px-4 sm:px-6 flex items-center justify-between shrink-0 z-20 select-none">
      <div className="flex items-center space-x-3">
        {/* Mobile Hamburger Menu Toggle */}
        {onToggleMobileSidebar && (
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="md:hidden p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Toggle navigation drawer"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}

        {/* Mobile Brand */}
        <div className="flex items-center space-x-2 md:hidden">
          <div className="h-8 w-8 rounded-lg bg-black border border-[#FFD400]/40 flex items-center justify-center shrink-0">
            <Activity className="h-4 w-4 text-[#FFD400]" />
          </div>
          <span className="font-bold text-base text-white">FinRecon</span>
          <span className="text-[10px] font-mono uppercase bg-[#FFD400]/15 text-[#FFD400] px-1.5 py-0.5 rounded border border-[#FFD400]/30 font-semibold">
            PRO
          </span>
        </div>

        {/* Desktop Breadcrumb / Console Context */}
        <div className="hidden md:flex items-center space-x-3">
          <div className="h-2 w-2 rounded-full bg-[#FFD400] animate-pulse" />
        </div>
      </div>

      {/* Right Side: Authenticated User Profile & Role Display */}
      {user && (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5 text-right">
            <div className="hidden sm:block">
              <div className="text-xs font-semibold text-white leading-tight">
                {user.name}
              </div>
              <div className="text-[11px] text-white/50 font-mono leading-tight">
                {user.email}
              </div>
            </div>
            <span className="font-mono text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded border border-[#FFD400]/40 bg-[#FFD400]/15 text-[#FFD400]">
              {user.role}
            </span>
          </div>

          <div className="h-4 w-px bg-white/15 hidden sm:block" />

          {/* Logout Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            iconLeft={<LogOut className="h-3.5 w-3.5 text-white/60 hover:text-[#FFD400] transition-colors" />}
            className="text-xs text-white/70 hover:text-white"
          >
            <span className="hidden sm:inline">Sign Out</span>
          </Button>
        </div>
      )}
    </header>
  );
};
