'use client';

import { useState, useEffect } from 'react';
import { Clock, Filter } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import ScanPanel from '@/components/layout/ScanPanel';
import EmptyState from '@/components/ui/EmptyState';
import { SkeletonTable } from '@/components/ui/Skeletons';
import type { AuditEvent, Scan } from '@/lib/types';
import { fetchAudit, fetchScans } from '@/lib/api';
import { formatDateTime, EVENT_ICONS, truncate } from '@/lib/utils';

const EVENT_COLORS: Record<string, string> = {
  STARTED:        '#3fb950',
  COMPLETE:       '#3fb950',
  SEARCH_COMPLETE: '#388bfd',
  SEARCHING:      '#388bfd',
  FETCHING:       '#388bfd',
  SECURITY_QUARANTINE: '#f85149',
  EXTRACTION_SUCCESS:  '#3fb950',
  FAILED:         '#f85149',
  PROCESSING_ERROR:    '#d29922',
  IMPORTING:      '#a371f7',
  DEFAULT:        '#8b949e',
};

function getEventColor(type: string): string {
  return EVENT_COLORS[type] || EVENT_COLORS.DEFAULT;
}

export default function AuditPage() {
  const [scanOpen, setScanOpen] = useState(false);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [scanFilter, setScanFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [a, s] = await Promise.all([
        fetchAudit(scanFilter || undefined, 200),
        fetchScans(),
      ]);
      setEvents(a);
      setScans(s);
    } catch { /* quiet */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, [scanFilter]);

  // Group events by scan_id for timeline view
  const grouped = events.reduce<Record<string, AuditEvent[]>>((acc, ev) => {
    const key = ev.scan_id || 'SYSTEM';
    if (!acc[key]) acc[key] = [];
    acc[key].push(ev);
    return acc;
  }, {});

  const scanMap = Object.fromEntries(scans.map(s => [s.id, s]));

  return (
    <>
      <TopBar title="Audit Trail" subtitle={`${events.length} events recorded`} onScanClick={() => setScanOpen(true)} />

      <div className="page-container fade-in">
        {/* Filter by scan */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
          <Filter size={14} color="var(--text-muted)" />
          <select className="select" style={{ maxWidth: 320 }} value={scanFilter} onChange={e => setScanFilter(e.target.value)}>
            <option value="">All Scans</option>
            {scans.map(s => (
              <option key={s.id} value={s.id}>
                {s.id.slice(0, 16)}… — {s.status} — {formatDateTime(s.started_at)}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <SkeletonTable rows={10} />
        ) : events.length === 0 ? (
          <EmptyState title="No audit events" message="Audit events are recorded automatically when the pipeline runs." />
        ) : (
          Object.entries(grouped).map(([scan_id, evList]) => {
            const scan = scanMap[scan_id];
            return (
              <div key={scan_id} style={{ marginBottom: 32 }}>
                {/* Scan header */}
                <div style={{
                  padding: '10px 16px',
                  background: 'var(--bg-raised)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 8,
                  marginBottom: 12,
                  display: 'flex', alignItems: 'center', gap: 12,
                }}>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    SCAN
                  </span>
                  <span className="mono" style={{ fontSize: 12, color: 'var(--accent-blue)' }}>
                    {scan_id.slice(0, 24)}…
                  </span>
                  {scan && (
                    <>
                      <span className="badge" style={{
                        background: scan.status === 'COMPLETE' ? 'var(--accent-green-muted)' : scan.status === 'FAILED' ? 'var(--accent-red-muted)' : 'var(--accent-blue-muted)',
                        color: scan.status === 'COMPLETE' ? 'var(--accent-green)' : scan.status === 'FAILED' ? 'var(--accent-red)' : 'var(--accent-blue)',
                        border: 'none',
                      }}>
                        {scan.status}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        Started: {formatDateTime(scan.started_at)}
                      </span>
                      {scan.sources_processed > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
                          {scan.sources_processed} sources · {scan.sources_quarantined} quarantined · {scan.new_regulations} new regs
                        </span>
                      )}
                    </>
                  )}
                </div>

                {/* Timeline */}
                <div style={{ paddingLeft: 16 }}>
                  {evList.map((ev, i) => {
                    const color = getEventColor(ev.event_type);
                    return (
                      <div key={ev.id} className="timeline-item">
                        <div style={{
                          width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                          background: `${color}22`,
                          border: `1px solid ${color}55`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 10,
                        }}>
                          {EVENT_ICONS[ev.event_type] ?? '·'}
                        </div>
                        <div style={{ flex: 1, paddingTop: 2 }}>
                          <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
                            <span style={{ fontSize: 12, fontWeight: 600, color }}>{ev.event_type.replace(/_/g, ' ')}</span>
                            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{formatDateTime(ev.created_at)}</span>
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                            {ev.message}
                          </div>
                          {ev.detail && (() => {
                            try {
                              const d = JSON.parse(ev.detail);
                              return (
                                <div className="mono" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                                  {JSON.stringify(d).slice(0, 200)}
                                </div>
                              );
                            } catch { return null; }
                          })()}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>

      <ScanPanel open={scanOpen} onClose={() => setScanOpen(false)} onComplete={() => { setScanOpen(false); load(); }} />
    </>
  );
}
