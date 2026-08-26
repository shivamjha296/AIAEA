import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';

export const metadata: Metadata = {
  title: 'Regulatory Compliance Radar — Indian Banking Intelligence',
  description:
    'Autonomous real-time regulatory surveillance platform for Indian cooperative banks. ' +
    'Monitors RBI, MeitY, CERT-In, SEBI and other regulators via live web data.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0d1117" />
      </head>
      <body>
        <Sidebar />
        <div className="main-layout">
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
