export type PickOption = '1' | 'X' | '2';

export type AppTab = 'creator' | 'bulletin' | 'vault' | 'live';

export interface LiveMatchDetail {
  no: number;
  home: string;
  away: string;
  date: string;
  status: 'NS' | 'LIVE' | 'HT' | 'FT';
  minute: string;
  score: string;
  current_outcome: '1' | 'X' | '2' | '-';
  is_official?: boolean;
}

export interface MatchData {
  id: number;
  date?: string;
  home: string;
  away: string;
  odds: [number, number, number]; // [1, X, 2]
  picks: PickOption[];
}

export type GuaranteeMode = '15G' | '14G' | '13G' | '12G';

export type SolverStrategy = 'pure' | 'hybrid' | 'base_only' | 'auto_boost';

export interface SheetStructure {
  sheet_id: number;
  cost_tl: number;
  A: string[];
  B: string[];
  C: string[];
  D: string[];
  types?: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
}

export interface SolutionPayload {
  status: string;
  mode: GuaranteeMode;
  solver_mode?: SolverStrategy;
  total_columns: number;
  baseline_columns?: number;
  booster_columns?: number;
  total_sheets: number;
  total_cost: number;
  columns: string[][];
  compact_columns: string[];
  column_types?: ('base' | 'booster')[];
  sheets: SheetStructure[];
  coverage_pct: number;
  is_full_coverage: boolean;
}

export interface ModeEstimate {
  columns: number;
  cost_tl: number;
  hit_15_pct: number;
  chance_pct: number;
  chance_label: string;
  chance_desc: string;
  guarantee: string;
}

export interface EstimatesMap {
  raw_combinations: number;
  singles: number;
  doubles: number;
  triples: number;
  modes: Record<GuaranteeMode, ModeEstimate>;
}
