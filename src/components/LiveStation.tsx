import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useToto } from '../context/TotoContext';
import { LiveMatchDetail, SavedCoupon } from '../types';
import { getSavedCoupons, deleteSavedCoupon, SAVED_COUPONS_EVENT } from '../lib/storage';
import { SaveCouponModal } from './SaveCouponModal';

function formatTL(val: number): string {
  return val.toLocaleString('tr-TR');
}

export const LiveStation: React.FC = () => {
  const { solution, matches, setToastMessage, programInfo } = useToto() as any;
  const [liveMatches, setLiveMatches] = useState<LiveMatchDetail[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>('-');

  // Saved Coupons State
  const [savedCoupons, setSavedCoupons] = useState<SavedCoupon[]>([]);
  const [selectedCouponId, setSelectedCouponId] = useState<string | null>(null);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState<boolean>(false);

  // What-If Manual Overrides: matchIndex -> '1' | 'X' | '2'
  const [manualOverrides, setManualOverrides] = useState<Record<number, '1' | 'X' | '2'>>({});

  // Load saved coupons from localStorage on mount & listen for changes
  const refreshSavedCoupons = useCallback(() => {
    const list = getSavedCoupons();
    setSavedCoupons(list);
    setSelectedCouponId(prev => {
      if (prev && list.some(c => c.id === prev)) return prev;
      return list.length > 0 ? list[0].id : null;
    });
  }, []);

  useEffect(() => {
    refreshSavedCoupons();
    if (typeof window !== 'undefined') {
      window.addEventListener(SAVED_COUPONS_EVENT, refreshSavedCoupons);
      return () => window.removeEventListener(SAVED_COUPONS_EVENT, refreshSavedCoupons);
    }
  }, [refreshSavedCoupons]);

  // Fetch Live Scores from API
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

  // Determine which coupon is currently being tracked
  const selectedCoupon = useMemo(() => {
    return savedCoupons.find(c => c.id === selectedCouponId) || null;
  }, [savedCoupons, selectedCouponId]);

  // Active columns for evaluation: selected saved coupon > active solution in context > empty
  const activeColumns: string[][] = useMemo(() => {
    if (selectedCoupon && selectedCoupon.columns && selectedCoupon.columns.length > 0) {
      return selectedCoupon.columns;
    }
    if (solution && solution.columns && solution.columns.length > 0) {
      return solution.columns;
    }
    return [];
  }, [selectedCoupon, solution]);

  const activeCouponTitle = selectedCoupon
    ? selectedCoupon.name
    : solution && solution.total_columns > 0
    ? `Aktif Üretici Kuponu (${solution.total_columns} Kolon)`
    : null;

  // Handle Delete Selected Coupon
  const handleDeleteSelected = () => {
    if (!selectedCoupon) return;
    if (confirm(`"${selectedCoupon.name}" başlıklı kayıtlı kuponu silmek istediğinize emin misiniz?`)) {
      const updated = deleteSavedCoupon(selectedCoupon.id);
      setSavedCoupons(updated);
      setSelectedCouponId(updated.length > 0 ? updated[0].id : null);
      setToastMessage('🗑️ Kupon başarıyla silindi.');
    }
  };

  // Toggle Manual Outcome Override (What-If simulation)
  const handleToggleOverride = (matchIdx: number, choice: '1' | 'X' | '2') => {
    setManualOverrides(prev => {
      const current = prev[matchIdx];
      const next = { ...prev };
      if (current === choice) {
        // Toggle off: revert to official score
        delete next[matchIdx];
      } else {
        next[matchIdx] = choice;
      }
      return next;
    });
  };

  // Reset all manual overrides back to official scores
  const handleResetOverrides = () => {
    setManualOverrides({});
    setToastMessage('🔄 Tüm maçlar resmi canlı skorlara sıfırlandı.');
  };

  const overrideCount = Object.keys(manualOverrides).length;
  const hasOverrides = overrideCount > 0;

  // Compute effective outcomes for all 15 matches
  // Durum Mantığı:
  // - Bekliyor / Başlamadı ('NS' or '-'): Henüz oynanmayan maçlar kolonları elemez (potansiyel korunur).
  // - Oynanıyor (Canlı): Anlık skora göre (1, X, 2) hesaplanır.
  // - MS (Bitti): Sonuç kilitlenir.
  // - Manual Override (What-If): Kullanıcı seçimi anında devreye girer.
  const matchOutcomes = useMemo(() => {
    return Array.from({ length: 15 }, (_, idx) => {
      if (manualOverrides[idx] !== undefined) {
        return {
          outcome: manualOverrides[idx],
          isOverridden: true,
          isDetermined: true
        };
      }
      const live = liveMatches[idx];
      const official = live?.current_outcome || '-';
      const isDetermined = official === '1' || official === 'X' || official === '2';
      return {
        outcome: isDetermined ? official : ('-' as const),
        isOverridden: false,
        isDetermined
      };
    });
  }, [liveMatches, manualOverrides]);

  // Indices of matches that have an outcome (live/FT or manual override)
  const determinedIndices = useMemo(() => {
    return matchOutcomes
      .map((m, idx) => (m.isDetermined ? idx : -1))
      .filter(idx => idx !== -1);
  }, [matchOutcomes]);

  const determinedCount = determinedIndices.length;
  const pendingCount = 15 - determinedCount;

  // Column Performance Evaluation (15, 14, 13, 12)
  const { c15, c14, c13, c12, scoredColumns } = useMemo(() => {
    let count15 = 0;
    let count14 = 0;
    let count13 = 0;
    let count12 = 0;

    const scored = activeColumns.map((col, cIdx) => {
      let errors = 0;
      let hits = 0;
      for (const idx of determinedIndices) {
        const expected = matchOutcomes[idx].outcome;
        if (col[idx] === expected) {
          hits++;
        } else {
          errors++;
        }
      }

      // Disjoint classification for accurate prize calculation & status
      if (errors === 0) count15++;
      else if (errors === 1) count14++;
      else if (errors === 2) count13++;
      else if (errors === 3) count12++;

      return {
        cIdx,
        col,
        hits,
        errors,
        maxPotential: 15 - errors
      };
    });

    scored.sort((a, b) => a.errors - b.errors || b.hits - a.hits);

    return {
      c15: count15,
      c14: count14,
      c13: count13,
      c12: count12,
      scoredColumns: scored
    };
  }, [activeColumns, determinedIndices, matchOutcomes]);

  const top4 = scoredColumns.slice(0, 4);

  // Surprise score and prize pool ranges
  const { climateBadge, climateColor, p15, p14, p13, p12, est15Str, est14Str, est13Str, est12Str } = useMemo(() => {
    let surpriseScore = 0;
    for (const idx of determinedIndices) {
      const outcome = matchOutcomes[idx].outcome;
      const matchOdds = matches[idx]?.odds || [33.3, 33.3, 33.4];
      const oddVal = outcome === '1' ? matchOdds[0] : outcome === 'X' ? matchOdds[1] : matchOdds[2];
      if (oddVal < 25) surpriseScore += 2;
      else if (oddVal < 35) surpriseScore += 1;
    }

    if (surpriseScore >= 4) {
      return {
        climateBadge: '🔥 ÇOK YÜKSEK İKRAMİYE (Devir Riski)',
        climateColor: 'text-rose-400',
        p15: [5000000, 15000000],
        p14: [80000, 450000],
        p13: [8000, 35000],
        p12: [800, 3000],
        est15Str: 'Devir / 5.000.000+ TL',
        est14Str: '80.000 TL - 450.000 TL',
        est13Str: '8.000 TL - 35.000 TL',
        est12Str: '800 TL - 3.000 TL'
      };
    } else if (surpriseScore >= 2) {
      return {
        climateBadge: '⚡ YÜKSEK İKRAMİYE POTANSİYELİ',
        climateColor: 'text-amber-400',
        p15: [1200000, 3500000],
        p14: [20000, 75000],
        p13: [2000, 8500],
        p12: [300, 1200],
        est15Str: '1.200.000 TL - 3.500.000 TL',
        est14Str: '20.000 TL - 75.000 TL',
        est13Str: '2.000 TL - 8.500 TL',
        est12Str: '300 TL - 1.200 TL'
      };
    } else {
      return {
        climateBadge: '⚖️ DENGELİ HAVUZ',
        climateColor: 'text-[#38bdf8]',
        p15: [500000, 1800000],
        p14: [10000, 35000],
        p13: [1000, 4000],
        p12: [150, 500],
        est15Str: '500.000 TL - 1.800.000 TL',
        est14Str: '10.000 TL - 35.000 TL',
        est13Str: '1.000 TL - 4.000 TL',
        est12Str: '150 TL - 500 TL'
      };
    }
  }, [determinedIndices, matchOutcomes, matches]);

  // Dynamic Prize Payout Simulation (min - max)
  const minGain = c15 * p15[0] + c14 * p14[0] + c13 * p13[0] + c12 * p12[0];
  const maxGain = c15 * p15[1] + c14 * p14[1] + c13 * p14[1] + c12 * p12[1];

  return (
    <div className="flex-1 flex flex-col gap-2.5 overflow-y-auto pr-0.5 select-none text-xs">
      {/* 1. Live Action Header & Coupon Selector */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-2.5 flex flex-col gap-2.5 shadow-md">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse shadow-[0_0_8px_#ef4444]"></span>
            <span className="font-extrabold text-[#38bdf8] text-xs">Nesine Canlı Skor Telemetrisi</span>
            <span className="text-[#64748b]">|</span>
            <span className="text-[#cbd5e1] font-mono">
              Biten/Canlı: <strong className="text-white">{determinedCount} / 15</strong>
            </span>
            <span className="text-[#64748b]">|</span>
            <span className="text-[#94a3b8] text-[10px]">Son Güncelleme: {lastUpdated}</span>
          </div>

          <div className="flex items-center gap-2">
            {hasOverrides && (
              <button
                onClick={handleResetOverrides}
                className="py-1 px-2.5 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 text-slate-950 font-black rounded-lg shadow-md shadow-amber-500/30 flex items-center gap-1.5 transition active:scale-95 cursor-pointer text-[11px] animate-pulse"
              >
                <span>🔄</span>
                <span>Canlı Skorlara Sıfırla ({overrideCount} Simüle)</span>
              </button>
            )}

            <button
              onClick={fetchLiveScores}
              disabled={isLoading}
              className="py-1 px-2.5 bg-rose-600 hover:bg-rose-500 text-white font-extrabold rounded-lg shadow-md flex items-center gap-1.5 transition active:scale-95 cursor-pointer disabled:opacity-50 text-[11px]"
            >
              <span className={isLoading ? "animate-spin inline-block" : ""}>🔴</span>
              <span>{isLoading ? "Çekiliyor..." : "Canlı Skorları Yenile"}</span>
            </button>
          </div>
        </div>

        {/* 🎯 Takip Edilen Kupon Dropdown Bar */}
        <div className="bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-2 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-[280px]">
            <span className="text-[11px] font-bold text-[#38bdf8] flex items-center gap-1.5 whitespace-nowrap">
              <span>🎯</span> Takip Edilen Kupon:
            </span>

            <div className="flex-1 flex items-center gap-1.5">
              <select
                value={selectedCouponId || (selectedCoupon ? selectedCoupon.id : '')}
                onChange={(e) => setSelectedCouponId(e.target.value)}
                className="bg-[#06080e] border border-[#334155] focus:border-[#38bdf8] text-white text-xs rounded-lg px-2.5 py-1.5 font-medium outline-none flex-1 max-w-lg truncate transition cursor-pointer"
              >
                {savedCoupons.map((c) => {
                  const dateStr = new Date(c.createdAt).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' });
                  const timeStr = new Date(c.createdAt).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
                  return (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.columnsCount} Kolon) — {dateStr} {timeStr}
                    </option>
                  );
                })}

                {savedCoupons.length === 0 && solution && solution.total_columns > 0 && (
                  <option value="active_session">
                    Aktif Üretici Kuponu ({solution.total_columns} Kolon) - Kaydedilmedi
                  </option>
                )}

                {savedCoupons.length === 0 && (!solution || solution.total_columns === 0) && (
                  <option value="" disabled>
                    Kayıtlı Kupon Bulunamadı - Lütfen Kupon Kaydedin
                  </option>
                )}
              </select>

              {selectedCoupon && (
                <button
                  onClick={handleDeleteSelected}
                  title="Seçili Kuponu Sil"
                  className="p-1.5 bg-rose-950/70 hover:bg-rose-900 border border-rose-700/60 hover:border-rose-500 text-rose-300 hover:text-white rounded-lg transition active:scale-95 cursor-pointer flex items-center justify-center text-xs"
                >
                  <span className="text-sm">🗑️</span>
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {solution && solution.total_columns > 0 && (
              <button
                onClick={() => setIsSaveModalOpen(true)}
                className="py-1 px-2.5 bg-emerald-600/90 hover:bg-emerald-500 text-white rounded-lg font-bold text-[11px] flex items-center gap-1 transition active:scale-95 cursor-pointer whitespace-nowrap shadow-sm"
              >
                <span>💾</span>
                <span>Mevcut Kuponu Kaydet</span>
              </button>
            )}

            {activeCouponTitle && (
              <span className="text-[10px] font-mono bg-[#06080e] text-emerald-400 px-2 py-1 rounded border border-[#1e293b] truncate max-w-[200px]">
                {activeColumns.length} Kolon Aktif
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 2. Dinamik İkramiye Kazanç Bannerı ("What-If Engine Banner") */}
      <div className="bg-gradient-to-r from-emerald-950/90 via-[#0d2218] to-cyan-950/90 border border-emerald-500/50 rounded-lg p-3 shadow-lg shadow-emerald-950/40 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl animate-bounce">🎯</span>
          <div>
            <span className="text-[10.5px] font-extrabold uppercase tracking-wider text-emerald-300 flex items-center gap-1.5">
              <span>{hasOverrides ? 'What-If Senaryo Simülatörü' : 'Anlık Canlı Skor Değerlendirmesi'}</span>
              {hasOverrides && (
                <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 px-1.5 py-0.2 rounded text-[9px]">
                  {overrideCount} Maç Simüle Edildi
                </span>
              )}
            </span>
            <div className="text-sm sm:text-base font-extrabold text-white font-mono mt-0.5">
              Bu Senaryoda Tahmini Kazancınız:{' '}
              {minGain > 0 || maxGain > 0 ? (
                <>
                  <span className="text-amber-300 font-black">{formatTL(minGain)} TL</span>
                  <span className="text-[#94a3b8] font-normal mx-1">–</span>
                  <span className="text-emerald-400 font-black">{formatTL(maxGain)} TL</span>
                </>
              ) : (
                <span className="text-slate-400 font-bold">0 TL (Henüz 12-15 eşleşme yok)</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono text-[#cbd5e1]">
          <div className="bg-[#06080e]/80 px-2.5 py-1.5 rounded border border-emerald-500/30 flex items-center gap-1.5">
            <span className="text-[#64748b]">Canlı Kolon:</span>
            <strong className="text-emerald-300">{c15 + c14 + c13 + c12}</strong>
            <span className="text-[#64748b]">/ {activeColumns.length}</span>
          </div>
          <div className="bg-[#06080e]/80 px-2.5 py-1.5 rounded border border-[#1e293b] flex items-center gap-1.5">
            <span className="text-[#64748b]">Kalan:</span>
            <strong className="text-amber-300">{pendingCount} Maç</strong>
          </div>
        </div>
      </div>

      {/* 3. Telemetry Gauges: Kolon Başarı & İkramiye İklimi */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5">
        {/* Kolon Başarı Durumu (7 cols) */}
        <div className="lg:col-span-7 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 flex flex-col justify-between gap-2">
          <div className="flex items-center justify-between border-b border-[#1e293b] pb-1.5">
            <span className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider flex items-center gap-1.5">
              <span>📊</span> Kupon Başarı Durumu ({activeColumns.length} Kolon)
            </span>
            <span className="text-[10px] font-mono text-[#94a3b8]">
              {activeColumns.length > 0 ? (pendingCount === 0 ? "Tüm Maçlar Kesinleşti" : "Gerçek Zamanlı İkramiye Radarı") : "Henüz Kupon Seçilmedi"}
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2 text-center font-mono">
            {/* 15 */}
            <div className={`bg-[#06080e] border rounded p-2 transition ${c15 > 0 ? 'border-amber-500/60 shadow-sm shadow-amber-950/40' : 'border-[#1e293b] opacity-70'}`}>
              <span className="text-[10px] text-amber-300 font-bold block">
                {pendingCount === 0 ? "👑 15 Bilen" : "👑 15'te 15"}
              </span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c15}</span>
              <span className="text-[9px] text-[#64748b]">
                {pendingCount === 0 ? "Kesinleşti" : "Kolon Canlı"}
              </span>
            </div>

            {/* 14 */}
            <div className={`bg-[#06080e] border rounded p-2 transition ${c14 > 0 ? 'border-sky-500/60 shadow-sm shadow-sky-950/40' : 'border-[#1e293b] opacity-70'}`}>
              <span className="text-[10px] text-sky-300 font-bold block">
                {pendingCount === 0 ? "🎯 14 Bilen" : "🎯 14 İhtimal"}
              </span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c14}</span>
              <span className="text-[9px] text-[#64748b]">
                {pendingCount === 0 ? "Kesinleşti" : "Kolon Canlı"}
              </span>
            </div>

            {/* 13 */}
            <div className={`bg-[#06080e] border rounded p-2 transition ${c13 > 0 ? 'border-emerald-500/60 shadow-sm shadow-emerald-950/40' : 'border-[#1e293b] opacity-70'}`}>
              <span className="text-[10px] text-emerald-300 font-bold block">
                {pendingCount === 0 ? "🛡️ 13 Bilen" : "🛡️ 13 İhtimal"}
              </span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c13}</span>
              <span className="text-[9px] text-[#64748b]">
                {pendingCount === 0 ? "Kesinleşti" : "Kolon Canlı"}
              </span>
            </div>

            {/* 12 */}
            <div className={`bg-[#06080e] border rounded p-2 transition ${c12 > 0 ? 'border-slate-500/60 shadow-sm shadow-slate-950/40' : 'border-[#1e293b] opacity-70'}`}>
              <span className="text-[10px] text-slate-300 font-bold block">
                {pendingCount === 0 ? "📊 12 Bilen" : "📊 12 İhtimal"}
              </span>
              <span className="text-lg font-extrabold text-white mt-1 block">{c12}</span>
              <span className="text-[9px] text-[#64748b]">
                {pendingCount === 0 ? "Kesinleşti" : "Kolon Canlı"}
              </span>
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
              <span className="font-bold text-emerald-400">{est15Str}</span>
            </div>
            <div className="bg-[#06080e] p-1.5 rounded border border-[#1e293b] flex justify-between">
              <span className="text-[#94a3b8]">14 Bilen:</span>
              <span className="font-bold text-sky-400">{est14Str}</span>
            </div>
            <div className="bg-[#06080e] p-1.5 rounded border border-[#1e293b] flex justify-between">
              <span className="text-[#94a3b8]">13 Bilen:</span>
              <span className="font-bold text-amber-300">{est13Str}</span>
            </div>
            <div className="bg-[#06080e] p-1.5 rounded border border-[#1e293b] flex justify-between">
              <span className="text-[#94a3b8]">12 Bilen:</span>
              <span className="font-bold text-slate-300">{est12Str}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Live 15 Match Table with Interactive "What-If" Simulation */}
      <div className="bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 flex flex-col gap-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h3 className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider flex items-center gap-1.5">
            <span>⚽</span> 15 Maç Canlı Skor Tablosu & Senaryo Simülatörü
          </h3>

          <div className="flex items-center gap-2 text-[10px] text-[#94a3b8]">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span> Simüle Seçim
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Resmi Canlı
            </span>
            <span className="text-[#64748b]">|</span>
            <span>Butonlara basarak sonucu manuel simüle edebilirsiniz</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="bg-[#0f172a] text-[#64748b] text-[10px] uppercase border-b border-[#1e293b]">
                <th className="py-1.5 px-2">#</th>
                <th className="py-1.5 px-2">Ev Sahibi</th>
                <th className="py-1.5 px-2 text-center">Skor</th>
                <th className="py-1.5 px-2">Deplasman</th>
                <th className="py-1.5 px-2">Durum / DK</th>
                <th className="py-1.5 px-2 text-center">Simülasyon / Canlı Sonuç</th>
              </tr>
            </thead>
            <tbody>
              {(liveMatches.length === 15 ? liveMatches : matches).map((m: any, idx: number) => {
                const live = liveMatches[idx];
                const score = live?.score || '- - -';
                const minute = live?.minute || '-';
                const isFT = live?.status === 'FT';
                const isLive = live?.status === 'LIVE';

                const outcomeInfo = matchOutcomes[idx];
                const effectiveOutcome = outcomeInfo.outcome;
                const isOverridden = outcomeInfo.isOverridden;
                const officialOutcome = live?.current_outcome || '-';

                return (
                  <tr key={idx} className={`border-b border-[#1e293b]/40 hover:bg-[#0f172a]/50 ${isOverridden ? 'bg-amber-950/10' : ''}`}>
                    <td className="py-1.5 px-2 font-bold text-[#38bdf8]">
                      {(idx + 1).toString().padStart(2, '0')}
                    </td>
                    <td className="py-1.5 px-2 font-semibold text-white truncate max-w-[150px]">
                      {m.home}
                    </td>
                    <td className="py-1.5 px-2 text-center font-extrabold text-amber-400 font-mono">
                      {score}
                    </td>
                    <td className="py-1.5 px-2 font-semibold text-white truncate max-w-[150px]">
                      {m.away}
                    </td>
                    <td className="py-1.5 px-2">
                      <span className={`px-1.5 py-0.5 rounded text-[9.5px] font-bold ${isFT ? 'bg-emerald-950 text-emerald-300 border border-emerald-600/40' : isLive ? 'bg-rose-950 text-rose-300 animate-pulse border border-rose-600/40' : 'bg-slate-900 text-slate-400'}`}>
                        {minute}
                      </span>
                    </td>

                    {/* Interactive "What-If" Outcome Selection Buttons */}
                    <td className="py-1.5 px-2 text-center">
                      <div className="inline-flex items-center justify-center gap-1 bg-[#06080e] p-0.5 rounded border border-[#1e293b]">
                        {(['1', 'X', '2'] as const).map(choice => {
                          const isChosen = effectiveOutcome === choice;
                          const isBtnOverridden = isOverridden && effectiveOutcome === choice;
                          const isOfficial = !isOverridden && officialOutcome === choice;

                          let btnStyle = "bg-transparent text-[#64748b] hover:text-white hover:bg-[#1e293b]";
                          if (isChosen) {
                            if (choice === '1') btnStyle = "bg-sky-600 text-white font-black shadow-sm";
                            else if (choice === 'X') btnStyle = "bg-amber-500 text-slate-950 font-black shadow-sm";
                            else btnStyle = "bg-emerald-600 text-white font-black shadow-sm";
                          }

                          return (
                            <button
                              key={choice}
                              onClick={() => handleToggleOverride(idx, choice)}
                              title={
                                isBtnOverridden
                                  ? `Manuel Simülasyon: ${choice} (İptal etmek için tıklayın)`
                                  : isOfficial
                                  ? `Resmi Canlı Sonuç: ${choice}`
                                  : `Senaryoyu ${choice} olarak ayarla`
                              }
                              className={`w-6 h-5 rounded text-[10.5px] font-mono font-bold transition active:scale-90 cursor-pointer flex items-center justify-center ${btnStyle} ${isBtnOverridden ? 'ring-2 ring-amber-400 shadow-md' : ''}`}
                            >
                              {choice}
                            </button>
                          );
                        })}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Best Performing Columns Inspector (Top 4) */}
      {top4.length > 0 && (
        <div className="bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3">
          <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-[#1e293b]">
            <h4 className="text-[10.5px] font-bold text-[#38bdf8] uppercase tracking-wider flex items-center gap-1.5">
              <span>🌟</span> En Yüksek Potansiyelli Kolonlar (Lider Tablosu)
            </h4>
            <span className="text-[10px] text-[#94a3b8] font-mono">
              Bu senaryoya en çok uyan ilk 4 kolon
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {top4.map((sc, rank) => (
              <div key={sc.cIdx} className="bg-[#06080e] border border-[#1e293b] rounded p-2 flex flex-col gap-1 text-[11px] font-mono">
                <div className="flex items-center justify-between text-[#94a3b8]">
                  <span>#{sc.cIdx + 1}. Kolon</span>
                  <span className={`font-bold ${sc.errors === 0 ? 'text-amber-300' : sc.errors === 1 ? 'text-sky-300' : 'text-emerald-300'}`}>
                    {sc.maxPotential === 15 ? '👑 15 Adayı' : `${sc.maxPotential} Hedef`}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-emerald-400">Tutan: {sc.hits}</span>
                  <span className="text-rose-400">Yatan: {sc.errors}</span>
                  <span className="text-amber-400">Kalan: {pendingCount}</span>
                </div>
                <div className="text-[9.5px] text-[#64748b] truncate mt-0.5 tracking-widest font-mono">
                  {sc.col.map((pick, mIdx) => {
                    const eff = matchOutcomes[mIdx].outcome;
                    const isDet = matchOutcomes[mIdx].isDetermined;
                    const isHit = isDet && pick === eff;
                    const isMiss = isDet && pick !== eff;
                    return (
                      <span
                        key={mIdx}
                        className={isHit ? 'text-emerald-400 font-bold' : isMiss ? 'text-rose-500 font-bold' : 'text-[#64748b]'}
                      >
                        {pick}
                      </span>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Save Coupon Modal */}
      <SaveCouponModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        solution={solution}
        week={programInfo?.week}
        onSuccess={(name) => {
          setToastMessage(`💾 Kupon "${name}" başarıyla kaydedildi.`);
          refreshSavedCoupons();
        }}
      />
    </div>
  );
};
