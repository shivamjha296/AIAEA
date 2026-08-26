// TypeScript interfaces matching the Python Pydantic models exactly.
// All types are derived from models.py — no invented fields.

export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
export type TrustLevel = 'AUTHORITATIVE' | 'HIGH' | 'MEDIUM' | 'UNTRUSTED';
export type VerificationStatus =
  | 'VERIFIED'
  | 'EVIDENCE_UNVERIFIED'
  | 'SOURCE_UNAVAILABLE'
  | 'SECURITY_QUARANTINED'
  | 'SOURCE_CONFLICT'
  | 'DATE_UNCLEAR'
  | 'APPLICABILITY_UNKNOWN'
  | 'REQUIRES_HUMAN_REVIEW';

export type ExtractionStatus =
  | 'SUCCESS'
  | 'FAILED'
  | 'PENDING'
  | 'QUARANTINED'
  | 'SECURITY_QUARANTINED'
  | 'SOURCE_UNAVAILABLE'
  | 'SKIPPED_LOW_TRUST'
  | 'EXTRACTION_FAILED';

export type RegStatus =
  | 'NEW' | 'AMENDMENT' | 'REPEAL' | 'CIRCULAR'
  | 'NOTIFICATION' | 'GUIDELINE' | 'GOVERNMENT_ORDER'
  | 'COURT_DECISION' | 'COMMENTARY' | 'IRRELEVANT' | 'UNKNOWN';

// ── Regulation list item (from /api/regulations) ──
export interface RegulationListItem {
  id: string;
  title: string;
  regulatory_body: string;
  risk_level: RiskLevel;
  effective_date: string;
  verification_status: VerificationStatus;
  extraction_status: ExtractionStatus;
  reg_status: RegStatus;
  source_url: string;
  trust_level: TrustLevel;
  source_tier: number;
  created_at: string;
  reg_publication_date: string;
  summary: string;
  security_quarantined: number;
}

// ── Key requirement / evidence ──
export interface EvidenceItem {
  claim: string;
  source_quote: string;
  page_or_section: string;
  verified?: boolean;
}

// ── Action item ──
export interface ActionItem {
  action_title: string;
  department: string;
  priority: RiskLevel;
  deadline: string;
  rationale: string;
}

// ── Security threat ──
export interface ThreatDetail {
  threat_type: string;
  pattern_matched: string;
  location: string;
  severity: string;
}

// ── Full regulation detail (from /api/regulations/:id) ──
export interface RegulationDetail extends RegulationListItem {
  scan_id: string;
  source_domain: string;
  source_title: string;
  content_type: string;
  search_query: string;
  retrieved_at: string;
  publication_date: string;
  verified_claims: number;
  total_claims: number;
  jurisdiction: string;
  summary: string;
  applicability_sectors: string[];
  penalties: string;
  key_requirements: EvidenceItem[];
  is_applicable: number;
  applicability_rationale: string;
  affected_processes: string[];
  compliance_gaps: string[];
  risk_rationale: string;
  recommended_actions: ActionItem[];
  internal_review_required: number;
  security_injection_detected: number;
  security_threats: ThreatDetail[];
  security_threat_count: number;
  security_scan_timestamp: string;
  processing_notes: string[];
}

// ── Paginated list response ──
export interface PaginatedRegulations {
  total: number;
  page: number;
  page_size: number;
  items: RegulationListItem[];
}

// ── Dashboard metrics ──
export interface DashboardMetrics {
  total_regulations: number;
  high_risk: number;
  critical: number;
  pending_review: number;
  verified_sources: number;
  quarantined_sources: number;
  security_events: number;
  last_scan_at: string | null;
}

// ── Risk distribution ──
export interface RiskDistribution {
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
  UNKNOWN: number;
}

// ── Regulator distribution ──
export interface RegulatorCount {
  regulatory_body: string;
  count: number;
}

// ── Activity chart ──
export interface ActivityPoint {
  date: string;
  count: number;
  bodies: string;
}

// ── Security event ──
export interface SecurityEvent {
  id: number;
  scan_id: string;
  source_url: string;
  threat_type: string;
  pattern_matched: string;
  severity: string;
  action: string;
  created_at: string;
  source_title?: string;
  trust_level?: TrustLevel;
}

// ── Security metrics ──
export interface SecurityMetrics {
  sources_scanned: number;
  suspicious: number;
  quarantined: number;
  security_events: number;
  clean: number;
}

// ── Review ──
export interface Review {
  id: number;
  regulation_id: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reviewer: string | null;
  decision: string | null;
  reason: string | null;
  risk_level: RiskLevel;
  recommendation: string;
  regulation_title: string;
  created_at: string;
  decided_at: string | null;
  // joined from regulations
  summary: string;
  affected_processes: string[];
  compliance_gaps: string[];
  recommended_actions: ActionItem[];
  source_url: string;
  effective_date: string;
  verification_status: VerificationStatus;
}

// ── Audit event ──
export interface AuditEvent {
  id: number;
  scan_id: string;
  regulation_id: string | null;
  event_type: string;
  message: string;
  detail: string | null;
  created_at: string;
}

// ── Scan ──
export interface Scan {
  id: string;
  started_at: string;
  completed_at: string | null;
  status: 'RUNNING' | 'COMPLETE' | 'FAILED';
  queries_run: number;
  sources_found: number;
  sources_processed: number;
  sources_quarantined: number;
  new_regulations: number;
  error_message: string | null;
}

// ── SSE event ──
export interface ScanEvent {
  event: string;
  message: string;
  data?: Record<string, unknown> | null;
  timestamp?: string;
}

// ── Health ──
export interface HealthStatus {
  api: string;
  database: string;
  llm: string;
  search: string;
  overall: string;
}
