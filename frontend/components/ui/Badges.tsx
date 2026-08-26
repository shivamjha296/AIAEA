import type { RiskLevel, TrustLevel, VerificationStatus, ExtractionStatus } from '@/lib/types';
import {
  RISK_COLORS, RISK_BG,
  TRUST_COLORS, TRUST_BG, TRUST_LABELS,
  VERIFICATION_COLORS, VERIFICATION_BG, VERIFICATION_LABELS
} from '@/lib/utils';

// ── Risk Badge ──────────────────────────────────────────────

export function RiskBadge({ level }: { level: RiskLevel | string }) {
  const l = (level || 'UNKNOWN') as RiskLevel;
  const color = RISK_COLORS[l] || RISK_COLORS.UNKNOWN;
  const bg = RISK_BG[l] || RISK_BG.UNKNOWN;
  return (
    <span className="badge" style={{
      background: bg,
      color: color,
      border: `1px solid ${color}33`,
    }}>
      {l === 'CRITICAL' && <span style={{ fontSize: 8 }}>●</span>}
      {l}
    </span>
  );
}

// ── Trust Badge ─────────────────────────────────────────────

export function TrustBadge({ level, tier }: { level: TrustLevel | string; tier?: number }) {
  const color = TRUST_COLORS[level as TrustLevel] || '#64748b';
  const bg = TRUST_BG[level as TrustLevel] || '#f1f5f9';
  return (
    <span className="badge" style={{
      background: bg,
      color,
      border: `1px solid ${color}33`,
    }}>
      {tier !== undefined ? `T${tier}` : ''} {TRUST_LABELS[level] || level}
    </span>
  );
}

// ── Verification Badge ──────────────────────────────────────

export function VerificationBadge({ status }: { status: VerificationStatus | string }) {
  const color = VERIFICATION_COLORS[status as VerificationStatus] || '#64748b';
  const bg = VERIFICATION_BG[status as VerificationStatus] || '#f1f5f9';
  return (
    <span className="badge" style={{
      background: bg,
      color,
      border: `1px solid ${color}33`,
    }}>
      {VERIFICATION_LABELS[status] || status}
    </span>
  );
}

// ── Extraction Status Badge ─────────────────────────────────

export function StatusBadge({ status }: { status: ExtractionStatus | string }) {
  const COLORS: Record<string, { color: string; bg: string }> = {
    SUCCESS: { color: '#16a34a', bg: '#f0fdf4' },
    FAILED: { color: '#dc2626', bg: '#fef2f2' },
    PENDING: { color: '#64748b', bg: '#f1f5f9' },
    QUARANTINED: { color: '#dc2626', bg: '#fef2f2' },
    SECURITY_QUARANTINED: { color: '#dc2626', bg: '#fef2f2' },
    SOURCE_UNAVAILABLE: { color: '#64748b', bg: '#f1f5f9' },
    SKIPPED_LOW_TRUST: { color: '#d97706', bg: '#fffbeb' },
    EXTRACTION_FAILED: { color: '#dc2626', bg: '#fef2f2' },
  };
  const item = COLORS[status] || { color: '#64748b', bg: '#f1f5f9' };
  return (
    <span className="badge" style={{
      background: item.bg,
      color: item.color,
      border: `1px solid ${item.color}33`,
    }}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

// ── Severity Badge ──────────────────────────────────────────

export function SeverityBadge({ severity }: { severity: string }) {
  const COLORS: Record<string, { color: string; bg: string }> = {
    CRITICAL: { color: '#dc2626', bg: '#fef2f2' },
    HIGH: { color: '#ea580c', bg: '#fff7ed' },
    MEDIUM: { color: '#2563eb', bg: '#eff6ff' },
    LOW: { color: '#16a34a', bg: '#f0fdf4' },
  };
  const item = COLORS[severity?.toUpperCase()] || { color: '#64748b', bg: '#f1f5f9' };
  return (
    <span className="badge" style={{
      background: item.bg,
      color: item.color,
      border: `1px solid ${item.color}33`,
    }}>
      {severity}
    </span>
  );
}
