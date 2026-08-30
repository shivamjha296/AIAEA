'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Search, ChevronRight } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import ScanPanel from '@/components/layout/ScanPanel';
import { RiskBadge, VerificationBadge, TrustBadge } from '@/components/ui/Badges';
import { SkeletonTable } from '@/components/ui/Skeletons';
import EmptyState from '@/components/ui/EmptyState';
import type { RegulationListItem } from '@/lib/types';
import { fetchRegulations, fetchRegulatorsList } from '@/lib/api';
import { formatDate, timeAgo, truncate, domainFromUrl } from '@/lib/utils';

export default function RegulationsPage() {
  const [scanOpen, setScanOpen] = useState(false);
  const [items, setItems] = useState<RegulationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [regulators, setRegulators] = useState<string[]>([]);

  const [filters, setFilters] = useState({
    search: '',
    regulator: '',
    risk: '',
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchRegulations({
        page,
        page_size: 20,
        search: filters.search || undefined,
        regulator: filters.regulator || undefined,
        risk: filters.risk || undefined,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch { /* quiet */ }
    setLoading(false);
  }, [page, filters]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    load();
  }, []);
  useEffect(() => {
    fetchRegulatorsList().then(setRegulators).catch(() => {});
  }, []);

  const totalPages = Math.ceil(total / 20);

  return (
    <>
      <TopBar title="Regulatory Updates" subtitle={`${total} notifications monitored`} onScanClick={() => setScanOpen(true)} />

      <div className="page-container fade-in">
        {/* Simple & Clean Filter Bar */}
        <div style={{
          display: 'flex',
          gap: 12,
          marginBottom: 16,
          alignItems: 'center',
        }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              className="input"
              placeholder="Search circulars, directives, topics..."
              value={filters.search}
              onChange={e => { setFilters(f => ({ ...f, search: e.target.value })); setPage(1); }}
              style={{ paddingLeft: 34 }}
            />
          </div>

          <select
            className="select"
            style={{ width: 170 }}
            value={filters.regulator}
            onChange={e => { setFilters(f => ({ ...f, regulator: e.target.value })); setPage(1); }}
          >
            <option value="">All Authorities</option>
            {regulators.map(r => <option key={r} value={r}>{r}</option>)}
          </select>

          <select
            className="select"
            style={{ width: 150 }}
            value={filters.risk}
            onChange={e => { setFilters(f => ({ ...f, risk: e.target.value })); setPage(1); }}
          >
            <option value="">All Risk Levels</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Clean Data Table */}
        <div className="card" style={{ overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '45%' }}>Regulation & Source</th>
                <th>Authority</th>
                <th>Risk Priority</th>
                <th>Effective Date</th>
                <th>Trust Tier</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ padding: 0 }}>
                  <SkeletonTable rows={8} />
                </td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: 0 }}>
                  <EmptyState title="No regulations matched" message="Try adjusting your search terms or filters." />
                </td></tr>
              ) : items.map(reg => (
                <tr key={reg.id}>
                  <td>
                    <Link href={`/regulations/${reg.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                        {truncate(reg.title || 'Regulatory Circular', 75)}
                      </div>
                      <div className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {domainFromUrl(reg.source_url)} · {timeAgo(reg.created_at)}
                      </div>
                    </Link>
                  </td>
                  <td>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#2563eb' }}>
                      {reg.regulatory_body || 'RBI'}
                    </span>
                  </td>
                  <td><RiskBadge level={reg.risk_level} /></td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {formatDate(reg.effective_date)}
                  </td>
                  <td>
                    <TrustBadge level={reg.trust_level} tier={reg.source_tier} />
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <Link href={`/regulations/${reg.id}`} className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: 11 }}>
                      Details <ChevronRight size={12} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{
              padding: '12px 20px',
              borderTop: '1px solid var(--border-default)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: '#f8fafc',
            }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Showing page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total} total)
              </span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  className="btn btn-ghost"
                  disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}
                  style={{ padding: '5px 12px', fontSize: 12 }}
                >
                  Previous
                </button>
                <button
                  className="btn btn-ghost"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                  style={{ padding: '5px 12px', fontSize: 12 }}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <ScanPanel open={scanOpen} onClose={() => setScanOpen(false)} onComplete={() => { setScanOpen(false); load(); }} />
    </>
  );
}
