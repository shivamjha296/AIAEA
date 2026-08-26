'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Clock, RefreshCw, Scan, X } from 'lucide-react';
import type { HealthStatus } from '@/lib/types';
import { fetchHealth } from '@/lib/api';

interface TopBarProps {
  title: string;
  subtitle?: string;
  onScanClick: () => void;
}

function StatusDot({ status }: { status: string }) {
  const color = status === 'operational' ? 'var(--accent-green)'
    : status === 'degraded' ? 'var(--accent-amber)'
    : 'var(--accent-red)';
  return (
    <span style={{
      display: 'inline-block', width: 7, height: 7,
      borderRadius: '50%', background: color, flexShrink: 0,
    }} />
  );
}

export default function TopBar({ title, subtitle, onScanClick }: TopBarProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const loadHealth = async () => {
    setLoading(true);
    try { setHealth(await fetchHealth()); }
    catch { /* quiet */ }
    finally { setLoading(false); }
  };

  useEffect(() => { loadHealth(); }, []);

  return (
    <div style={{
      height: 60,
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-default)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      position: 'sticky',
      top: 0,
      zIndex: 30,
      backdropFilter: 'blur(8px)',
    }}>
      {/* Title */}
      <div>
        <h1 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1 }}>{subtitle}</p>
        )}
      </div>

      {/* Right actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {/* Health indicators */}
        {health && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {(['database', 'llm', 'search'] as const).map(key => (
              <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <StatusDot status={health[key]} />
                <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                  {key}
                </span>
              </div>
            ))}
          </div>
        )}

        <button
          onClick={loadHealth}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 4 }}
          title="Refresh status"
        >
          <RefreshCw size={13} style={{ transform: loading ? 'rotate(360deg)' : 'none', transition: 'transform 0.5s' }} />
        </button>

        <div style={{ width: 1, height: 20, background: 'var(--border-default)' }} />

        {/* Run Scan button */}
        <button className="btn btn-primary" onClick={onScanClick} style={{ fontSize: 12, padding: '6px 14px' }}>
          <Scan size={13} />
          Run Live Scan
        </button>
      </div>
    </div>
  );
}
