import axios from "axios";
import { HealthResponse, IngestionSummary, SourceType, AuthUser, LoginResponse, DemoUser } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Auto-sync baseURL hostname and attach JWT Bearer token from localStorage
if (typeof window !== "undefined") {
  apiClient.interceptors.request.use((config) => {
    if (window.location && window.location.hostname) {
      const currentHost = window.location.hostname;
      if (
        config.baseURL &&
        (config.baseURL.includes("127.0.0.1:8000") || config.baseURL.includes("localhost:8000"))
      ) {
        config.baseURL = `http://${currentHost}:8000/api/v1`;
      }
    }
    const token = localStorage.getItem("finrecon_token");
    if (token && config.headers && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Global 401 Session Expiration Handler
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401 && window.location.pathname !== "/login") {
        localStorage.removeItem("finrecon_token");
        localStorage.removeItem("finrecon_user");
        window.dispatchEvent(new CustomEvent("finrecon_auth_expired"));
      }
      return Promise.reject(error);
    }
  );
}

export interface DataSourceItem {
  id: string;
  name: string;
  source_type: SourceType;
  file_format: string;
  account_identifier: string;
  currency: string;
  is_active: boolean;
  records_count: number;
  owner_id?: string;
  created_at: string;
}

export interface IngestionApiResponse {
  status: string;
  message: string;
  summary: IngestionSummary & {
    detected_columns: Record<string, string>;
    preview: Array<Record<string, unknown>>;
  };
}

// ---------------------------------------------------------------------------
// High-Performance In-Memory Client Cache & In-Flight Request Deduplication
// ---------------------------------------------------------------------------
interface CacheEntry<T = unknown> {
  data: T;
  timestamp: number;
}

const memoryCache = new Map<string, CacheEntry<any>>();
const inFlightRequests = new Map<string, Promise<any>>();

export function clearApiCache(prefix?: string) {
  if (!prefix) {
    memoryCache.clear();
    return;
  }
  memoryCache.forEach((_, key) => {
    if (key.includes(prefix)) {
      memoryCache.delete(key);
    }
  });
}

async function cachedGet<T>(
  url: string,
  config?: Record<string, any>,
  ttlMs: number = 30000,
  bypassCache: boolean = false
): Promise<T> {
  const cacheKey = config ? `${url}_${JSON.stringify(config)}` : url;
  const now = Date.now();

  if (!bypassCache) {
    const cached = memoryCache.get(cacheKey);
    if (cached && now - cached.timestamp < ttlMs) {
      return cached.data as T;
    }
  }

  // Deduplicate concurrent in-flight requests
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)! as Promise<T>;
  }

  const promise = apiClient
    .get<T>(url, config)
    .then((res) => {
      memoryCache.set(cacheKey, { data: res.data, timestamp: Date.now() });
      inFlightRequests.delete(cacheKey);
      return res.data;
    })
    .catch((err) => {
      inFlightRequests.delete(cacheKey);
      const stale = memoryCache.get(cacheKey);
      if (stale) {
        console.warn(`[FinRecon API] Network request to ${url} failed, serving stale cache.`, err?.message);
        return stale.data as T;
      }
      throw err;
    });

  inFlightRequests.set(cacheKey, promise);
  return promise;
}

export const api = {
  // Authentication & Access Control
  login: async (credentials: { email: string; password: string; role?: string }): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>("/auth/login", credentials);
    if (res.data?.access_token && typeof window !== "undefined") {
      localStorage.setItem("finrecon_token", res.data.access_token);
      localStorage.setItem("finrecon_user", JSON.stringify(res.data.user));
    }
    return res.data;
  },

  signup: async (userData: { name: string; email: string; password: string }): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>("/auth/signup", userData);
    if (res.data?.access_token && typeof window !== "undefined") {
      localStorage.setItem("finrecon_token", res.data.access_token);
      localStorage.setItem("finrecon_user", JSON.stringify(res.data.user));
    }
    return res.data;
  },

  getMe: async (): Promise<AuthUser> => {
    const res = await apiClient.get<AuthUser>("/auth/me");
    if (res.data && typeof window !== "undefined") {
      localStorage.setItem("finrecon_user", JSON.stringify(res.data));
    }
    return res.data;
  },

  logout: async (): Promise<any> => {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem("finrecon_token");
        localStorage.removeItem("finrecon_user");
      }
      clearApiCache();
    }
  },

  getDemoUsers: async (): Promise<DemoUser[]> => {
    return cachedGet<DemoUser[]>("/auth/demo-users", undefined, 60000);
  },

  // Cache utilities
  clearCache: clearApiCache,
  invalidateCache: clearApiCache,

  // Health
  getHealth: async (bypassCache: boolean = false): Promise<HealthResponse> => {
    return cachedGet<HealthResponse>("/health", undefined, 10000, bypassCache);
  },

  // Ingestion
  uploadFile: async (
    file: File,
    sourceType: SourceType,
    sourceName?: string,
    accountId?: string,
    accountIdentifier?: string
  ): Promise<IngestionApiResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("source_type", sourceType);
    if (sourceName) {
      formData.append("source_name", sourceName);
    }
    if (accountId) {
      formData.append("account_id", accountId);
    }
    if (accountIdentifier) {
      formData.append("account_identifier", accountIdentifier);
    }
    const res = await apiClient.post<IngestionApiResponse>("/ingestion/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    clearApiCache();
    return res.data;
  },

  getAccounts: async (bypassCache: boolean = false): Promise<DataSourceItem[]> => {
    return cachedGet<DataSourceItem[]>("/ingestion/accounts", undefined, 10000, bypassCache);
  },

  createAccount: async (payload: {
    name: string;
    source_type: string;
    account_identifier?: string;
    currency?: string;
    file_format?: string;
  }): Promise<any> => {
    const res = await apiClient.post("/ingestion/accounts", payload);
    clearApiCache("/ingestion");
    return res.data;
  },

  deleteAccount: async (accountId: string): Promise<any> => {
    const res = await apiClient.delete(`/ingestion/accounts/${accountId}`);
    clearApiCache("/ingestion");
    return res.data;
  },

  getDataSources: async (bypassCache: boolean = false): Promise<DataSourceItem[]> => {
    return cachedGet<DataSourceItem[]>("/ingestion/sources", undefined, 30000, bypassCache);
  },

  getDatabaseSummary: async (bypassCache: boolean = false): Promise<Record<string, any>> => {
    return cachedGet<Record<string, any>>("/database-summary", undefined, 30000, bypassCache);
  },

  // Aczen Nova Live Books Sync
  syncAczenData: async (purgeOldData: boolean = true): Promise<any> => {
    const res = await apiClient.post(`/ingestion/sync-aczen?purge_old_data=${purgeOldData}`);
    clearApiCache();
    return res.data;
  },

  getAczenStatus: async (bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>("/ingestion/aczen-status", undefined, 30000, bypassCache);
  },

  // Entity Resolution
  resolveEntity: async (query: {
    name?: string;
    email?: string;
    phone?: string;
    tax_id?: string;
    wallet_address?: string;
    bank_account_number?: string;
  }): Promise<any> => {
    const res = await apiClient.post("/entities/resolve", query);
    return res.data;
  },

  getEntities: async (bypassCache: boolean = false): Promise<any[]> => {
    return cachedGet<any[]>("/entities", undefined, 45000, bypassCache);
  },

  // Reconciliation
  runReconciliation: async (params: {
    case_title?: string;
    amount_tolerance?: number;
    date_tolerance_days?: number;
    date_from?: string;
    date_to?: string;
  } = {}): Promise<any> => {
    const res = await apiClient.post("/reconciliation/run", params);
    clearApiCache();
    return res.data;
  },

  getReconciliationCases: async (bypassCache: boolean = false): Promise<any[]> => {
    return cachedGet<any[]>("/reconciliation/cases", undefined, 30000, bypassCache);
  },

  getReconciliationCaseDetail: async (caseId: string, bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>(`/reconciliation/cases/${caseId}`, undefined, 30000, bypassCache);
  },

  getMatches: async (caseId?: string, status?: string, bypassCache: boolean = false): Promise<any[]> => {
    const params: Record<string, string> = {};
    if (caseId) params.case_id = caseId;
    if (status) params.match_status = status;
    return cachedGet<any[]>("/reconciliation/matches", { params }, 30000, bypassCache);
  },

  submitMatchReview: async (
    matchId: string,
    payload: { reviewer_name: string; action: string; notes?: string }
  ): Promise<any> => {
    const res = await apiClient.post(`/reconciliation/matches/${matchId}/review`, payload);
    clearApiCache("/reconciliation");
    clearApiCache("/audit");
    clearApiCache("/database-summary");
    return res.data;
  },

  // Crypto
  getCryptoTransactions: async (
    params: { network?: string; limit?: number } = {},
    bypassCache: boolean = false
  ): Promise<any[]> => {
    return cachedGet<any[]>("/crypto/transactions", { params }, 30000, bypassCache);
  },

  getCryptoWallets: async (bypassCache: boolean = false): Promise<any[]> => {
    return cachedGet<any[]>("/crypto/wallets", undefined, 30000, bypassCache);
  },

  getCryptoAnalytics: async (bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>("/crypto/analytics", undefined, 30000, bypassCache);
  },

  calculateGas: async (params: {
    blockchain_network: string;
    gas_units: number;
    gas_price_gwei: number;
    native_usd_price?: number;
  }): Promise<any> => {
    const res = await apiClient.post("/crypto/calculate-gas", params);
    return res.data;
  },

  analyzeSlippage: async (params: {
    expected_fiat_amount: number;
    actual_fiat_amount: number;
    tolerance_percentage?: number;
  }): Promise<any> => {
    const res = await apiClient.post("/crypto/slippage-analysis", params);
    return res.data;
  },

  // Exception Workbench
  getExceptions: async (
    params: {
      status?: string;
      severity?: string;
      root_cause?: string;
      discrepancy_type?: string;
      limit?: number;
    } = {},
    bypassCache: boolean = false
  ): Promise<any[]> => {
    return cachedGet<any[]>("/exceptions", { params }, 30000, bypassCache);
  },

  getExceptionsSummary: async (bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>("/exceptions/summary", undefined, 30000, bypassCache);
  },

  getExceptionDetail: async (exceptionId: string, bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>(`/exceptions/${exceptionId}`, undefined, 30000, bypassCache);
  },

  applyExceptionAction: async (
    exceptionId: string,
    payload: {
      reviewer_name: string;
      action: string;
      notes?: string;
      adjustment_amount?: number;
      assigned_to?: string;
    }
  ): Promise<any> => {
    const res = await apiClient.post(`/exceptions/${exceptionId}/action`, payload);
    clearApiCache("/exceptions");
    clearApiCache("/audit");
    clearApiCache("/database-summary");
    return res.data;
  },

  applyBulkExceptionActions: async (payload: {
    exception_ids: string[];
    reviewer_name: string;
    action: string;
    notes?: string;
  }): Promise<any> => {
    const res = await apiClient.post("/exceptions/bulk-action", payload);
    clearApiCache("/exceptions");
    clearApiCache("/audit");
    clearApiCache("/database-summary");
    return res.data;
  },

  // Step 9: Audit & Compliance Endpoints
  getAuditLogs: async (
    params?: {
      actor_type?: string;
      actor_id?: string;
      action?: string;
      entity_type?: string;
      entity_id?: string;
      case_id?: string;
      query?: string;
      limit?: number;
      offset?: number;
    },
    bypassCache: boolean = false
  ): Promise<any> => {
    const cleanParams: Record<string, any> = {};
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== "") {
          cleanParams[key] = value;
        }
      }
    }
    return cachedGet<any>(
      "/audit/logs",
      Object.keys(cleanParams).length > 0 ? { params: cleanParams } : undefined,
      30000,
      bypassCache
    );
  },

  getAuditSummary: async (bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>("/audit/summary", undefined, 30000, bypassCache);
  },

  verifyAuditIntegrity: async (): Promise<any> => {
    const res = await apiClient.post("/audit/verify-integrity");
    clearApiCache("/audit");
    return res.data;
  },

  getAuditLogDetail: async (logId: string, bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>(`/audit/logs/${logId}`, undefined, 30000, bypassCache);
  },

  getAuditCSVUrl: (params?: {
    actor_type?: string;
    action?: string;
    entity_type?: string;
    query?: string;
  }) => {
    const base = `${API_BASE_URL}/audit/export/csv`;
    const searchParams = new URLSearchParams();
    if (params?.actor_type) searchParams.set("actor_type", params.actor_type);
    if (params?.action) searchParams.set("action", params.action);
    if (params?.entity_type) searchParams.set("entity_type", params.entity_type);
    if (params?.query) searchParams.set("query", params.query);
    const qs = searchParams.toString();
    return qs ? `${base}?${qs}` : base;
  },

  exportCompliancePackage: async (): Promise<any> => {
    const res = await apiClient.get("/audit/export/compliance-package");
    return res.data;
  },

  // Step 10: AI Assistant & Natural Language Explanations
  getAIPrompts: async (bypassCache: boolean = false): Promise<any[]> => {
    return cachedGet<any[]>("/ai-assistant/prompts", undefined, 60000, bypassCache);
  },

  sendAIChat: async (payload: { query: string; case_id?: string }): Promise<any> => {
    const res = await apiClient.post("/ai-assistant/chat", payload);
    return res.data;
  },

  explainAICase: async (caseId: string): Promise<any> => {
    const res = await apiClient.post(`/ai-assistant/explain/case/${caseId}`);
    return res.data;
  },

  explainAIDiscrepancy: async (discrepancyId: string): Promise<any> => {
    const res = await apiClient.post(`/ai-assistant/explain/discrepancy/${discrepancyId}`);
    return res.data;
  },

  // FIN-26 Nova Investigation Endpoint
  explainCaseWithNova: async (payload: { reconciliation_case_id: string; question?: string }): Promise<any> => {
    const res = await apiClient.post("/ai-assistant/explain", payload);
    return res.data;
  },

  getAIStatus: async (bypassCache: boolean = false): Promise<{
    openai_configured: boolean;
    model: string;
    provider: string;
    key_preview?: string;
    nova_configured: boolean;
    active_engine: string;
  }> => {
    return cachedGet<any>("/ai-assistant/status", undefined, 5000, bypassCache);
  },

  configureAIKey: async (payload: { api_key: string; model?: string }): Promise<any> => {
    const res = await apiClient.post("/ai-assistant/configure-key", payload);
    clearApiCache("/ai-assistant");
    return res.data;
  },

  getSystemHealth: async (bypassCache: boolean = false): Promise<any> => {
    return cachedGet<any>("/health", undefined, 10000, bypassCache);
  },
};
