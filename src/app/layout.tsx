import React from 'react';
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SüperToto Terminali | Profesyonel Spor Toto Kurgu ve Garanti Sistemi',
  description: 'Bloomberg tarzı yüksek yoğunluklu, matematiksel kalkan ve yapay zeka sürpriz avcısı Spor Toto kokpiti',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" className="dark">
      <body className="bg-[#06080e] text-[#f8fafc] antialiased overflow-x-hidden overflow-y-auto lg:overflow-hidden m-0 p-0">
        {children}
      </body>
    </html>
  );
}
