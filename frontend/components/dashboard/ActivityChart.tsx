'use client';

import { useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { ActivityPoint } from '@/lib/types';
import { formatDate } from '@/lib/utils';

const PERIODS = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
];

interface Props {
  data: ActivityPoint[];
  onPeriodChange: (days: number) => void;
  period: number;
}

export default function ActivityChart({ data, onPeriodChange, period }: Props) {
  return (
    <div className="card" style={{ padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            Regulatory Activity
          </h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
            New regulations discovered over time
          </p>
        </div>
        <div style={{ display: 'flex', gap: 4, background: 'var(--bg-raised)', borderRadius: 6, padding: 3 }}>
          {PERIODS.map(p => (
            <button
              key={p.days}
              onClick={() => onPeriodChange(p.days)}
              style={{
                padding: '4px 10px',
                borderRadius: 4,
                border: 'none',
                fontSize: 11,
                fontWeight: 600,
                cursor: 'pointer',
                background: period === p.days ? 'var(--bg-surface)' : 'transparent',
                color: period === p.days ? 'var(--text-primary)' : 'var(--text-muted)',
                transition: 'all 0.15s',
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {data.length === 0 ? (
        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No activity data yet — run a scan to populate</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id="actGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#388bfd" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#388bfd" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={d => {
                try { return new Date(d).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }); }
                catch { return d; }
              }}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: 8,
                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                fontSize: 12,
                color: '#0f172a',
              }}
              labelStyle={{ color: '#64748b', marginBottom: 4, fontWeight: 500 }}
              formatter={(v: unknown) => [v as number, 'Regulations']}
              labelFormatter={(d: unknown) => formatDate(String(d))}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#2563eb"
              strokeWidth={2}
              fill="url(#actGrad)"
              dot={false}
              activeDot={{ r: 4, fill: '#2563eb', stroke: '#ffffff', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
