"use client";

import React, { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";
import { Activity } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { ToastProvider } from "@/components/ui/Toast";
import { NavigationContext } from "@/components/layout/NavigationContext";
import { AuthProvider, useAuth } from "@/lib/AuthContext";
import { AccessDenied } from "@/components/layout/AccessDenied";

// Direct component imports for instant 0ms routing
import DashboardPage from "@/app/page";
import LoginPage from "@/app/login/page";
import IngestionPage from "@/app/ingestion/page";
import EntityResolutionPage from "@/app/entities/page";
import ReconciliationPage from "@/app/reconciliation/page";
import ExceptionsPage from "@/app/exceptions/page";
import CryptoPage from "@/app/crypto/page";
import AuditPage from "@/app/audit/page";
import AiAssistantPage from "@/app/ai-assistant/page";
import LandingPage from "@/app/home/LandingPage";

const VIEW_MAP: Record<string, React.ComponentType> = {
  "/": DashboardPage,
  "/login": LoginPage,
  "/ingestion": IngestionPage,
  "/entities": EntityResolutionPage,
  "/reconciliation": ReconciliationPage,
  "/exceptions": ExceptionsPage,
  "/crypto": CryptoPage,
  "/audit": AuditPage,
  "/ai-assistant": AiAssistantPage,
};

interface AppShellProps {
  children: React.ReactNode;
}

const AppShellInternal: React.FC<AppShellProps> = ({ children }) => {
  const nextPathname = usePathname();
  const { user, isAuthenticated, isLoading, canAccessRoute } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [currentPath, setCurrentPath] = useState<string>(nextPathname || "/");
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    if (typeof window !== "undefined") {
      setCurrentPath(window.location.pathname || nextPathname || "/");
    }
  }, [nextPathname]);

  const navigateTo = useCallback((href: string) => {
    if (typeof window !== "undefined") {
      if (window.location.pathname !== href) {
        window.history.pushState(null, "", href);
      }
      setCurrentPath(href);
      const scrollEl = document.getElementById("main-content-scroll");
      if (scrollEl) {
        scrollEl.scrollTop = 0;
      }
    }
  }, []);

  // Handle browser Back / Forward buttons
  useEffect(() => {
    const handlePopState = () => {
      if (typeof window !== "undefined") {
        setCurrentPath(window.location.pathname);
      }
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Global click interceptor for instant navigation on all internal links
  useEffect(() => {
    const handleGlobalClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) {
        return;
      }
      const target = (e.target as HTMLElement).closest("a");
      if (!target) return;
      const href = target.getAttribute("href");
      if (
        href &&
        href.startsWith("/") &&
        !href.startsWith("//") &&
        !target.getAttribute("target") &&
        !target.getAttribute("download")
      ) {
        if (VIEW_MAP[href] !== undefined) {
          e.preventDefault();
          navigateTo(href);
        }
      }
    };

    document.addEventListener("click", handleGlobalClick, { capture: true });
    return () => document.removeEventListener("click", handleGlobalClick, { capture: true });
  }, [navigateTo]);

  // Handle authenticated redirect from /login to /
  useEffect(() => {
    if (isAuthenticated && currentPath === "/login") {
      navigateTo("/");
    }
  }, [isAuthenticated, currentPath, navigateTo]);

  // 1. Initial Authentication Check Loading State
  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-[#000000] flex flex-col items-center justify-center space-y-4 select-none">
        <div className="h-12 w-12 rounded-xl bg-[#FFD400] flex items-center justify-center shadow-lg shadow-[#FFD400]/20 animate-pulse">
          <Activity className="h-6 w-6 text-black" />
        </div>
        <div className="text-center space-y-1">
          <p className="text-sm font-semibold text-white tracking-tight">FinRecon Enterprise</p>
          <p className="text-xs text-muted-foreground font-mono">Verifying authenticated session...</p>
        </div>
      </div>
    );
  }

  // 2. Unauthenticated: Show Landing Page on "/" or Login Page on "/login"
  if (!isAuthenticated) {
    // If on root path, show the public landing page
    if (currentPath === "/" || currentPath === "") {
      return <LandingPage />;
    }
    // For any other path (including /login), show login
    return (
      <NavigationContext.Provider value={{ currentPath: "/login", navigateTo }}>
        <ToastProvider>
          <LoginPage />
        </ToastProvider>
      </NavigationContext.Provider>
    );
  }

  // 3. Authenticated: Check Role Route Permissions
  const effectivePath = currentPath === "/login" ? "/" : currentPath;
  const isAllowed = canAccessRoute(effectivePath);
  const ActiveComponent = isAllowed && isClient ? VIEW_MAP[effectivePath] : null;

  return (
    <NavigationContext.Provider value={{ currentPath, navigateTo }}>
      <ToastProvider>
        <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
          {/* 1. Stationary Left Sidebar (fixed, viewport height 100vh) */}
          <Sidebar
            mobileOpen={mobileSidebarOpen}
            onCloseMobile={() => setMobileSidebarOpen(false)}
          />

          {/* 2. Main Layout Area */}
          <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
            {/* Stationary Top Header */}
            <Navbar onToggleMobileSidebar={() => setMobileSidebarOpen((prev) => !prev)} />

            {/* Sole scrollable container */}
            <main
              id="main-content-scroll"
              className="flex-1 overflow-y-auto min-h-0 p-4 sm:p-6 lg:p-8 bg-[#000000]"
            >
              {isAllowed ? (
                ActiveComponent ? <ActiveComponent /> : children
              ) : (
                <AccessDenied attemptedPath={currentPath} />
              )}
            </main>
          </div>
        </div>
      </ToastProvider>
    </NavigationContext.Provider>
  );
};

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <AuthProvider>
      <AppShellInternal>{children}</AppShellInternal>
    </AuthProvider>
  );
};
