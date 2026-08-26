'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  RadialBarChart, RadialBar, PieChart, Pie, Cell,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import Link from 'next/link';
import TopBar from '@/components/layout/TopBar';
import ScanPanel from '@/components/layout/ScanPanel';
import { RiskBadge, VerificationBadge } from '@/components/ui/Badges';
import EmptyState from '@/components/ui/EmptyState';
import { SkeletonTable } from '@/components/ui/Skeletons';
import type { RiskDistribution, RegulationListItem } from '@/lib/types';
import { fetchRiskRegister } from '@/lib/api';
import { RISK_COLORS, formatDate, truncate } from '@/lib/utils';

const RISK_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'] as const;

export default function RiskPage() {
  const [scanOpen, setScanOpen] = useState(false);
  const [items, setItems] = useState<RegulationListItem[]>([]);
  const [dist, setDist] = useState<RiskDistribution>({ CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, UNKNOWN: 0 });
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchRiskRegister({ risk: riskFilter || undefined, page_size: 100 });
      setItems(res.items);
      setDist(res.distribution);
      setTotal(res.total);
    } catch { /* quiet */ }
    setLoading(false);
  }, [riskFilter]);

  useEffect(() => { load(); }, [load]);

  const pieData = RISK_ORDER
    .filter(k => dist[k] > 0)
    .map(k => ({ name: k, value: dist[k], color: RISK_COLORS[k] }));

  const totalRisked = dist.CRITICAL + dist.HIGH;

  return (
    <>
      <TopBar title="Risk Register" subtitle={`${total} regulations assessed`} onScanClick={() => setScanOpen(true)} />

      <div className="page-container fade-in">
        {/* Risk overview cards + donut */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20, marginBottom: 24 }}>
          {/* Distribution bars */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 20 }}>Risk Level Distribution</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 12 }}>
              {RISK_ORDER.map(level => (
                <div
                  key={level}
                  onClick={() => setRiskFilter(riskFilter === level ? '' : level)}
                  style={{
                    padding: '16px 12px',
                    background: riskFilter === level ? `${RISK_COLORS[level]}22` : 'var(--bg-raised)',
                    border: `1px solid ${riskFilter === level ? RISK_COLORS[level] + '66' : 'var(--border-default)'}`,
                    borderRadius: 8,
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: RISK_COLORS[level], marginBottom: 4 }}>
                    {dist[level]}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    {level}
                  </div>
                </div>
              ))}
            </div>
            {totalRisked > 0 && (
              <div style={{
                marginTop: 16, padding: '10px 14px',
                background: 'var(--accent-red-muted)',
                border: '1px solid rgba(248,81,73,0.2)',
                borderRadius: 6,
                fontSize: 12, color: 'var(--accent-red)',
              }}>
                ⚠ {totalRisked} regulation{totalRisked > 1 ? 's' : ''} at HIGH or CRITICAL risk — immediate review required
              </div>
            )}
          </div>

          {/* Pie chart */}
          <div className="card" style={{ padding: '20px 16px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, alignSelf: 'flex-start' }}>Composition</h3>
            {pieData.length === 0 ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                No data
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%" cy="50%"
                    innerRadius={55} outerRadius={85}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: 8,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      fontSize: 12,
                      color: '#0f172a',
                    }}
                    formatter={(v: unknown, name: unknown) => [v as number, name as string]}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
            <div style={{ width: '100%', marginTop: 4 }}>
              {pieData.map(d => (
                <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: d.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{d.name}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', marginLeft: 'auto' }}>{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Risk register table */}
        <div className="card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600 }}>
              Risk Register
              {riskFilter && <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 8 }}>· Filtered: {riskFilter}</span>}
            </h3>
            {riskFilter && (
              <button className="btn btn-ghost" onClick={() => setRiskFilter('')} style={{ fontSize: 12, padding: '4px 10px' }}>
                Clear filter
              </button>
            )}
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Regulation</th>
                <th>Regulator</th>
                <th>Risk</th>
                <th>Verification</th>
                <th>Effective</th>
                <th>Sectors</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ padding: 0 }}><SkeletonTable rows={8} /></td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: 0 }}><EmptyState /></td></tr>
              ) : items.map(reg => (
                <tr key={reg.id}>
                  <td>
                    <Link href={`/regulations/${reg.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                        {truncate(reg.title || 'UNKNOWN', 60)}
                      </div>
                    </Link>
                  </td>
                  <td style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-blue)' }}>
                    {reg.regulatory_body}
                  </td>
                  <td><RiskBadge level={reg.risk_level} /></td>
                  <td><VerificationBadge status={reg.verification_status} /></td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {formatDate(reg.effective_date)}
                  </td>
                  <td>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {reg.summary ? truncate(reg.summary, 40) : '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <ScanPanel open={scanOpen} onClose={() => setScanOpen(false)} onComplete={() => { setScanOpen(false); load(); }} />
    </>
  );
}
