import React from 'react';
import { useToto, getCascadingOdds } from '../context/TotoContext';
import { GuaranteeMode } from '../types';

export const SolverControls: React.FC = () => {
  const {
    matches,
    selectedMode,
    setSelectedMode,
    solverStrategy,
    setSolverStrategy,
    targetColumns,
    setTargetColumns,
    applyQuickFilter,
    solution,
    setSolution,
    isSolving,
    setIsSolving,
    toastMessage,
    setToastMessage,
    clearToast,
    estimates,
    rawPoolSize,
    solveWithStrategy
  } = useToto();

  const modes: { id: GuaranteeMode; label: string }[] = [
    { id: '15G', label: '15G' },
    { id: '14G', label: '14G' },
    { id: '13G', label: '13G' },
    { id: '12G', label: '12G' },
  ];

  // Derive dynamic baseline figures for currently selected mode
  const currentEstimate = estimates.modes[selectedMode] || estimates.modes['13G'];
  const baselineCols = currentEstimate.columns;
  const baselineCost = currentEstimate.cost_tl;

  // Telemetry figures
  const activeTotalCols = solution ? solution.total_columns : baselineCols;
  const activeTotalCost = activeTotalCols * 10;
  const activeSheetsCount = Math.ceil(activeTotalCols / 4);

  // Single / Double / Triple stats
  const singles = matches.filter(m => m.picks.length === 1).length;
  const doubles = matches.filter(m => m.picks.length === 2).length;
  const triples = matches.filter(m => m.picks.length === 3).length;

  const handleSolve = (chosenStrategy: 'base_only' | 'auto_boost') => {
    solveWithStrategy(chosenStrategy);
  };

  const is13 = selectedMode === '13G';
  const btn1Title = is13 ? "🛡️ Ekonomik 13 Garantili" : `🛡️ Ekonomik ${selectedMode} Garantili`;
  const btn1Desc = is13
    ? "En ucuz 13G sistemi. Fazladan kolon atmaz."
    : `En ucuz ${selectedMode} sistemi. Fazladan kolon atmaz.`;

  const btn2Title = is13 ? "🚀 Akıllı 13G + Sürpriz Avcısı" : `🚀 Akıllı ${selectedMode} + Sürpriz Avcısı`;
  const btn2Desc = is13
    ? "13 garantisi + yapay zekanın bulduğu en kârlı sürpriz kolonlar."
    : `${selectedMode} garantisi + yapay zekanın bulduğu en kârlı sürpriz kolonlar.`;

  return (
    <div className="bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-2.5 space-y-2.5 select-none text-xs">
      {/* 1. Quick Filter Bar: High-contrast pill buttons */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748b]">
            ⚡ Hızlı Kurgu Filtreleri
          </span>
          <div className="flex items-center gap-1.5 text-[9.5px] font-mono text-[#94a3b8]">
            <span className="text-emerald-400 font-bold">{singles} Tek</span>
            <span>•</span>
            <span className="text-sky-400 font-bold">{doubles} Çift</span>
            <span>•</span>
            <span className="text-amber-400 font-bold">{triples} Kapalı</span>
            <span>•</span>
            <span className="text-[#f8fafc] font-bold">Havuz: {rawPoolSize.toLocaleString()}</span>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-1">
          <button
            onClick={() => applyQuickFilter('cifte')}
            className="px-1.5 py-1 bg-[#0f172a] hover:bg-[#1e293b] text-[#f8fafc] border border-[#1e293b] hover:border-[#38bdf8]/50 text-[10.5px] font-bold rounded shadow-sm transition active:scale-95 text-center"
          >
            Tümü Çifte
          </button>
          <button
            onClick={() => applyQuickFilter('kapali')}
            className="px-1.5 py-1 bg-[#0f172a] hover:bg-[#1e293b] text-[#f8fafc] border border-[#1e293b] hover:border-[#10b981]/50 text-[10.5px] font-bold rounded shadow-sm transition active:scale-95 text-center"
          >
            Tümü Kapalı
          </button>
          <button
            onClick={() => applyQuickFilter('banko')}
            className="px-1.5 py-1 bg-[#0f172a] hover:bg-[#1e293b] text-[#f8fafc] border border-[#1e293b] hover:border-[#f59e0b]/50 text-[10.5px] font-bold rounded shadow-sm transition active:scale-95 text-center"
          >
            Bankoları Koru
          </button>
          <button
            id="btn-reset-all"
            onClick={() => applyQuickFilter('sifirla')}
            className="px-1.5 py-1 bg-[#0f172a] hover:bg-rose-950/40 text-rose-300 border border-[#1e293b] hover:border-rose-500/60 text-[10.5px] font-bold rounded shadow-sm transition active:scale-95 text-center"
          >
            🔄 Sıfırla
          </button>
        </div>
      </div>

      {/* 2. Reactive 2x2 Guarantee Mode Cards (15G, 14G, 13G, 12G) with Cascading Odds */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748b]">
            🛡️ Garanti Seviyesi Seçimi
          </span>
          <span className="text-[9.5px] font-mono text-[#38bdf8]">
            Normal Kupon: {(rawPoolSize * 10).toLocaleString()} TL
          </span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {modes.map(m => {
            const est = estimates.modes[m.id];
            const isSelected = selectedMode === m.id;
            const odds = getCascadingOdds(m.id, selectedMode, estimates);
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => setSelectedMode(m.id)}
                className={`p-1.5 rounded-lg border transition-all flex items-center justify-between cursor-pointer select-none ${
                  isSelected
                    ? 'bg-[#111c2e] border-2 border-[#38bdf8] shadow-[0_0_12px_rgba(56,189,248,0.25)] text-white'
                    : 'bg-[#0f172a] hover:bg-[#162033] border border-[#1e293b] hover:border-[#334155] text-[#94a3b8]'
                }`}
              >
                {/* Left: Green Badge */}
                <div className="bg-[#059669] text-white font-extrabold text-xs px-2.5 py-1.5 rounded-md flex items-center justify-center min-w-[44px] shadow-sm">
                  {m.label}
                </div>

                {/* Right: Columns count on top, Percentage on bottom */}
                <div className="flex flex-col items-end justify-center pr-1">
                  <span className="text-xs font-extrabold font-mono text-[#f8fafc]">
                    {est.columns.toLocaleString()}
                  </span>
                  <span
                    className={`text-[11px] font-mono font-bold ${
                      odds.isGuaranteed ? 'text-emerald-400' : 'text-[#38bdf8]'
                    }`}
                  >
                    {odds.percentStr}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Stat Cards Refactor: Normal Kupon Bedeli, Sistem Bedeli, Nesine Kupon Sayısı */}
      <div className="grid grid-cols-3 gap-1.5 font-mono">
        <div className="bg-[#0f172a] border border-[#1e293b] rounded p-1.5 flex flex-col justify-between">
          <span className="text-[8.5px] text-[#94a3b8] leading-tight">Normal Kupon Bedeli (15 Garantili)</span>
          <span className="text-[11px] font-bold text-[#f8fafc] mt-0.5">
            {(rawPoolSize * 10).toLocaleString()} TL
          </span>
          <span className="text-[8px] text-[#64748b]">({rawPoolSize.toLocaleString()} Kolon)</span>
        </div>

        <div className="bg-[#0f172a] border border-[#1e293b] rounded p-1.5 flex flex-col justify-between">
          <span className="text-[8.5px] text-[#94a3b8] leading-tight">Sistem Bedeli</span>
          <span className="text-[11px] font-extrabold text-emerald-400 mt-0.5">
            {activeTotalCost.toLocaleString()} TL
          </span>
          <span className="text-[8px] text-[#38bdf8]">({activeTotalCols} Kolon)</span>
        </div>

        <div className="bg-[#0f172a] border border-[#1e293b] rounded p-1.5 flex flex-col justify-between">
          <span className="text-[8.5px] text-[#94a3b8] leading-tight">Nesine Kupon Sayısı</span>
          <span className="text-[11px] font-extrabold text-[#38bdf8] mt-0.5">
            {activeSheetsCount} Kupon
          </span>
          <span className="text-[8px] text-[#64748b]">(4'er Kolon)</span>
        </div>
      </div>

      {/* 4. Two Action Buttons (Ekonomik vs Akıllı Sürpriz Avcısı) */}
      <div className="space-y-1.5">
        {/* Button 1: Ekonomik */}
        <button
          onClick={() => handleSolve('base_only')}
          disabled={isSolving}
          className="w-full p-2.5 rounded-lg border text-left transition-all bg-[#0b1b15] hover:bg-[#0f2820] border-[#10b981]/70 hover:border-[#10b981] shadow-md hover:shadow-[0_0_12px_rgba(16,185,129,0.3)] active:scale-[0.99] flex flex-col gap-0.5 group cursor-pointer"
        >
          <div className="flex items-center justify-between w-full">
            <span className="font-extrabold text-[12px] text-[#34d399] group-hover:text-white transition">
              {btn1Title}
            </span>
            <span className="text-[10px] font-mono font-bold text-[#34d399] bg-[#062419] px-2 py-0.5 rounded border border-[#10b981]/40">
              {baselineCols} Kolon / {baselineCost.toLocaleString()} TL
            </span>
          </div>
          <p className="text-[9.5px] text-[#94a3b8] leading-tight">
            {btn1Desc}
          </p>
        </button>

        {/* Button 2: Akıllı + Sürpriz Avcısı */}
        <button
          onClick={() => handleSolve('auto_boost')}
          disabled={isSolving}
          className="w-full p-2.5 rounded-lg border text-left transition-all bg-[#0d1829] hover:bg-[#13233c] border-[#38bdf8]/70 hover:border-[#38bdf8] shadow-md hover:shadow-[0_0_12px_rgba(56,189,248,0.3)] active:scale-[0.99] flex flex-col gap-0.5 group cursor-pointer"
        >
          <div className="flex items-center justify-between w-full">
            <span className="font-extrabold text-[12px] text-[#38bdf8] group-hover:text-white transition">
              {btn2Title}
            </span>
            <span className="text-[9.5px] font-mono font-bold text-amber-300 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-500/40">
              ⚡ Yapay Zeka Otonom
            </span>
          </div>
          <p className="text-[9.5px] text-[#94a3b8] leading-tight">
            {btn2Desc}
          </p>
        </button>
      </div>

      {/* Toast feedback */}
      {toastMessage && (
        <div
          id="toast-notification"
          className="flex items-center justify-between bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 px-3 py-1.5 rounded text-[10.5px] font-semibold shadow"
        >
          <div className="flex items-center gap-1.5">
            <span>✅</span>
            <span>{toastMessage}</span>
          </div>
          <button onClick={clearToast} className="text-emerald-400 hover:text-white font-bold ml-2 cursor-pointer">
            ✕
          </button>
        </div>
      )}
    </div>
  );
};
