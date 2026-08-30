'use client';

import { useState, useRef, useCallback } from 'react';
import { CheckCircle, AlertCircle, Loader, X, ChevronDown, ChevronUp } from 'lucide-react';
import type { ScanEvent } from '@/lib/types';
import { startScan, getScanEventsUrl } from '@/lib/api';
import { EVENT_ICONS } from '@/lib/utils';

interface ScanPanelProps {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}


const STAGES = [
  'INITIALIZING', 'QUERY_GENERATION', 'SEARCHING',
  'FETCHING', 'EXTRACTION_SUCCESS', 'GENERATING_REPORT', 'COMPLETE',
];

export default function ScanPanel({ open, onClose, onComplete }: ScanPanelProps) {
  const [scanId, setScanId] = useState<string | null>(null);
  const [events, setEvents] = useState<ScanEvent[]>([]);
  const [status, setStatus] = useState<'idle' | 'running' | 'complete' | 'failed'>('idle');
  const [currentStage, setCurrentStage] = useState<string>('');
  const [expanded, setExpanded] = useState(true);
  const [maxQueries, setMaxQueries] = useState(2);
  const [maxSources, setMaxSources] = useState(3);
  const logRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  };

  const handleStart = useCallback(async () => {
    setEvents([]);
    setStatus('running');
    setCurrentStage('INITIALIZING');

    try {
      const { scan_id } = await startScan(maxQueries, maxSources);
      setScanId(scan_id);

      // Open SSE connection
      const url = getScanEventsUrl(scan_id);
      const es = new EventSource(url);
      esRef.current = es;

      es.onmessage = (e) => {
        try {
          const payload: ScanEvent = JSON.parse(e.data);
          setEvents(prev => [...prev, payload]);
          setCurrentStage(payload.event);
          if (payload.event === 'COMPLETE') {
            setStatus('complete');
            es.close();
            onComplete();
          } else if (payload.event === 'FAILED') {
            setStatus('failed');
            es.close();
          }
          setTimeout(scrollToBottom, 50);
        } catch { /* ignore parse errors */ }
      };

      es.onerror = () => {
        setStatus('failed');
        es.close();
      };
    } catch (err) {
      setEvents(prev => [...prev, {
        event: 'FAILED',
        message: `Failed to start scan: ${err}`,
      }]);
      setStatus('failed');
    }
  }, [maxQueries, maxSources, onComplete]);

  const handleClose = () => {
    esRef.current?.close();
    onClose();
  };

  const reset = () => {
    esRef.current?.close();
    setStatus('idle');
    setScanId(null);
    setEvents([]);
    setCurrentStage('');
  };

  const progress = (() => {
    if (status === 'complete') return 100;
    if (status === 'idle') return 0;
    const idx = STAGES.indexOf(currentStage);
    return idx >= 0 ? Math.round(((idx + 1) / STAGES.length) * 100) : 10;
  })();

  return (
    <>
      {/* Overlay */}
      {open && <div className="overlay" onClick={handleClose} />}

      {/* Panel */}
      <div className={`scan-panel ${open ? 'open' : ''}`}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {status === 'running' && <div className="pulse-dot" />}
            {status === 'complete' && <CheckCircle size={16} color="var(--accent-green)" />}
            {status === 'failed' && <AlertCircle size={16} color="var(--accent-red)" />}
            {status === 'idle' && <Loader size={16} color="var(--text-muted)" />}
            <span style={{ fontSize: 14, fontWeight: 600 }}>Live Regulatory Scan</span>
          </div>
          <button
            onClick={handleClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4 }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Config (idle only) */}
        {status === 'idle' && (
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-default)' }}>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.6 }}>
              Starts a live DDGS search → HTML/PDF extraction → IPI security scan → Ollama LLM extraction → Pydantic validation → SQLite import.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                  Max Queries
                </label>
                <select
                  className="select"
                  value={maxQueries}
                  onChange={e => setMaxQueries(+e.target.value)}
                >
                  {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                  Sources / Query
                </label>
                <select
                  className="select"
                  value={maxSources}
                  onChange={e => setMaxSources(+e.target.value)}
                >
                  {[2,3,5,8].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            </div>
            <button className="btn btn-primary" onClick={handleStart} style={{ width: '100%', justifyContent: 'center' }}>
              Start Live Scan
            </button>
          </div>
        )}

        {/* Progress bar */}
        {status !== 'idle' && (
          <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-default)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {status === 'running' ? currentStage.replace(/_/g, ' ') : status.toUpperCase()}
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                {progress}%
              </span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${progress}%`,
                  background: status === 'complete' ? 'var(--accent-green)'
                    : status === 'failed' ? 'var(--accent-red)'
                    : 'var(--accent-blue)',
                }}
              />
            </div>
            {scanId && (
              <div className="mono" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6 }}>
                scan: {scanId.slice(0, 20)}…
              </div>
            )}
          </div>
        )}

        {/* Log */}
        {status !== 'idle' && (
          <>
            <div
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 20px', cursor: 'pointer', userSelect: 'none',
              }}
              onClick={() => setExpanded(e => !e)}
            >
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Event Log ({events.length})
              </span>
              {expanded ? <ChevronUp size={13} color="var(--text-muted)" /> : <ChevronDown size={13} color="var(--text-muted)" />}
            </div>

            {expanded && (
              <div ref={logRef} style={{ flex: 1, overflowY: 'auto', padding: '0 20px 16px' }}>
                {events.map((ev, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>
                      {EVENT_ICONS[ev.event] ?? 'ℹ️'}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-word' }}>
                        {ev.message}
                      </div>
                      {ev.data && (
                        <div className="mono" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
                          {JSON.stringify(ev.data).slice(0, 120)}
                        </div>
                      )}
                      {ev.timestamp && (
                        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>
                          {new Date(ev.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {status === 'running' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 12 }}>
                    <Loader size={12} style={{ animation: 'spin 1s linear infinite' }} />
                    Processing…
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Footer actions */}
        {status !== 'idle' && status !== 'running' && (
          <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border-default)', display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost" onClick={reset} style={{ flex: 1, justifyContent: 'center', fontSize: 12 }}>
              New Scan
            </button>
            <button className="btn btn-ghost" onClick={handleClose} style={{ flex: 1, justifyContent: 'center', fontSize: 12 }}>
              Close
            </button>
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  );
}
