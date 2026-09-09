import React, { createContext, useContext, useState, useCallback, useMemo, useEffect, ReactNode } from 'react';
import { MatchData, PickOption, GuaranteeMode, SolutionPayload, SolverStrategy, EstimatesMap, AppTab } from '../types';
import { solveLocally } from '../lib/solver';

export interface TotoContextType {
  matches: MatchData[];
  selectedMode: GuaranteeMode;
  setSelectedMode: (mode: GuaranteeMode) => void;
  solverStrategy: SolverStrategy;
  setSolverStrategy: (strategy: SolverStrategy) => void;
  boosterBudget: number;
  setBoosterBudget: (cols: number) => void;
  targetColumns: number;
  setTargetColumns: (cols: number) => void;
  solution: SolutionPayload | null;
  setSolution: (sol: SolutionPayload | null) => void;
  networkDelay: number;
  setNetworkDelay: (delay: number) => void;
  togglePick: (matchIndex: number, pick: PickOption) => void;
  resetAllToDefault: () => void;
  applyQuickFilter: (filter: 'cifte' | 'kapali' | 'banko' | 'sifirla') => void;
  isSolving: boolean;
  setIsSolving: (val: boolean) => void;
  toastMessage: string | null;
  setToastMessage: (val: string | null) => void;
  clearToast: () => void;
  estimates: EstimatesMap;
  rawPoolSize: number;
  solveWithStrategy: (strategy: 'base_only' | 'auto_boost') => Promise<void>;
  programInfo: {
    pNo?: string | number;
    week?: string | number;
    startDate?: string;
    endDate?: string;
    status?: boolean;
  } | null;
  isLoadingBulletin: boolean;
  fetchLiveBulletin: () => Promise<void>;
  selectedTab: AppTab;
  setSelectedTab: (tab: AppTab) => void;
}

function computeClientEstimates(matches: MatchData[]): EstimatesMap {
  const lengths = matches.map(m => Math.max(1, m.picks.length));
  const raw_combinations = lengths.reduce((acc, len) => acc * len, 1);

  const d = lengths.filter(l => l === 2).length;
  const t = lengths.filter(l => l >= 3).length;
  const s = 15 - d - t;

  const v0 = 1;
  const v1 = 1 + d + 2 * t;
  const v2 = v1 + (d * (d - 1) / 2) + (d * t * 2) + (t * (t - 1) * 2);

  const term_d3 = d >= 3 ? (d * (d - 1) * (d - 2)) / 6 : 0;
  const term_d2t = d >= 2 ? ((d * (d - 1)) / 2) * t * 2 : 0;
  const term_dt2 = t >= 2 ? d * ((t * (t - 1)) / 2) * 4 : 0;
  const term_t3 = t >= 3 ? ((t * (t - 1) * (t - 2)) / 6) * 8 : 0;
  const v3 = v2 + term_d3 + term_d2t + term_dt2 + term_t3;

  // 15G
  const cols_15 = raw_combinations;
  const cost_15 = cols_15 * 10;
  const pct_15 = 100.0;

  // 14G (R=1, packing efficiency ~1.25)
  const raw_14 = Math.max(1, Math.ceil(raw_combinations / Math.max(1, v1)));
  const cols_14 = Math.min(raw_combinations, Math.max(4, Math.ceil((raw_14 * 1.25) / 4) * 4));
  const cost_14 = cols_14 * 10;
  const pct_14 = Math.min(100.0, Number(((cols_14 / Math.max(1, raw_combinations)) * 100).toFixed(1)));

  // 13G (R=2, packing efficiency ~1.55)
  const raw_13 = Math.max(1, Math.ceil(raw_combinations / Math.max(1, v2)));
  const cols_13 = Math.min(raw_combinations, Math.max(4, Math.ceil((raw_13 * 1.55) / 4) * 4));
  const cost_13 = cols_13 * 10;
  const pct_13 = Math.min(100.0, Number(((cols_13 / Math.max(1, raw_combinations)) * 100).toFixed(1)));
  const pct_13_14_15 = Math.min(100.0, Number(((cols_13 * v1 / Math.max(1, raw_combinations)) * 100).toFixed(1)));

  // 12G (R=3, packing efficiency ~1.85)
  const raw_12 = Math.max(1, Math.ceil(raw_combinations / Math.max(1, v3)));
  const cols_12 = Math.min(raw_combinations, Math.max(4, Math.ceil((raw_12 * 1.85) / 4) * 4));
  const cost_12 = cols_12 * 10;
  const pct_12 = Math.min(100.0, Number(((cols_12 / Math.max(1, raw_combinations)) * 100).toFixed(1)));
  const pct_12_13_15 = Math.min(100.0, Number(((cols_12 * v2 / Math.max(1, raw_combinations)) * 100).toFixed(1)));

  return {
    raw_combinations,
    singles: s,
    doubles: d,
    triples: t,
    modes: {
      '15G': {
        columns: cols_15,
        cost_tl: cost_15,
        hit_15_pct: pct_15,
        chance_pct: 100.0,
        chance_label: '%100',
        chance_desc: '%100',
        guarantee: '100%'
      },
      '14G': {
        columns: cols_14,
        cost_tl: cost_14,
        hit_15_pct: pct_14,
        chance_pct: pct_14,
        chance_label: `%${pct_14} 15 Şansı`,
        chance_desc: '15 Gelme Şansı',
        guarantee: '100%'
      },
      '13G': {
        columns: cols_13,
        cost_tl: cost_13,
        hit_15_pct: pct_13,
        chance_pct: pct_13_14_15,
        chance_label: `%${pct_13_14_15} 14-15 Şansı`,
        chance_desc: '14 ve 15 Gelme Şansı',
        guarantee: '100%'
      },
      '12G': {
        columns: cols_12,
        cost_tl: cost_12,
        hit_15_pct: pct_12,
        chance_pct: pct_12_13_15,
        chance_label: `%${pct_12_13_15} 13-15 Şansı`,
        chance_desc: '13, 14 ve 15 Gelme Şansı',
        guarantee: '100%'
      },
    }
  };
}

export const TIER_RANKS: Record<GuaranteeMode, number> = {
  '12G': 12,
  '13G': 13,
  '14G': 14,
  '15G': 15,
};

/**
 * Calculates dynamic cascading probability percentages matching the Sportoto standard:
 * - If card tier <= selected mode tier (e.g. 13G and 12G when 13G selected): guaranteed 100%
 * - If card tier > selected mode tier: (cols_selected / cols_card) * 100
 */
export function getCascadingOdds(
  cardMode: GuaranteeMode,
  selectedMode: GuaranteeMode,
  estimates: EstimatesMap
): { percentStr: string; isGuaranteed: boolean; pctValue: number } {
  const cardRank = TIER_RANKS[cardMode];
  const selectedRank = TIER_RANKS[selectedMode];

  if (cardRank <= selectedRank) {
    return { percentStr: '100%', isGuaranteed: true, pctValue: 100.0 };
  }

  const selectedCols = estimates.modes[selectedMode]?.columns || 1;
  const cardCols = estimates.modes[cardMode]?.columns || 1;

  const rawPct = Math.min(100.0, (selectedCols / Math.max(1, cardCols)) * 100.0);
  const formatted = (rawPct % 1 === 0 ? rawPct.toFixed(0) : rawPct.toFixed(1)) + '%';

  return { percentStr: formatted, isGuaranteed: false, pctValue: rawPct };
}

const DEFAULT_MATCHES: MatchData[] = [
  { id: 1, date: "11.09 20:00", home: "Beşiktaş A.Ş.", away: "Erzurumspor FK", odds: [90.0, 7.0, 3.0], picks: ['1'] },
  { id: 2, date: "12.09 17:00", home: "Eyüpspor", away: "Çaykur Rizespor A.Ş.", odds: [22.0, 28.0, 50.0], picks: ['1'] },
  { id: 3, date: "12.09 17:00", home: "Samsunspor A.Ş.", away: "Çorum FK", odds: [56.0, 24.0, 20.0], picks: ['1'] },
  { id: 4, date: "12.09 20:00", home: "Alanyaspor", away: "Göztepe A.Ş.", odds: [42.0, 30.0, 28.0], picks: ['1'] },
  { id: 5, date: "12.09 20:00", home: "Konyaspor", away: "Trabzonspor A.Ş.", odds: [15.0, 19.0, 66.0], picks: ['1'] },
  { id: 6, date: "13.09 17:00", home: "Gençlerbirliği", away: "Kasımpaşa A.Ş.", odds: [46.0, 29.0, 25.0], picks: ['1'] },
  { id: 7, date: "13.09 20:00", home: "Amed Sportif", away: "Başakşehir FK", odds: [35.0, 28.0, 37.0], picks: ['1'] },
  { id: 8, date: "13.09 20:00", home: "Galatasaray A.Ş.", away: "Kocaelispor", odds: [76.0, 17.0, 7.0], picks: ['1'] },
  { id: 9, date: "14.09 20:00", home: "Gaziantep F.K. A.Ş.", away: "Fenerbahçe A.Ş.", odds: [11.0, 16.0, 73.0], picks: ['1'] },
  { id: 10, date: "12.09 16:30", home: "Augsburg", away: "B. Leverkusen", odds: [25.0, 22.0, 53.0], picks: ['1'] },
  { id: 11, date: "11.09 21:45", home: "Rennes", away: "Marsilya", odds: [35.0, 29.0, 36.0], picks: ['1'] },
  { id: 12, date: "12.09 17:00", home: "Chelsea", away: "Hull City", odds: [81.0, 12.0, 7.0], picks: ['1'] },
  { id: 13, date: "13.09 18:30", home: "Manchester United", away: "Manchester City", odds: [25.0, 26.0, 49.0], picks: ['1'] },
  { id: 14, date: "13.09 17:15", home: "Levante", away: "Barcelona", odds: [6.0, 9.0, 85.0], picks: ['1'] },
  { id: 15, date: "12.09 19:00", home: "Lazio", away: "AC Milan", odds: [26.0, 30.0, 44.0], picks: ['1'] },
];

const TotoContext = createContext<TotoContextType | undefined>(undefined);

export const TotoProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [matches, setMatches] = useState<MatchData[]>(DEFAULT_MATCHES);
  const [selectedMode, setSelectedMode] = useState<GuaranteeMode>('13G');
  const [solverStrategy, setSolverStrategy] = useState<SolverStrategy>('pure');
  const [boosterBudget, setBoosterBudget] = useState<number>(40);
  const [targetColumns, setTargetColumns] = useState<number>(48);
  const [solution, setSolution] = useState<SolutionPayload | null>(null);
  const [networkDelay, setNetworkDelay] = useState<number>(750); // Lag Shield default 750ms
  const [isSolving, setIsSolving] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [programInfo, setProgramInfo] = useState<{ pNo?: string | number; week?: string | number; startDate?: string; endDate?: string; status?: boolean } | null>({
    pNo: "357",
    week: "141236",
    startDate: "2026-09-11T19:55:00+03:00",
    endDate: "2026-09-14T21:45:00+03:00"
  });
  const [isLoadingBulletin, setIsLoadingBulletin] = useState<boolean>(false);
  const [selectedTab, setSelectedTab] = useState<AppTab>('creator');

  // Restore active solution from localStorage on load if available
  useEffect(() => {
    try {
      const saved = localStorage.getItem('TOTO_ACTIVE_SOLUTION');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.columns && parsed.columns.length > 0) {
          setSolution(parsed);
          setTargetColumns(parsed.total_columns);
        }
      }
    } catch {}
  }, []);
  const estimates = useMemo(() => computeClientEstimates(matches), [matches]);
  const rawPoolSize = estimates.raw_combinations;

  const clearToast = useCallback(() => {
    setToastMessage(null);
  }, []);

  // Match toggle logic with strict Minimum 1 Pick Invariant
  const togglePick = useCallback((matchIndex: number, pick: PickOption) => {
    setMatches(prevMatches => {
      const updated = [...prevMatches];
      const match = { ...updated[matchIndex] };
      const currentPicks = [...match.picks];

      if (currentPicks.includes(pick)) {
        // PREVENT deselecting if it is the ONLY pick on this match
        if (currentPicks.length > 1) {
          match.picks = currentPicks.filter(p => p !== pick);
        } else {
          return prevMatches;
        }
      } else {
        match.picks = [...currentPicks, pick];
      }

      updated[matchIndex] = match;
      return updated;
    });
    // Invalidate stale solution so real-time card estimates reflect newly toggled picks immediately
    setSolution(null);
  }, []);

  // "Hepsini Sıfırla / Reset All" button action
  const resetAllToDefault = useCallback(() => {
    setMatches(prevMatches =>
      prevMatches.map(m => ({
        ...m,
        picks: ['1']
      }))
    );
    setSolution(null);
    setToastMessage("Tüm maçlar varsayılana sıfırlandı");
  }, []);

  // High-contrast quick filter actions
  const applyQuickFilter = useCallback((filter: 'cifte' | 'kapali' | 'banko' | 'sifirla') => {
    if (filter === 'sifirla') {
      resetAllToDefault();
      return;
    }

    setMatches(prevMatches =>
      prevMatches.map(m => {
        if (filter === 'kapali') {
          return { ...m, picks: ['1', 'X', '2'] };
        } else if (filter === 'cifte') {
          const odds = m.odds;
          const choices: PickOption[] = odds[0] >= odds[2] ? ['1', 'X'] : ['X', '2'];
          return { ...m, picks: choices };
        } else if (filter === 'banko') {
          // Keep singles intact, cover others
          if (m.picks.length === 1) {
            return m;
          }
          return { ...m, picks: ['1', 'X', '2'] };
        }
        return m;
      })
    );
    setSolution(null);

    const labels: Record<string, string> = {
      kapali: "Tüm maçlar 1-X-2 kapatıldı",
      cifte: "Tüm maçlar çifte tercihlere ayarlandı",
      banko: "Bankolar korundu, diğer maçlar kapatıldı"
    };
    setToastMessage(labels[filter] || "Filtre uygulandı");
  }, [resetAllToDefault]);

  // Fetch live Nesine bulletin and odds
  const fetchLiveBulletin = useCallback(async () => {
    setIsLoadingBulletin(true);
    try {
      const res = await fetch('/api/bulletin');
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.fixtures && data.fixtures.length === 15) {
          setMatches(prevMatches =>
            data.fixtures.map((f: any, idx: number) => {
              const existing = prevMatches[idx];
              return {
                id: f.no || (idx + 1),
                date: f.date || existing?.date || '',
                home: f.home || existing?.home || `Takım ${idx + 1}`,
                away: f.away || existing?.away || `Rakip ${idx + 1}`,
                odds: (f.odds && f.odds.length === 3 ? f.odds : existing?.odds) || [33.3, 33.3, 33.4],
                picks: existing?.picks || ['1'],
              };
            })
          );
          if (data.program_info) {
            setProgramInfo(data.program_info);
          }
          if (data.is_fallback) {
            setToastMessage(`🛡️ Nesine bülteni yüklendi (${data.fallback_source || 'Yedek'})`);
          } else {
            setToastMessage("⚡ Nesine canlı bülteni ve güncel kamu oranları yüklendi!");
          }
        }
      }
    } catch (err) {
      console.warn("Bülten çekme hatası:", err);
      setToastMessage("Bülten çekilirken bağlantı hatası oluştu.");
    } finally {
      setIsLoadingBulletin(false);
    }
  }, []);

  // Fetch live bulletin on mount
  useEffect(() => {
    fetchLiveBulletin();
  }, [fetchLiveBulletin]);

  // Hybrid Quant Solver Dispatch (Base Only vs AI Auto Boost)
  const solveWithStrategy = useCallback(async (chosenStrategy: 'base_only' | 'auto_boost') => {
    setIsSolving(true);
    setSolverStrategy(chosenStrategy);
    try {
      const payload = {
        matches: matches.map(m => ({
          id: m.id,
          home: m.home,
          away: m.away,
          odds: m.odds,
          picks: m.picks
        })),
        mode: selectedMode,
        solver_mode: chosenStrategy,
        booster_columns: null
      };

      let data: any = null;
      try {
        const res = await fetch('/api/solve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch (netErr) {
        console.warn('Network solver error, falling back to local deterministic solver:', netErr);
      }

      // If serverless is unavailable or threw error, run deterministic local solver
      if (!data || !data.columns || data.columns.length === 0) {
        data = solveLocally(matches, selectedMode, chosenStrategy);
      }

      setSolution(data);
      setTargetColumns(data.total_columns);
      try {
        localStorage.setItem('TOTO_ACTIVE_SOLUTION', JSON.stringify(data));
      } catch {}

      if (chosenStrategy === 'auto_boost') {
        setToastMessage("Yapay zeka bülteni analiz edip en kârlı ekstra kolonları kupona ekledi.");
      } else {
        setToastMessage("Ekonomik sistem kuponu oluşturuldu (Minimum maliyet).");
      }
    } catch (e: any) {
      console.error('Solve error:', e);
      // Failsafe local solver execution
      try {
        const fallbackData = solveLocally(matches, selectedMode, chosenStrategy);
        setSolution(fallbackData);
        setTargetColumns(fallbackData.total_columns);
        setToastMessage("Kupon başarıyla oluşturuldu.");
      } catch (innerErr) {
        setToastMessage("Kupon oluşturulurken bir hata oluştu.");
      }
    } finally {
      setIsSolving(false);
    }
  }, [matches, selectedMode]);

  return (
    <TotoContext.Provider
      value={{
        matches,
        selectedMode,
        setSelectedMode,
        solverStrategy,
        setSolverStrategy,
        boosterBudget,
        setBoosterBudget,
        targetColumns,
        setTargetColumns,
        solution,
        setSolution,
        networkDelay,
        setNetworkDelay,
        togglePick,
        resetAllToDefault,
        applyQuickFilter,
        isSolving,
        setIsSolving,
        toastMessage,
        setToastMessage,
        clearToast,
        estimates,
        rawPoolSize,
        solveWithStrategy,
        programInfo,
        isLoadingBulletin,
        fetchLiveBulletin,
        selectedTab,
        setSelectedTab
      }}
    >
      {children}
    </TotoContext.Provider>
  );
};

export const useToto = (): TotoContextType => {
  const ctx = useContext(TotoContext);
  if (!ctx) {
    throw new Error("useToto must be used within a TotoProvider");
  }
  return ctx;
};
