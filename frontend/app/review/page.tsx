'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import ScanPanel from '@/components/layout/ScanPanel';
import EmptyState from '@/components/ui/EmptyState';
import { RiskBadge, VerificationBadge } from '@/components/ui/Badges';
import { SkeletonCard } from '@/components/ui/Skeletons';
import type { Review } from '@/lib/types';
import { fetchPendingReviews, fetchReviewHistory, approveReview, rejectReview } from '@/lib/api';
import { formatDateTime, truncate, domainFromUrl } from '@/lib/utils';

// ── Approval modal ────────────────────────────────────────────
function ApprovalModal({
  review, decision, onConfirm, onCancel,
}: {
  review: Review;
  decision: 'APPROVE' | 'REJECT';
  onConfirm: (reviewer: string, reason: string) => void;
  onCancel: () => void;
}) {
  const [reviewer, setReviewer] = useState('');
  const [reason, setReason] = useState('');
  const isApprove = decision === 'APPROVE';

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div className="card" style={{ width: 480, padding: 24 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
          {isApprove ? '✅ Approve Regulation' : '❌ Reject Regulation'}
        </h3>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>
          {truncate(review.regulation_title, 80)}
        </p>
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            Reviewer Name *
          </label>
          <input
            className="input"
            placeholder="Enter your name or ID"
            value={reviewer}
            onChange={e => setReviewer(e.target.value)}
          />
        </div>
        <div style={{ marginBottom: 20 }}>
          <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            {isApprove ? 'Approval Notes' : 'Rejection Reason'} *
          </label>
          <textarea
            className="input"
            placeholder={isApprove ? 'Confirm compliance assessment or add notes…' : 'State reason for rejection…'}
            value={reason}
            onChange={e => setReason(e.target.value)}
            rows={3}
            style={{ resize: 'vertical' }}
          />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost" onClick={onCancel} style={{ flex: 1, justifyContent: 'center' }}>Cancel</button>
          <button
            className={`btn ${isApprove ? 'btn-success' : 'btn-danger'}`}
            disabled={!reviewer.trim() || !reason.trim()}
            onClick={() => onConfirm(reviewer.trim(), reason.trim())}
            style={{ flex: 1, justifyContent: 'center' }}
          >
            {isApprove ? 'Approve' : 'Reject'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  const [scanOpen, setScanOpen] = useState(false);
  const [pending, setPending] = useState<Review[]>([]);
  const [history, setHistory] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'pending' | 'history'>('pending');
  const [modal, setModal] = useState<{ review: Review; decision: 'APPROVE' | 'REJECT' } | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [p, h] = await Promise.all([fetchPendingReviews(), fetchReviewHistory()]);
      setPending(p);
      setHistory(h);
    } catch { /* quiet */ }
    setLoading(false);
  };
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load(); }, []);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const handleDecision = async (reviewer: string, reason: string) => {
    if (!modal) return;
    try {
      if (modal.decision === 'APPROVE') {
        await approveReview(modal.review.id, reviewer, reason);
        showToast('Regulation approved successfully');
      } else {
        await rejectReview(modal.review.id, reviewer, reason);
        showToast('Regulation rejected');
      }
      setModal(null);
      await load();
    } catch (e) {
      showToast(`Error: ${e}`);
    }
  };

  return (
    <>
      <TopBar
        title="Human Review Queue"
        subtitle={`${pending.length} pending · ${history.length} decided`}
        onScanClick={() => setScanOpen(true)}
      />

      <div className="page-container fade-in">
        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, background: 'var(--bg-raised)', borderRadius: 8, padding: 4, width: 'fit-content', marginBottom: 20 }}>
          {(['pending', 'history'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: '6px 16px',
                borderRadius: 6,
                border: 'none',
                fontSize: 13,
                fontWeight: 500,
                cursor: 'pointer',
                background: tab === t ? 'var(--bg-surface)' : 'transparent',
                color: tab === t ? 'var(--text-primary)' : 'var(--text-muted)',
                transition: 'all 0.15s',
              }}
            >
              {t === 'pending' ? `Pending (${pending.length})` : `History (${history.length})`}
            </button>
          ))}
        </div>

        {tab === 'pending' ? (
          loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[...Array(3)].map((_, i) => <SkeletonCard key={i} height={180} />)}
            </div>
          ) : pending.length === 0 ? (
            <EmptyState
              title="No pending reviews"
              message="All HIGH and CRITICAL risk regulations have been reviewed. Run a new scan to discover more."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {pending.map(rev => (
                <div key={rev.id} className="card" style={{ padding: '18px 20px', borderLeft: `3px solid ${rev.risk_level === 'CRITICAL' ? 'var(--accent-red)' : 'var(--accent-amber)'}` }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 10 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>
                        {truncate(rev.regulation_title, 80)}
                      </div>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        <RiskBadge level={rev.risk_level} />
                        <VerificationBadge status={rev.verification_status} />
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                          {formatDateTime(rev.created_at)}
                        </span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                      <button
                        className="btn btn-success"
                        style={{ fontSize: 12, padding: '6px 12px' }}
                        onClick={() => setModal({ review: rev, decision: 'APPROVE' })}
                      >
                        <CheckCircle size={12} /> Approve
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ fontSize: 12, padding: '6px 12px' }}
                        onClick={() => setModal({ review: rev, decision: 'REJECT' })}
                      >
                        <XCircle size={12} /> Reject
                      </button>
                    </div>
                  </div>

                  {rev.recommendation && (
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10, padding: '8px 12px', background: 'var(--bg-raised)', borderRadius: 6 }}>
                      <strong style={{ color: 'var(--text-primary)' }}>Recommended Action:</strong> {rev.recommendation}
                    </div>
                  )}

                  {rev.compliance_gaps?.length > 0 && (
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                        Potential Compliance Gaps
                      </div>
                      {rev.compliance_gaps.slice(0, 3).map((gap, i) => (
                        <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 4, alignItems: 'flex-start' }}>
                          <AlertTriangle size={11} color="var(--accent-amber)" style={{ marginTop: 2, flexShrink: 0 }} />
                          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{truncate(gap, 100)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )
        ) : (
          /* History tab */
          history.length === 0 ? (
            <EmptyState title="No review history" message="No regulations have been approved or rejected yet." />
          ) : (
            <div className="card" style={{ overflow: 'hidden' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Regulation</th>
                    <th>Risk</th>
                    <th>Decision</th>
                    <th>Reviewer</th>
                    <th>Reason</th>
                    <th>Decided At</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(rev => (
                    <tr key={rev.id}>
                      <td style={{ maxWidth: 240 }}>
                        <div style={{ fontSize: 13, fontWeight: 500 }}>{truncate(rev.regulation_title, 50)}</div>
                      </td>
                      <td><RiskBadge level={rev.risk_level} /></td>
                      <td>
                        <span className="badge" style={{
                          background: rev.decision === 'APPROVED' ? 'var(--accent-green-muted)' : 'var(--accent-red-muted)',
                          color: rev.decision === 'APPROVED' ? 'var(--accent-green)' : 'var(--accent-red)',
                          border: `1px solid ${rev.decision === 'APPROVED' ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}`,
                        }}>
                          {rev.decision === 'APPROVED' ? <CheckCircle size={10} /> : <XCircle size={10} />}
                          {rev.decision}
                        </span>
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{rev.reviewer || '—'}</td>
                      <td style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 200 }}>{truncate(rev.reason || '—', 60)}</td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>{formatDateTime(rev.decided_at || '')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>

      {/* Modal */}
      {modal && (
        <ApprovalModal
          review={modal.review}
          decision={modal.decision}
          onConfirm={handleDecision}
          onCancel={() => setModal(null)}
        />
      )}

      {/* Toast */}
      {toast && (
        <div
          className="toast-enter"
          style={{
            position: 'fixed', bottom: 24, right: 24, zIndex: 200,
            background: 'var(--bg-raised)',
            border: '1px solid var(--border-default)',
            borderRadius: 8, padding: '12px 20px',
            fontSize: 13, color: 'var(--text-primary)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          }}
        >
          {toast}
        </div>
      )}

      <ScanPanel open={scanOpen} onClose={() => setScanOpen(false)} onComplete={() => { setScanOpen(false); load(); }} />
    </>
  );
}
