import React, { useState, useEffect, useRef } from 'react';
import { SolutionPayload } from '../types';
import { saveCoupon } from '../lib/storage';

interface SaveCouponModalProps {
  isOpen: boolean;
  onClose: () => void;
  solution: SolutionPayload | null;
  week?: string | number;
  onSuccess?: (couponName: string) => void;
}

export const SaveCouponModal: React.FC<SaveCouponModalProps> = ({
  isOpen,
  onClose,
  solution,
  week = '141236',
  onSuccess
}) => {
  const [couponName, setCouponName] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && solution) {
      const defaultMode = solution.solver_mode === 'base_only' ? 'Ekonomik 13G' : (solution.mode || '13G');
      const defaultTitle = `Hafta ${week} - ${solution.total_columns} Kolon (${defaultMode})`;
      setCouponName(defaultTitle);
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
          inputRef.current.select();
        }
      }, 50);
    }
  }, [isOpen, solution, week]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !solution) return null;

  const handleSave = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const finalName = couponName.trim() || `Hafta ${week} - ${solution.total_columns} Kolon`;

    saveCoupon({
      name: finalName,
      week: week,
      columnsCount: solution.total_columns,
      columns: solution.columns,
      compact_columns: solution.compact_columns,
      mode: solution.mode,
      total_cost: solution.total_cost
    });

    if (onSuccess) {
      onSuccess(finalName);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      {/* Click outside backdrop */}
      <div className="absolute inset-0" onClick={onClose} />

      <div className="relative w-full max-w-md bg-[#0a0f1d] border border-[#1e293b] rounded-xl shadow-2xl p-5 z-10 flex flex-col gap-4 text-xs font-sans">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1e293b] pb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">💾</span>
            <div>
              <h3 className="text-sm font-extrabold text-white">Kuponu Kaydet</h3>
              <p className="text-[10px] text-[#64748b]">Kupon havuzunuza isimlendirerek ekleyin</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg bg-[#0f172a] hover:bg-[#1e293b] text-[#94a3b8] hover:text-white flex items-center justify-center transition text-sm cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] font-bold text-[#94a3b8]">Kupon Başlığı / İsmi</label>
            <input
              ref={inputRef}
              type="text"
              value={couponName}
              onChange={(e) => setCouponName(e.target.value)}
              placeholder="Örn: Hafta 141236 - 120 Kolon (13G)"
              className="w-full bg-[#06080e] border border-[#334155] focus:border-[#38bdf8] focus:ring-1 focus:ring-[#38bdf8] rounded-lg px-3 py-2 text-white font-medium text-xs outline-none transition"
            />
          </div>

          {/* Quick Metrics Capsule */}
          <div className="grid grid-cols-3 gap-2 bg-[#06080e] border border-[#1e293b] rounded-lg p-2.5 text-center font-mono">
            <div>
              <span className="text-[9.5px] text-[#64748b] block">Kolon Sayısı</span>
              <span className="text-xs font-bold text-[#38bdf8]">{solution.total_columns}</span>
            </div>
            <div>
              <span className="text-[9.5px] text-[#64748b] block">Toplam Maliyet</span>
              <span className="text-xs font-bold text-amber-400">{solution.total_cost || solution.total_columns * 10} TL</span>
            </div>
            <div>
              <span className="text-[9.5px] text-[#64748b] block">Kalkan Koruması</span>
              <span className="text-xs font-bold text-emerald-400">%{solution.coverage_pct.toFixed(1)}</span>
            </div>
          </div>

          <div className="text-[10px] text-[#64748b] leading-relaxed">
            💡 Kaydedilen kuponları <strong>🔴 Canlı Skor Telemetrisi</strong> istasyonunda takip edebilir veya senaryo simülasyonlarında kullanabilirsiniz.
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-1 border-t border-[#1e293b]">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-2 bg-[#0f172a] hover:bg-[#1e293b] text-[#94a3b8] hover:text-white rounded-lg font-bold text-xs transition cursor-pointer"
            >
              Vazgeç
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-lg font-extrabold text-xs shadow-md shadow-emerald-950/40 transition active:scale-95 cursor-pointer flex items-center gap-1.5"
            >
              <span>💾</span>
              <span>Kaydet</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
