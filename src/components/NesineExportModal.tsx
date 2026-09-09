import React, { useState, useEffect } from 'react';
import { generateNesineTransferScript } from '../lib/nesineScriptGenerator';

interface NesineExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  columns: string[];
  memberId?: number | string;
  pno?: number | string;
}

export const NesineExportModal: React.FC<NesineExportModalProps> = ({
  isOpen,
  onClose,
  columns,
  memberId,
  pno
}) => {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const totalCoupons = Math.ceil(columns.length / 4);

  const handleCopy = () => {
    const scriptCode = generateNesineTransferScript(columns, memberId, pno);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(scriptCode).catch(() => {});
    } else {
      prompt("Kodu kopyalamak için Ctrl+C yapınız:", scriptCode);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 3500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fadeIn select-none">
      {/* Backdrop */}
      <div className="absolute inset-0" onClick={onClose} />

      <div className="relative bg-[#0a0f1d] border border-[#1e293b] rounded-2xl w-full max-w-md p-6 shadow-2xl text-slate-100 flex flex-col gap-4 z-10 font-sans">
        {/* Başlık */}
        <div className="flex justify-between items-center border-b border-[#1e293b] pb-3">
          <h3 className="text-base font-extrabold text-emerald-400 flex items-center gap-2">
            <span className="text-lg">🚀</span>
            <span>Nesine'ye Otomatik Aktar</span>
          </h3>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg bg-[#0f172a] hover:bg-[#1e293b] text-slate-400 hover:text-white flex items-center justify-center transition cursor-pointer text-sm font-bold"
          >
            ✕
          </button>
        </div>

        {/* Bilgilendirme */}
        <div className="bg-[#06080e] border border-[#1e293b] rounded-xl p-3 flex items-center justify-between text-xs font-mono">
          <div>
            <span className="text-[#64748b] block text-[10px]">Toplam Kolon</span>
            <span className="text-emerald-400 font-extrabold text-sm">{columns.length} Adet</span>
          </div>
          <div>
            <span className="text-[#64748b] block text-[10px]">Nesine Kuponu (A-B-C-D)</span>
            <span className="text-amber-300 font-extrabold text-sm">{totalCoupons} Sayfa</span>
          </div>
          <div>
            <span className="text-[#64748b] block text-[10px]">Tutar</span>
            <span className="text-[#38bdf8] font-extrabold text-sm">{(columns.length * 10).toLocaleString('tr-TR')} TL</span>
          </div>
        </div>

        {/* Adımlar */}
        <div className="bg-[#0f172a]/80 rounded-xl p-3.5 space-y-2.5 text-xs text-slate-300 border border-[#1e293b]">
          <div className="flex items-start gap-2.5">
            <span className="bg-emerald-500/20 text-emerald-400 font-extrabold px-2 py-0.5 rounded text-[11px] shrink-0 mt-0.5">
              1
            </span>
            <span>Aşağıdaki butona basarak <b>Aktarım Kodunu Kopyalayın</b>.</span>
          </div>
          <div className="flex items-start gap-2.5">
            <span className="bg-emerald-500/20 text-emerald-400 font-extrabold px-2 py-0.5 rounded text-[11px] shrink-0 mt-0.5">
              2
            </span>
            <span>
              <a
                href="https://www.nesine.com/sportoto"
                target="_blank"
                rel="noreferrer"
                className="text-sky-400 underline hover:text-sky-300 font-semibold"
              >
                Nesine Spor Toto
              </a>{' '}
              sayfasında klavyeden <b>F12</b> tuşuna basıp <b>Console (Konsol)</b> sekmesini açın.
            </span>
          </div>
          <div className="flex items-start gap-2.5">
            <span className="bg-emerald-500/20 text-emerald-400 font-extrabold px-2 py-0.5 rounded text-[11px] shrink-0 mt-0.5">
              3
            </span>
            <span>Kodu yapıştırıp <b>Enter</b>'a basın; kuponlar 10'arlı paketler halinde güvenle <b>Kayıtlı Kuponlarım</b>'a eklensin.</span>
          </div>
        </div>

        {/* Kopyalama Butonu */}
        <button
          onClick={handleCopy}
          className={`w-full py-3.5 rounded-xl font-bold transition-all duration-200 shadow-lg text-xs cursor-pointer flex items-center justify-center gap-2 ${
            copied
              ? 'bg-emerald-400 text-slate-950 font-black shadow-emerald-500/30 scale-[1.01]'
              : 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-950/50 active:scale-[0.98]'
          }`}
        >
          <span className="text-base">{copied ? '✓' : '📋'}</span>
          <span className="text-[12.5px]">{copied ? 'Kod Kopyalandı! (Nesine Konsoluna Yapıştırın)' : 'Tek Tıkla Kodu Kopyala'}</span>
        </button>

        {/* Nesine Linki */}
        <div className="text-center pt-1 border-t border-[#1e293b]/60">
          <a
            href="https://www.nesine.com/sportoto"
            target="_blank"
            rel="noreferrer"
            className="text-[11px] text-slate-400 hover:text-emerald-400 transition inline-flex items-center gap-1.5"
          >
            <span>Nesine Spor Toto Sayfasını Yeni Sekmede Aç</span>
            <span>➔</span>
          </a>
        </div>
      </div>
    </div>
  );
};
