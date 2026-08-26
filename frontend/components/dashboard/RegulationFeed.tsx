'use client';

import Link from 'next/link';
import { ExternalLink, ChevronRight } from 'lucide-react';
import type { RegulationListItem, RiskDistribution } from '@/lib/types';
import { RiskBadge, VerificationBadge } from '@/components/ui/Badges';
import { timeAgo, truncate, domainFromUrl, RISK_COLORS } from '@/lib/utils';

function RiskBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 600, color }}>{value}</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

interface Props {
  items: RegulationListItem[];
  distribution: RiskDistribution;
}

export default function RegulationFeed({ items, distribution }: Props) {
  const maxVal = Math.max(...Object.values(distribution), 1);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20 }}>
      {/* Recent regulations */}
      <div className="card">
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600 }}>Recent Regulatory Updates</h3>
          <Link href="/regulations" style={{ fontSize: 12, color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
            View all <ChevronRight size={12} />
          </Link>
        </div>
        <div>
          {items.length === 0 && (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              No regulations yet — run a live scan
            </div>
          )}
          {items.map(reg => (
            <Link key={reg.id} href={`/regulations/${reg.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div style={{
                padding: '14px 20px',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex', gap: 12, alignItems: 'flex-start',
                transition: 'background 0.12s',
                cursor: 'pointer',
              }}
              className="hover-row"
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-raised)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                <div style={{
                  width: 3, height: 40, borderRadius: 2, flexShrink: 0, marginTop: 2,
                  background: RISK_COLORS[reg.risk_level as keyof typeof RISK_COLORS] || RISK_COLORS.UNKNOWN,
                }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
                    {truncate(reg.title || reg.source_url, 80)}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 11, color: 'var(--accent-blue)', fontWeight: 600 }}>
                      {reg.regulatory_body || 'Unknown'}
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>·</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {domainFromUrl(reg.source_url)}
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>·</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {timeAgo(reg.created_at)}
                    </span>
                  </div>
                </div>
                <RiskBadge level={reg.risk_level} />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Risk distribution sidebar */}
      <div className="card" style={{ padding: '16px 20px', height: 'fit-content' }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Risk Distribution</h3>
        <RiskBar label="Critical" value={distribution.CRITICAL} max={maxVal} color="var(--risk-critical)" />
        <RiskBar label="High" value={distribution.HIGH} max={maxVal} color="var(--risk-high)" />
        <RiskBar label="Medium" value={distribution.MEDIUM} max={maxVal} color="var(--risk-medium)" />
        <RiskBar label="Low" value={distribution.LOW} max={maxVal} color="var(--risk-low)" />
        <RiskBar label="Unknown" value={distribution.UNKNOWN} max={maxVal} color="var(--risk-unknown)" />

        <div className="divider" style={{ margin: '16px 0' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
            {Object.values(distribution).reduce((a, b) => a + b, 0)}
          </span>
        </div>
      </div>
    </div>
  );
}
