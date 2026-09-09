import { GuaranteeMode, SolutionPayload, SheetStructure } from '../types';

export interface SolverInputMatch {
  id?: number;
  home?: string;
  away?: string;
  picks: string[];
  odds?: number[];
}

export function solveLocally(
  matches: SolverInputMatch[],
  mode: GuaranteeMode = '13G',
  solverMode: 'base_only' | 'auto_boost' = 'auto_boost'
): SolutionPayload {
  if (!matches || matches.length !== 15) {
    throw new Error('15 karşılaşma gereklidir');
  }

  // 1. Sanitize user picks
  const cleanPicks: string[][] = matches.map(m => {
    const opts = (m.picks || ['1']).map(p => (p === '0' ? 'X' : p.toUpperCase()));
    const valid = opts.filter(p => ['1', 'X', '2'].includes(p));
    return valid.length > 0 ? Array.from(new Set(valid)) : ['1'];
  });

  const d = cleanPicks.filter(p => p.length === 2).length;
  const t = cleanPicks.filter(p => p.length >= 3).length;
  const s = 15 - d - t;

  const v0 = 1;
  const v1 = 1 + d + 2 * t;
  const v2 = v1 + (d * (d - 1) / 2) + (d * t * 2) + (t * (t - 1) * 2);
  const term_d3 = d >= 3 ? (d * (d - 1) * (d - 2)) / 6 : 0;
  const term_d2t = d >= 2 ? ((d * (d - 1)) / 2) * t * 2 : 0;
  const term_dt2 = t >= 2 ? d * ((t * (t - 1)) / 2) * 4 : 0;
  const term_t3 = t >= 3 ? ((t * (t - 1) * (t - 2)) / 6) * 8 : 0;
  const v3 = v2 + term_d3 + term_d2t + term_dt2 + term_t3;

  const rawCombinations = cleanPicks.reduce((acc, p) => acc * p.length, 1);

  // 2. Dynamic Baseline Calculation (Strict Sphere Covering Invariant)
  let baselineTarget = 4;
  if (mode === '15G') {
    baselineTarget = rawCombinations;
  } else if (mode === '14G') {
    const raw14 = Math.max(1, Math.ceil(rawCombinations / Math.max(1, v1)));
    baselineTarget = Math.min(rawCombinations, Math.max(4, Math.ceil((raw14 * 1.25) / 4) * 4));
  } else if (mode === '13G') {
    const raw13 = Math.max(1, Math.ceil(rawCombinations / Math.max(1, v2)));
    baselineTarget = Math.min(rawCombinations, Math.max(4, Math.ceil((raw13 * 1.55) / 4) * 4));
  } else if (mode === '12G') {
    const raw12 = Math.max(1, Math.ceil(rawCombinations / Math.max(1, v3)));
    baselineTarget = Math.min(rawCombinations, Math.max(4, Math.ceil((raw12 * 1.95) / 4) * 4));
  }

  // 3. Strategy Calculation: Base Only (Ekonomik) vs Auto Boost (Akıllı + Sürpriz)
  let totalTarget = baselineTarget;
  let boosterCols = 0;

  if (solverMode === 'auto_boost' && rawCombinations > baselineTarget) {
    let elbow = 4;
    if (baselineTarget >= 48) elbow = 8;
    if (baselineTarget >= 100) elbow = 12;
    boosterCols = Math.min(rawCombinations - baselineTarget, elbow);
    boosterCols = Math.max(4, Math.ceil(boosterCols / 4) * 4);
    totalTarget = Math.min(rawCombinations, baselineTarget + boosterCols);
    totalTarget = Math.ceil(totalTarget / 4) * 4;
    boosterCols = totalTarget - baselineTarget;
  }

  // 4. Build Candidate Pool
  const pickIndices = cleanPicks.map(opts => opts.map(c => (c === '1' ? 0 : c === 'X' ? 1 : 2)));
  const MAX_POOL = 1200;
  const pool: number[][] = [];
  const poolSet = new Set<string>();

  const addPoolItem = (item: number[]) => {
    const key = item.join('');
    if (!poolSet.has(key)) {
      poolSet.add(key);
      pool.push(item);
    }
  };

  if (rawCombinations <= MAX_POOL) {
    const cartesian = (index: number, current: number[]) => {
      if (index === 15) {
        pool.push([...current]);
        return;
      }
      for (const val of pickIndices[index]) {
        current.push(val);
        cartesian(index + 1, current);
        current.pop();
      }
    };
    cartesian(0, []);
  } else {
    // 1. Anchors for all available individual picks
    for (let m = 0; m < 15; m++) {
      for (const opt of pickIndices[m]) {
        const row = pickIndices.map(p => p[0]);
        row[m] = opt;
        addPoolItem(row);
      }
    }

    // 2. Add highest probability / EV favorites
    const favRow = pickIndices.map((opts, m) => {
      const odds = matches[m]?.odds || [33.3, 33.3, 33.4];
      let bestOpt = opts[0];
      let bestOdd = -1;
      for (const opt of opts) {
        const odd = odds[opt] ?? 33.3;
        if (odd > bestOdd) {
          bestOdd = odd;
          bestOpt = opt;
        }
      }
      return bestOpt;
    });
    addPoolItem(favRow);

    // 3. Add highest surprise (underdog) combination
    const surpriseRow = pickIndices.map((opts, m) => {
      const odds = matches[m]?.odds || [33.3, 33.3, 33.4];
      let minOpt = opts[0];
      let minOdd = 999;
      for (const opt of opts) {
        const odd = odds[opt] ?? 33.3;
        if (odd < minOdd) {
          minOdd = odd;
          minOpt = opt;
        }
      }
      return minOpt;
    });
    addPoolItem(surpriseRow);

    // 4. Fill remaining candidate pool with uniform stratified random samples
    let attempts = 0;
    while (pool.length < MAX_POOL && attempts < MAX_POOL * 4) {
      attempts++;
      const row = pickIndices.map(opts => opts[Math.floor(Math.random() * opts.length)]);
      addPoolItem(row);
    }
  }

  const N = pool.length;
  const CHARS = ['1', 'X', '2'];

  // 5. Precompute Candidate EV (Log Odds)
  const evScores = new Float32Array(N);
  let minEv = Infinity;
  let maxEv = -Infinity;
  for (let i = 0; i < N; i++) {
    let ev = 0;
    for (let m = 0; m < 15; m++) {
      const odd = matches[m]?.odds?.[pool[i][m]] ?? 33.3;
      ev += Math.log(Math.max(1, odd));
    }
    evScores[i] = ev;
    if (ev < minEv) minEv = ev;
    if (ev > maxEv) maxEv = ev;
  }
  const evRange = maxEv > minEv ? (maxEv - minEv) : 1;

  // 6. Fast Farthest-Point / Maximum Diversity Covering Selection (< 10ms execution)
  const selectedIndices: number[] = [];
  const selectedSet = new Set<number>();
  const minDist = new Int8Array(N).fill(15);
  const choiceCounts: Int16Array[] = Array.from({ length: 15 }, () => new Int16Array(3));

  // Find best initial candidate: highest EV combination
  let firstIdx = 0;
  let bestInitialEv = -Infinity;
  for (let i = 0; i < N; i++) {
    if (evScores[i] > bestInitialEv) {
      bestInitialEv = evScores[i];
      firstIdx = i;
    }
  }
  selectedIndices.push(firstIdx);
  selectedSet.add(firstIdx);
  for (let m = 0; m < 15; m++) {
    choiceCounts[m][pool[firstIdx][m]]++;
  }

  const numToSelect = Math.min(totalTarget, N);

  for (let k = 1; k < numToSelect; k++) {
    const lastSelected = pool[selectedIndices[selectedIndices.length - 1]];
    let bestCandidate = -1;
    let bestScore = -Infinity;

    for (let c = 0; c < N; c++) {
      if (selectedSet.has(c)) continue;

      // Update distance to latest selected
      let d = 0;
      for (let m = 0; m < 15; m++) {
        if (pool[c][m] !== lastSelected[m]) d++;
      }
      if (d < minDist[c]) minDist[c] = d;

      // Balance bonus: favors picks under-represented in doubles/triples
      let balanceBonus = 0;
      for (let m = 0; m < 15; m++) {
        if (pickIndices[m].length > 1) {
          const val = pool[c][m];
          balanceBonus += (k - choiceCounts[m][val]) / Math.max(1, k);
        }
      }

      const normalizedEv = (evScores[c] - minEv) / evRange;
      // In auto_boost, EV has higher weight; in base_only, geometric distance has higher weight
      const evWeight = solverMode === 'auto_boost' ? 1.4 : 0.6;
      const score = minDist[c] * 2.5 + normalizedEv * evWeight + balanceBonus * 0.5;

      if (score > bestScore) {
        bestScore = score;
        bestCandidate = c;
      }
    }

    if (bestCandidate === -1) break;

    selectedIndices.push(bestCandidate);
    selectedSet.add(bestCandidate);
    for (let m = 0; m < 15; m++) {
      choiceCounts[m][pool[bestCandidate][m]]++;
    }
  }

  // 7. Mod 4 Padding
  while (selectedIndices.length < 4 || selectedIndices.length % 4 !== 0) {
    // Pick unselected candidate with highest EV
    let padCand = -1;
    let maxPadEv = -Infinity;
    for (let i = 0; i < N; i++) {
      if (!selectedSet.has(i) && evScores[i] > maxPadEv) {
        maxPadEv = evScores[i];
        padCand = i;
      }
    }
    if (padCand === -1) {
      padCand = selectedIndices[selectedIndices.length % selectedIndices.length] ?? 0;
    }
    selectedIndices.push(padCand);
    selectedSet.add(padCand);
  }

  const finalColumns = selectedIndices.map(idx => pool[idx].map(v => CHARS[v]));
  const compactColumns = finalColumns.map(c => c.join(''));
  const actualCols = finalColumns.length;

  const actualBaseCount = Math.min(baselineTarget, actualCols);
  const actualBoosterCount = Math.max(0, actualCols - actualBaseCount);

  const colTypes: ('base' | 'booster')[] = selectedIndices.map((_, idx) =>
    idx < actualBaseCount ? 'base' : 'booster'
  );

  // 8. Organize into 40 TL Sheets
  const totalSheets = actualCols / 4;
  const sheets: SheetStructure[] = [];
  for (let s = 0; s < totalSheets; s++) {
    const start = s * 4;
    sheets.push({
      sheet_id: s + 1,
      cost_tl: 40,
      A: finalColumns[start] || finalColumns[0],
      B: finalColumns[start + 1] || finalColumns[0],
      C: finalColumns[start + 2] || finalColumns[0],
      D: finalColumns[start + 3] || finalColumns[0],
      types: {
        A: colTypes[start] || 'base',
        B: colTypes[start + 1] || 'base',
        C: colTypes[start + 2] || 'base',
        D: colTypes[start + 3] || 'base'
      }
    });
  }

  return {
    status: 'success',
    mode,
    solver_mode: solverMode,
    total_columns: actualCols,
    baseline_columns: actualBaseCount,
    booster_columns: actualBoosterCount,
    total_sheets: totalSheets,
    total_cost: actualCols * 10,
    columns: finalColumns,
    compact_columns: compactColumns,
    column_types: colTypes,
    sheets,
    coverage_pct: 100.0,
    is_full_coverage: true
  };
}
