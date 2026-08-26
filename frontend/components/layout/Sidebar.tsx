'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ShieldAlert, BookOpen, ChevronRight,
  ClipboardList, FileText, Home, Shield, Users, Radio,
} from 'lucide-react';

const NAV = [
  { href: '/', label: 'Overview', icon: Home },
  { href: '/regulations', label: 'Regulatory Updates', icon: BookOpen },
  { href: '/risk', label: 'Risk Register', icon: ShieldAlert },
  { href: '/evidence', label: 'Evidence Explorer', icon: FileText },
  { href: '/security', label: 'Security Monitor', icon: Shield },
  { href: '/review', label: 'Human Review', icon: Users },
  { href: '/audit', label: 'Audit Trail', icon: ClipboardList },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border-default)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            boxShadow: '0 2px 6px rgba(37, 99, 235, 0.25)',
          }}>
            <Radio size={16} color="white" />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
              Compliance Radar
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Banking Surveillance
            </div>
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ flex: 1, padding: '16px 8px' }}>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', padding: '0 12px 10px', letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600 }}>
          Navigation
        </div>
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link key={href} href={href} className={`sidebar-nav-item ${active ? 'active' : ''}`}>
              <Icon size={16} />
              <span style={{ flex: 1 }}>{label}</span>
              {active && <ChevronRight size={14} style={{ opacity: 0.8 }} />}
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border-default)',
        background: '#f8fafc',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="pulse-dot" />
          <span style={{ fontSize: 11, fontWeight: 600, color: '#166534' }}>
            Live Surveillance Active
          </span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
          RBI · MeitY · CERT-In · SEBI
        </div>
      </div>
    </aside>
  );
}
