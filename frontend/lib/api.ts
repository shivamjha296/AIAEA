// All API calls to the FastAPI backend.
// Base URL is configured via NEXT_PUBLIC_API_URL env var.

import type {
  ActivityPoint,
  AuditEvent,
  DashboardMetrics,
  HealthStatus,
  PaginatedRegulations,
  RegulationDetail,
  RegulatorCount,
  Review,
  RiskDistribution,
  Scan,
  SecurityEvent,
  SecurityMetrics,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Health ──────────────────────────────────────────────────
export const fetchHealth = () => apiFetch<HealthStatus>('/api/health');

// ── Dashboard ────────────────────────────────────────────────
export const fetchMetrics = () =>
  apiFetch<DashboardMetrics>('/api/dashboard/metrics');

export const fetchActivity = (days = 30) =>
  apiFetch<ActivityPoint[]>(`/api/dashboard/activity?days=${days}`);

export const fetchRegulatorDistribution = () =>
  apiFetch<RegulatorCount[]>('/api/dashboard/regulators');

// ── Regulations ──────────────────────────────────────────────
export interface RegulationFilters {
  page?: number;
  page_size?: number;
  regulator?: string;
  risk?: string;
  verification?: string;
  search?: string;
  days?: number;
}

export const fetchRegulations = (filters: RegulationFilters = {}) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v));
  });
  return apiFetch<PaginatedRegulations>(`/api/regulations?${params}`);
};

export const fetchRegulatorsList = () =>
  apiFetch<string[]>('/api/regulations/regulators');

export const fetchRegulation = (id: string) =>
  apiFetch<RegulationDetail>(`/api/regulations/${id}`);

export const exportRegulation = (id: string) =>
  `${API_BASE}/api/regulations/${id}/export`;

// ── Risk ─────────────────────────────────────────────────────
export const fetchRiskDistribution = () =>
  apiFetch<RiskDistribution>('/api/risk/distribution');

export const fetchRiskRegister = (filters: RegulationFilters = {}) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v));
  });
  return apiFetch<PaginatedRegulations & { distribution: RiskDistribution }>(
    `/api/risk?${params}`
  );
};

// ── Security ─────────────────────────────────────────────────
export const fetchSecurityEvents = (limit = 50) =>
  apiFetch<SecurityEvent[]>(`/api/security/events?limit=${limit}`);

export const fetchSecurityMetrics = () =>
  apiFetch<SecurityMetrics>('/api/security/metrics');

// ── Reviews ──────────────────────────────────────────────────
export const fetchPendingReviews = () =>
  apiFetch<Review[]>('/api/reviews/pending');

export const fetchReviewHistory = () =>
  apiFetch<Review[]>('/api/reviews/history');

export const approveReview = (id: number, reviewer: string, reason: string) =>
  apiFetch<{ status: string }>(`/api/reviews/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ reviewer, reason }),
  });

export const rejectReview = (id: number, reviewer: string, reason: string) =>
  apiFetch<{ status: string }>(`/api/reviews/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reviewer, reason }),
  });

// ── Scans ────────────────────────────────────────────────────
export const startScan = (max_queries = 2, max_sources = 3) =>
  apiFetch<{ scan_id: string; status: string }>('/api/scans', {
    method: 'POST',
    body: JSON.stringify({ max_queries, max_sources }),
  });

export const fetchScans = () => apiFetch<Scan[]>('/api/scans');

export const fetchScan = (id: string) => apiFetch<Scan>(`/api/scans/${id}`);

export const getScanEventsUrl = (scanId: string) =>
  `${API_BASE}/api/scans/${scanId}/events`;

// ── Audit ────────────────────────────────────────────────────
export const fetchAudit = (scan_id?: string, limit = 100) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (scan_id) params.set('scan_id', scan_id);
  return apiFetch<AuditEvent[]>(`/api/audit?${params}`);
};
