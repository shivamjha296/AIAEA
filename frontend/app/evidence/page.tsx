'use client';

import { useState, useEffect, useCallback } from 'react';
import { CheckCircle, XCircle, ExternalLink, Search, Filter } from 'lucide-react';
import Link from 'next/link';
import TopBar from '@/components/layout/TopBar';
import ScanPanel from '@/components/layout/ScanPanel';
import EmptyState from '@/components/ui/EmptyState';
import { VerificationBadge } from '@/components/ui/Badges';
import { SkeletonTable } from '@/components/ui/Skeletons';
import type { RegulationListItem } from '@/lib/types';
import { fetchRegulations } from '@/lib/api';
import { truncate, domainFromUrl, timeAgo } from '@/lib/utils';

interface EvidenceItem {
  claim: string;
  source_quote: string;
  page_or_section: string;
  verified?: boolean;
}

interface RegWithEvidence extends RegulationListItem {
  key_requirements?: EvidenceItem[];
}

export default function EvidencePage() {
  const [scanOpen, setScanOpen] = useState(false);
  const [regs, setRegs] = useState<RegulationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [verFilter, setVerFilter] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<RegWithEvidence | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchRegulations({
        page_size: 50,
        verification: verFilter || undefined,
        search: search || undefined,
      });
      setRegs(res.items);
    } catch { /* quiet */ }
    setLoading(false);
  }, [search, verFilter]);

  useEffect(() => { load(); }, [load]);

  const loadDetail = async (id: string) => {
    setSelected(id);
    try {
      const { fetchRegulation } = await import('@/lib/api');
      const d = await fetchRegulation(id);
      setDetail(d as unknown as RegWithEvidence);
    } catch { setDetail(null); }
  };

  // Flatten all evidence items for list view
  const allEvidence = regs.flatMap(reg =>
    ((reg as RegWithEvidence).key_requirements || []).map(e => ({ ...e, reg }))
  );

  return (
    <>
      <TopBar title="Evidence Explorer" subtitle="Verbatim quotes from live sources" onScanClick={() => setScanOpen(true)} />

      <div className="page-container fade-in">
        {/* Filters */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              className="input"
              placeholder="Search claims, quotes, sources…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: 30 }}
            />
          </div>
          <select className="select" style={{ flex: '0 0 180px' }}
            value={verFilter}
            onChange={e => setVerFilter(e.target.value)}>
            <option value="">All Verification</option>
            <option value="VERIFIED">Verified Only</option>
            <option value="EVIDENCE_UNVERIFIED">Unverified</option>
            <option value="REQUIRES_HUMAN_REVIEW">Needs Review</option>
          </select>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 420px', gap: 20 }}>
          {/* Source list */}
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-default)' }}>
              <span style={{ fontSize: 14, fontWeight: 600 }}>Regulatory Sources</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 8 }}>({regs.length})</span>
            </div>
            {loading ? (
              <SkeletonTable rows={6} />
            ) : regs.length === 0 ? (
              <EmptyState />
            ) : (
              <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                {regs.map(reg => (
                  <div
                    key={reg.id}
                    onClick={() => loadDetail(reg.id)}
                    style={{
                      padding: '12px 20px',
                      borderBottom: '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      background: selected === reg.id ? 'var(--accent-blue-muted)' : 'transparent',
                      borderLeft: selected === reg.id ? '3px solid var(--accent-blue)' : '3px solid transparent',
                      transition: 'all 0.12s',
                    }}
                    onMouseEnter={e => { if (selected !== reg.id) e.currentTarget.style.background = 'var(--bg-raised)'; }}
                    onMouseLeave={e => { if (selected !== reg.id) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>
                      {truncate(reg.title || 'UNKNOWN', 55)}
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent-blue)' }}>{reg.regulatory_body}</span>
                      <VerificationBadge status={reg.verification_status} />
                      <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{timeAgo(reg.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Evidence detail */}
          <div>
            {!detail && !selected ? (
              <div className="card" style={{ padding: 32, textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                  Select a source to view its evidence
                </p>
              </div>
            ) : detail ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="card" style={{ padding: '14px 20px' }}>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                    {truncate(detail.title || 'UNKNOWN', 60)}
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                    <VerificationBadge status={detail.verification_status} />
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {(detail as any).verified_claims ?? 0}/{(detail as any).total_claims ?? 0} verified
                    </span>
                  </div>
                  <a
                    href={detail.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mono"
                    style={{ fontSize: 11, color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    <ExternalLink size={10} /> {domainFromUrl(detail.source_url)}
                  </a>
                </div>

                {((detail as any).key_requirements || []).length === 0 && (
                  <div className="card" style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    No evidence items extracted for this source
                  </div>
                )}

                {((detail as any).key_requirements || []).map((ev: EvidenceItem, i: number) => (
                  <div key={i} className="card" style={{ padding: '14px 20px', borderLeft: `3px solid ${ev.verified ? 'var(--accent-green)' : 'var(--border-strong)'}` }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 10 }}>
                      {ev.verified
                        ? <CheckCircle size={13} color="var(--accent-green)" style={{ marginTop: 2, flexShrink: 0 }} />
                        : <XCircle size={13} color="var(--text-muted)" style={{ marginTop: 2, flexShrink: 0 }} />}
                      <span style={{ fontSize: 13, fontWeight: 500, lineHeight: 1.5 }}>{ev.claim}</span>
                    </div>
                    {ev.source_quote && (
                      <div className="evidence-quote">
                        "{ev.source_quote}"
                      </div>
                    )}
                    {ev.page_or_section && ev.page_or_section !== 'UNKNOWN' && (
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6 }}>
                        📍 {ev.page_or_section}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="card" style={{ padding: 32, textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading evidence…</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <ScanPanel open={scanOpen} onClose={() => setScanOpen(false)} onComplete={() => { setScanOpen(false); load(); }} />
    </>
  );
}
