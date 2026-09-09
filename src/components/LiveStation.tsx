import React, { useState, useEffect, useCallback } from 'react';
import { useToto } from '../context/TotoContext';
import { LiveMatchDetail } from '../types';

export const LiveStation: React.FC = () => {
  const { solution, matches, setToastMessage } = useToto() as any;
  const [liveMatches, setLiveMatches] = useState<LiveMatchDetail[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>('-');

  const fetchLiveScores = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/live');
      if (res.ok) {
        const data = await res.json();
        if (data.matches && data.matches.length === 15) {
          setLiveMatches(data.matches);
          setLastUpdated(new Date().toLocaleTimeString('tr-TR'));
          setToastMessage('🔴 Nesine canlı maç skorları güncellendi!');
        }
      }
    } catch (err) {
      console.warn('Canlı skor çekme hatası:', err);
      setToastMessage('Canlı skorlar çekilemedi.');
    } finally {
      setIsLoading(false);
    }
  }, [setToastMessage]);

  useEffect(() => {
    fetchLiveScores();
    const interval = setInterval(fetchLiveScores, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, [fetchLiveScores]);

  const columns: string[][] = solution?.columns || [];
  const finishedOutcomes = liveMatches.map(m => m.current_outcome);
  const finishedIndices = finishedOutcomes
    .map((o, idx) => (o && ['1', 'X', '2'].includes(o) ? idx : -1))
    .filter(idx => idx !== -1);

  // Column performance evaluation
  let c15 = 0, c14 = 0, c13 = 0, c12 = 0;
  if (columns.length > 0 && finishedIndices.length > 0) {
    for (const col of columns) {
      let errors = 0;
      for (const idx of finishedIndices) {
        if (col[idx] !== finishedOutcomes[idx]) {
          errors++;
        }
      }
      if (errors === 0) c15++;
      if (errors <= 1) c14++;
      if (errors <= 2) c13++;
      if (errors <= 3) c12++;
    }
  }

  // Top 4 columns
  const scoredColumns = columns.map((col, cIdx) => {
    let hits = 0;
    let errors = 0;
    for (const idx of finishedIndices) {
      if (col[idx] === finishedOutcomes[idx]) hits++;
      else errors++;
    }
    return {
      cIdx,
      col,
      hits,
      errors,
      potential: 15 - errors
    };
  });
  scoredColumns.sort((a, b) => a.errors - b.errors || b.hits - a.hits);
  const top4 = scoredColumns.slice(0, 4);

  // Climate calculation
  const finishedCount = finishedIndices.length;
  let climateBadge = "⚖️ DENGELİ HAVUZ";
  let climateColor = "text-[#38bdf8]";
  let est15 = "500.000 TL - 1.800.000 TL";
  let est14 = "10.000 TL - 35.000 TL";
  let est13 = "1.000 TL - 4.000 TL";
  let est12 = "150 TL - 500 TL";

  // Check surprise level from finished matches
  let surpriseScore = 0;
  for (const idx of finishedIndices) {
    const outcome = finishedOutcomes[idx];
    const matchOdds = matches[idx]?.odds || [33.3, 33.3, 33.4];
    const oddVal = outcome === '1' ? matchOdds[0] : outcome === 'X' ? matchOdds[1] : matchOdds[2];
    if (oddVal < 25) surpriseScore += 2;
    else if (oddVal < 35) surpriseScore += 1;
  }

  if (surpriseScore >= 4) {
    climateBadge = "🔥 ÇOK YÜKSEK İKRAMİYE (Devir Riski)";
    climateColor = "text-rose-400";
    est15 = "Devir / 5.000.000+ TL";
    est14 = "80.000 TL - 450.000 TL";
    est13 = "8.000 TL - 35.000 TL";
    est12 = "800 TL - 3.000 TL";
  } else if (surpriseScore >= 2) {
    climateBadge = "⚡ YÜKSEK İKRAMİYE POTANSİYELİ";
    climateColor = "text-amber-400";
    est15 = "1.200.000 TL - 3.500.000 TL";
    est14 = "20.000 TL - 75.000 TL";
    est13 = "2.000 TL - 8.500 TL";
    est12 = "300 TL - 1.200 TL";
  }

  return (
    <div className="flex-1 flex flex-col gap-2.5 overflow-y-auto pr-0.5 select-none text-xs">
      {/* 1. Live Action Header */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-2.5 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse shadow-[0_0_8px_#ef4444]"></span>
          <span className="font-extrabold text-[#38bdf8] text-xs">Nesine Canlı Skor Telemetrisi</span>
          <span className="text-[#64748b]">|</span>
          <span className="text-[#cbd5e1] font-mono">Biten/Canlı: <strong className="text-white">{finishedCount} / 15</strong></span>
          <span className="text-[#64748b]">|</span>
          <span className="text-[#94a3b8] text-[10px]">Son Güncelleme: {lastUpdated}</span>
        </div>

        <button
          onClick={fetchLiveScores}
          disabled={isLoading}
          className="py-1.5 px-3 bg-rose-600 hover:bg-rose-500 text-white font-extrabold rounded-lg shadow-md flex items-center gap-1.5 transition active:scale-95 cursor-pointer disabled:opacity-50"
        >
          <span className={isLoading ? "animate-spin inline-block" : ""}>🔴</span>
          <span>{isLoading ? "Çekiliyor..." : "Canlı Skorları Yenile"}</span>
        </button>
      </div>

      {/* 2. Telemetry Gauges: Kolon Başarı & İkramiye İklimi */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5">
        {/* Kolon Başarı Durumu (7 cols) */}
        <div className="lg:col-span-7 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 flex flex-col justify-between gap-2">
          <div className="flex items-center justify-between border-b border-[#1e293b] pb-1.5">
            <span className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider">
              📊 Kupon Başarı Durumu ({columns.length} Kolon)
            </span>
            <span className="text-[10px] font-mono text-[#94a3b8]">
              {columns.length > 0 ? "Gerçek Zamanlı İkramiye Radarı" : "Henüz Kupon Üretilmedi"}
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2 text-center font-mono">
            <div className="bg-[#06080e] border border-amber-500/30 rounded p-2">
              <span className="text-[10px] text-amber-300 font-bold block">👑 15'te 15</span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c15}</span>
              <span className="text-[9px] text-[#64748b]">Kolon Canlı</span>
            </div>
            <div className="bg-[#06080e] border border-sky-500/30 rounded p-2">
              <span className="text-[10px] text-sky-300 font-bold block">🎯 14 İhtimal</span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c14}</span>
              <span className="text-[9px] text-[#64748b]">Kolon Canlı</span>
            </div>
            <div className="bg-[#06080e] border border-emerald-500/30 rounded p-2">
              <span className="text-[10px] text-emerald-300 font-bold block">🛡️ 13 İhtimal</span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c13}</span>
              <span className="text-[9px] text-[#64748b]">Kolon Canlı</span>
            </div>
            <div className="bg-[#06080e] border border-slate-700 rounded p-2">
              <span className="text-[10px] text-slate-300 font-bold block">📊 12 İhtimal</span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c12}</span>
              <span className="text-[9px] text-[#64748b]">Kolon Canlı</span>
            </div>
          </div>
        </div>

        {/* İkramiye İklimi (5 cols) */}
        <div className="lg:col-span-5 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 flex flex-col justify-between gap-1.5">
          <div className="flex items-center justify-between border-b border-[#1e293b] pb-1.5">
            <span className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider">
              🌡️ İkramiye İklimi
            </span>
            <span className={`text-[10.5px] font-extrabold ${climateColor}`}>
              {climateBadge}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-1.5 text-[10.5px] font-mono">
            <div className="bg-[#06080e] p-1.5 rounded border border-[#1e293b] flex justify-between">
              <span className="text-[#94a3b8]">15 Bilen:</span>
              <span className="font-bold text-emerald-400">{est15}</span>
            </div>
            <div className="bg-[#06080e] p-1.5 rounded border border-[#1e293b] flex justify-between">
              <span className="text-[#94a3b8]">14 Bilen:</span>
              <span className="font-bold text-sky-400">{est14}</span>
            </div>
            <div className="bg-[#06080e] p-1.5 rounded border border-[#1e293b] flex justify-between">
              <span className="text-[#94a3b8]">13 Bilen:</span>
              <span className="font-bold text-amber-300">{est13}</span>
            </div>
            <div className="bg-[#06080e] p-1.5 rounded border border-[#1e293b] flex justify-between">
              <span className="text-[#94a3b8]">12 Bilen:</span>
              <span className="font-bold text-slate-300">{est12}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Live 15 Match Table */}
      <div className="bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3">
        <h3 className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <span>⚽</span> 15 Maç Canlı Skor Tablosu
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="bg-[#0f172a] text-[#64748b] text-[10px] uppercase border-b border-[#1e293b]">
                <th className="py-1.5 px-2">#</th>
                <th className="py-1.5 px-2">Ev Sahibi</th>
                <th className="py-1.5 px-2">Skor</th>
                <th className="py-1.5 px-2">Deplasman</th>
                <th className="py-1.5 px-2">Durum / DK</th>
                <th className="py-1.5 px-2 text-center">Canlı Sonuç</th>
              </tr>
            </thead>
            <tbody>
              {(liveMatches.length === 15 ? liveMatches : matches).map((m: any, idx: number) => {
                const live = liveMatches[idx];
                const score = live?.score || '- - -';
                const minute = live?.minute || '-';
                const outcome = live?.current_outcome || '-';
                const isFT = live?.status === 'FT';
                const isLive = live?.status === 'LIVE';

                const outcomePill = () => {
                  if (outcome === '1') return <span className="px-2 py-0.5 rounded bg-sky-950 text-sky-400 font-extrabold border border-sky-600">1</span>;
                  if (outcome === 'X') return <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-400 font-extrabold border border-amber-600">X</span>;
                  if (outcome === '2') return <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-extrabold border border-emerald-600">2</span>;
                  return <span className="text-[#64748b]">-</span>;
                };

                return (
                  <tr key={idx} className="border-b border-[#1e293b]/40 hover:bg-[#0f172a]/50">
                    <td className="py-1.5 px-2 font-bold text-[#38bdf8]">{(idx + 1).toString().padStart(2, '0')}</td>
                    <td className="py-1.5 px-2 font-semibold text-white truncate max-w-[150px]">{m.home}</td>
                    <td className="py-1.5 px-2 font-extrabold text-amber-400">{score}</td>
                    <td className="py-1.5 px-2 font-semibold text-white truncate max-w-[150px]">{m.away}</td>
                    <td className="py-1.5 px-2">
                      <span className={`px-1.5 py-0.5 rounded text-[9.5px] font-bold ${isFT ? 'bg-emerald-950 text-emerald-300 border border-emerald-600/40' : isLive ? 'bg-rose-950 text-rose-300 animate-pulse border border-rose-600/40' : 'bg-slate-900 text-slate-400'}`}>
                        {minute}
                      </span>
                    </td>
                    <td className="py-1.5 px-2 text-center">{outcomePill()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
