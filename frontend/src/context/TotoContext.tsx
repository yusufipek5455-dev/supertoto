import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';
import { MatchData, PickOption, GuaranteeMode, SolutionPayload, SolverStrategy, EstimatesMap } from '../types';

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

const DEFAULT_MATCHES: MatchData[] = Array.from({ length: 15 }, (_, i) => ({
  id: i + 1,
  home: `Ev Sahibi ${i + 1}`,
  away: `Deplasman ${i + 1}`,
  odds: i === 0 ? [78.0, 14.0, 8.0] : (i === 1 ? [23.0, 27.0, 50.0] : [45.0, 30.0, 25.0]),
  picks: ['1']
}));

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

  // Dynamic real-time calculation of raw combinations (1^x * 2^y * 3^z) and sphere volume models
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
          picks: m.picks
        })),
        mode: selectedMode,
        solver_mode: chosenStrategy,
        booster_columns: null
      };

      const res = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Solver error: ${res.status}`);
      }

      const data = await res.json();
      setSolution(data);
      setTargetColumns(data.total_columns);

      if (chosenStrategy === 'auto_boost') {
        setToastMessage("Yapay zeka bülteni analiz edip en kârlı ekstra kolonları kupona ekledi.");
      } else {
        setToastMessage("Ekonomik sistem kuponu oluşturuldu (Minimum maliyet).");
      }
    } catch (e) {
      console.error(e);
      setToastMessage("Kupon oluşturulurken bir hata oluştu.");
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
        solveWithStrategy
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
