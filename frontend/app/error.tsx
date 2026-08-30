'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('System Connection Error:', error);
  }, [error]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--bg-default)',
      color: 'var(--text-primary)',
      fontFamily: 'var(--font-sans)',
      padding: 24,
      textAlign: 'center'
    }}>
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: 12,
        padding: '40px 48px',
        maxWidth: 480,
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)'
      }}>
        <AlertTriangle size={48} color="var(--accent-red)" style={{ marginBottom: 24, margin: '0 auto' }} />
        
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 12 }}>
          SYSTEM CONNECTION ERROR
        </h2>
        
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 32, lineHeight: 1.5 }}>
          Unable to connect to the compliance backend. Please ensure the FastAPI service is running on the correct port and try again.
        </p>
        
        <button 
          onClick={() => {
            // Force a hard reload if simply resetting state fails
            window.location.reload();
          }}
          className="btn btn-primary"
          style={{ width: '100%', padding: '12px 16px', display: 'flex', justifyContent: 'center', gap: 8 }}
        >
          <RefreshCw size={16} />
          RETRY CONNECTION
        </button>
      </div>
    </div>
  );
}
