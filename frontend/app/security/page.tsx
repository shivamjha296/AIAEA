'use client';

import { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import ScanPanel from '@/components/layout/ScanPanel';
import { SeverityBadge } from '@/components/ui/Badges';
import type { SecurityEvent, SecurityMetrics } from '@/lib/types';
import { fetchSecurityEvents, fetchSecurityMetrics } from '@/lib/api';
import { domainFromUrl, formatDateTime } from '@/lib/utils';
import { ShieldCheck } from 'lucide-react';

function TrustBoundaryDiagram() {
  const steps = [
    { title: 'Live Search', sub: 'DuckDuckGo Engine', icon: '🌐', color: '#64748b', bg: '#f1f5f9' },
    { title: 'IPI Security Scan', sub: '20+ attack patterns', icon: '🛡️', color: '#dc2626', bg: '#fef2f2' },
    { title: 'Quarantined LLM', sub: 'Ollama factual extraction', icon: '⚙️', color: '#ea580c', bg: '#fff7ed' },
    { title: 'Pydantic Schema', sub: 'Strict structure check', icon: '✅', color: '#2563eb', bg: '#eff6ff' },
    { title: 'Privileged LLM', sub: 'Banking impact analysis', icon: '🎯', color: '#16a34a', bg: '#f0fdf4' },
    { title: 'Audit Trail', sub: 'SQLite permanent log', icon: '🗄️', color: '#7c3aed', bg: '#f5f3ff' },
  ];

  return (
    <div className="card" style={{ padding: '20px 24px', marginBottom: 24 }}>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
          Dual-LLM Security Pipeline & Isolation Boundary
        </h2>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          Untrusted public web text is strictly quarantined. The privileged decision model only ever sees validated, sanitized JSON.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(6, 1fr)',
        gap: 10,
        alignItems: 'center',
      }}>
        {steps.map((step, idx) => (
          <div
            key={idx}
            style={{
              padding: '14px 12px',
              background: step.bg,
              border: `1px solid ${step.color}22`,
              borderRadius: 8,
              textAlign: 'center',
              position: 'relative',
            }}
          >
            <div style={{ fontSize: 20, marginBottom: 4 }}>{step.icon}</div>
            <div style={{ fontSize: 12, fontWeight: 700, color: step.color, marginBottom: 2 }}>
              {step.title}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              {step.sub}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SecurityPage() {
  const [scanOpen, setScanOpen] = useState(false);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [error, setError] = useState<Error | null>(null);

  if (error) throw error;

  const load = async () => {
    try {
      const [e, m] = await Promise.all([
        fetchSecurityEvents(50),
        fetchSecurityMetrics(),
      ]);
      setEvents(e);
      setMetrics(m);
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    }
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load(); }, []);

  return (
    <>
      <TopBar title="Security & Threat Monitor" subtitle="Indirect Prompt Injection (IPI) Defense System" onScanClick={() => setScanOpen(true)} />

      <div className="page-container fade-in">
        {/* KPI Metrics */}
        {metrics && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 20 }}>
            <div className="metric-tile" style={{ padding: '16px 20px' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Sources Scanned</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#2563eb' }}>{metrics.sources_scanned}</div>
            </div>
            <div className="metric-tile" style={{ padding: '16px 20px' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Clean Sources</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#16a34a' }}>{metrics.clean}</div>
            </div>
            <div className="metric-tile" style={{ padding: '16px 20px' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Quarantined Sources</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#dc2626' }}>{metrics.quarantined}</div>
            </div>
            <div className="metric-tile" style={{ padding: '16px 20px' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Security Threats</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: metrics.security_events > 0 ? '#dc2626' : '#16a34a' }}>{metrics.security_events}</div>
            </div>
          </div>
        )}

        {/* Clean Pipeline Architecture Diagram */}
        <TrustBoundaryDiagram />

        {/* Security Events Feed */}
        <div className="card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-default)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              Live Security Threat Feed
            </h3>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {events.length} threat event{events.length !== 1 ? 's' : ''} logged
            </span>
          </div>

          {events.length === 0 ? (
            <div style={{ padding: '36px 24px', textAlign: 'center' }}>
              <ShieldCheck size={32} color="#16a34a" style={{ margin: '0 auto 10px' }} />
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                All Sources Passed Security Filter
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                No prompt-injection attacks or adversarial directives detected in retrieved regulatory sources.
              </div>
            </div>
          ) : (
            <div>
              {events.map((ev) => (
                <div key={ev.id} style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#dc2626', marginBottom: 2 }}>
                      {ev.threat_type}
                    </div>
                    <div className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {domainFromUrl(ev.source_url)} · {formatDateTime(ev.created_at)}
                    </div>
                  </div>
                  <SeverityBadge severity={ev.severity} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ScanPanel open={scanOpen} onClose={() => setScanOpen(false)} onComplete={() => { setScanOpen(false); load(); }} />
    </>
  );
}
