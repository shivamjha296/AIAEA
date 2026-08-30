'use client';

import { useState, useEffect, useCallback } from 'react';
import TopBar from '@/components/layout/TopBar';
import ScanPanel from '@/components/layout/ScanPanel';
import MetricsRow from '@/components/dashboard/MetricsRow';
import ActivityChart from '@/components/dashboard/ActivityChart';
import RegulationFeed from '@/components/dashboard/RegulationFeed';
import { SkeletonCard } from '@/components/ui/Skeletons';
import type { DashboardMetrics, ActivityPoint, RegulationListItem, RiskDistribution } from '@/lib/types';
import { fetchMetrics, fetchActivity, fetchRegulations, fetchRiskDistribution } from '@/lib/api';

export default function OverviewPage() {
  const [scanOpen, setScanOpen] = useState(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [activity, setActivity] = useState<ActivityPoint[]>([]);
  const [regs, setRegs] = useState<RegulationListItem[]>([]);
  const [dist, setDist] = useState<RiskDistribution>({ CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, UNKNOWN: 0 });
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  if (error) throw error;

  const loadAll = useCallback(async () => {
    try {
      const [m, a, r, d] = await Promise.all([
        fetchMetrics(),
        fetchActivity(period),
        fetchRegulations({ page_size: 8 }),
        fetchRiskDistribution(),
      ]);
      setMetrics(m);
      setActivity(a);
      setRegs(r.items);
      setDist(d);
    } catch (e) {
      console.error('Dashboard load error:', e);
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    loadAll();
  }, []);

  const handlePeriod = (d: number) => {
    setPeriod(d);
    fetchActivity(d).then(setActivity).catch(() => {});
  };

  return (
    <>
      <TopBar
        title="Compliance Command Center"
        subtitle="Real-time Indian Banking Regulatory Surveillance"
        onScanClick={() => setScanOpen(true)}
      />

      <div className="page-container fade-in">
        {/* KPI Metrics */}
        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 24 }}>
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} height={100} />)}
          </div>
        ) : metrics ? (
          <MetricsRow metrics={metrics} onScanClick={() => setScanOpen(true)} />
        ) : null}

        {/* Activity Trend Graph */}
        <div style={{ marginBottom: 24 }}>
          <ActivityChart data={activity} onPeriodChange={handlePeriod} period={period} />
        </div>

        {/* Feed & Distribution */}
        {!loading && (
          <RegulationFeed items={regs} distribution={dist} />
        )}
      </div>

      <ScanPanel
        open={scanOpen}
        onClose={() => setScanOpen(false)}
        onComplete={() => { setScanOpen(false); loadAll(); }}
      />
    </>
  );
}
