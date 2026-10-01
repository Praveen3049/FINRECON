"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Upload,
  Layers,
  Users,
  GitMerge,
  Search,
  AlertTriangle,
  Coins,
  Shield,
  Clock,
  BarChart3,
  CheckCircle2,
  Eye,
  FileText,
  Lock,
  Menu,
  X,
  ChevronRight,
  Zap,
  Database,
  Bot,
  Fingerprint,
  Scale,
  ArrowUpRight,
  Check,
} from "lucide-react";

/* ─────────────────────── Scroll Reveal Hook ─────────────────────── */

function useScrollReveal(threshold = 0.15) {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          obs.unobserve(el);
        }
      },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);

  return { ref, isVisible };
}

function RevealSection({
  children,
  className = "",
  delay = "",
}: {
  children: React.ReactNode;
  className?: string;
  delay?: string;
}) {
  const { ref, isVisible } = useScrollReveal();
  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ease-out ${delay} ${
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
      } ${className}`}
    >
      {children}
    </div>
  );
}

/* ─────────────────────── Animated Counter ─────────────────────── */

function AnimatedNumber({ target, suffix = "" }: { target: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const { ref, isVisible } = useScrollReveal();

  useEffect(() => {
    if (!isVisible) return;
    let start = 0;
    const duration = 1400;
    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [isVisible, target]);

  return (
    <span ref={ref}>
      {count.toLocaleString()}
      {suffix}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  FINRECON ENTERPRISE HOMEPAGE — BLACK, WHITE & YELLOW (#FFD400)      */
/* ═══════════════════════════════════════════════════════════════════ */

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const el = document.getElementById("landing-scroll");
    if (!el) return;
    const handler = () => setScrolled(el.scrollTop > 30);
    el.addEventListener("scroll", handler, { passive: true });
    return () => el.removeEventListener("scroll", handler);
  }, []);

  const scrollToSection = useCallback((id: string) => {
    setMobileMenuOpen(false);
    const el = document.getElementById(id);
    const container = document.getElementById("landing-scroll");
    if (el && container) {
      const top = el.offsetTop - 75;
      container.scrollTo({ top, behavior: "smooth" });
    }
  }, []);

  const NAV_LINKS = [
    { label: "Platform", id: "platform" },
    { label: "Solutions", id: "solutions" },
    { label: "How It Works", id: "how-it-works" },
    { label: "Features", id: "features" },
    { label: "Resources", id: "resources" },
  ];

  return (
    <div
      id="landing-scroll"
      className="h-screen w-screen overflow-y-auto bg-[#000000] text-white selection:bg-[#FFD400] selection:text-black font-sans scroll-smooth"
    >
      {/* ═══════ 1. STICKY PUBLIC NAVBAR ═══════ */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-[#080808]/90 backdrop-blur-md border-b border-white/10"
            : "bg-transparent border-b border-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 flex items-center justify-between h-16 sm:h-20">
          {/* Brand */}
          <div className="flex items-center gap-3 select-none">
            <div className="h-8 w-8 rounded-lg bg-black border border-[#FFD400]/40 flex items-center justify-center shadow-sm">
              <Activity className="h-4 w-4 text-[#FFD400]" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              FINRECON
            </span>
            <span className="hidden sm:inline-block text-[10px] font-mono uppercase bg-[#FFD400]/15 text-[#FFD400] px-2 py-0.5 rounded border border-[#FFD400]/30 font-semibold">
              INFRASTRUCTURE
            </span>
          </div>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((l) => (
              <button
                key={l.id}
                type="button"
                onClick={() => scrollToSection(l.id)}
                className="text-xs uppercase tracking-wider font-mono font-medium text-white/70 hover:text-[#FFD400] transition-colors"
              >
                {l.label}
              </button>
            ))}
          </div>

          {/* Right Action CTAs */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              href="/login"
              className="text-xs uppercase tracking-wider font-mono font-semibold text-white/80 hover:text-white px-3 py-2 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/login"
              className="text-xs uppercase tracking-wider font-mono font-bold bg-[#FFD400] hover:bg-[#E6BE00] text-black px-4 py-2.5 rounded-lg shadow-md shadow-[#FFD400]/20 transition-all duration-150 flex items-center gap-1.5"
            >
              <span>Get Started</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-white/80 hover:text-white p-2"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Nav Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#080808] border-b border-white/10 px-6 py-6 space-y-4 animate-fade-in">
            {NAV_LINKS.map((l) => (
              <button
                key={l.id}
                type="button"
                onClick={() => scrollToSection(l.id)}
                className="block w-full text-left text-xs uppercase font-mono tracking-wider text-white/70 hover:text-[#FFD400] py-2"
              >
                {l.label}
              </button>
            ))}
            <div className="pt-4 border-t border-white/10 space-y-3">
              <Link
                href="/login"
                className="block text-xs uppercase font-mono tracking-wider text-white/80 hover:text-white py-2"
              >
                Sign In
              </Link>
              <Link
                href="/login"
                className="block text-center text-xs uppercase font-mono font-bold bg-[#FFD400] text-black px-4 py-2.5 rounded-lg"
              >
                Get Started →
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* ═══════ 2. HERO SECTION ═══════ */}
      <section className="min-h-screen flex flex-col justify-center px-6 sm:px-8 lg:px-12 pt-28 pb-16 relative">
        <div className="max-w-7xl mx-auto w-full">
          <RevealSection className="max-w-4xl">
            {/* Live Status Pill */}
            <div className="inline-flex items-center gap-2 border border-white/10 bg-[#0D0D0D] rounded-full px-3.5 py-1 text-xs font-mono font-medium text-white/80 mb-6">
              <span className="h-2 w-2 rounded-full bg-[#FFD400] animate-pulse" />
              <span className="tracking-wider uppercase">
                ENTERPRISE RECONCILIATION INFRASTRUCTURE
              </span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] text-white uppercase">
              RECONCILE EVERY<br />
              <span className="text-[#FFD400]">FINANCIAL RECORD.</span><br />
              INVESTIGATE EVERY<br />
              <span className="text-white/40">EXCEPTION.</span>
            </h1>

            {/* Supporting Text */}
            <p className="mt-8 text-base sm:text-lg text-white/70 max-w-2xl leading-relaxed">
              FinRecon brings bank transactions, payment gateways, accounting records,
              invoices, and blockchain transactions into one intelligent reconciliation platform.
            </p>

            {/* Hero CTAs */}
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Link
                href="/login"
                className="bg-[#FFD400] hover:bg-[#E6BE00] text-black px-7 py-3.5 rounded-xl font-bold text-xs uppercase tracking-wider font-mono shadow-lg shadow-[#FFD400]/20 transition-all flex items-center gap-2 group"
              >
                <span>GET STARTED</span>
                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <button
                type="button"
                onClick={() => scrollToSection("platform")}
                className="border border-white/20 hover:border-white/40 bg-white/5 hover:bg-white/10 text-white px-7 py-3.5 rounded-xl font-semibold text-xs uppercase tracking-wider font-mono transition-all flex items-center gap-2"
              >
                <span>EXPLORE PLATFORM</span>
                <ChevronRight className="h-4 w-4 text-[#FFD400]" />
              </button>
            </div>
          </RevealSection>

          {/* ═══════ HERO RECONCILIATION FLOW VISUAL ═══════ */}
          <RevealSection className="mt-16 sm:mt-20 w-full" delay="delay-200">
            <div className="border border-white/10 rounded-2xl bg-[#080808] p-6 sm:p-10 shadow-2xl relative overflow-hidden">
              {/* Subtle yellow ambient blur */}
              <div className="absolute top-0 right-1/4 w-96 h-96 bg-[#FFD400]/5 rounded-full blur-3xl pointer-events-none" />

              <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-8 items-center">
                {/* 1. Feed Ingestion Column */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-[11px] font-mono uppercase tracking-widest text-[#FFD400] font-semibold">
                      01 • DATA SOURCES
                    </p>
                    <span className="text-[10px] font-mono text-white/40">5 Active</span>
                  </div>
                  {[
                    { label: "BANK STATEMENTS", type: "HDFC / SBI / ICICI", icon: Database },
                    { label: "PAYMENT GATEWAY", type: "Stripe / Razorpay", icon: Zap },
                    { label: "ACCOUNTING / ERP", type: "General Ledger", icon: FileText },
                    { label: "INVOICES & BILLING", type: "Accounts Receivable", icon: Layers },
                    { label: "CRYPTO LEDGERS", type: "ETH / Polygon / USDC", icon: Coins },
                  ].map((s) => (
                    <div
                      key={s.label}
                      className="flex items-center justify-between border border-white/10 rounded-xl px-4 py-3 bg-[#0D0D0D] hover:border-white/20 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <s.icon className="h-4 w-4 text-[#FFD400] shrink-0" />
                        <span className="text-xs font-mono font-semibold text-white truncate">
                          {s.label}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-white/40 truncate ml-2">
                        {s.type}
                      </span>
                    </div>
                  ))}
                </div>

                {/* 2. Central Engine Visual */}
                <div className="flex flex-col items-center gap-3 py-4 select-none">
                  <div className="hidden md:block w-px h-8 bg-gradient-to-b from-transparent via-[#FFD400]/60 to-[#FFD400]" />
                  <div className="border-2 border-[#FFD400] rounded-2xl p-5 text-center bg-black shadow-xl shadow-[#FFD400]/10 max-w-[200px]">
                    <div className="h-10 w-10 mx-auto rounded-xl bg-[#FFD400]/15 border border-[#FFD400]/30 flex items-center justify-center mb-2">
                      <Activity className="h-5 w-5 text-[#FFD400] animate-pulse" />
                    </div>
                    <p className="text-xs font-mono font-bold tracking-wider text-white">
                      FINRECON
                    </p>
                    <p className="text-[10px] font-mono text-[#FFD400] uppercase font-semibold">
                      7-PASS ENGINE
                    </p>
                    <div className="mt-2 pt-2 border-t border-white/10 text-[9px] font-mono text-white/50">
                      Zero Drift • Deterministic
                    </div>
                  </div>
                  <div className="hidden md:block w-px h-8 bg-gradient-to-b from-[#FFD400] via-[#FFD400]/60 to-transparent" />
                </div>

                {/* 3. Output Classification Column */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-[11px] font-mono uppercase tracking-widest text-[#FFD400] font-semibold">
                      02 • RECONCILED OUTPUTS
                    </p>
                    <span className="text-[10px] font-mono text-white/40">100% Accounted</span>
                  </div>
                  {[
                    { label: "EXACT MATCH", count: "12,298 Records", highlight: true },
                    { label: "PARTIAL MATCH", count: "112 Adjusted", highlight: false },
                    { label: "DUPLICATE DETECTION", count: "38 Isolated", highlight: false },
                    { label: "MISSING RECORD", count: "24 Investigated", highlight: false },
                    { label: "CONFLICT LEDGER", count: "10 Flagged", highlight: false },
                  ].map((r) => (
                    <div
                      key={r.label}
                      className={`flex items-center justify-between border rounded-xl px-4 py-3 bg-[#0D0D0D] transition-colors ${
                        r.highlight
                          ? "border-[#FFD400]/40 text-white shadow-sm"
                          : "border-white/10 text-white/80"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`h-2 w-2 rounded-full ${
                            r.highlight ? "bg-[#FFD400]" : "bg-white/40"
                          }`}
                        />
                        <span className="text-xs font-mono font-semibold tracking-wider">
                          {r.label}
                        </span>
                      </div>
                      <span
                        className={`text-xs font-mono ${
                          r.highlight ? "text-[#FFD400] font-bold" : "text-white/50"
                        }`}
                      >
                        {r.count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 3. HERO DATA VISUALIZATION BAR (Section 7) ═══════ */}
      <section className="border-y border-white/10 bg-[#080808] py-12 px-6 sm:px-8 lg:px-12 select-none">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 lg:gap-8">
            {[
              { label: "MATCH RATE", value: "99.2%", sub: "Deterministic accuracy" },
              { label: "TRANSACTIONS", value: "12,482", sub: "Normalized & indexed" },
              { label: "EXCEPTIONS", value: "184", sub: "Active investigations" },
              { label: "LEDGER SOURCES", value: "5", sub: "Banks, gateways, ERPs" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="border border-white/10 rounded-2xl p-6 bg-[#0D0D0D] flex flex-col justify-between"
              >
                <span className="text-[11px] font-mono tracking-widest text-[#FFD400] uppercase font-semibold">
                  {stat.label}
                </span>
                <p className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-mono text-white mt-2 mb-1">
                  {stat.value}
                </p>
                <span className="text-xs text-white/50 font-mono">{stat.sub}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════ 4. PROBLEM SECTION (Section 8) ═══════ */}
      <section id="solutions" className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#000000]">
        <div className="max-w-5xl mx-auto">
          <RevealSection className="text-center mb-16">
            <div className="inline-flex items-center gap-2 border border-white/10 bg-[#0D0D0D] rounded-full px-3.5 py-1 text-xs font-mono font-medium text-[#FFD400] mb-4">
              <span>● THE RECONCILIATION PROBLEM</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Financial data is everywhere.<br />
              <span className="text-white/40">The truth is not.</span>
            </h2>
            <p className="text-white/60 text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
              The exact same transaction appears with different IDs, net amounts, fee deductions, and dates across every disconnected system.
            </p>
          </RevealSection>

          {/* 3 Source Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[
              { source: "BANK STATEMENT", id: "TXN-10482", amount: "₹50,000", date: "01 OCT 2026" },
              { source: "PAYMENT GATEWAY", id: "PG-88192", amount: "₹50,000", date: "02 OCT 2026" },
              { source: "ACCOUNTING / ERP", id: "INV-4821", amount: "₹49,950", date: "01 OCT 2026" },
            ].map((card, i) => (
              <RevealSection key={card.source} delay={`delay-${(i + 1) * 100}`}>
                <div className="border border-white/10 rounded-2xl p-6 bg-[#0D0D0D] h-full flex flex-col justify-between">
                  <p className="text-[11px] font-mono tracking-widest text-[#FFD400] uppercase font-semibold mb-4">
                    {card.source}
                  </p>
                  <div className="space-y-2.5 font-mono text-xs">
                    <div className="flex justify-between py-1 border-b border-white/5">
                      <span className="text-white/40">Record ID</span>
                      <span className="text-white font-medium">{card.id}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-white/5">
                      <span className="text-white/40">Net Amount</span>
                      <span className="text-white font-bold">{card.amount}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-white/40">Timestamp</span>
                      <span className="text-white/80">{card.date}</span>
                    </div>
                  </div>
                </div>
              </RevealSection>
            ))}
          </div>

          {/* FinRecon Result Card */}
          <RevealSection delay="delay-300">
            <div className="border-2 border-[#FFD400] rounded-2xl p-6 bg-[#0D0D0D] text-center shadow-xl shadow-[#FFD400]/10">
              <p className="text-[11px] font-mono tracking-widest text-[#FFD400] uppercase font-bold mb-1">
                FINRECON 7-PASS ENGINE RESULT
              </p>
              <h3 className="text-2xl font-extrabold font-mono text-white tracking-tight">
                PARTIAL MATCH DETECTED
              </h3>
              <p className="text-xs sm:text-sm font-mono text-[#FFD400] mt-1 font-semibold">
                Δ ₹50 difference detected • T+1 settlement lag identified • Fee deduction isolated
              </p>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 5. HOW FINRECON WORKS (Section 9) ═══════ */}
      <section id="how-it-works" className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#080808] border-y border-white/10">
        <div className="max-w-7xl mx-auto">
          <RevealSection className="text-center mb-16">
            <div className="inline-flex items-center gap-2 border border-white/10 bg-[#0D0D0D] rounded-full px-3.5 py-1 text-xs font-mono font-medium text-[#FFD400] mb-4">
              <span>● THE 7-STEP RECONCILIATION FLOW</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              ONE RECONCILIATION LAYER.<br />
              <span className="text-white/40">EVERY FINANCIAL SOURCE.</span>
            </h2>
          </RevealSection>

          {/* 7-Step Process Grid */}
          <RevealSection>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
              {[
                { step: "01", name: "INGEST", desc: "Automated ingestion from bank feeds, APIs, and CSVs." },
                { step: "02", name: "NORMALIZE", desc: "Standardize dates, currencies, and net monetary amounts." },
                { step: "03", name: "RESOLVE", desc: "Deterministic entity matching across legal names." },
                { step: "04", name: "MATCH", desc: "7-pass reference, fuzzy, and tolerance matching." },
                { step: "05", name: "RECONCILE", desc: "Classify into exact, partial, missing, or duplicates." },
                { step: "06", name: "INVESTIGATE", desc: "Interactive exception workbench with AI copilot." },
                { step: "07", name: "AUDIT", desc: "Cryptographic SHA-256 chained audit verification." },
              ].map((s) => (
                <div
                  key={s.step}
                  className="border border-white/10 rounded-2xl p-5 bg-[#0D0D0D] flex flex-col justify-between hover:border-[#FFD400]/40 transition-colors group"
                >
                  <div>
                    <span className="text-2xl font-extrabold font-mono text-[#FFD400] block mb-2 group-hover:scale-105 transition-transform">
                      {s.step}
                    </span>
                    <h4 className="text-xs font-mono font-bold tracking-wider text-white uppercase mb-2">
                      {s.name}
                    </h4>
                  </div>
                  <p className="text-[11px] text-white/50 leading-relaxed font-mono">
                    {s.desc}
                  </p>
                </div>
              ))}
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 6. PLATFORM FEATURES (Section 10) ═══════ */}
      <section id="features" className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#000000]">
        <div className="max-w-7xl mx-auto">
          <RevealSection className="text-center mb-16">
            <div className="inline-flex items-center gap-2 border border-white/10 bg-[#0D0D0D] rounded-full px-3.5 py-1 text-xs font-mono font-medium text-[#FFD400] mb-4">
              <span>● PLATFORM CAPABILITIES</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Enterprise-Grade Financial Features
            </h2>
          </RevealSection>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              {
                icon: Upload,
                title: "Multi-Source Data Ingestion",
                desc: "Import financial data from banks, payment gateways, accounting ERPs, invoices, and crypto networks with automatic column inference.",
              },
              {
                icon: Layers,
                title: "Data Normalization",
                desc: "Standardize dates, amounts, currency exchange, identifiers, and customer names into canonical ledger models.",
              },
              {
                icon: Users,
                title: "Entity Resolution",
                desc: "Identify when different names or identifiers refer to the same organization using RapidFuzz scoring and tax ID matching.",
              },
              {
                icon: GitMerge,
                title: "Transaction Matching",
                desc: "Support exact UTR, reference number, invoice cross-correlation, amount tolerance, date variance, and split settlement.",
              },
              {
                icon: Search,
                title: "Duplicate Detection",
                desc: "Identify duplicate financial records, repeated gateway webhooks, and dual-posted bank files instantly.",
              },
              {
                icon: AlertTriangle,
                title: "Exception Detection",
                desc: "Detect missing records, amount discrepancies, timing differences, orphan bank charges, and ledger conflicts.",
              },
              {
                icon: Coins,
                title: "Crypto Reconciliation",
                desc: "Compare blockchain transactions on Ethereum and Polygon against internal fiat accounts with gas variance tracking.",
              },
              {
                icon: Scale,
                title: "Exception Investigation",
                desc: "Provide finance teams with side-by-side comparison tools, manual review actions, and resolution workflows.",
              },
              {
                icon: Bot,
                title: "AI Investigation Assistant",
                desc: "Contextual investigation assistant that strictly separates verified facts, computed discrepancies, and suggestions.",
              },
              {
                icon: Clock,
                title: "Cryptographic Audit Trail",
                desc: "Maintain a traceable, SHA-256 chained transaction log with automated continuous integrity verification.",
              },
            ].map((f, i) => (
              <RevealSection key={f.title} delay={`delay-${Math.min(i * 50, 300)}`}>
                <div className="border border-white/10 rounded-2xl p-6 bg-[#0D0D0D] hover:border-[#FFD400]/40 transition-all h-full flex flex-col justify-between group">
                  <div>
                    <div className="h-10 w-10 rounded-xl bg-black border border-white/10 flex items-center justify-center text-[#FFD400] mb-4 group-hover:scale-105 transition-transform">
                      <f.icon className="h-5 w-5" />
                    </div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono mb-2">
                      {f.title}
                    </h3>
                    <p className="text-xs text-white/60 leading-relaxed font-mono">
                      {f.desc}
                    </p>
                  </div>
                </div>
              </RevealSection>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════ 7. TRANSACTION MATCHING VISUAL (Section 11) ═══════ */}
      <section className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#080808] border-y border-white/10">
        <div className="max-w-5xl mx-auto">
          <RevealSection className="text-center mb-16">
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Intelligent Transaction Matching
            </h2>
            <p className="text-white/60 text-sm mt-3 font-mono">
              Live matching between bank transactions and merchant settlement feeds
            </p>
          </RevealSection>

          <RevealSection>
            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 items-center">
              {/* Source A */}
              <div className="border border-white/10 rounded-2xl p-6 bg-[#0D0D0D]">
                <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/10">
                  <span className="text-[11px] font-mono uppercase tracking-widest text-[#FFD400] font-bold">
                    SOURCE A: BANK
                  </span>
                  <span className="text-[10px] font-mono text-white/50">HDFC Feed</span>
                </div>
                <div className="space-y-3 font-mono text-xs">
                  <div className="flex justify-between">
                    <span className="text-white/40">Transaction ID</span>
                    <span className="text-white font-medium">TXN-48201</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Customer Entity</span>
                    <span className="text-white">ACME Corporation</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Net Amount</span>
                    <span className="text-white font-bold text-sm">₹125,000</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Date</span>
                    <span className="text-white/80">30 Sep 2026</span>
                  </div>
                </div>
              </div>

              {/* Match Engine Indicator */}
              <div className="flex flex-col items-center gap-3 py-4">
                <div className="border-2 border-[#FFD400] rounded-2xl px-6 py-5 text-center bg-black shadow-xl shadow-[#FFD400]/15">
                  <CheckCircle2 className="h-7 w-7 text-[#FFD400] mx-auto mb-2" />
                  <p className="text-xl font-bold font-mono text-white">98.7%</p>
                  <p className="text-[10px] font-mono text-[#FFD400] font-semibold uppercase tracking-wider">
                    CONFIDENCE MATCH
                  </p>
                </div>
                <div className="space-y-1 text-center font-mono text-[10px] text-white/60">
                  <p className="flex items-center justify-center gap-1">
                    <Check className="h-3 w-3 text-[#FFD400]" /> Entity similarity
                  </p>
                  <p className="flex items-center justify-center gap-1">
                    <Check className="h-3 w-3 text-[#FFD400]" /> Amount match
                  </p>
                  <p className="flex items-center justify-center gap-1">
                    <Check className="h-3 w-3 text-[#FFD400]" /> Date match
                  </p>
                </div>
              </div>

              {/* Source B */}
              <div className="border border-white/10 rounded-2xl p-6 bg-[#0D0D0D]">
                <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/10">
                  <span className="text-[11px] font-mono uppercase tracking-widest text-[#FFD400] font-bold">
                    SOURCE B: GATEWAY
                  </span>
                  <span className="text-[10px] font-mono text-white/50">Stripe/Razorpay</span>
                </div>
                <div className="space-y-3 font-mono text-xs">
                  <div className="flex justify-between">
                    <span className="text-white/40">Transaction ID</span>
                    <span className="text-white font-medium">PG-98212</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Customer Entity</span>
                    <span className="text-white">ACME CORP.</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Net Amount</span>
                    <span className="text-white font-bold text-sm">₹125,000</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Date</span>
                    <span className="text-white/80">30 Sep 2026</span>
                  </div>
                </div>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 8. EXCEPTION INVESTIGATION (Section 12) ═══════ */}
      <section className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#000000]">
        <div className="max-w-5xl mx-auto">
          <RevealSection className="text-center mb-16">
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Exceptions become investigations.<br />
              <span className="text-[#FFD400]">Not spreadsheets.</span>
            </h2>
            <p className="text-white/60 text-sm mt-3 font-mono">
              Actionable root-cause resolution for financial variance
            </p>
          </RevealSection>

          <RevealSection>
            <div className="border border-white/10 rounded-2xl p-6 sm:p-8 bg-[#0D0D0D]">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6 pb-6 border-b border-white/10">
                <div className="space-y-1">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-white/40">Source A</p>
                  <p className="text-2xl font-bold font-mono text-white">₹125,000</p>
                  <p className="text-xs text-white/50 font-mono">Bank Statement</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-white/40">Source B</p>
                  <p className="text-2xl font-bold font-mono text-white">₹124,750</p>
                  <p className="text-xs text-white/50 font-mono">Payment Gateway</p>
                </div>
                <div className="space-y-1 sm:border-l sm:border-white/10 sm:pl-6">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-[#FFD400]">Difference</p>
                  <p className="text-2xl font-bold font-mono text-[#FFD400]">Δ ₹250</p>
                  <p className="text-xs text-white/50 font-mono">Processing Fee Isolated</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="inline-flex items-center gap-2 border border-[#FFD400]/40 bg-[#FFD400]/10 rounded-lg px-3 py-1.5 text-xs font-mono font-bold text-[#FFD400]">
                  <span>CLASSIFICATION: AMOUNT DISCREPANCY</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="border border-white/20 bg-white/5 hover:bg-white/10 text-white text-xs font-mono uppercase px-4 py-2 rounded-lg"
                  >
                    Compare
                  </button>
                  <button
                    type="button"
                    className="border border-white/20 bg-white/5 hover:bg-white/10 text-white text-xs font-mono uppercase px-4 py-2 rounded-lg"
                  >
                    Investigate
                  </button>
                  <button
                    type="button"
                    className="bg-[#FFD400] text-black font-bold text-xs font-mono uppercase px-4 py-2 rounded-lg shadow-sm"
                  >
                    Resolve
                  </button>
                </div>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 9. CRYPTO RECONCILIATION (Section 13) ═══════ */}
      <section className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#080808] border-y border-white/10">
        <div className="max-w-5xl mx-auto">
          <RevealSection className="text-center mb-16">
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Traditional finance meets blockchain.
            </h2>
            <p className="text-white/60 text-sm mt-3 font-mono">
              Reconcile on-chain wallet addresses and transaction hashes with general ledgers
            </p>
          </RevealSection>

          <RevealSection>
            <div className="border border-white/10 rounded-2xl p-6 sm:p-8 bg-[#0D0D0D]">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-center">
                <div className="border border-white/10 rounded-xl p-4 bg-black text-center">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-[#FFD400] mb-1">
                    WALLET ADDRESS
                  </p>
                  <p className="text-xs font-mono text-white font-medium">0x8A...92F</p>
                  <p className="text-[10px] font-mono text-white/40 mt-1">Ethereum Mainnet</p>
                </div>

                <div className="border border-white/10 rounded-xl p-4 bg-black text-center">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-[#FFD400] mb-1">
                    BLOCKCHAIN TX
                  </p>
                  <p className="text-xs font-mono text-white font-medium">0x7F...ABC</p>
                  <p className="text-[10px] font-mono text-white/40 mt-1">2.5 ETH Transfer</p>
                </div>

                <div className="border border-white/10 rounded-xl p-4 bg-black text-center">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-[#FFD400] mb-1">
                    INTERNAL LEDGER
                  </p>
                  <p className="text-xs font-mono text-white font-medium">₹50,000</p>
                  <p className="text-[10px] font-mono text-white/40 mt-1">Aczen Treasury Account</p>
                </div>

                <div className="border-2 border-[#FFD400] rounded-xl p-4 bg-black text-center shadow-lg shadow-[#FFD400]/10">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-[#FFD400] font-bold mb-1">
                    STATUS
                  </p>
                  <p className="text-sm font-bold font-mono text-white">MATCHED</p>
                  <p className="text-[10px] font-mono text-[#FFD400] mt-1">Zero Gas Drift</p>
                </div>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 10. AI INVESTIGATION ASSISTANT (Section 14) ═══════ */}
      <section className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#000000]">
        <div className="max-w-4xl mx-auto">
          <RevealSection className="text-center mb-16">
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Investigate exceptions with context.
            </h2>
            <p className="text-white/60 text-sm mt-3 font-mono">
              Strictly verifiable distinction between Facts, Computed Figures, and Suggestions
            </p>
          </RevealSection>

          <RevealSection>
            <div className="border border-white/10 rounded-2xl p-6 sm:p-8 bg-[#0D0D0D]">
              {/* User Prompt */}
              <div className="flex justify-end mb-6">
                <div className="bg-[#171717] border border-white/10 text-white rounded-2xl px-5 py-3 max-w-md font-mono text-xs">
                  Why was transaction TXN-10482 classified as a partial match?
                </div>
              </div>

              {/* AI Copilot Answer */}
              <div className="flex justify-start">
                <div className="border border-white/10 rounded-2xl p-5 max-w-lg bg-black space-y-3 font-mono text-xs">
                  <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/10">
                    <Bot className="h-4 w-4 text-[#FFD400]" />
                    <span className="text-[11px] font-bold text-white uppercase tracking-wider">
                      FINRECON COPILOT ANALYSIS
                    </span>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-[10px] font-bold bg-white/15 text-white px-2 py-0.5 rounded border border-white/20 shrink-0">
                      FACT
                    </span>
                    <span className="text-white/80">
                      The primary bank source and gateway records differ by exactly ₹250.
                    </span>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-[10px] font-bold bg-white/15 text-white px-2 py-0.5 rounded border border-white/20 shrink-0">
                      CALCULATED
                    </span>
                    <span className="text-white/80">
                      Transaction dates reflect a 1-day variance (30 Sep 2026 vs 01 Oct 2026).
                    </span>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-[10px] font-bold bg-[#FFD400]/20 text-[#FFD400] px-2 py-0.5 rounded border border-[#FFD400]/40 shrink-0">
                      SUGGESTION
                    </span>
                    <span className="text-[#FFD400]">
                      The ₹250 discrepancy corresponds to standard merchant interchange processing fees.
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 11. AUDIT TRAIL TIMELINE (Section 15) ═══════ */}
      <section className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#080808] border-y border-white/10">
        <div className="max-w-3xl mx-auto">
          <RevealSection className="text-center mb-16">
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Every reconciliation decision leaves a trace.
            </h2>
            <p className="text-white/60 text-sm mt-3 font-mono">
              SHA-256 chained transaction blocks with cryptographic immutability
            </p>
          </RevealSection>

          <RevealSection>
            <div className="relative pl-6 sm:pl-8 border-l-2 border-white/10 space-y-6">
              {[
                { time: "10:42:18", event: "Transaction imported from corporate bank feed" },
                { time: "10:42:22", event: "Entity matched: ACME Corporation → ACME CORP." },
                { time: "10:44:03", event: "Partial discrepancy detected: ₹250 fee variance" },
                { time: "10:44:31", event: "Analyst reviewed exception in investigation workbench" },
                { time: "10:45:12", event: "Resolution recorded: processing fee verified" },
                { time: "10:45:13", event: "SHA-256 audit event block sealed into chain" },
              ].map((item) => (
                <div key={item.time} className="relative flex items-start gap-4">
                  <div className="absolute -left-[31px] sm:-left-[39px] h-3 w-3 rounded-full bg-[#FFD400] ring-4 ring-black" />
                  <div>
                    <span className="text-[10px] font-mono text-[#FFD400] font-bold block">
                      {item.time}
                    </span>
                    <span className="text-xs sm:text-sm font-mono text-white/90">
                      {item.event}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 12. PRODUCT METRICS SECTION (Section 16) ═══════ */}
      <section id="platform" className="py-24 sm:py-32 px-6 sm:px-8 lg:px-12 bg-[#000000]">
        <div className="max-w-6xl mx-auto text-center">
          <RevealSection className="mb-16">
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white uppercase">
              Operational Scale
            </h2>
            <p className="text-white/60 text-sm mt-3 font-mono">
              Proven accuracy across high-volume financial ledgers
            </p>
          </RevealSection>

          <RevealSection>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
              {[
                { value: 99, suffix: ".2%", label: "MATCH RATE" },
                { value: 12482, suffix: "", label: "TRANSACTIONS" },
                { value: 184, suffix: "", label: "EXCEPTIONS" },
                { value: 5, suffix: "", label: "FINANCIAL SOURCES" },
              ].map((k) => (
                <div
                  key={k.label}
                  className="border border-white/10 rounded-2xl p-6 sm:p-8 bg-[#0D0D0D] flex flex-col justify-center"
                >
                  <div className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-mono text-white mb-2">
                    <AnimatedNumber target={k.value} suffix={k.suffix} />
                  </div>
                  <span className="text-xs font-mono tracking-widest text-[#FFD400] uppercase font-semibold">
                    {k.label}
                  </span>
                </div>
              ))}
            </div>
          </RevealSection>

          {/* CTA Banner */}
          <RevealSection className="mt-16 sm:mt-20" delay="delay-200">
            <div className="border border-white/10 rounded-2xl p-8 sm:p-12 bg-[#0D0D0D] text-center">
              <h3 className="text-2xl sm:text-4xl font-extrabold uppercase text-white tracking-tight mb-4">
                Ready to reconcile your financial ledgers?
              </h3>
              <p className="text-xs sm:text-sm text-white/60 max-w-xl mx-auto mb-8 font-mono">
                Deploy FinRecon across your banks, gateways, accounting ERPs, and blockchain networks in minutes.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4">
                <Link
                  href="/login"
                  className="bg-[#FFD400] hover:bg-[#E6BE00] text-black font-bold text-xs uppercase tracking-wider font-mono px-8 py-3.5 rounded-xl shadow-lg shadow-[#FFD400]/20 transition-all flex items-center gap-2 group"
                >
                  <span>GET STARTED</span>
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  href="/login"
                  className="border border-white/20 hover:border-white/40 text-white font-semibold text-xs uppercase tracking-wider font-mono px-8 py-3.5 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                >
                  SIGN IN TO CONSOLE
                </Link>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════ 13. FOOTER (Section 27) ═══════ */}
      <footer id="resources" className="border-t border-white/10 bg-[#080808] py-16 px-6 sm:px-8 lg:px-12 select-none">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
            {/* Brand Col */}
            <div className="col-span-2 md:col-span-1 space-y-3">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-lg bg-black border border-[#FFD400]/40 flex items-center justify-center shadow-sm">
                  <Activity className="h-4 w-4 text-[#FFD400]" />
                </div>
                <span className="font-bold text-base text-white">FINRECON</span>
              </div>
              <p className="text-xs text-white/50 font-mono leading-relaxed">
                Multi-Source Financial Reconciliation &amp; Investigation Platform
              </p>
            </div>

            {/* PRODUCT */}
            <div>
              <p className="text-[11px] font-mono tracking-widest text-[#FFD400] uppercase font-bold mb-4">
                PRODUCT
              </p>
              <ul className="space-y-2 text-xs font-mono text-white/60">
                <li><Link href="/login" className="hover:text-white transition-colors">Platform</Link></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Dashboard</Link></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Data Ingestion</Link></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Entity Resolution</Link></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Transaction Matching</Link></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Exception Workbench</Link></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Crypto Ledger</Link></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Audit Trail</Link></li>
              </ul>
            </div>

            {/* SOLUTIONS */}
            <div>
              <p className="text-[11px] font-mono tracking-widest text-[#FFD400] uppercase font-bold mb-4">
                SOLUTIONS
              </p>
              <ul className="space-y-2 text-xs font-mono text-white/60">
                <li><span className="hover:text-white cursor-pointer">Financial Reconciliation</span></li>
                <li><span className="hover:text-white cursor-pointer">Transaction Matching</span></li>
                <li><span className="hover:text-white cursor-pointer">Exception Management</span></li>
                <li><span className="hover:text-white cursor-pointer">Crypto Reconciliation</span></li>
                <li><span className="hover:text-white cursor-pointer">Audit &amp; Compliance</span></li>
                <li><span className="hover:text-white cursor-pointer">Financial Investigation</span></li>
              </ul>
            </div>

            {/* RESOURCES */}
            <div>
              <p className="text-[11px] font-mono tracking-widest text-[#FFD400] uppercase font-bold mb-4">
                RESOURCES
              </p>
              <ul className="space-y-2 text-xs font-mono text-white/60">
                <li><span className="hover:text-white cursor-pointer">Documentation</span></li>
                <li><span className="hover:text-white cursor-pointer">API Documentation</span></li>
                <li><span className="hover:text-white cursor-pointer">How It Works</span></li>
                <li><span className="hover:text-white cursor-pointer">Reconciliation Guide</span></li>
                <li><span className="hover:text-white cursor-pointer">Demo</span></li>
                <li><span className="hover:text-white cursor-pointer">FAQ</span></li>
              </ul>
            </div>

            {/* COMPANY & LEGAL */}
            <div>
              <p className="text-[11px] font-mono tracking-widest text-[#FFD400] uppercase font-bold mb-4">
                COMPANY &amp; LEGAL
              </p>
              <ul className="space-y-2 text-xs font-mono text-white/60">
                <li><span className="hover:text-white cursor-pointer">About FinRecon</span></li>
                <li><span className="hover:text-white cursor-pointer">Technology</span></li>
                <li><span className="hover:text-white cursor-pointer">Privacy</span></li>
                <li><span className="hover:text-white cursor-pointer">Terms</span></li>
                <li><span className="hover:text-white cursor-pointer">Security</span></li>
                <li><span className="hover:text-white cursor-pointer">Responsible AI</span></li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-white/40">
            <p>© 2026 FinRecon. All rights reserved.</p>
            <p>Strictly Black, White &amp; Yellow Enterprise Fintech System</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
