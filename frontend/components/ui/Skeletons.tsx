export function SkeletonCard({ height = 120 }: { height?: number }) {
  return (
    <div className="card" style={{ padding: 20, height }}>
      <div className="skeleton" style={{ height: 14, width: '40%', marginBottom: 12 }} />
      <div className="skeleton" style={{ height: 32, width: '60%', marginBottom: 8 }} />
      <div className="skeleton" style={{ height: 12, width: '80%' }} />
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div style={{ display: 'flex', gap: 16, padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
      <div className="skeleton" style={{ height: 14, flex: 2 }} />
      <div className="skeleton" style={{ height: 14, flex: 1 }} />
      <div className="skeleton" style={{ height: 14, flex: 1 }} />
      <div className="skeleton" style={{ height: 14, width: 80 }} />
    </div>
  );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div>
      {Array.from({ length: rows }).map((_, i) => <SkeletonRow key={i} />)}
    </div>
  );
}
