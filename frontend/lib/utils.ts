import type { RiskLevel } from './types';

// ── Risk colors (Professional Light Theme) ───────────────────
export const RISK_COLORS: Record<RiskLevel, string> = {
  CRITICAL: '#dc2626',
  HIGH:     '#ea580c',
  MEDIUM:   '#2563eb',
  LOW:      '#16a34a',
  UNKNOWN:  '#64748b',
};

export const RISK_BG: Record<RiskLevel, string> = {
  CRITICAL: '#fef2f2',
  HIGH:     '#fff7ed',
  MEDIUM:   '#eff6ff',
  LOW:      '#f0fdf4',
  UNKNOWN:  '#f1f5f9',
};

// ── Trust level display ──────────────────────────────────────
export const TRUST_LABELS: Record<string, string> = {
  AUTHORITATIVE: 'Tier 1 — Authoritative',
  HIGH:          'Tier 2 — High Trust',
  MEDIUM:        'Tier 3 — Medium Trust',
  UNTRUSTED:     'Tier 4 — Untrusted',
};

export const TRUST_COLORS: Record<string, string> = {
  AUTHORITATIVE: '#16a34a',
  HIGH:          '#2563eb',
  MEDIUM:        '#d97706',
  UNTRUSTED:     '#dc2626',
};

export const TRUST_BG: Record<string, string> = {
  AUTHORITATIVE: '#f0fdf4',
  HIGH:          '#eff6ff',
  MEDIUM:        '#fffbeb',
  UNTRUSTED:     '#fef2f2',
};

// ── Verification status display ──────────────────────────────
export const VERIFICATION_LABELS: Record<string, string> = {
  VERIFIED:                'Verified',
  EVIDENCE_UNVERIFIED:     'Unverified',
  SOURCE_UNAVAILABLE:      'Source Unavailable',
  SECURITY_QUARANTINED:    'Quarantined',
  SOURCE_CONFLICT:         'Source Conflict',
  DATE_UNCLEAR:            'Date Unclear',
  APPLICABILITY_UNKNOWN:   'Applicability Unknown',
  REQUIRES_HUMAN_REVIEW:   'Requires Review',
};

export const VERIFICATION_COLORS: Record<string, string> = {
  VERIFIED:                '#16a34a',
  EVIDENCE_UNVERIFIED:     '#d97706',
  SOURCE_UNAVAILABLE:      '#64748b',
  SECURITY_QUARANTINED:    '#dc2626',
  SOURCE_CONFLICT:         '#dc2626',
  DATE_UNCLEAR:            '#d97706',
  APPLICABILITY_UNKNOWN:   '#64748b',
  REQUIRES_HUMAN_REVIEW:   '#d97706',
};

export const VERIFICATION_BG: Record<string, string> = {
  VERIFIED:                '#f0fdf4',
  EVIDENCE_UNVERIFIED:     '#fffbeb',
  SOURCE_UNAVAILABLE:      '#f1f5f9',
  SECURITY_QUARANTINED:    '#fef2f2',
  SOURCE_CONFLICT:         '#fef2f2',
  DATE_UNCLEAR:            '#fffbeb',
  APPLICABILITY_UNKNOWN:   '#f1f5f9',
  REQUIRES_HUMAN_REVIEW:   '#fffbeb',
};

// ── Regulatory body short labels ─────────────────────────────
export const REG_BODY_COLORS: Record<string, string> = {
  RBI:      '#2563eb',
  MeitY:    '#16a34a',
  'CERT-In': '#d97706',
  MCA:      '#7c3aed',
  SEBI:     '#e11d48',
  IRDAI:    '#0284c7',
};

// ── Event type icons (SSE) ───────────────────────────────────
export const EVENT_ICONS: Record<string, string> = {
  STARTED:           '🚀',
  INITIALIZING:      '⚙️',
  QUERY_GENERATION:  '🔍',
  QUERIES_READY:     '📋',
  SEARCHING:         '🌐',
  SEARCH_RESULTS:    '📊',
  SEARCH_COMPLETE:   '✅',
  FETCHING:          '📥',
  SECURITY_QUARANTINE: '🛡️',
  EXTRACTION_SUCCESS: '✨',
  EXTRACTION_STATUS: 'ℹ️',
  PROCESSING_ERROR:  '⚠️',
  GENERATING_REPORT: '📝',
  REPORT_SAVED:      '💾',
  IMPORTING:         '🗄️',
  COMPLETE:          '🎯',
  FAILED:            '❌',
  TIMEOUT:           '⏱️',
};

// ── Formatting helpers ───────────────────────────────────────
export function formatDate(iso: string): string {
  if (!iso || iso === 'DATE_UNCLEAR' || iso === 'UNKNOWN') return '—';
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  } catch {
    return iso;
  }
}

export function formatDateTime(iso: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export function timeAgo(iso: string): string {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function truncate(s: string, n: number): string {
  if (!s) return '';
  return s.length <= n ? s : s.slice(0, n) + '…';
}

export function domainFromUrl(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}
