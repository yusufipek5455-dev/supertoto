import React, { useState } from 'react';
import { useToto } from '../context/TotoContext';
import { SaveCouponModal } from './SaveCouponModal';
import { NesineExportModal } from './NesineExportModal';

export const VaultStation: React.FC = () => {
  const { solution, matches, setToastMessage, setSelectedTab, programInfo } = useToto() as any;
  const [activeFormat, setActiveFormat] = useState<'txt' | 'compact' | 'std'>('txt');
  const [copiedType, setCopiedType] = useState<string | null>(null);
  const [selectedSheetIdx, setSelectedSheetIdx] = useState<number>(0);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState<boolean>(false);
  const [isNesineModalOpen, setIsNesineModalOpen] = useState<boolean>(false);

  if (!solution || !solution.columns || solution.columns.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-[#0a0f1d] border border-[#1e293b] rounded-lg text-center select-none">
        <div className="text-4xl mb-3">⚠️</div>
        <h3 className="text-sm font-bold text-amber-300 mb-1">Henüz Üretilmiş Kupon Bulunmuyor</h3>
        <p className="text-xs text-[#94a3b8] mb-4 max-w-md">
          Kupon kasasını ve Nesine aktarım köprüsünü kullanmak için önce Kupon Oluşturucu sekmesinden bir sistem kuponu oluşturun.
        </p>
        <button
          onClick={() => setSelectedTab && setSelectedTab('creator')}
          className="px-4 py-2 bg-[#059669] hover:bg-[#047857] text-white font-bold text-xs rounded-lg transition active:scale-95 cursor-pointer shadow-md"
        >
          🎯 Kupon Oluşturucuya Git
        </button>
      </div>
    );
  }

  const columns: string[][] = solution.columns;
  const totCols = solution.total_columns || columns.length;
  const totCost = solution.total_cost || totCols * 10;
  const sheets = solution.sheets || [];
  const totSheets = solution.total_sheets || (sheets.length > 0 ? sheets.length : Math.ceil(totCols / 4));
  const mode = solution.mode || '13G';

  // Safe sheet index
  const safeIdx = Math.min(Math.max(0, selectedSheetIdx), Math.max(0, sheets.length - 1));
  const currentSheet = sheets[safeIdx] || null;

  // Export payloads
  const plainText = solution.compact_columns ? solution.compact_columns.join('\n') : columns.map(c => c.join('')).join('\n');
  const compactJson = JSON.stringify({
    compact: true,
    cols: solution.compact_columns || columns.map(c => c.join('')),
    total_columns: totCols,
    total_sheets: totSheets,
    total_cost_tl: totCost
  });
  const stdJson = JSON.stringify({
    sheets: sheets,
    total_columns: totCols,
    total_sheets: totSheets,
    total_cost_tl: totCost
  }, null, 2);

  const handleCopy = (text: string, label: string) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        setCopiedType(label);
        setToastMessage(`${label} panoya kopyalandı!`);
        setTimeout(() => setCopiedType(null), 2000);
      });
    } else {
      prompt("Kopyalayın:", text);
      setToastMessage(`${label} panoya kopyalandı!`);
    }
  };

  const handleDownload = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setToastMessage(`💾 ${filename} başarıyla indirildi.`);
  };

  return (
    <div className="flex-1 flex flex-col gap-2.5 overflow-y-auto pr-0.5 select-none text-xs">
      {/* 1. Header Metrics */}
      <div className="grid grid-cols-3 gap-2 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3">
        <div className="flex flex-col">
          <span className="text-[10px] text-[#94a3b8] uppercase font-bold">Paket Tutarı</span>
          <span className="text-base font-extrabold text-emerald-400 font-mono">{totCost.toLocaleString()} TL</span>
          <span className="text-[9px] text-[#64748b]">10.00 TL / Kolon</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-[#94a3b8] uppercase font-bold">Üretilen Kolon</span>
          <span className="text-base font-extrabold text-[#38bdf8] font-mono">{totCols} Adet</span>
          <span className="text-[9px] text-[#64748b]">{mode} Matematiksel Kalkan</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-[#94a3b8] uppercase font-bold">Nesine Kupon Sayısı</span>
          <span className="text-base font-extrabold text-amber-300 font-mono">{totSheets} Sayfa</span>
          <span className="text-[9px] text-[#64748b]">Her Kupon 40 TL (A-B-C-D)</span>
        </div>
      </div>

      {/* 2. Main Grid: Left Export Hub / Right Single Sheet Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 flex-1">
        {/* Left Column (5 cols): Streamlined Nesine Direct Upload Hub */}
        <div className="lg:col-span-5 flex flex-col justify-between gap-3 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-4 shadow-xl">
          <div className="flex flex-col gap-3">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
              <h3 className="text-xs font-extrabold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                <span className="text-sm">🚀</span>
                <span>Nesine Konsol Enjektörü</span>
              </h3>
              <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-500/40 px-2 py-0.5 rounded-full font-bold">
                10'lu Paket Motoru
              </span>
            </div>

            {/* Primary Action: Direct Nesine Upload Button */}
            <button
              onClick={() => setIsNesineModalOpen(true)}
              className="w-full py-3.5 px-4 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black rounded-xl shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2.5 transition-all duration-200 active:scale-[0.98] cursor-pointer text-xs"
            >
              <span className="text-lg">🚀</span>
              <span>Nesine'ye Otomatik Aktar</span>
              <span className="text-[10px] font-bold bg-slate-950 text-emerald-300 px-2 py-0.5 rounded-md">
                10'lu Batch
              </span>
            </button>

            {/* Feature Information Cards */}
            <div className="bg-[#06080e] border border-[#1e293b] rounded-xl p-3 flex flex-col gap-2 text-xs text-slate-300">
              <div className="flex items-center justify-between font-mono pb-1 border-b border-[#1e293b]/60 text-[11px]">
                <span className="text-[#64748b]">Aktarım Şekli:</span>
                <span className="font-bold text-white">10 Kuponda Bir 2.5s Dinlenme</span>
              </div>
              <div className="flex items-center justify-between font-mono pb-1 border-b border-[#1e293b]/60 text-[11px]">
                <span className="text-[#64748b]">Hedef Konum:</span>
                <span className="font-bold text-emerald-400">Nesine Kayıtlı Kuponlarım</span>
              </div>
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#64748b]">Güvenlik:</span>
                <span className="font-bold text-amber-300">Rate-Limit & XSRF Korumalı</span>
              </div>
            </div>

            <div className="p-2.5 bg-[#06080e]/70 border border-[#1e293b] rounded-lg text-[10.5px] text-[#94a3b8] leading-relaxed">
              💡 <b>Nasıl Çalışır?</b> Yukarıdaki butona basarak aktarım kodunu kopyalayın, Nesine sayfasında <b>F12 &gt; Console</b> sekmesine yapıştırıp Enter'a basın. Tüm {totCols} kolonunuz otomatik olarak hesabınıza işlenir.
            </div>
          </div>

          {/* Secondary Actions: Kupon Havuzu & Çevrimdışı İndirme */}
          <div className="flex flex-col gap-2 pt-2 border-t border-[#1e293b]">
            <button
              onClick={() => setIsSaveModalOpen(true)}
              className="w-full py-2.5 px-3 bg-[#0f172a] hover:bg-[#1e293b] text-sky-300 hover:text-white border border-[#1e293b] hover:border-sky-500/50 rounded-xl font-bold flex items-center justify-center gap-2 transition cursor-pointer text-xs"
            >
              <span>💾</span>
              <span>Kupon Havuzuna Ekle (Çoklu Takip)</span>
            </button>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleDownload(plainText, `supertoto_${mode}_${totCols}kolon.txt`, 'text/plain')}
                className="py-1.5 px-2 bg-[#06080e] hover:bg-[#0f172a] text-[#94a3b8] hover:text-white border border-[#1e293b] rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 transition cursor-pointer"
              >
                <span>📝</span> .TXT İndir
              </button>
              <button
                onClick={() => handleDownload(`No,Kolon\n` + columns.map((c, i) => `${i + 1},${c.join('')}`).join('\n'), `supertoto_${mode}_${totCols}kolon.csv`, 'text/csv')}
                className="py-1.5 px-2 bg-[#06080e] hover:bg-[#0f172a] text-[#94a3b8] hover:text-white border border-[#1e293b] rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 transition cursor-pointer"
              >
                <span>📊</span> .CSV İndir
              </button>
            </div>
          </div>
        </div>


        {/* Right Column (7 cols): Single 40 TL Sheet Inspector (Zero DOM Overload) */}
        <div className="lg:col-span-7 flex flex-col bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 overflow-hidden">
          {/* Header & Sheet Paging Controls */}
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#1e293b] flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <h3 className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider flex items-center gap-1.5">
                <span>📋</span> 40 TL Sayfa Önizleme
              </h3>
              <span className="text-[10px] font-mono text-[#94a3b8]">
                (Sayfa {safeIdx + 1} / {totSheets})
              </span>
            </div>

            {sheets.length > 1 && (
              <div className="flex items-center gap-1.5">
                <button
                  disabled={safeIdx <= 0}
                  onClick={() => setSelectedSheetIdx(p => Math.max(0, p - 1))}
                  className="px-2 py-1 bg-[#0f172a] hover:bg-[#1e293b] disabled:opacity-30 rounded text-[10.5px] text-[#cbd5e1] border border-[#1e293b] transition cursor-pointer"
                >
                  ◀ Önceki
                </button>
                <select
                  value={safeIdx}
                  onChange={(e) => setSelectedSheetIdx(Number(e.target.value))}
                  className="bg-[#06080e] text-[#38bdf8] font-bold text-[10.5px] rounded px-2 py-1 border border-[#1e293b] focus:outline-none cursor-pointer"
                >
                  {sheets.map((_: any, idx: number) => (
                    <option key={idx} value={idx}>
                      Sayfa #{idx + 1} ({idx * 4 + 1}-{Math.min(totCols, (idx + 1) * 4)}. Kolonlar)
                    </option>
                  ))}
                </select>
                <button
                  disabled={safeIdx >= sheets.length - 1}
                  onClick={() => setSelectedSheetIdx(p => Math.min(sheets.length - 1, p + 1))}
                  className="px-2 py-1 bg-[#0f172a] hover:bg-[#1e293b] disabled:opacity-30 rounded text-[10.5px] text-[#cbd5e1] border border-[#1e293b] transition cursor-pointer"
                >
                  Sonraki ▶
                </button>
              </div>
            )}
          </div>

          {/* Single Sheet Table (Lightweight: Exactly 15 Rows) */}
          {currentSheet ? (
            <div className="flex-1 flex flex-col bg-[#06080e] border border-[#1e293b] rounded-lg overflow-hidden">
              <div className="bg-[#0f172a] px-3 py-1.5 flex items-center justify-between border-b border-[#1e293b]">
                <span className="font-mono font-extrabold text-[#38bdf8] text-xs">
                  KUPON #{currentSheet.sheet_id || (safeIdx + 1)}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-[9.5px] font-mono text-emerald-400 font-bold bg-[#062419] px-2 py-0.5 rounded border border-emerald-500/30">
                    40.00 TL
                  </span>
                  <span className="text-[9.5px] font-mono text-[#64748b]">4 Kolon (A, B, C, D)</span>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto">
                <table className="w-full text-center text-xs font-mono">
                  <thead>
                    <tr className="bg-[#0a0f1d] text-[#64748b] text-[9.5px] border-b border-[#1e293b]/60 sticky top-0 z-10">
                      <th className="py-1 px-2 text-left">Maç</th>
                      <th className="py-1 text-[#38bdf8]">Harf A</th>
                      <th className="py-1 text-[#38bdf8]">Harf B</th>
                      <th className="py-1 text-[#38bdf8]">Harf C</th>
                      <th className="py-1 text-[#38bdf8]">Harf D</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.from({ length: 15 }, (_, mIdx) => {
                      const matchName = matches[mIdx] ? `${matches[mIdx].home} - ${matches[mIdx].away}` : `Maç #${mIdx + 1}`;
                      const pickA = currentSheet.A?.[mIdx] || '-';
                      const pickB = currentSheet.B?.[mIdx] || '-';
                      const pickC = currentSheet.C?.[mIdx] || '-';
                      const pickD = currentSheet.D?.[mIdx] || '-';

                      const getPill = (val: string) => {
                        if (val === '1') return <span className="inline-block w-5 h-5 leading-5 rounded bg-sky-950/80 text-sky-300 font-extrabold border border-sky-600/50">1</span>;
                        if (val === 'X') return <span className="inline-block w-5 h-5 leading-5 rounded bg-amber-950/80 text-amber-300 font-extrabold border border-amber-600/50">X</span>;
                        if (val === '2') return <span className="inline-block w-5 h-5 leading-5 rounded bg-emerald-950/80 text-emerald-300 font-extrabold border border-emerald-600/50">2</span>;
                        return <span className="text-[#64748b]">-</span>;
                      };

                      return (
                        <tr key={mIdx} className="border-b border-[#1e293b]/40 hover:bg-[#0f172a]/50">
                          <td className="py-1 px-2 text-left text-[10px] text-[#94a3b8] truncate max-w-[160px]">
                            <span className="font-bold text-[#64748b] mr-1.5">{(mIdx + 1).toString().padStart(2, '0')}</span>
                            {matchName}
                          </td>
                          <td className="py-1">{getPill(pickA)}</td>
                          <td className="py-1">{getPill(pickB)}</td>
                          <td className="py-1">{getPill(pickC)}</td>
                          <td className="py-1">{getPill(pickD)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-xs text-[#64748b]">
              Sayfa bulunamadı.
            </div>
          )}
        </div>
      </div>

      {/* Save Coupon Modal */}
      <SaveCouponModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        solution={solution}
        week={programInfo?.week}
        onSuccess={(name) => {
          setToastMessage(`💾 Kupon "${name}" başarıyla kaydedildi.`);
        }}
      />

      {/* Nesine Direct 10-Batch Export Modal */}
      <NesineExportModal
        isOpen={isNesineModalOpen}
        onClose={() => setIsNesineModalOpen(false)}
        columns={solution.compact_columns || columns.map(c => c.join(''))}
        pno={programInfo?.pNo}
      />
    </div>
  );
};


