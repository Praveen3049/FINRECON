"use client";

import React, { useState } from "react";
import {
  Activity,
  Lock,
  Mail,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  HelpCircle,
  UserCheck,
  Building2,
  Scale,
  Sparkles,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/AuthContext";
import { useInstantNav } from "@/components/layout/NavigationContext";
import { useToast } from "@/components/ui/Toast";
import { UserRole } from "@/lib/types";

const ROLE_OPTIONS = [
  {
    role: "USER" as UserRole,
    title: "User",
    badge: "Analyst",
    desc: "CSV Ingestion, Crypto & AI Copilot",
    email: "user@finrecon.com",
    password: "User@123",
    icon: User,
  },
  {
    role: "AUDITOR" as UserRole,
    title: "Auditor",
    badge: "Reviewer",
    desc: "Reconciliation & Exception Workbench",
    email: "auditor@finrecon.com",
    password: "Auditor@123",
    icon: Scale,
  },
  {
    role: "MANAGER" as UserRole,
    title: "Manager",
    badge: "Executive",
    desc: "Full Access & Auditor Task Assignment",
    email: "manager@finrecon.com",
    password: "Manager@123",
    icon: Building2,
  },
];

const DEMO_PRESETS = [
  {
    role: "USER" as UserRole,
    title: "Operational Analyst",
    email: "user@finrecon.com",
    password: "User@123",
    desc: "CSV Data Ingestion, Crypto Ledger & AI Assistant",
  },
  {
    role: "AUDITOR" as UserRole,
    title: "Compliance Auditor",
    email: "auditor@finrecon.com",
    password: "Auditor@123",
    desc: "Exception Investigation, Resolving & Escalations",
  },
  {
    role: "MANAGER" as UserRole,
    title: "Operations Manager",
    email: "manager@finrecon.com",
    password: "Manager@123",
    desc: "Full Platform Access & Auditor Task Assignment",
  },
  {
    role: "MANAGER" as UserRole,
    title: "Executive Admin",
    email: "admin@finrecon.com",
    password: "Admin@123",
    desc: "Full Administrative Oversight & System Control",
  },
];

export default function LoginPage() {
  const { login, signup } = useAuth();
  const { navigateTo } = useInstantNav();
  const { success } = useToast();

  // Mode: "signin" | "signup"
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");

  // Sign In State
  const [selectedRole, setSelectedRole] = useState<UserRole>("USER");
  const [loginEmail, setLoginEmail] = useState<string>("user@finrecon.com");
  const [loginPassword, setLoginPassword] = useState<string>("User@123");
  const [showLoginPassword, setShowLoginPassword] = useState<boolean>(false);

  // Sign Up State
  const [signupName, setSignupName] = useState<string>("");
  const [signupEmail, setSignupEmail] = useState<string>("");
  const [signupPassword, setSignupPassword] = useState<string>("");
  const [signupConfirmPassword, setSignupConfirmPassword] = useState<string>("");
  const [showSignupPassword, setShowSignupPassword] = useState<boolean>(false);

  // Common UI State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [showForgotModal, setShowForgotModal] = useState<boolean>(false);

  // Validate Sign In
  const validateSignIn = () => {
    let isValid = true;
    setEmailError(null);
    setPasswordError(null);
    setErrorMsg(null);

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!loginEmail.trim()) {
      setEmailError("Corporate email address is required.");
      isValid = false;
    } else if (!emailRegex.test(loginEmail.trim())) {
      setEmailError("Enter a valid corporate email address.");
      isValid = false;
    }

    if (!loginPassword) {
      setPasswordError("Account password is required.");
      isValid = false;
    }

    return isValid;
  };

  // Validate Sign Up
  const validateSignUp = () => {
    let isValid = true;
    setNameError(null);
    setEmailError(null);
    setPasswordError(null);
    setConfirmError(null);
    setErrorMsg(null);

    if (!signupName.trim() || signupName.trim().length < 2) {
      setNameError("Full name must be at least 2 characters.");
      isValid = false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!signupEmail.trim()) {
      setEmailError("Email address is required.");
      isValid = false;
    } else if (!emailRegex.test(signupEmail.trim())) {
      setEmailError("Enter a valid email address.");
      isValid = false;
    }

    if (!signupPassword || signupPassword.length < 6) {
      setPasswordError("Password must be at least 6 characters.");
      isValid = false;
    }

    if (signupPassword !== signupConfirmPassword) {
      setConfirmError("Passwords do not match.");
      isValid = false;
    }

    return isValid;
  };

  // Handle Sign In Submit
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateSignIn() || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      await login(loginEmail.trim(), loginPassword, selectedRole);
      success("Authenticated", `Signed in successfully as ${selectedRole}. Launching workspace...`);
      navigateTo("/");
    } catch (err: any) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;

      if (detail && detail.includes("Role mismatch")) {
        setErrorMsg(detail);
      } else if (status === 401) {
        setErrorMsg("Invalid email or password. Please verify your credentials.");
      } else if (err?.code === "ERR_NETWORK" || !status) {
        setErrorMsg("Unable to reach authentication server. Check network connection.");
      } else {
        setErrorMsg(detail || "Authentication service temporarily unavailable. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Sign Up Submit
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateSignUp() || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      await signup(signupName.trim(), signupEmail.trim(), signupPassword);
      success("Account Provisioned", "Welcome to FinRecon! Signed in under standard User role.");
      navigateTo("/");
    } catch (err: any) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;

      if (status === 400 || detail) {
        setErrorMsg(detail || "An account with this email address already exists.");
      } else if (err?.code === "ERR_NETWORK" || !status) {
        setErrorMsg("Unable to connect to the authentication server.");
      } else {
        setErrorMsg("Account registration failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Quick-Fill Demo Accounts
  const handleQuickFill = (presetRole: UserRole, presetEmail: string, presetPass: string) => {
    setAuthMode("signin");
    setSelectedRole(presetRole);
    setLoginEmail(presetEmail);
    setLoginPassword(presetPass);
    setEmailError(null);
    setPasswordError(null);
    setErrorMsg(null);
  };

  return (
    <div className="fixed inset-0 z-50 h-screen w-screen bg-[#000000] overflow-y-auto overflow-x-hidden font-mono">
      {/* Background ambient lighting - strictly Yellow glow */}
      <div className="fixed top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[540px] h-[320px] bg-[#FFD400]/5 rounded-full blur-[140px] pointer-events-none" />

      {/* Scrollable Content Container */}
      <div className="min-h-full w-full flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8 py-10 sm:py-12">
        <div className="w-full max-w-lg relative z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-xl bg-[#FFD400] text-black shadow-lg shadow-[#FFD400]/20 mb-1">
            <Activity className="h-6 w-6 text-black" />
          </div>
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white uppercase font-mono">
              FINRECON
            </h1>
            <span className="text-[10px] font-mono uppercase bg-white/10 text-[#FFD400] px-2 py-0.5 rounded border border-[#FFD400]/30 font-semibold">
              Enterprise
            </span>
          </div>
          <p className="text-xs text-white/50 uppercase tracking-wider font-medium font-mono">
            Financial Reconciliation & Investigation Platform
          </p>
        </div>

        {/* Auth Mode Tabs: Sign In vs Sign Up */}
        <div className="bg-[#0D0D0D] border border-white/10 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-5">
          <div className="grid grid-cols-2 p-1 bg-black rounded-xl border border-white/10 text-xs font-mono">
            <button
              type="button"
              onClick={() => {
                setAuthMode("signin");
                setErrorMsg(null);
              }}
              className={`py-2 px-3 rounded-lg font-semibold uppercase tracking-wider transition-all ${
                authMode === "signin"
                  ? "bg-[#171717] text-[#FFD400] border border-[#FFD400]/40 shadow-sm"
                  : "text-white/50 hover:text-white"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode("signup");
                setErrorMsg(null);
              }}
              className={`py-2 px-3 rounded-lg font-semibold uppercase tracking-wider transition-all ${
                authMode === "signup"
                  ? "bg-[#171717] text-[#FFD400] border border-[#FFD400]/40 shadow-sm"
                  : "text-white/50 hover:text-white"
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Error Alert Box */}
          {errorMsg && (
            <div className="p-3.5 rounded-lg bg-black border border-[#FFD400]/60 text-[#FFD400] text-xs flex items-start gap-2.5 font-mono animate-in fade-in duration-200">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-bold uppercase tracking-wider block text-[10px] text-white">
                  Authentication Notice
                </span>
                <span className="leading-relaxed">{errorMsg}</span>
              </div>
            </div>
          )}

          {/* MODE 1: SIGN IN */}
          {authMode === "signin" ? (
            <form onSubmit={handleSignIn} className="space-y-4" noValidate>
              {/* Role Selector */}
              <div className="space-y-1.5 font-mono">
                <label className="block text-xs font-semibold uppercase tracking-wider text-white/70">
                  Select Your Account Role <span className="text-[#FFD400]">*</span>
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {ROLE_OPTIONS.map((item) => {
                    const isSelected = selectedRole === item.role;
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.role}
                        type="button"
                        onClick={() => {
                          setSelectedRole(item.role);
                          setLoginEmail(item.email);
                          setLoginPassword(item.password);
                          setEmailError(null);
                          setPasswordError(null);
                          setErrorMsg(null);
                        }}
                        className={`p-2.5 rounded-xl border text-left transition-all relative flex flex-col justify-between ${
                          isSelected
                            ? "bg-[#171717] border-[#FFD400] ring-1 ring-[#FFD400] shadow-sm"
                            : "bg-black border-white/10 hover:border-white/25 text-white/70"
                        }`}
                      >
                        <div className="flex items-center justify-between w-full mb-1.5">
                          <Icon className={`h-4 w-4 ${isSelected ? "text-[#FFD400]" : "text-white/40"}`} />
                          <span
                            className={`text-[9px] uppercase font-mono px-1 py-0.2 rounded border ${
                              isSelected
                                ? "bg-[#FFD400]/15 text-[#FFD400] border-[#FFD400]/40"
                                : "bg-white/5 text-white/40 border-white/10"
                            }`}
                          >
                            {item.badge}
                          </span>
                        </div>
                        <div>
                          <span className={`block text-xs font-bold ${isSelected ? "text-white" : "text-white/70"}`}>
                            {item.title}
                          </span>
                          <span className="block text-[9px] text-white/40 leading-tight mt-0.5 line-clamp-1">
                            {item.desc}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Role Account Helper */}
                <div className="flex items-center justify-between p-2 rounded-lg bg-black border border-white/10 text-[11px] font-mono">
                  <div className="flex items-center gap-1.5 text-white/70">
                    <CheckCircle2 className="h-3.5 w-3.5 text-[#FFD400]" />
                    <span>Role Account:</span>
                    <strong className="text-white font-mono">{ROLE_OPTIONS.find((r) => r.role === selectedRole)?.email}</strong>
                  </div>
                  <span className="text-[#FFD400] text-[10px] font-mono">
                    Pass: {ROLE_OPTIONS.find((r) => r.role === selectedRole)?.password}
                  </span>
                </div>
              </div>

              {/* Corporate Email Field */}
              <div className="space-y-1.5 font-mono">
                <label className="block text-xs font-semibold uppercase tracking-wider text-white/50">
                  Corporate Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/40">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => {
                      setLoginEmail(e.target.value);
                      if (emailError) setEmailError(null);
                    }}
                    placeholder="member@finrecon.com"
                    disabled={isLoading}
                    autoComplete="email"
                    className={`w-full pl-10 pr-3 py-2.5 bg-black border rounded-lg text-sm font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-[#FFD400] transition-all ${
                      emailError ? "border-[#FFD400]" : "border-white/10"
                    }`}
                  />
                </div>
                {emailError && <p className="text-[11px] text-[#FFD400] font-medium pl-1">{emailError}</p>}
              </div>

              {/* Password Field */}
              <div className="space-y-1.5 font-mono">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-white/50">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowForgotModal(true)}
                    className="text-xs text-[#FFD400] hover:text-white transition-colors"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/40">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type={showLoginPassword ? "text" : "password"}
                    value={loginPassword}
                    onChange={(e) => {
                      setLoginPassword(e.target.value);
                      if (passwordError) setPasswordError(null);
                    }}
                    placeholder="••••••••••••"
                    disabled={isLoading}
                    autoComplete="current-password"
                    className={`w-full pl-10 pr-10 py-2.5 bg-black border rounded-lg text-sm font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-[#FFD400] transition-all ${
                      passwordError ? "border-[#FFD400]" : "border-white/10"
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-white/40 hover:text-white transition-colors"
                    aria-label={showLoginPassword ? "Hide password" : "Show password"}
                  >
                    {showLoginPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {passwordError && <p className="text-[11px] text-[#FFD400] font-medium pl-1">{passwordError}</p>}
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full mt-2"
                isLoading={isLoading}
                disabled={isLoading}
                iconRight={<ArrowRight className="h-4 w-4 text-black" />}
              >
                {isLoading ? "Authenticating Session..." : `Sign In as ${selectedRole}`}
              </Button>
            </form>
          ) : (
            /* MODE 2: SIGN UP */
            <form onSubmit={handleSignUp} className="space-y-4" noValidate>
              {/* Role Scope Notice */}
              <div className="p-3 rounded-xl bg-black border border-white/15 flex items-start gap-2.5 text-xs text-white/70">
                <Info className="h-4 w-4 text-[#FFD400] shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold text-white text-[11px] uppercase tracking-wider block">
                    Account Tier: Operational User
                  </span>
                  <p className="text-[11px] leading-relaxed text-white/60">
                    New accounts are registered under the <strong>USER</strong> role with access to CSV file ingestion, Crypto ledger analysis, and AI Copilot. Discrepancy investigation and reconciliation are reserved for Compliance Auditors and Operations Managers.
                  </p>
                </div>
              </div>

              {/* Full Name */}
              <div className="space-y-1.5 font-mono">
                <label className="block text-xs font-semibold uppercase tracking-wider text-white/50">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/40">
                    <User className="h-4 w-4" />
                  </div>
                  <input
                    type="text"
                    value={signupName}
                    onChange={(e) => {
                      setSignupName(e.target.value);
                      if (nameError) setNameError(null);
                    }}
                    placeholder="e.g. Alex Morgan"
                    disabled={isLoading}
                    autoComplete="name"
                    className={`w-full pl-10 pr-3 py-2.5 bg-black border rounded-lg text-sm font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-[#FFD400] transition-all ${
                      nameError ? "border-[#FFD400]" : "border-white/10"
                    }`}
                  />
                </div>
                {nameError && <p className="text-[11px] text-[#FFD400] font-medium pl-1">{nameError}</p>}
              </div>

              {/* Email Address */}
              <div className="space-y-1.5 font-mono">
                <label className="block text-xs font-semibold uppercase tracking-wider text-white/50">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/40">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    value={signupEmail}
                    onChange={(e) => {
                      setSignupEmail(e.target.value);
                      if (emailError) setEmailError(null);
                    }}
                    placeholder="user@finrecon.com"
                    disabled={isLoading}
                    autoComplete="email"
                    className={`w-full pl-10 pr-3 py-2.5 bg-black border rounded-lg text-sm font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-[#FFD400] transition-all ${
                      emailError ? "border-[#FFD400]" : "border-white/10"
                    }`}
                  />
                </div>
                {emailError && <p className="text-[11px] text-[#FFD400] font-medium pl-1">{emailError}</p>}
              </div>

              {/* Password */}
              <div className="space-y-1.5 font-mono">
                <label className="block text-xs font-semibold uppercase tracking-wider text-white/50">
                  Password (min 6 characters)
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/40">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type={showSignupPassword ? "text" : "password"}
                    value={signupPassword}
                    onChange={(e) => {
                      setSignupPassword(e.target.value);
                      if (passwordError) setPasswordError(null);
                    }}
                    placeholder="••••••••••••"
                    disabled={isLoading}
                    autoComplete="new-password"
                    className={`w-full pl-10 pr-10 py-2.5 bg-black border rounded-lg text-sm font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-[#FFD400] transition-all ${
                      passwordError ? "border-[#FFD400]" : "border-white/10"
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowSignupPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-white/40 hover:text-white transition-colors"
                    aria-label={showSignupPassword ? "Hide password" : "Show password"}
                  >
                    {showSignupPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {passwordError && <p className="text-[11px] text-[#FFD400] font-medium pl-1">{passwordError}</p>}
              </div>

              {/* Confirm Password */}
              <div className="space-y-1.5 font-mono">
                <label className="block text-xs font-semibold uppercase tracking-wider text-white/50">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/40">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type={showSignupPassword ? "text" : "password"}
                    value={signupConfirmPassword}
                    onChange={(e) => {
                      setSignupConfirmPassword(e.target.value);
                      if (confirmError) setConfirmError(null);
                    }}
                    placeholder="••••••••••••"
                    disabled={isLoading}
                    autoComplete="new-password"
                    className={`w-full pl-10 pr-3 py-2.5 bg-black border rounded-lg text-sm font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-[#FFD400] transition-all ${
                      confirmError ? "border-[#FFD400]" : "border-white/10"
                    }`}
                  />
                </div>
                {confirmError && <p className="text-[11px] text-[#FFD400] font-medium pl-1">{confirmError}</p>}
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full mt-2"
                isLoading={isLoading}
                disabled={isLoading}
                iconRight={<Sparkles className="h-4 w-4 text-black" />}
              >
                {isLoading ? "Creating Account..." : "Create User Account"}
              </Button>
            </form>
          )}

          {/* Security Assurance Badge */}
          <div className="pt-2 border-t border-white/10 flex items-center justify-center gap-1.5 text-[11px] text-white/50 font-mono">
            <ShieldCheck className="h-3.5 w-3.5 text-[#FFD400]" />
            <span>SHA-256 Chained Audit Trail & Role Validation</span>
          </div>
        </div>

        {/* Demo Accounts Quick-Select for Evaluation */}
        <div className="bg-[#0D0D0D] border border-white/10 rounded-xl p-4 space-y-3 font-mono">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-white">
              <UserCheck className="h-3.5 w-3.5 text-[#FFD400]" />
              <span className="uppercase">Role Evaluation Credentials</span>
            </div>
            <span className="text-[10px] font-mono uppercase bg-black px-1.5 py-0.5 rounded text-[#FFD400] border border-[#FFD400]/30">
              1-Click Role & Login
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {DEMO_PRESETS.map((preset) => {
              const isSelected =
                authMode === "signin" && selectedRole === preset.role && loginEmail === preset.email;
              return (
                <button
                  key={preset.role}
                  type="button"
                  onClick={() => handleQuickFill(preset.role, preset.email, preset.password)}
                  className={`p-2.5 rounded-lg border text-left transition-all group ${
                    isSelected
                      ? "bg-[#171717] border-[#FFD400] ring-1 ring-[#FFD400] shadow-sm"
                      : "bg-black border-white/10 hover:border-white/30"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-white">{preset.role}</span>
                    {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-[#FFD400]" />}
                  </div>
                  <p className="text-[10px] text-white/50 font-mono truncate">{preset.email}</p>
                  <p className="text-[9px] text-white/40 mt-1 line-clamp-1">{preset.title}</p>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>

      {/* Forgot Password Modal Dialog */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200 font-mono">
          <div className="bg-[#0D0D0D] border border-white/15 rounded-xl p-6 max-w-sm w-full space-y-4 shadow-2xl text-center">
            <div className="h-12 w-12 rounded-xl bg-black border border-[#FFD400]/40 text-[#FFD400] mx-auto flex items-center justify-center">
              <HelpCircle className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-white uppercase tracking-wider">Password Recovery</h3>
              <p className="text-xs text-white/50 leading-relaxed font-sans">
                FinRecon corporate policies require password resets to be provisioned via Security Operations.
              </p>
            </div>
            <div className="bg-black border border-white/10 rounded-lg p-3 text-left space-y-1 text-xs">
              <span className="text-white/40 block text-[10px] uppercase font-mono">Internal Helpdesk</span>
              <span className="font-semibold text-white font-mono">secops@finrecon.internal</span>
              <span className="text-white/50 block text-[11px] pt-1 font-sans">
                For demo testing, use the pre-configured <strong>User@123</strong>, <strong>Auditor@123</strong>, or <strong>Manager@123</strong> accounts.
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => setShowForgotModal(false)}
            >
              Understood
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
