import React, { useState } from 'react';
import { useToto } from '../context/TotoContext';
import { BookmarkletButton } from './BookmarkletButton';

export const VaultStation: React.FC = () => {
  const { solution, matches, setToastMessage, setSelectedTab } = useToto() as any;
  const [activeFormat, setActiveFormat] = useState<'txt' | 'compact' | 'std'>('txt');
  const [copiedType, setCopiedType] = useState<string | null>(null);

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
  const totSheets = solution.total_sheets || Math.ceil(totCols / 4);
  const mode = solution.mode || '13G';

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
    sheets: solution.sheets || [],
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

  const handleOneClickNesine = () => {
    const jsonStr = JSON.stringify(solution);
    try {
      localStorage.setItem("TOTO_AUTO_INJECT", jsonStr);
    } catch {}
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(jsonStr).catch(() => {});
    }
    window.open("https://www.nesine.com/sportoto#auto_inject=1", "_blank");
    setToastMessage("⚡ Kupon tarayıcı hafızasına yazıldı ve Nesine sekmesi açıldı!");
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

      {/* 2. Main Grid: Left Export Hub / Right Sheets Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 flex-1">
        {/* Left Column (5 cols): Export Hub */}
        <div className="lg:col-span-5 flex flex-col gap-2 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3">
          <h3 className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider flex items-center gap-1.5">
            <span>📤</span> Dışa Aktarım & Nesine Köprüsü
          </h3>

          {/* Direct Nesine 1-Click Injection CTA */}
          <button
            onClick={handleOneClickNesine}
            className="w-full py-2.5 px-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold rounded-lg shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-2 text-xs transition active:scale-98 cursor-pointer"
          >
            <span>🚀</span>
            <span>Tek Tıkla Nesine'ye Gönder</span>
            <span className="text-[9px] font-normal bg-emerald-900/80 px-1.5 py-0.5 rounded border border-emerald-400/40">Tampermonkey</span>
          </button>

          {/* Format Tabs */}
          <div className="flex items-center gap-1 bg-[#06080e] p-1 rounded border border-[#1e293b]">
            <button
              onClick={() => setActiveFormat('txt')}
              className={`flex-1 py-1 text-[10px] font-bold rounded transition ${activeFormat === 'txt' ? 'bg-[#1e293b] text-[#38bdf8]' : 'text-[#94a3b8] hover:text-white'}`}
            >
              📝 Düz (.TXT)
            </button>
            <button
              onClick={() => setActiveFormat('compact')}
              className={`flex-1 py-1 text-[10px] font-bold rounded transition ${activeFormat === 'compact' ? 'bg-[#1e293b] text-[#38bdf8]' : 'text-[#94a3b8] hover:text-white'}`}
            >
              ⚡ Kompakt JSON
            </button>
            <button
              onClick={() => setActiveFormat('std')}
              className={`flex-1 py-1 text-[10px] font-bold rounded transition ${activeFormat === 'std' ? 'bg-[#1e293b] text-[#38bdf8]' : 'text-[#94a3b8] hover:text-white'}`}
            >
              📄 Geniş JSON
            </button>
          </div>

          {/* Text Area */}
          <div className="relative">
            <textarea
              readOnly
              rows={5}
              value={activeFormat === 'txt' ? plainText : activeFormat === 'compact' ? compactJson : stdJson}
              className="w-full bg-[#06080e] border border-[#1e293b] rounded p-2 text-[10.5px] font-mono text-[#cbd5e1] resize-none focus:outline-none focus:border-[#38bdf8]"
            />
            <button
              onClick={() => handleCopy(activeFormat === 'txt' ? plainText : activeFormat === 'compact' ? compactJson : stdJson, activeFormat.toUpperCase())}
              className="absolute top-2 right-2 bg-[#0f172a] hover:bg-[#1e293b] text-sky-400 hover:text-white border border-[#1e293b] px-2 py-0.5 rounded text-[10px] font-bold transition cursor-pointer"
            >
              {copiedType === activeFormat.toUpperCase() ? '✅ Kopyalandı' : 'Kopyala'}
            </button>
          </div>

          {/* Quick Action Download Buttons */}
          <div className="grid grid-cols-3 gap-1.5 pt-1">
            <button
              onClick={() => handleDownload(plainText, `supertoto_${mode}_${totCols}kolon.txt`, 'text/plain')}
              className="py-1.5 px-2 bg-[#0f172a] hover:bg-[#1e293b] text-[#f8fafc] border border-[#1e293b] rounded text-[10.5px] font-bold flex items-center justify-center gap-1 transition cursor-pointer"
            >
              <span>💾</span> .TXT İndir
            </button>
            <button
              onClick={() => handleDownload(`No,Kolon\n` + columns.map((c, i) => `${i + 1},${c.join('')}`).join('\n'), `supertoto_${mode}_${totCols}kolon.csv`, 'text/csv')}
              className="py-1.5 px-2 bg-[#0f172a] hover:bg-[#1e293b] text-[#f8fafc] border border-[#1e293b] rounded text-[10.5px] font-bold flex items-center justify-center gap-1 transition cursor-pointer"
            >
              <span>📊</span> .CSV İndir
            </button>
            <button
              onClick={() => handleDownload(stdJson, `supertoto_${mode}_${totCols}kolon.json`, 'application/json')}
              className="py-1.5 px-2 bg-[#0f172a] hover:bg-[#1e293b] text-[#f8fafc] border border-[#1e293b] rounded text-[10.5px] font-bold flex items-center justify-center gap-1 transition cursor-pointer"
            >
              <span>📦</span> .JSON İndir
            </button>
          </div>

          {/* Bookmarklet Bridge */}
          <div className="pt-2 border-t border-[#1e293b]">
            <BookmarkletButton />
          </div>
        </div>

        {/* Right Column (7 cols): 40 TL Sheets Table Visualization */}
        <div className="lg:col-span-7 flex flex-col bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 overflow-hidden">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#1e293b]">
            <h3 className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider flex items-center gap-1.5">
              <span>📋</span> 40 TL Kupon Yaprakları (A-B-C-D)
            </h3>
            <span className="text-[10px] font-mono text-[#94a3b8]">
              Toplam: {totSheets} Sayfa ({totCols} Kolon)
            </span>
          </div>

          {/* Scrollable Sheets Container */}
          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {solution.sheets && solution.sheets.map((sheet: any, sIdx: number) => (
              <div key={sIdx} className="bg-[#06080e] border border-[#1e293b] rounded-lg overflow-hidden">
                <div className="bg-[#0f172a] px-3 py-1.5 flex items-center justify-between border-b border-[#1e293b]">
                  <span className="font-mono font-extrabold text-[#38bdf8] text-xs">
                    KUPON #{sheet.sheet_id || (sIdx + 1)}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[9.5px] font-mono text-emerald-400 font-bold bg-[#062419] px-2 py-0.5 rounded border border-emerald-500/30">
                      40.00 TL
                    </span>
                    <span className="text-[9.5px] font-mono text-[#64748b]">4 Kolon</span>
                  </div>
                </div>

                <table className="w-full text-center text-xs font-mono">
                  <thead>
                    <tr className="bg-[#0a0f1d] text-[#64748b] text-[9.5px] border-b border-[#1e293b]/60">
                      <th className="py-1 px-2 text-left">Maç</th>
                      <th className="py-1">A</th>
                      <th className="py-1">B</th>
                      <th className="py-1">C</th>
                      <th className="py-1">D</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.from({ length: 15 }, (_, mIdx) => {
                      const matchName = matches[mIdx] ? `${matches[mIdx].home} - ${matches[mIdx].away}` : `Maç #${mIdx + 1}`;
                      const pickA = sheet.A?.[mIdx] || '-';
                      const pickB = sheet.B?.[mIdx] || '-';
                      const pickC = sheet.C?.[mIdx] || '-';
                      const pickD = sheet.D?.[mIdx] || '-';

                      const getPill = (val: string) => {
                        if (val === '1') return <span className="inline-block w-5 h-5 leading-5 rounded bg-sky-950/80 text-sky-300 font-extrabold border border-sky-600/50">1</span>;
                        if (val === 'X') return <span className="inline-block w-5 h-5 leading-5 rounded bg-amber-950/80 text-amber-300 font-extrabold border border-amber-600/50">X</span>;
                        if (val === '2') return <span className="inline-block w-5 h-5 leading-5 rounded bg-emerald-950/80 text-emerald-300 font-extrabold border border-emerald-600/50">2</span>;
                        return <span className="text-[#64748b]">-</span>;
                      };

                      return (
                        <tr key={mIdx} className="border-b border-[#1e293b]/40 hover:bg-[#0f172a]/50">
                          <td className="py-1 px-2 text-left text-[10px] text-[#94a3b8] truncate max-w-[140px]">
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
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
