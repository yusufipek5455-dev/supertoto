import React from 'react';
import { useToto } from '../context/TotoContext';
import { MatchData, PickOption } from '../types';

export interface MatchRowProps {
  match: MatchData;
  index: number;
}

export const MatchRow: React.FC<MatchRowProps> = ({ match, index }) => {
  const { togglePick } = useToto();
  const options: PickOption[] = ['1', 'X', '2'];

  return (
    <div 
      data-testid={`match-row-${index}`}
      className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 p-2 sm:px-2 sm:py-1 bg-[#0a0f1d] hover:bg-[#0f172a] border border-[#1e293b]/60 rounded transition-colors text-xs select-none min-h-[52px] lg:min-h-0 lg:h-[28px] lg:p-0 lg:px-2"
    >
      {/* Team info & index */}
      <div className="flex items-center gap-2 min-w-0 flex-1 pr-1">
        {/* Fixed mono match index */}
        <div className="w-[24px] h-[22px] lg:h-[20px] flex-shrink-0 flex items-center justify-center font-mono font-bold text-xs lg:text-[10.5px] text-[#64748b] bg-[#06080e] border border-[#1e293b] rounded">
          {(index + 1).toString().padStart(2, '0')}
        </div>

        {/* Embedded Team Names */}
        <div className="flex-1 min-w-0 truncate">
          <span className="text-xs sm:text-[11px] font-semibold text-[#f8fafc] truncate tracking-tight">
            {match.home} <span className="text-[#64748b] font-normal">–</span> {match.away}
          </span>
        </div>
      </div>

      {/* Action Buttons with 44px touch target on mobile and 22px on desktop */}
      <div className="grid grid-cols-3 gap-1.5 w-full sm:w-auto sm:flex sm:items-center sm:gap-1 flex-shrink-0">
        {options.map((opt, optIdx) => {
          const isSelected = match.picks.includes(opt);
          const oddPct = match.odds ? match.odds[optIdx] : 33.3;
          const isFavorite = oddPct >= 60.0;

          return (
            <button
              key={opt}
              data-testid={`btn-pick-${index}-${opt}`}
              onClick={() => togglePick(index, opt)}
              className={`min-h-[44px] h-[44px] sm:min-h-[34px] sm:h-[34px] lg:min-h-[22px] lg:h-[22px] min-w-[56px] lg:min-w-[50px] px-2 lg:px-1.5 text-xs lg:text-[10.5px] font-bold rounded flex items-center justify-center sm:justify-between gap-1 transition-all duration-100 active:scale-95 cursor-pointer select-none ${
                isSelected
                  ? 'bg-[#047857] text-[#ffffff] border border-[#10b981] shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                  : 'bg-[#0f172a] text-[#94a3b8] hover:text-[#f8fafc] border border-[#1e293b] hover:border-[#334155]'
              }`}
            >
              <div className="flex items-center gap-1">
                {isFavorite && (
                  <span 
                    className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-amber-300 shadow-[0_0_4px_#f59e0b]' : 'bg-amber-400/80 animate-pulse'}`}
                    title="Favori Karşılaşma (>%60)"
                  />
                )}
                <span className="text-xs lg:text-[11px] font-extrabold">{opt}</span>
              </div>
              <span className="font-mono tracking-tight text-[11px] lg:text-[9.5px] opacity-80">
                %{Math.round(oddPct)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
