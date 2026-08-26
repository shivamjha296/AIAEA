'use client';

import { AlertTriangle, ShieldCheck, FileText, CheckCircle2 } from 'lucide-react';
import type { DashboardMetrics } from '@/lib/types';
import { timeAgo } from '@/lib/utils';

interface MetricsRowProps {
  metrics: DashboardMetrics;
  onScanClick: () => void;
}

export default function MetricsRow({ metrics }: MetricsRowProps) {
  const cards = [
    {
      label: 'Regulations Monitored',
      value: metrics.total_regulations,
      sub: metrics.last_scan_at ? `Updated ${timeAgo(metrics.last_scan_at)}` : 'Live web feed active',
      icon: FileText,
      color: '#2563eb',
      bg: '#eff6ff',
    },
    {
      label: 'High Priority Risk',
      value: metrics.high_risk + metrics.critical,
      sub: 'Requires compliance attention',
      icon: AlertTriangle,
      color: '#ea580c',
      bg: '#fff7ed',
    },
    {
      label: 'Pending Review',
      value: metrics.pending_review,
      sub: 'Awaiting human sign-off',
      icon: CheckCircle2,
      color: '#0284c7',
      bg: '#f0f9ff',
    },
    {
      label: 'Security & Sources',
      value: `${metrics.quarantined_sources} Blocked`,
      sub: 'IPI prompt-injection filter active',
      icon: ShieldCheck,
      color: '#16a34a',
      bg: '#f0fdf4',
    },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: 16,
      marginBottom: 24,
    }}>
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="metric-tile"
            style={{ padding: '18px 20px' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                {card.label}
              </span>
              <div style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: card.bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Icon size={16} color={card.color} />
              </div>
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.1 }}>
              {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>
              {card.sub}
            </div>
          </div>
        );
      })}
    </div>
  );
}
