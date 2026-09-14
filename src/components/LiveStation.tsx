import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useToto } from '../context/TotoContext';
import { LiveMatchDetail, SavedCoupon } from '../types';
import { getSavedCoupons, deleteSavedCoupon, SAVED_COUPONS_EVENT } from '../lib/storage';
import { SaveCouponModal } from './SaveCouponModal';
import { calculateRealisticPrize, formatPrizeTL, MatchProbability, VOLUME_PRESETS, VolumePresetKey } from '../lib/prizeEngine';

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

  // Realistic Pari-Mutuel Prize Settings (Volume Presets & Custom Revenue/Carryover)
  const [selectedPreset, setSelectedPreset] = useState<VolumePresetKey>('normal');
  const [totalRevenue, setTotalRevenue] = useState<number>(45000000); // 45M TL (~4.5M kolon)
  const [carryover, setCarryover] = useState<number>(0);
  const [showPrizeSettings, setShowPrizeSettings] = useState<boolean>(false);

  const handleSelectPreset = (key: Exclude<VolumePresetKey, 'custom'>) => {
    setSelectedPreset(key);
    const p = VOLUME_PRESETS[key];
    setTotalRevenue(p.revenue);
    setCarryover(p.defaultCarryover);
    setToastMessage(`İkramiye Hacmi: ${p.label} (${(p.revenue / 1000000)}M TL) ayarlandı.`);
  };

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
      const res = await fetch(`/api/live?t=${Date.now()}`, { cache: 'no-store' });
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

  // Convert match odds into normalized probability maps [{ '1': p1, 'X': pX, '2': p2 }, ...]
  const matchProbabilities: MatchProbability[] = useMemo(() => {
    return Array.from({ length: 15 }, (_, i) => {
      const m = matches?.[i];
      const rawOdds = m?.odds;
      if (rawOdds && rawOdds.length === 3) {
        const sum = (rawOdds[0] || 0) + (rawOdds[1] || 0) + (rawOdds[2] || 0);
        if (sum > 0) {
          return {
            '1': (rawOdds[0] || 0) / sum,
            'X': (rawOdds[1] || 0) / sum,
            '2': (rawOdds[2] || 0) / sum
          };
        }
      }
      return { '1': 0.3333, 'X': 0.3333, '2': 0.3334 };
    });
  }, [matches]);

  // Construct 15-character active scenario choices string ("121121212221222")
  // For determined matches (live/FT or user override), use the actual outcome.
  // For pending matches, fallback to highest-probability favorite outcome as baseline projection.
  const activeScenarioChoices = useMemo(() => {
    return matchOutcomes.map((m, idx) => {
      if (m.isDetermined && (m.outcome === '1' || m.outcome === 'X' || m.outcome === '2')) {
        return m.outcome;
      }
      const probs = matchProbabilities[idx] || { '1': 0.33, 'X': 0.33, '2': 0.34 };
      if (probs['1'] >= probs['X'] && probs['1'] >= probs['2']) return '1';
      if (probs['2'] >= probs['X']) return '2';
      return 'X';
    }).join('');
  }, [matchOutcomes, matchProbabilities]);

  // Execute Realistic Prize Engine calculation
  const prizeCalc = useMemo(() => {
    return calculateRealisticPrize({
      couponChoices: activeScenarioChoices,
      matchProbabilities,
      totalRevenue,
      carryover
    });
  }, [activeScenarioChoices, matchProbabilities, totalRevenue, carryover]);

  // Dynamic user's total estimated prize based on their matched columns
  const userTotalEstimatedPrize = useMemo(() => {
    return (
      c15 * prizeCalc.tier15.rawPrize +
      c14 * prizeCalc.tier14.rawPrize +
      c13 * prizeCalc.tier13.rawPrize +
      c12 * prizeCalc.tier12.rawPrize
    );
  }, [c15, c14, c13, c12, prizeCalc]);

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
            <span className="text-[10.5px] font-extrabold uppercase tracking-wider text-emerald-300 flex items-center gap-1.5 flex-wrap">
              <span>{hasOverrides ? 'What-If Senaryo Simülatörü' : 'Anlık Canlı Skor Değerlendirmesi'}</span>
              {hasOverrides && (
                <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 px-1.5 py-0.2 rounded text-[9px]">
                  {overrideCount} Maç Simüle Edildi
                </span>
              )}
              {prizeCalc.isHighDevirRisk && (
                <span className="bg-rose-950/80 text-rose-300 border border-rose-500/60 px-1.5 py-0.2 rounded text-[9px] font-extrabold animate-pulse shadow-sm shadow-rose-950">
                  🔥 Devir Olasılığı Yüksek
                </span>
              )}
            </span>
            <div className="text-sm sm:text-base font-extrabold text-white font-mono mt-0.5 flex items-center flex-wrap gap-2">
              <span>Bu Senaryoda Tahmini Kazancınız:</span>
              {userTotalEstimatedPrize > 0 ? (
                <span className="text-emerald-300 font-black text-base sm:text-lg bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-500/40 shadow-sm shadow-emerald-950">
                  {formatPrizeTL(userTotalEstimatedPrize)}
                </span>
              ) : (
                <span className="text-slate-400 font-bold">0 TL (Henüz 12-15 eşleşme yok)</span>
              )}
              {pendingCount > 0 && userTotalEstimatedPrize > 0 && (
                <span className="text-[10px] text-amber-300 font-normal bg-amber-950/50 px-1.5 py-0.5 rounded border border-amber-500/30">
                  (Kalan {pendingCount} maç favori kabul edilerek modellendi)
                </span>
              )}
            </div>

            {/* Kazanan kolon detay hapları */}
            {(c15 > 0 || c14 > 0 || c13 > 0 || c12 > 0) && (
              <div className="flex items-center gap-1.5 text-[10px] font-mono mt-1.5 flex-wrap">
                {c15 > 0 && (
                  <span className="bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/40 font-bold">
                    👑 15 Bilen: {c15} x {prizeCalc.tier15.estimatedPrize}
                  </span>
                )}
                {c14 > 0 && (
                  <span className="bg-sky-500/20 text-sky-300 px-1.5 py-0.5 rounded border border-sky-500/40 font-bold">
                    🎯 14 Bilen: {c14} x {prizeCalc.tier14.estimatedPrize}
                  </span>
                )}
                {c13 > 0 && (
                  <span className="bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-500/40 font-bold">
                    🛡️ 13 Bilen: {c13} x {prizeCalc.tier13.estimatedPrize}
                  </span>
                )}
                {c12 > 0 && (
                  <span className="bg-slate-700/40 text-slate-300 px-1.5 py-0.5 rounded border border-slate-600/40 font-bold">
                    📊 12 Bilen: {c12} x {prizeCalc.tier12.estimatedPrize}
                  </span>
                )}
              </div>
            )}
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

        {/* İkramiye İklimi & Olasılık Modeli (5 cols) */}
        <div className="lg:col-span-5 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 flex flex-col justify-between gap-1.5">
          <div className="flex items-center justify-between border-b border-[#1e293b] pb-1.5 flex-wrap gap-1">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-extrabold text-[#38bdf8] uppercase tracking-wider">
                🌡️ İkramiye İklimi
              </span>
              <button
                onClick={() => setShowPrizeSettings(prev => !prev)}
                title="Hasılat ve Devir Ayarlarını Aç/Kapat"
                className="text-[11px] hover:scale-110 transition p-0.5 rounded cursor-pointer"
              >
                ⚙️
              </button>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[9.5px] font-mono text-cyan-300 bg-[#06080e] px-1.5 py-0.5 rounded border border-[#1e293b]">
                P: {prizeCalc.couponPopularityScore}
              </span>
              <span className={`text-[10.5px] font-extrabold ${prizeCalc.climateColor}`}>
                {prizeCalc.climateBadge}
              </span>
            </div>
          </div>

          {/* Dinamik Hacim / Devir Durumu Preset Butonları */}
          <div className="grid grid-cols-3 gap-1 my-0.5">
            {(['normal', 'single_devir', 'record_devir'] as const).map((key) => {
              const p = VOLUME_PRESETS[key];
              const isSelected = selectedPreset === key;
              return (
                <button
                  key={key}
                  onClick={() => handleSelectPreset(key)}
                  className={`py-1 px-1.5 rounded text-[9.5px] font-bold font-mono transition flex flex-col items-center justify-center cursor-pointer border ${
                    isSelected
                      ? 'bg-cyan-950/80 border-cyan-400 text-cyan-300 shadow-sm shadow-cyan-950'
                      : 'bg-[#06080e] border-[#1e293b] text-[#94a3b8] hover:text-white hover:border-[#334155]'
                  }`}
                  title={p.description}
                >
                  <span className="truncate">{p.label}</span>
                  <span className="text-[8.5px] opacity-75">{p.badge} TL</span>
                </button>
              );
            })}
          </div>

          {/* Collapsible Revenue & Carryover Custom Settings */}
          {showPrizeSettings && (
            <div className="bg-[#06080e] border border-cyan-500/30 rounded p-2 text-[10px] font-mono flex flex-col gap-1.5 my-1 animate-fadeIn">
              <div className="flex items-center justify-between">
                <span className="text-cyan-300 font-bold">Haftalık Hasılat (TL):</span>
                <input
                  type="number"
                  step="1000000"
                  value={totalRevenue}
                  onChange={(e) => {
                    setSelectedPreset('custom');
                    setTotalRevenue(Math.max(1000000, Number(e.target.value) || 0));
                  }}
                  className="w-28 bg-[#0a0f1d] border border-[#334155] rounded px-1.5 py-0.5 text-right text-white text-xs outline-none focus:border-cyan-400"
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-amber-300 font-bold">15 Devir Tutarı (TL):</span>
                <input
                  type="number"
                  step="500000"
                  value={carryover}
                  onChange={(e) => {
                    setSelectedPreset('custom');
                    setCarryover(Math.max(0, Number(e.target.value) || 0));
                  }}
                  className="w-28 bg-[#0a0f1d] border border-[#334155] rounded px-1.5 py-0.5 text-right text-white text-xs outline-none focus:border-amber-400"
                />
              </div>
              <div className="flex items-center justify-between text-[9px] text-[#64748b] pt-1 border-t border-[#1e293b]">
                <span>Toplam Havuz (%55): <strong className="text-white">{formatPrizeTL(prizeCalc.totalPrizePool)}</strong></span>
                <span>Oynanan Kolon: <strong className="text-emerald-400 font-mono">{(totalRevenue / 10).toLocaleString('tr-TR')}</strong></span>
              </div>
              <div className="flex justify-end pt-0.5">
                <button
                  onClick={() => handleSelectPreset('normal')}
                  className="text-cyan-400 hover:underline cursor-pointer text-[9px]"
                >
                  Varsayılana Dön (45M Normal)
                </button>
              </div>
            </div>
          )}

          {/* 4 Tier Prize Display */}
          <div className="grid grid-cols-2 gap-1.5 text-[10.5px] font-mono">
            {/* 15 */}
            <div className={`bg-[#06080e] p-1.5 rounded border transition ${c15 > 0 ? 'border-amber-500/60 bg-amber-950/20' : 'border-[#1e293b]'}`}>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-amber-300 font-bold">15 Bilen:</span>
                <span className="text-[9px] text-[#94a3b8]">({prizeCalc.tier15.expectedWinners} kişi)</span>
              </div>
              <div className="text-xs sm:text-sm font-extrabold text-emerald-400 mt-0.5 truncate">
                {prizeCalc.tier15.estimatedPrize}
              </div>
            </div>

            {/* 14 */}
            <div className={`bg-[#06080e] p-1.5 rounded border transition ${c14 > 0 ? 'border-sky-500/60 bg-sky-950/20' : 'border-[#1e293b]'}`}>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-sky-300 font-bold">14 Bilen:</span>
                <span className="text-[9px] text-[#94a3b8]">({prizeCalc.tier14.expectedWinners} kişi)</span>
              </div>
              <div className="text-xs sm:text-sm font-extrabold text-sky-400 mt-0.5 truncate">
                {prizeCalc.tier14.estimatedPrize}
              </div>
            </div>

            {/* 13 */}
            <div className={`bg-[#06080e] p-1.5 rounded border transition ${c13 > 0 ? 'border-emerald-500/60 bg-emerald-950/20' : 'border-[#1e293b]'}`}>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-emerald-300 font-bold">13 Bilen:</span>
                <span className="text-[9px] text-[#94a3b8]">({prizeCalc.tier13.expectedWinners} kişi)</span>
              </div>
              <div className="text-xs sm:text-sm font-extrabold text-amber-300 mt-0.5 truncate">
                {prizeCalc.tier13.estimatedPrize}
              </div>
            </div>

            {/* 12 */}
            <div className={`bg-[#06080e] p-1.5 rounded border border-[#1e293b] transition ${c12 > 0 ? 'border-slate-500/60 bg-slate-900/40' : 'border-[#1e293b]'}`}>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-slate-300 font-bold">12 Bilen:</span>
                <span className="text-[9px] text-[#94a3b8]">({prizeCalc.tier12.expectedWinners} kişi)</span>
              </div>
              <div className="text-xs sm:text-sm font-extrabold text-slate-300 mt-0.5 truncate">
                {prizeCalc.tier12.estimatedPrize}
              </div>
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
