import React from 'react';
import { useToto } from '../context/TotoContext';

export const BulletinStation: React.FC = () => {
  const { matches, programInfo, isLoadingBulletin, fetchLiveBulletin, setSelectedTab, setToastMessage } = useToto() as any;

  const pNo = programInfo?.pNo || '357';
  const week = programInfo?.week || '141236';
  const startDate = (programInfo?.startDate || '11.09.2026 19:55').replace('T', ' ').slice(0, 16);
  const endDate = (programInfo?.endDate || '14.09.2026 21:45').replace('T', ' ').slice(0, 16);

  return (
    <div className="flex-1 flex flex-col gap-2.5 overflow-y-auto pr-0.5 select-none text-xs">
      {/* 1. Status Bar Banner */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-2.5 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]"></span>
          <span className="font-extrabold text-[#38bdf8] text-xs">Nesine.com Canlı API Köprüsü</span>
          <span className="text-[#64748b]">|</span>
          <span className="text-[#cbd5e1] font-mono">Program No: <strong className="text-white">{pNo}</strong></span>
          <span className="text-[#64748b]">|</span>
          <span className="text-[#cbd5e1] font-mono">Hafta: <strong className="text-white">{week}</strong></span>
        </div>
        <div className="text-[11px] font-mono text-[#94a3b8]">
          📅 Başlangıç: {startDate} — Bitiş: {endDate}
        </div>
      </div>

      {/* 2. Action Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <button
          onClick={() => fetchLiveBulletin()}
          disabled={isLoadingBulletin}
          className="py-2.5 px-3 bg-[#059669] hover:bg-[#047857] text-white font-extrabold rounded-lg shadow-md flex items-center justify-center gap-2 transition active:scale-98 cursor-pointer disabled:opacity-50"
        >
          <span className={isLoadingBulletin ? "animate-spin inline-block" : ""}>🌐</span>
          <span>{isLoadingBulletin ? "Nesine'den Çekiliyor..." : "Nesine'den Canlı Bülteni & Oranları Çek"}</span>
        </button>

        <button
          onClick={() => {
            fetchLiveBulletin();
            setToastMessage("💾 Son geçerli disk yedeği yüklendi.");
          }}
          className="py-2.5 px-3 bg-[#0f172a] hover:bg-[#1e293b] text-[#cbd5e1] border border-[#1e293b] hover:border-[#38bdf8]/60 font-bold rounded-lg transition active:scale-98 cursor-pointer flex items-center justify-center gap-1.5"
        >
          <span>💾</span>
          <span>Disk Yedeğini Yükle (Snapshot)</span>
        </button>

        <button
          onClick={() => setSelectedTab && setSelectedTab('creator')}
          className="py-2.5 px-3 bg-[#0d1829] hover:bg-[#13233c] text-[#38bdf8] border border-[#38bdf8]/40 hover:border-[#38bdf8] font-bold rounded-lg transition active:scale-98 cursor-pointer flex items-center justify-center gap-1.5"
        >
          <span>🎯</span>
          <span>Kupon Oluşturucuya Geç ➔</span>
        </button>
      </div>

      {/* 3. 15 Match Detail Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2 flex-1">
        {matches.map((m: any, idx: number) => {
          const odds = m.odds || [33.3, 33.3, 33.4];
          const p1 = odds[0] ?? 33.3;
          const p0 = odds[1] ?? 33.3;
          const p2 = odds[2] ?? 33.4;
          const maxOdd = Math.max(p1, p0, p2);

          return (
            <div
              key={m.id || idx}
              className="bg-[#0a0f1d] border border-[#1e293b] hover:border-[#334155] rounded-lg p-2.5 flex flex-col justify-between gap-2 transition-all shadow-sm"
            >
              {/* Match Header */}
              <div className="flex items-center justify-between pb-1 border-b border-[#1e293b]/60">
                <div className="flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded bg-[#06080e] border border-[#1e293b] font-mono font-bold text-xs text-[#38bdf8] flex items-center justify-center">
                    {(idx + 1).toString().padStart(2, '0')}
                  </span>
                  <span className="font-bold text-[#f8fafc] text-xs truncate max-w-[190px]">
                    {m.home} – {m.away}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-[#64748b]">
                  {m.date || '11.09 20:00'}
                </span>
              </div>

              {/* Percentage Bars & Values */}
              <div className="space-y-1 text-[11px] font-mono">
                {/* 1 */}
                <div className="flex items-center gap-2">
                  <span className="w-4 font-extrabold text-sky-400">1</span>
                  <div className="flex-1 h-2.5 bg-[#06080e] rounded-full overflow-hidden border border-[#1e293b]">
                    <div
                      className={`h-full rounded-full transition-all ${p1 >= 60 ? 'bg-amber-400' : 'bg-sky-500'}`}
                      style={{ width: `${p1}%` }}
                    />
                  </div>
                  <span className={`w-10 text-right font-bold ${p1 === maxOdd ? 'text-white font-extrabold' : 'text-[#94a3b8]'}`}>
                    %{p1.toFixed(1)}
                  </span>
                </div>

                {/* X */}
                <div className="flex items-center gap-2">
                  <span className="w-4 font-extrabold text-amber-400">X</span>
                  <div className="flex-1 h-2.5 bg-[#06080e] rounded-full overflow-hidden border border-[#1e293b]">
                    <div
                      className={`h-full rounded-full transition-all ${p0 >= 60 ? 'bg-amber-400' : 'bg-amber-500'}`}
                      style={{ width: `${p0}%` }}
                    />
                  </div>
                  <span className={`w-10 text-right font-bold ${p0 === maxOdd ? 'text-white font-extrabold' : 'text-[#94a3b8]'}`}>
                    %{p0.toFixed(1)}
                  </span>
                </div>

                {/* 2 */}
                <div className="flex items-center gap-2">
                  <span className="w-4 font-extrabold text-emerald-400">2</span>
                  <div className="flex-1 h-2.5 bg-[#06080e] rounded-full overflow-hidden border border-[#1e293b]">
                    <div
                      className={`h-full rounded-full transition-all ${p2 >= 60 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                      style={{ width: `${p2}%` }}
                    />
                  </div>
                  <span className={`w-10 text-right font-bold ${p2 === maxOdd ? 'text-white font-extrabold' : 'text-[#94a3b8]'}`}>
                    %{p2.toFixed(1)}
                  </span>
                </div>
              </div>

              {/* Footer status */}
              <div className="flex items-center justify-between text-[9.5px] text-[#64748b] pt-1 border-t border-[#1e293b]/40">
                <span>Tercih: {m.picks.join(', ')}</span>
                {maxOdd >= 60 && (
                  <span className="text-amber-400 font-bold bg-amber-950/60 px-1.5 py-0.2 rounded border border-amber-600/40">
                    ⭐ Net Favori (%{maxOdd.toFixed(0)})
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
