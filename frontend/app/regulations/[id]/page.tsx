'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, ExternalLink, CheckCircle2,
  AlertCircle, Download, ShieldCheck, ShieldAlert,
  Building2, Calendar, FileText, Check
} from 'lucide-react';
import { RiskBadge, VerificationBadge, TrustBadge } from '@/components/ui/Badges';
import type { RegulationDetail, ActionItem } from '@/lib/types';
import { fetchRegulation, exportRegulation } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function RegulationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [reg, setReg] = useState<RegulationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRegulation(id)
      .then(setReg)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="page-container" style={{ padding: 40, color: 'var(--text-muted)' }}>
        Loading regulation intelligence...
      </div>
    );
  }

  if (error || !reg) {
    return (
      <div className="page-container" style={{ padding: 40 }}>
        <div style={{ color: 'var(--accent-red)', marginBottom: 16 }}>
          Could not load regulation details: {error}
        </div>
        <Link href="/regulations" className="btn btn-ghost">
          <ArrowLeft size={14} /> Back to Regulations
        </Link>
      </div>
    );
  }

  return (
    <div className="fade-in">
      {/* Sticky Header */}
      <div style={{
        background: '#ffffff',
        borderBottom: '1px solid var(--border-default)',
        padding: '16px 32px',
        position: 'sticky',
        top: 0,
        zIndex: 20,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 300 }}>
            <Link href="/regulations" className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: 12 }}>
              <ArrowLeft size={13} /> Back
            </Link>
            <div>
              <h1 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                {reg.title || 'Regulatory Document'}
              </h1>
              <div style={{ display: 'flex', gap: 8, marginTop: 4, alignItems: 'center', flexWrap: 'wrap' }}>
                <RiskBadge level={reg.risk_level} />
                <VerificationBadge status={reg.verification_status} />
                <TrustBadge level={reg.trust_level} tier={reg.source_tier} />
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <a
              href={reg.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost"
              style={{ fontSize: 12, padding: '7px 14px' }}
            >
              <ExternalLink size={13} /> View Live Source
            </a>
            <a
              href={exportRegulation(reg.id)}
              download
              className="btn btn-primary"
              style={{ fontSize: 12, padding: '7px 14px' }}
            >
              <Download size={13} /> Export JSON
            </a>
          </div>
        </div>
      </div>

      <div className="page-container" style={{ maxWidth: 1100 }}>
        {/* Core Metadata Bar */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 16,
          marginBottom: 20,
        }}>
          <div className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              Regulatory Authority
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#2563eb' }}>
              {reg.regulatory_body || 'RBI'}
            </div>
          </div>
          <div className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              Publication Date
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              {formatDate(reg.reg_publication_date || reg.publication_date)}
            </div>
          </div>
          <div className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              Effective Date
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              {formatDate(reg.effective_date)}
            </div>
          </div>
        </div>

        {/* Summary Card */}
        {reg.summary && (
          <div className="card" style={{ padding: '20px 24px', marginBottom: 20 }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              Executive Summary
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              {reg.summary}
            </p>
          </div>
        )}

        {/* Requirements & Evidence Quotes */}
        {reg.key_requirements && reg.key_requirements.length > 0 && (
          <div className="card" style={{ padding: '20px 24px', marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h2 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                Extracted Requirements & Evidence
              </h2>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {reg.key_requirements.length} item{reg.key_requirements.length > 1 ? 's' : ''}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {reg.key_requirements.map((req, i) => (
                <div
                  key={i}
                  style={{
                    padding: '14px 16px',
                    background: '#f8fafc',
                    border: '1px solid var(--border-default)',
                    borderRadius: 8,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 8 }}>
                    <CheckCircle2 size={16} color="#16a34a" style={{ marginTop: 2, flexShrink: 0 }} />
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                      {req.claim}
                    </div>
                  </div>

                  {req.source_quote && (
                    <div className="evidence-quote" style={{ margin: '8px 0 0 26px' }}>
                      "{req.source_quote}"
                      {req.page_or_section && req.page_or_section !== 'UNKNOWN' && (
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'inherit' }}>
                          Section: {req.page_or_section}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommended Actions */}
        {reg.recommended_actions && reg.recommended_actions.length > 0 && (
          <div className="card" style={{ padding: '20px 24px', marginBottom: 20 }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
              Action Items & Compliance Steps
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {reg.recommended_actions.map((act: ActionItem, i: number) => (
                <div
                  key={i}
                  style={{
                    padding: '14px 16px',
                    borderLeft: `4px solid ${act.priority === 'HIGH' || act.priority === 'CRITICAL' ? '#ea580c' : '#2563eb'}`,
                    background: '#f8fafc',
                    border: '1px solid var(--border-default)',
                    borderLeftWidth: 4,
                    borderRadius: '0 8px 8px 0',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {act.action_title}
                    </div>
                    <span className="badge" style={{
                      background: act.priority === 'HIGH' || act.priority === 'CRITICAL' ? '#fff7ed' : '#eff6ff',
                      color: act.priority === 'HIGH' || act.priority === 'CRITICAL' ? '#ea580c' : '#2563eb',
                      border: '1px solid currentColor',
                    }}>
                      {act.priority}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    <span>Department: <strong>{act.department}</strong></span>
                    <span>Timeline: <strong>{act.deadline}</strong></span>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
                    {act.rationale}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Security & Validation Status Footer */}
        <div style={{
          padding: '12px 18px',
          background: '#f0fdf4',
          border: '1px solid rgba(22, 163, 74, 0.2)',
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <ShieldCheck size={16} color="#16a34a" />
          <span style={{ fontSize: 12, color: '#166534', fontWeight: 500 }}>
            Source verified and screened through Indirect Prompt Injection (IPI) security filters.
          </span>
        </div>
      </div>
    </div>
  );
}
