export type SourceType = 'BANK' | 'PAYMENT_GATEWAY' | 'ACCOUNTING' | 'INVOICE' | 'CRYPTO';

export type MatchStatus = 
  | 'EXACT_MATCH'
  | 'PARTIAL_MATCH'
  | 'DUPLICATE'
  | 'POSSIBLE_DUPLICATE'
  | 'MISSING_RECORD'
  | 'CONFLICTING_RECORD'
  | 'UNMATCHED';

export type DiscrepancyType = 
  | 'NONE'
  | 'AMOUNT'
  | 'DATE'
  | 'ENTITY'
  | 'DUPLICATE_ENTRY'
  | 'MISSING_ENTRY'
  | 'CONFLICTING_DATA'
  | 'CURRENCY'
  | 'STATUS'
  | 'MULTI_FIELD';

export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type ReviewStatus = 'OPEN' | 'UNDER_REVIEW' | 'RECONCILED' | 'REJECTED' | 'ESCALATED';

export type BlockchainNetwork = 'ETHEREUM' | 'POLYGON' | 'BITCOIN' | 'SOLANA' | 'ARBITRUM';

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  database_connected: boolean;
  python_version: string;
  supported_sources: SourceType[];
  nova_configured?: boolean;
  NOVA_CONFIGURED?: boolean;
}

export interface CanonicalTransaction {
  id: string;
  transaction_id: string;
  source_type: SourceType;
  source_name: string;
  account_reference?: string;
  counterparty_name?: string;
  counterparty_id?: string;
  amount: number;
  currency: string;
  direction: 'CREDIT' | 'DEBIT';
  transaction_date: string;
  transaction_timestamp?: string;
  reference_number?: string;
  invoice_id?: string;
  payment_reference?: string;
  description?: string;
  raw_data?: Record<string, unknown>;
  normalized_at: string;
  created_at: string;
}

export interface CanonicalInvoice {
  id: string;
  invoice_number: string;
  issuer_name: string;
  recipient_name: string;
  recipient_email?: string;
  total_amount: number;
  currency: string;
  issue_date: string;
  due_date?: string;
  status: string;
  reference_order_id?: string;
  created_at: string;
}

export interface CanonicalCryptoTransaction {
  id: string;
  transaction_hash: string;
  blockchain_network: BlockchainNetwork;
  wallet_from: string;
  wallet_to: string;
  asset: string;
  token_amount: number;
  fiat_value?: number;
  fiat_currency: string;
  transaction_timestamp: string;
  block_number?: number;
  gas_fee?: number;
  gas_fee_currency?: string;
  confirmation_status: string;
  associated_invoice_id?: string;
  associated_reference?: string;
  created_at: string;
}

export interface MatchEvidence {
  rule_applied: string;
  entity_similarity_score?: number;
  amount_difference?: number;
  amount_difference_percentage?: number;
  date_difference_days?: number;
  reference_match: boolean;
  hash_match: boolean;
  details: string[];
}

export interface ReconciliationMatchResult {
  case_id: string;
  primary_transaction_id: string;
  matched_transaction_id?: string;
  status: MatchStatus;
  confidence_score: number;
  confidence_level: ConfidenceLevel;
  discrepancy_type: DiscrepancyType;
  evidence: MatchEvidence;
}

export interface IngestionSummary {
  file_name: string;
  source_type: SourceType;
  total_records: number;
  processed_records: number;
  failed_records: number;
  warnings: string[];
  ingested_at: string;
}

export type UserRole = 'USER' | 'AUDITOR' | 'MANAGER';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
  last_login_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface DemoUser {
  role: UserRole;
  name: string;
  email: string;
  description: string;
}
