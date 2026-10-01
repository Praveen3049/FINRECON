"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  Sparkles,
  Send,
  User,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Calculator,
  Lightbulb,
  Copy,
  Check,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  RotateCcw,
  Layers,
  Key,
  Settings,
  X,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  PageHeader,
  Button,
  Badge,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  EmptyState,
  useToast,
} from "@/components/ui";

interface FactItem {
  field: string;
  value: any;
  source: string;
  description?: string;
}

interface CalculatedItem {
  metric: string;
  value: any;
  formula: string;
  interpretation?: string;
}

interface SuggestionItem {
  action: string;
  justification: string;
  confidence_level: string;
  recommended_entry?: string;
}

interface JournalEntryLine {
  account_number: string;
  account_name: string;
  debit: number;
  credit: number;
  memo: string;
}

interface SuggestedJournalEntry {
  title: string;
  memo: string;
  reference: string;
  total_debit: number;
  total_credit: number;
  lines: JournalEntryLine[];
}

interface InvestigationExplanation {
  case_id: string;
  case_number: string;
  status: string;
  confidence_score: number;
  summary: string;
  why_flagged: string;
  matched_evidence: any[];
  discrepancies: any[];
  explanation: string;
  reviewer_attention: string;
  suggested_next_checks: string[];
  facts?: FactItem[];
  calculated?: CalculatedItem[];
  suggestions?: SuggestionItem[];
  suggested_journal_entry?: SuggestedJournalEntry;
  ai_provider: string;
}

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  quickFollowups?: string[];
  provider?: string;
}

interface PrebuiltPrompt {
  id: string;
  category: string;
  label: string;
  prompt: string;
}

export default function AiAssistantPage() {
  const { warning, info, success, error } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [prompts, setPrompts] = useState<PrebuiltPrompt[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>("CASE-2026-0002");
  const [novaConfigured, setNovaConfigured] = useState<boolean>(false);

  // ChatGPT Configuration State
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [keyModalOpen, setKeyModalOpen] = useState<boolean>(false);
  const [apiKeyInput, setApiKeyInput] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("gpt-4o-mini");
  const [savingKey, setSavingKey] = useState<boolean>(false);

  // Investigation state
  const [investigation, setInvestigation] = useState<InvestigationExplanation | null>(null);
  const [investigationLoading, setInvestigationLoading] = useState<boolean>(false);
  const [investigationError, setInvestigationError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const loadInitialData = async () => {
    try {
      const [promptsRes, casesRes, healthRes, statusRes] = await Promise.all([
        api.getAIPrompts().catch(() => []),
        api.getReconciliationCases().catch(() => []),
        api.getSystemHealth().catch(() => null),
        api.getAIStatus().catch(() => null),
      ]);
      setPrompts(promptsRes || []);
      setCases(casesRes || []);
      if (healthRes && healthRes.nova_configured) {
        setNovaConfigured(true);
      }
      if (statusRes) {
        setAiStatus(statusRes);
        if (statusRes.model) setSelectedModel(statusRes.model);
      }

      const activeCase =
        (casesRes || []).find((c: any) => c.status === "UNDER_REVIEW")?.case_number ||
        (casesRes && casesRes[0]?.case_number) ||
        "CASE-ACZEN-10-0299";

      setSelectedCaseId(activeCase);

      const isChatGPT = statusRes?.openai_configured;
      const initialText = isChatGPT
        ? `Hello! I am your FinRecon AI, powered by **OpenAI ChatGPT (${statusRes.model})** with live multi-source financial and blockchain ledger grounding.\n\nI perform deep forensic investigation on deterministic reconciliation evidence across Bank Statements (NEFT/RTGS/IMPS), Payment Gateways (Stripe/Razorpay), Invoices (TDS 194C/J), and On-Chain Ledgers.\n\nAsk me any question below or click "Explain This Case" to audit any exception.`
        : `Hello! I am your FinRecon AI Investigation Assistant, integrated with official Aczen Nova company books.\n\nI explain deterministic reconciliation evidence across Bank Statements, Payment Gateways (RTGS/NEFT), and Customer Invoices, identifying root causes for variances (TDS withholding under Section 194C/J, partial installments, clearing lag) without ever modifying deterministic matching decisions.\n\nTo activate live **ChatGPT (GPT-4o)** reasoning, click **"Connect ChatGPT"** at the top right, or ask any question below.`;

      setMessages([
        {
          id: "welcome-msg",
          sender: "assistant",
          text: initialText,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          provider: isChatGPT ? `OpenAI ChatGPT (${statusRes.model})` : "FinRecon Forensic Engine",
          quickFollowups: [
            "Why was CASE-ACZEN-10-0299 flagged for Kapoor Textiles Pvt Ltd?",
            "Explain the exact settlement match on CASE-ACZEN-10-0297 (Anand Motors)",
            "Summarize all open Aczen invoice reconciliation discrepancies",
          ],
        },
      ]);
    } catch (err) {
      console.error("Failed to load initial assistant data:", err);
      warning("Assistant Data", "Could not load prebuilt prompts or active cases.");
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKeyInput.trim() || apiKeyInput.trim().length < 10) {
      warning("API Key Required", "Please enter a valid OpenAI API key (starts with sk-).");
      return;
    }
    try {
      setSavingKey(true);
      const updatedStatus = await api.configureAIKey({
        api_key: apiKeyInput.trim(),
        model: selectedModel,
      });
      setAiStatus(updatedStatus);
      setKeyModalOpen(false);
      setApiKeyInput("");
      success("ChatGPT Connected", `Successfully activated ${updatedStatus.model} for FinRecon AI.`);

      setMessages((prev) => [
        ...prev,
        {
          id: `activated-${Date.now()}`,
          sender: "assistant",
          text: `### ⚡ OpenAI ChatGPT Activated (${updatedStatus.model})\n\nOpenAI ChatGPT integration is now active! All subsequent financial forensic inquiries and case investigations will be grounded in live database evidence and analyzed using **${updatedStatus.model}**.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          provider: `OpenAI ChatGPT (${updatedStatus.model})`,
          quickFollowups: [
            "Explain CASE-2026-0002 fee variance",
            "Analyze Acme Corp's Ethereum payment on CASE-2026-0009",
            "Summarize all open critical exceptions across bank statements",
          ],
        },
      ]);
    } catch (err: any) {
      console.error("Failed to configure AI key:", err);
      error("Connection Error", err?.response?.data?.detail || "Could not validate or save OpenAI API key.");
    } finally {
      setSavingKey(false);
    }
  };

  const runCaseInvestigation = async (caseId: string, customQuestion?: string) => {
    try {
      setInvestigationLoading(true);
      setInvestigationError(null);
      const res = await api.explainCaseWithNova({
        reconciliation_case_id: caseId,
        question: customQuestion || "Why was this transaction flagged?",
      });
      setInvestigation(res);
      if (res.ai_provider === "NOVA_AI") {
        setNovaConfigured(true);
      }
    } catch (err: any) {
      console.error("Failed to investigate case:", err);
      setInvestigationError(
        err?.response?.data?.detail ||
          "AI Investigation Assistant is temporarily unavailable. The core reconciliation engine remains unaffected."
      );
    } finally {
      setInvestigationLoading(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputQuery;
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const res = await api.sendAIChat({ query });

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        quickFollowups: res.quick_followups,
        provider: res.ai_provider || (aiStatus?.openai_configured ? `OpenAI ChatGPT (${aiStatus.model})` : undefined),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Sync investigation pane if a case was targeted
      if (res.related_cases && res.related_cases.length > 0) {
        setSelectedCaseId(res.related_cases[0]);
        runCaseInvestigation(res.related_cases[0], query);
      }
    } catch (err) {
      console.error("Chat query error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text:
            "AI Investigation Assistant is temporarily unavailable. You can still inspect discrepancies and reconcile transactions manually.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    info("Copied", "Journal entry JSON copied to clipboard.");
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 font-mono">
      {/* Page Header */}
      <PageHeader
        title="AI Investigation Assistant"
        subtitle="Explains deterministic reconciliation evidence, analyzes variances, and assists human reviewers without altering reconciliation results."
        badge={{
          text: aiStatus?.openai_configured
            ? `ChatGPT Active (${aiStatus.model})`
            : novaConfigured
            ? "Aczen Nova AI Connected"
            : "Deterministic Engine Active",
          variant: "yellow",
          pulse: Boolean(aiStatus?.openai_configured || novaConfigured),
        }}
        secondaryActions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setKeyModalOpen(true)}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 font-mono transition-all ${
                aiStatus?.openai_configured
                  ? "bg-black text-[#FFD400] border border-[#FFD400]/40 hover:border-[#FFD400] hover:bg-[#111111]"
                  : "bg-[#FFD400] hover:bg-[#e6be00] text-black font-bold shadow-sm"
              }`}
            >
              <Key className="h-3.5 w-3.5" />
              {aiStatus?.openai_configured
                ? `ChatGPT (${aiStatus.model})`
                : "Connect ChatGPT (API Key)"}
            </button>
            <span className="text-xs bg-black text-[#FFD400] border border-[#FFD400]/30 px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 font-mono">
              <ShieldCheck className="h-4 w-4 text-[#FFD400]" />
              FIN-26 Truth Preservation Guaranteed
            </span>
          </div>
        }
      />

      {/* Suggested Prompt Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono">
        <span className="text-white/50 font-medium shrink-0 flex items-center gap-1.5">
          <Lightbulb className="h-4 w-4 text-[#FFD400]" />
          Suggested Inquiries:
        </span>
        {prompts.map((p) => (
          <button
            key={p.id}
            onClick={() => handleSendMessage(p.prompt)}
            className="shrink-0 bg-black hover:bg-[#171717] text-white/80 hover:text-white px-3 py-1.5 rounded-full border border-white/10 hover:border-[#FFD400]/40 transition-colors text-xs font-medium"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Dual-Pane Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start font-mono">
        {/* Left Pane: Interactive Chat (5 Cols) */}
        <Card className="lg:col-span-5 flex flex-col h-[780px] overflow-hidden">
          <CardHeader className="px-5 py-3.5 border-b border-white/10 bg-black flex flex-row items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-white/5 text-[#FFD400] border border-white/10">
                <Bot className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold uppercase tracking-wider font-mono">
                  Investigation Chat
                </CardTitle>
                <CardDescription className="text-[11px] font-mono">
                  {aiStatus?.openai_configured
                    ? `Powered by OpenAI ChatGPT (${aiStatus.model})`
                    : "Deterministic Financial Forensic Engine"}
                </CardDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                setMessages([
                  {
                    id: `new-${Date.now()}`,
                    sender: "assistant",
                    text: "Conversation reset. How can I assist with your financial investigations?",
                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                  },
                ])
              }
              className="text-xs text-white/50 hover:text-white h-8 font-mono"
              iconLeft={<RefreshCw className="h-3 w-3" />}
            >
              Reset
            </Button>
          </CardHeader>

          <CardContent className="flex-1 p-4 overflow-y-auto space-y-4 bg-[#0A0A0A]">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.sender === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-black text-[#FFD400] border border-[#FFD400]/40 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`max-w-[88%] rounded-xl p-3.5 text-xs leading-relaxed font-mono ${
                    msg.sender === "user"
                      ? "bg-[#FFD400] text-black font-semibold shadow-sm"
                      : "bg-black border border-white/10 text-white"
                  }`}
                >
                  {msg.sender === "assistant" && msg.provider && (
                    <div className="flex items-center gap-1.5 mb-2 pb-1.5 border-b border-white/10">
                      <Sparkles className="h-3 w-3 text-[#FFD400]" />
                      <span className="text-[10px] text-[#FFD400] font-semibold tracking-wider uppercase font-mono">
                        {msg.provider}
                      </span>
                    </div>
                  )}

                  <div className="whitespace-pre-wrap space-y-2 font-mono">
                    {msg.text.split("\n\n").map((para, i) => (
                      <p key={i}>{para}</p>
                    ))}
                  </div>

                  {msg.quickFollowups && msg.quickFollowups.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/10">
                      <span className="text-[10px] uppercase font-semibold text-white/50 tracking-wider block mb-1.5 font-mono">
                        Suggested Follow-ups:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.quickFollowups.map((q, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(q)}
                            className="text-[11px] bg-[#111111] hover:bg-[#1a1a1a] text-white/90 hover:text-white px-2.5 py-1 rounded-md border border-white/10 hover:border-[#FFD400]/40 transition-colors text-left font-mono"
                          >
                            &rarr; {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className={`mt-2 text-[10px] text-right font-mono ${msg.sender === "user" ? "text-black/60" : "text-white/40"}`}>
                    {msg.timestamp}
                  </div>
                </div>

                {msg.sender === "user" && (
                  <div className="w-7 h-7 rounded-full bg-white text-black flex items-center justify-center shrink-0 mt-0.5 font-bold">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-3 items-center text-xs text-white/50 font-mono">
                <div className="w-7 h-7 rounded-full bg-black text-[#FFD400] border border-[#FFD400]/40 flex items-center justify-center shrink-0">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="bg-black border border-white/10 rounded-xl px-4 py-2.5 flex items-center gap-2">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-[#FFD400]" />
                  <span>Querying Nova AI & reconciling evidence...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </CardContent>

          <div className="p-3 border-t border-white/10 bg-black">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask e.g. 'Why was Check #994821 flagged?' or 'Explain TDS discrepancy'..."
                className="flex-1 bg-black border border-white/10 rounded-lg px-3.5 py-2.5 text-xs font-mono text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400]"
              />
              <Button
                type="submit"
                disabled={!inputQuery.trim() || loading}
                size="sm"
                className="h-9 w-9 p-0 flex items-center justify-center"
              >
                <Send className="h-4 w-4 text-black" />
              </Button>
            </form>
          </div>
        </Card>

        {/* Right Pane: Formal Case Investigation Workbench (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Case Selection & Action Bar */}
          <Card>
            <CardContent className="p-4 font-mono">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex-1 w-full">
                  <label className="text-[11px] font-semibold text-white/50 uppercase tracking-wider block mb-1">
                    Select Target Reconciliation Case
                  </label>
                  <select
                    value={selectedCaseId}
                    onChange={(e) => {
                      setSelectedCaseId(e.target.value);
                      runCaseInvestigation(e.target.value);
                    }}
                    className="w-full bg-black border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-[#FFD400]"
                  >
                    {cases.length === 0 ? (
                      <option value="CASE-ACZEN-10-0299">Loading Aczen cases...</option>
                    ) : (
                      cases.map((c: any) => {
                        const varAmt = Number(c.total_variance_amount || 0);
                        const isZero = varAmt === 0;
                        return (
                          <option key={c.id} value={c.case_number || c.id} className="bg-black text-white py-1">
                            {c.case_number} &bull; [{c.status}] &bull; {c.title?.slice(0, 48)}{" "}
                            {isZero
                              ? "(Zero Variance)"
                              : `(Diff: ₹${varAmt.toLocaleString("en-IN")})`}
                          </option>
                        );
                      })
                    )}
                  </select>
                </div>

                <Button
                  variant="primary"
                  onClick={() => runCaseInvestigation(selectedCaseId)}
                  isLoading={investigationLoading}
                  iconLeft={<Sparkles className="h-3.5 w-3.5 text-black" />}
                  className="w-full sm:w-auto mt-auto shrink-0"
                >
                  Explain This Case
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Loading State */}
          {investigationLoading && (
            <Card className="p-12 text-center text-white/50 flex flex-col items-center font-mono">
              <RefreshCw className="h-8 w-8 animate-spin mb-3 text-[#FFD400]" />
              <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
                Analyzing Reconciliation Case with Nova AI
              </h4>
              <p className="text-xs text-white/40 mt-1 max-w-sm font-sans">
                Retrieving multi-source transaction evidence, calculating deterministic variances, and generating explainable insights.
              </p>
            </Card>
          )}

          {/* Error State - Fallback Behavior */}
          {investigationError && !investigationLoading && (
            <Card className="border-[#FFD400]/40 p-6 text-center space-y-4 font-mono">
              <AlertCircle className="h-8 w-8 text-[#FFD400] mx-auto" />
              <div>
                <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
                  AI Investigation Assistant is temporarily unavailable.
                </h4>
                <p className="text-xs text-white/50 mt-1 max-w-lg mx-auto font-sans">
                  The deterministic reconciliation engine remains active, reliable, and unaffected. You can still inspect discrepancies, manually reconcile transactions, and view audit history.
                </p>
              </div>

              <div className="pt-2 flex flex-wrap items-center justify-center gap-2 text-xs">
                <Link href="/reconciliation">
                  <Button variant="secondary" size="sm" iconLeft={<FileText className="h-3.5 w-3.5 text-white" />}>
                    Reconciliation Results
                  </Button>
                </Link>
                <Link href="/exceptions">
                  <Button variant="secondary" size="sm" iconLeft={<AlertTriangle className="h-3.5 w-3.5 text-[#FFD400]" />}>
                    Inspect Discrepancies
                  </Button>
                </Link>
                <Link href="/audit">
                  <Button variant="secondary" size="sm" iconLeft={<ShieldCheck className="h-3.5 w-3.5 text-white" />}>
                    Audit History
                  </Button>
                </Link>
              </div>

              <div className="pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => runCaseInvestigation(selectedCaseId)}
                  iconLeft={<RotateCcw className="h-3.5 w-3.5" />}
                >
                  Retry Investigation
                </Button>
              </div>
            </Card>
          )}

          {/* Empty State */}
          {!investigation && !investigationLoading && !investigationError && (
            <Card className="py-12">
              <EmptyState
                icon={<Bot className="h-10 w-10 text-[#FFD400]" />}
                title="Select a Case to Investigate"
                description="Click 'Explain This Case' above to view the summary, matching evidence, and reviewer attention."
                action={{
                  label: "Explain Active Case",
                  onClick: () => runCaseInvestigation(selectedCaseId),
                  icon: <Sparkles className="h-4 w-4" />,
                }}
              />
            </Card>
          )}

          {/* Structured Investigation Results */}
          {investigation && !investigationLoading && !investigationError && (
            <div className="space-y-4 max-h-[660px] overflow-y-auto pr-1 font-mono">
              {/* Investigation Provider Banner */}
              {investigation.ai_provider?.includes("ChatGPT") ? (
                <div className="bg-black border border-[#FFD400]/40 rounded-lg p-3 flex items-center justify-between text-xs text-white">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-[#FFD400] shrink-0" />
                    <span>
                      <strong>OpenAI {investigation.ai_provider}:</strong> Live forensic report grounded in multi-source ledger evidence.
                    </span>
                  </div>
                  <span className="text-[10px] bg-[#FFD400] text-black font-bold px-2 py-0.5 rounded uppercase font-mono">
                    LIVE GPT
                  </span>
                </div>
              ) : investigation.ai_provider === "DETERMINISTIC_FALLBACK" ? (
                <div className="bg-black border border-white/10 rounded-lg p-3 flex items-center justify-between text-xs text-white/70">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-[#FFD400] shrink-0" />
                    <span>
                      <strong>Deterministic Rule-Based Fallback Active:</strong> Reconciled using verified rules and multi-source evidence.
                    </span>
                  </div>
                  <button
                    onClick={() => setKeyModalOpen(true)}
                    className="text-[11px] underline text-[#FFD400] hover:text-white shrink-0 ml-2"
                  >
                    Activate ChatGPT &rarr;
                  </button>
                </div>
              ) : null}

              {/* Case Overview Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between py-3.5 px-5 border-b border-white/10">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-sm font-bold text-[#FFD400]">
                      {investigation.case_number}
                    </span>
                    <Badge
                      variant={
                        investigation.status === "RECONCILED"
                          ? "matched"
                          : investigation.status === "ESCALATED"
                          ? "critical"
                          : "warning"
                      }
                      size="sm"
                    >
                      {investigation.status}
                    </Badge>
                    <Badge variant="neutral" size="sm" showIcon={false}>
                      Confidence: {investigation.confidence_score}%
                    </Badge>
                  </div>

                  <Badge
                    variant={investigation.ai_provider?.includes("ChatGPT") || investigation.ai_provider === "NOVA_AI" ? "yellow" : "neutral"}
                    size="sm"
                  >
                    Provider: {investigation.ai_provider}
                  </Badge>
                </CardHeader>

                <CardContent className="p-5 space-y-5">
                  {/* 1. Executive Summary */}
                  <div>
                    <h4 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                      <FileText className="h-3.5 w-3.5 text-[#FFD400]" />
                      1. Executive Summary
                    </h4>
                    <p className="text-xs text-white bg-black p-3.5 rounded-lg border border-white/10 leading-relaxed font-sans">
                      {investigation.summary}
                    </p>
                  </div>

                  {/* 2. Why It Was Flagged */}
                  <div>
                    <h4 className="text-xs font-semibold text-[#FFD400] uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      2. Why It Was Flagged
                    </h4>
                    <p className="text-xs text-white/90 bg-black p-3 rounded-lg border border-[#FFD400]/30 leading-relaxed font-sans">
                      {investigation.why_flagged}
                    </p>
                  </div>

                  {/* 3. FACTS Panel */}
                  {investigation.facts && investigation.facts.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                        <Layers className="h-3.5 w-3.5 text-[#FFD400]" />
                        3. Ground Truth Facts (Deterministic Sources)
                      </h4>
                      <div className="bg-black rounded-lg border border-white/10 overflow-hidden font-mono">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-white/10 bg-[#111111] text-white/50 text-[11px]">
                              <th className="py-2 px-3">Field</th>
                              <th className="py-2 px-3">Value</th>
                              <th className="py-2 px-3">Source</th>
                              <th className="py-2 px-3">Description</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/5">
                            {investigation.facts.map((fact, idx) => (
                              <tr key={idx} className="hover:bg-white/[0.02]">
                                <td className="py-2 px-3 font-semibold text-white font-mono text-[11px]">
                                  {fact.field}
                                </td>
                                <td className="py-2 px-3 font-mono text-[#FFD400]">
                                  {String(fact.value)}
                                </td>
                                <td className="py-2 px-3 text-white/60">{fact.source}</td>
                                <td className="py-2 px-3 text-white/40">{fact.description || "—"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* 4. CALCULATIONS Panel */}
                  {investigation.calculated && investigation.calculated.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                        <Calculator className="h-3.5 w-3.5 text-[#FFD400]" />
                        4. Calculated Metrics & Formulas
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono">
                        {investigation.calculated.map((calc, idx) => (
                          <div
                            key={idx}
                            className="bg-black p-3 rounded-lg border border-white/10 text-xs"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-semibold text-white">{calc.metric}</span>
                              <span className="font-mono font-bold text-[#FFD400]">{String(calc.value)}</span>
                            </div>
                            <div className="font-mono text-[10px] text-white/50 bg-[#111111] p-1.5 rounded mb-1">
                              {calc.formula}
                            </div>
                            {calc.interpretation && (
                              <p className="text-[11px] text-white/60 font-sans">{calc.interpretation}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 5. Matching Evidence */}
                  <div>
                    <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                      <FileText className="h-3.5 w-3.5 text-[#FFD400]" />
                      5. Cross-Source Ledger Evidence
                    </h4>
                    {investigation.matched_evidence.length === 0 ? (
                      <div className="text-xs text-white/40 italic p-3 bg-black rounded-lg border border-white/10">
                        No paired transaction records found.
                      </div>
                    ) : (
                      <div className="space-y-1.5 font-mono">
                        {investigation.matched_evidence.map((src: any, idx: number) => (
                          <div
                            key={idx}
                            className="bg-black p-2.5 rounded-lg border border-white/10 flex items-center justify-between text-xs"
                          >
                            <div>
                              <span className="font-semibold text-white">
                                {src.source} #{src.transaction_id || src.invoice_number || `REC-${idx + 1}`}
                              </span>
                              <span className="text-white/40 ml-2">
                                {src.counterparty ? `Counterparty: ${src.counterparty}` : ""}
                              </span>
                            </div>
                            <div className="font-mono font-medium text-[#FFD400]">
                              ₹{Number(src.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })} {src.currency || "INR"}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 6. Discrepancies */}
                  <div>
                    <h4 className="text-xs font-semibold text-[#FFD400] uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                      <AlertCircle className="h-3.5 w-3.5" />
                      6. Flagged Discrepancies
                    </h4>
                    {investigation.discrepancies.length === 0 ? (
                      <div className="text-xs text-white bg-black border border-white/10 p-2.5 rounded-lg font-mono">
                        &check; Zero discrepancies flagged. All multi-source attributes match within tolerance.
                      </div>
                    ) : (
                      <div className="space-y-1.5 text-xs font-mono">
                        {investigation.discrepancies.map((d: any, idx: number) => (
                          <div
                            key={idx}
                            className="bg-black p-2.5 rounded-lg border border-white/10 flex items-center justify-between"
                          >
                            <div>
                              <span className="font-semibold text-[#FFD400] uppercase text-[11px]">
                                {d.type}: {d.field_name}
                              </span>
                              <div className="text-[11px] text-white/50 mt-0.5">
                                Source: <code className="text-white">{String(d.source_value)}</code> vs Matched:{" "}
                                <code className="text-white">{String(d.matched_value)}</code>
                              </div>
                            </div>
                            <div className="text-right">
                              <Badge variant="critical" size="xs">
                                {d.severity}
                              </Badge>
                              {d.difference_numeric !== null && (
                                <span className="font-mono text-white/60 text-[11px] block mt-0.5">
                                  &Delta; ₹{Number(d.difference_numeric).toFixed(2)}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 7. AI SUGGESTIONS Panel */}
                  {investigation.suggestions && investigation.suggestions.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-[#FFD400] uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                        <Lightbulb className="h-3.5 w-3.5" />
                        7. AI Resolution Suggestions
                      </h4>
                      <div className="space-y-2 font-mono">
                        {investigation.suggestions.map((sug, idx) => (
                          <div
                            key={idx}
                            className="bg-black p-3 rounded-lg border border-white/10 text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-white">{sug.action}</span>
                              <Badge variant="yellow" size="xs">
                                {sug.confidence_level} Confidence
                              </Badge>
                            </div>
                            <p className="text-white/60 font-sans">{sug.justification}</p>
                            {sug.recommended_entry && (
                              <div className="font-mono text-[10px] text-[#FFD400] bg-black p-1.5 rounded border border-[#FFD400]/30">
                                {sug.recommended_entry}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 8. Reviewer Attention */}
                  <div>
                    <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                      <ShieldCheck className="h-3.5 w-3.5 text-[#FFD400]" />
                      8. Reviewer Attention (Key Risk / Consideration)
                    </h4>
                    <p className="text-xs text-white bg-black p-3 rounded-lg border border-white/10 leading-relaxed font-sans">
                      {investigation.reviewer_attention}
                    </p>
                  </div>

                  {/* 9. Suggested Next Checks */}
                  <div>
                    <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
                      <CheckCircle2 className="h-3.5 w-3.5 text-[#FFD400]" />
                      9. Suggested Next Checks
                    </h4>
                    <ul className="space-y-1.5 text-xs font-mono">
                      {investigation.suggested_next_checks.map((check: string, idx: number) => (
                        <li
                          key={idx}
                          className="bg-black p-2.5 rounded-lg border border-white/10 flex items-start gap-2.5"
                        >
                          <span className="w-5 h-5 rounded-full bg-white/10 text-[#FFD400] flex items-center justify-center shrink-0 font-bold text-[10px]">
                            {idx + 1}
                          </span>
                          <span className="text-white leading-normal font-sans">{check}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 10. Suggested ERP Journal Adjustment Entry */}
                  {investigation.suggested_journal_entry && (
                    <div className="border-t border-white/10 pt-4 font-mono">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-semibold text-[#FFD400] uppercase tracking-wider flex items-center gap-1.5">
                          <Calculator className="h-3.5 w-3.5" />
                          Suggested ERP Journal Adjustment Entry
                        </h4>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            copyToClipboard(
                              JSON.stringify(investigation.suggested_journal_entry, null, 2),
                              "je"
                            )
                          }
                          className="h-7 text-xs text-white/50 hover:text-white font-mono"
                          iconLeft={
                            copiedKey === "je" ? (
                              <Check className="h-3 w-3 text-[#FFD400]" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )
                          }
                        >
                          Copy Entry JSON
                        </Button>
                      </div>

                      <div className="bg-black border border-white/10 rounded-lg p-3.5 text-xs space-y-2.5">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-white">
                            {investigation.suggested_journal_entry.title}
                          </span>
                          <span className="font-mono text-white/40">
                            Ref: {investigation.suggested_journal_entry.reference}
                          </span>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-[11px] border-collapse font-mono">
                            <thead>
                              <tr className="border-b border-white/10 text-white/50">
                                <th className="py-1.5 px-2">Account</th>
                                <th className="py-1.5 px-2">Description</th>
                                <th className="py-1.5 px-2 text-right">Debit ($)</th>
                                <th className="py-1.5 px-2 text-right">Credit ($)</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                              {investigation.suggested_journal_entry.lines.map((l: any, idx: number) => (
                                <tr key={idx} className="hover:bg-white/[0.02]">
                                  <td className="py-1.5 px-2 font-mono text-white">{l.account_number}</td>
                                  <td className="py-1.5 px-2 text-white/60">{l.account_name}</td>
                                  <td className="py-1.5 px-2 text-right font-mono text-[#FFD400]">
                                    {l.debit > 0 ? `$${Number(l.debit).toFixed(2)}` : "—"}
                                  </td>
                                  <td className="py-1.5 px-2 text-right font-mono text-white">
                                    {l.credit > 0 ? `$${Number(l.credit).toFixed(2)}` : "—"}
                                  </td>
                                </tr>
                              ))}
                              <tr className="font-bold border-t border-white/10 pt-1 text-white">
                                <td colSpan={2} className="py-2 px-2">
                                  Total Balanced
                                </td>
                                <td className="py-2 px-2 text-right font-mono text-[#FFD400]">
                                  ${Number(investigation.suggested_journal_entry.total_debit).toFixed(2)}
                                </td>
                                <td className="py-2 px-2 text-right font-mono text-white">
                                  ${Number(investigation.suggested_journal_entry.total_credit).toFixed(2)}
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* OpenAI ChatGPT Configuration Modal */}
      {keyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#0A0A0A] border border-white/20 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden font-mono">
            {/* Modal Header */}
            <div className="p-5 border-b border-white/10 bg-black flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-[#FFD400]/10 border border-[#FFD400]/30 text-[#FFD400]">
                  <Key className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Connect OpenAI ChatGPT
                  </h3>
                  <p className="text-[11px] text-white/50">
                    Live GPT-4o financial forensic reasoning across reconciliation ledgers
                  </p>
                </div>
              </div>
              <button
                onClick={() => setKeyModalOpen(false)}
                className="p-1 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-5">
              {/* Current Status Pill */}
              <div className="p-3 rounded-xl bg-black border border-white/10 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      aiStatus?.openai_configured ? "bg-[#FFD400] animate-pulse" : "bg-white/30"
                    }`}
                  />
                  <span className="text-white/70">Status:</span>
                  <span className="text-white font-semibold">
                    {aiStatus?.openai_configured ? `Active (${aiStatus.model})` : "Key Required"}
                  </span>
                </div>
                {aiStatus?.key_preview && (
                  <span className="text-[11px] text-[#FFD400] bg-[#FFD400]/10 px-2 py-0.5 rounded border border-[#FFD400]/20 font-mono">
                    {aiStatus.key_preview}
                  </span>
                )}
              </div>

              {/* Model Selection */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-white/80 uppercase tracking-wider block">
                  Select Reasoning Model
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedModel("gpt-4o-mini")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      selectedModel === "gpt-4o-mini"
                        ? "bg-black border-[#FFD400] text-white"
                        : "bg-black/50 border-white/10 text-white/60 hover:border-white/30"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-[#FFD400]">gpt-4o-mini</span>
                      {selectedModel === "gpt-4o-mini" && <Check className="h-3.5 w-3.5 text-[#FFD400]" />}
                    </div>
                    <p className="text-[10px] text-white/50 leading-tight">
                      Fast, lightweight, ideal for standard exception inquiries.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedModel("gpt-4o")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      selectedModel === "gpt-4o"
                        ? "bg-black border-[#FFD400] text-white"
                        : "bg-black/50 border-white/10 text-white/60 hover:border-white/30"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-[#FFD400]">gpt-4o</span>
                      {selectedModel === "gpt-4o" && <Check className="h-3.5 w-3.5 text-[#FFD400]" />}
                    </div>
                    <p className="text-[10px] text-white/50 leading-tight">
                      Flagship intelligence for deep forensic audits and complex ERP entries.
                    </p>
                  </button>
                </div>
              </div>

              {/* API Key Input */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-white/80 uppercase tracking-wider">
                    OpenAI API Key
                  </label>
                  <span className="text-[10px] text-white/40">sk-proj-...</span>
                </div>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder={aiStatus?.openai_configured ? "Enter new key to replace current key..." : "Paste your sk-... key here"}
                  className="w-full bg-black border border-white/20 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-white/30 focus:outline-none focus:border-[#FFD400] transition-colors font-mono"
                />
                <p className="text-[10px] text-white/40 leading-relaxed">
                  Your key is sent securely to the local FinRecon backend and saved in <code className="text-white/60">.env</code>. It is never exposed in client browser bundles.
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-white/10 bg-black flex items-center justify-end gap-2.5">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setKeyModalOpen(false)}
                className="text-xs text-white/70 hover:text-white font-mono"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveApiKey}
                disabled={savingKey || !apiKeyInput.trim()}
                className="text-xs font-mono font-bold bg-[#FFD400] hover:bg-[#e6be00] text-black"
                iconLeft={savingKey ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Key className="h-3.5 w-3.5" />}
              >
                {savingKey ? "Activating..." : "Save & Activate ChatGPT"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

