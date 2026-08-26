import { Database } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  cta?: { label: string; onClick: () => void };
}

export default function EmptyState({
  title = 'No data yet',
  message = 'Run a live scan to populate this view with real regulatory intelligence.',
  cta,
}: EmptyStateProps) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '64px 32px', textAlign: 'center',
    }}>
      <div style={{
        width: 64, height: 64, borderRadius: 16,
        background: 'var(--bg-raised)',
        border: '1px solid var(--border-default)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: 20,
      }}>
        <Database size={28} color="var(--text-muted)" />
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
        {title}
      </h3>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 360, lineHeight: 1.6 }}>
        {message}
      </p>
      {cta && (
        <button
          className="btn btn-primary"
          onClick={cta.onClick}
          style={{ marginTop: 20 }}
        >
          {cta.label}
        </button>
      )}
    </div>
  );
}
