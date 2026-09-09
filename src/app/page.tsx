'use client';

import React from 'react';
import { TotoProvider, useToto } from '../context/TotoContext';
import { MatchRow } from '../components/MatchRow';
import { SolverControls } from '../components/SolverControls';
import { PinGate } from '../components/PinGate';
import { VaultStation, BulletinStation, LiveStation, SaveCouponModal, NesineExportModal } from '../components';
import { AppTab } from '../types';

const navTabs: { id: AppTab; label: string; icon: string }[] = [
  { id: 'creator', label: 'Kupon Oluşturucu', icon: '🎯' },
  { id: 'bulletin', label: 'Canlı Bülten & Oran', icon: '📥' },
  { id: 'vault', label: 'Kuponlarım', icon: '💼' },
  { id: 'live', label: 'Canlı Maç Sonuçları', icon: '📊' },
];

const DashboardContent: React.FC = () => {
  const {
    matches,
    solution,
    targetColumns,
    selectedMode,
    estimates,
    rawPoolSize,
    solveWithStrategy,
    isSolving,
    programInfo,
    isLoadingBulletin,
    fetchLiveBulletin,
    selectedTab,
    setSelectedTab,
    toastMessage,
    setToastMessage,
    clearToast
  } = useToto();

  const [isSaveModalOpen, setIsSaveModalOpen] = React.useState<boolean>(false);
  const [isNesineModalOpen, setIsNesineModalOpen] = React.useState<boolean>(false);

  // Telemetry statistics: strictly dynamic based on active picks & chosen mode
  const currentEstimate = estimates.modes[selectedMode] || estimates.modes['13G'];
  const baselineCols = currentEstimate.columns;
  const totCols = solution ? solution.total_columns : baselineCols;
  const totSheets = Math.ceil(totCols / 4);
  const totCost = totCols * 10;
  const covPct = solution ? solution.coverage_pct : 100.0;

  const handleLock = () => {
    try {
      localStorage.removeItem('SUPER_TOTO_AUTH');
      window.location.reload();
    } catch {}
  };

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-[#06080e] text-[#f8fafc] flex flex-col font-sans select-none lg:h-screen lg:w-screen lg:overflow-hidden">
      {/* 1. Bloomberg-Style Quantitative Header Bar */}
      <header className="h-[44px] lg:h-[42px] px-3 sm:px-4 flex-shrink-0 bg-[#0a0f1d] border-b border-[#1e293b] flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5 sm:gap-2">
            <span className="text-xs sm:text-sm font-extrabold text-[#38bdf8] tracking-wider font-mono">
              ⚡ SÜPERTOTO
            </span>
            <span className="text-[9px] sm:text-[10px] font-extrabold text-emerald-400 bg-emerald-950/80 px-1.5 sm:px-2 py-0.5 rounded-full border border-emerald-500/50 font-mono">
              PRO TERMINAL
            </span>
          </div>
          <span className="text-[#64748b] text-xs hidden sm:inline">|</span>
          <span className="text-[11px] text-[#94a3b8] font-medium hidden md:inline">
            15 Maç Matematiksel Kalkan Kokpiti
          </span>
        </div>

        {/* Global Institutional Telemetry */}
        <div className="flex items-center gap-1.5 sm:gap-2 text-xs font-mono">
          <div className="hidden sm:flex items-center gap-1.5 bg-[#06080e] px-2.5 py-1 rounded border border-[#1e293b]">
            <span className="text-[#64748b]">Sistem:</span>
            <span className="text-emerald-400 font-extrabold">{totCols} Kolon</span>
            <span className="text-[#64748b]">({totCost.toLocaleString()} TL)</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 bg-[#06080e] px-2.5 py-1 rounded border border-[#1e293b]">
            <span className="text-[#64748b]">Kalkan:</span>
            <span className="text-cyan-400 font-bold">%{covPct.toFixed(1)}</span>
          </div>

          {/* Nesine Live Fetch Button */}
          <button
            onClick={() => fetchLiveBulletin()}
            disabled={isLoadingBulletin}
            title="Nesine'den Güncel Bülteni ve Oranları Çek"
            className="flex items-center gap-1 bg-[#0f172a] hover:bg-[#1e293b] text-emerald-400 hover:text-white px-2 sm:px-2.5 py-1 rounded border border-emerald-500/40 text-[10.5px] sm:text-[11px] font-bold transition cursor-pointer"
          >
            <span className={isLoadingBulletin ? "animate-spin inline-block" : ""}>🌐</span>
            <span className="hidden sm:inline">{isLoadingBulletin ? "Çekiliyor..." : "Bülteni Çek"}</span>
          </button>

          <a 
            href="https://www.nesine.com/sportoto" 
            target="_blank" 
            rel="noreferrer"
            className="flex items-center gap-1 bg-[#0f172a] hover:bg-[#1e293b] text-sky-400 hover:text-white px-2 sm:px-2.5 py-1 rounded border border-[#1e293b] text-[10.5px] sm:text-[11px] font-bold transition"
          >
            <span>Nesine</span>
            <span>↗</span>
          </a>

          <button
            onClick={handleLock}
            title="Terminali Kilitle"
            className="flex items-center gap-1 bg-[#1e131d] hover:bg-rose-950/60 text-rose-300 hover:text-white px-2 py-1 rounded border border-rose-900/40 text-[10.5px] sm:text-[11px] font-bold transition cursor-pointer"
          >
            <span>🔒</span>
            <span className="hidden sm:inline">Kilitle</span>
          </button>
        </div>
      </header>

      {/* 2. Four-Station Navigation Sub-Bar */}
      <nav className="bg-[#080d1a] border-b border-[#1e293b] px-3 sm:px-4 py-1.5 flex items-center justify-between gap-2 overflow-x-auto no-scrollbar flex-shrink-0">
        <div className="flex items-center gap-1 sm:gap-1.5 min-w-max">
          {navTabs.map(tab => {
            const isActive = selectedTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id)}
                className={`px-3 py-1 rounded-md text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  isActive
                    ? 'bg-[#1e293b] text-[#38bdf8] border border-[#38bdf8]/60 shadow-[0_0_10px_rgba(56,189,248,0.25)]'
                    : 'text-[#94a3b8] hover:text-white hover:bg-[#1e293b]/40 border border-transparent'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Global Institutional Telemetry in Nav */}
        <div className="hidden lg:flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1 text-[#94a3b8]">
            <span>Normal:</span>
            <span className="text-white font-bold">{(rawPoolSize * 10).toLocaleString()} TL</span>
          </div>
          <span className="text-[#334155]">|</span>
          <div className="flex items-center gap-1">
            <span className="text-[#64748b]">Sistem:</span>
            <span className="text-emerald-400 font-extrabold">{totCols} Kolon ({totCost.toLocaleString()} TL)</span>
            <span className="text-[#38bdf8]">({totSheets} Sayfa)</span>
          </div>
          <span className="text-[#334155]">|</span>
          <div className="flex items-center gap-1">
            <span className="text-[#64748b]">Kalkan:</span>
            <span className="text-cyan-400 font-bold">%{covPct.toFixed(1)}</span>
          </div>
        </div>
      </nav>

      {/* 3. Responsive Main Viewport */}
      <main className="flex-1 p-2 sm:p-2.5 flex flex-col pb-20 lg:pb-0 overflow-y-auto lg:overflow-hidden">
        {selectedTab === 'creator' && (
          <div className="flex-1 flex flex-col lg:grid lg:grid-cols-12 gap-2.5 overflow-hidden">
            {/* Left Column (7 cols on desktop): 15-Match Operational Matrix */}
            <section className="w-full lg:col-span-7 flex flex-col bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-2 sm:p-2.5 overflow-hidden shadow-sm">
              <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-[#1e293b]/80">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-extrabold uppercase tracking-wider text-[#38bdf8]">
                    📋 15 Maç Tercih Matrisi
                  </span>
                  <div className="flex items-center gap-1.5 text-[9.5px] font-mono text-[#94a3b8]">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
                    <span>Program #{programInfo?.pNo || '357'}</span>
                    <span>•</span>
                    <span>Hafta {programInfo?.week || '141236'}</span>
                  </div>
                </div>
                <div className="text-[9.5px] sm:text-[10px] font-mono text-[#64748b]">
                  <span className="lg:hidden">44px Dokunmatik Alan</span>
                  <span className="hidden lg:inline">Yükseklik: ~28px/maç (1080p Uyumlu)</span>
                </div>
              </div>

              {/* 15 Match Rows */}
              <div className="flex-1 flex flex-col gap-1 sm:gap-1 lg:justify-between overflow-hidden">
                {matches.map((m, idx) => (
                  <MatchRow key={m.id} match={m} index={idx} />
                ))}
              </div>
            </section>

            {/* Right Column (5 cols on desktop): Controls, Telemetry & Bookmarklet Dispatch */}
            <section className="w-full lg:col-span-5 flex flex-col gap-2.5 overflow-hidden">
              {/* Solver Controls Card */}
              <div className="flex-shrink-0">
                <SolverControls />
              </div>

              {/* Kuponlarım Transition CTA Card */}
              {solution && solution.total_columns > 0 ? (
                <div className="flex-1 bg-[#0a0f1d] border border-emerald-500/40 rounded-lg p-2.5 sm:p-3 flex flex-col justify-between shadow-lg overflow-y-auto">
                  <div className="flex flex-col gap-1.5 sm:gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        Sistem Kuponu Üretildi ({solution.solver_mode === 'base_only' ? 'Ekonomik' : 'Akıllı + Sürpriz'})
                      </span>
                      <span className="text-[11px] font-mono text-[#38bdf8] font-extrabold">
                        {totCols} Kolon / {totCost.toLocaleString()} TL
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-[#94a3b8] font-mono bg-[#06080e] px-2.5 py-1.5 rounded border border-[#1e293b]">
                      <span>Nesine Kupon Sayısı: <strong className="text-amber-300">{totSheets} Sayfa</strong> (40 TL)</span>
                      <span className="text-emerald-400 font-bold">Kalkan: %{covPct.toFixed(1)}</span>
                    </div>
                    <p className="text-[10px] text-[#94a3b8] leading-relaxed">
                      Kupon yapraklarını 10'lu paket dinlenmeli konsol betiğiyle doğrudan Nesine Kayıtlı Kuponlarım'a aktarabilir veya kupon havuzunuza kaydedebilirsiniz.
                    </p>
                  </div>
                  <div className="flex flex-col gap-1.5 mt-2">
                    <button
                      onClick={() => setIsNesineModalOpen(true)}
                      className="w-full py-2 px-3 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-xs rounded-lg shadow-md transition active:scale-98 cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <span>🚀</span>
                      <span>Nesine'ye Otomatik Aktar (10'lu Batch)</span>
                    </button>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setIsSaveModalOpen(true)}
                        className="flex-1 py-1.5 px-2 bg-[#0f172a] hover:bg-[#1e293b] text-sky-300 hover:text-white border border-[#1e293b] font-bold text-[11px] rounded-lg transition active:scale-98 cursor-pointer flex items-center justify-center gap-1"
                      >
                        <span>💾</span>
                        <span>Kuponu Kaydet</span>
                      </button>
                      <button
                        onClick={() => setSelectedTab('vault')}
                        className="flex-1 py-1.5 px-2 bg-[#06080e] hover:bg-[#1e293b] text-[#94a3b8] hover:text-white border border-[#1e293b] font-bold text-[11px] rounded-lg transition active:scale-98 cursor-pointer flex items-center justify-center gap-1"
                      >
                        <span>💼</span>
                        <span>Kuponlarım ({totSheets}S) ➔</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (


                <div className="flex-1 bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 flex flex-col justify-between text-xs text-[#94a3b8] overflow-hidden">
                  <div className="flex flex-col gap-1.5">
                    <div className="font-bold text-[#38bdf8] text-[11px] flex items-center gap-1.5">
                      <span>💡</span> Matematiksel Kalkan Kokpiti
                    </div>
                    <p className="text-[10.5px] leading-relaxed">
                      Sol taraftaki 15 maçlık matriste tercihlerinizi belirledikten sonra <b>[🛡️ Ekonomik]</b> veya <b>[🚀 Akıllı Sürpriz Avcısı]</b> butonuna basarak kuponunuzu oluşturun.
                    </p>
                    <p className="text-[10px] text-[#64748b]">
                      Üretilen kolonlar 40 TL'lik Nesine yapraklarına (A-B-C-D) paylaştırılarak <b>💼 Kuponlarım</b> istasyonunda eklentisiz Bookmarklet aktarımına hazır hale gelecektir.
                    </p>
                  </div>
                </div>
              )}

              {/* Bloomberg Status Bar */}
              <div className="h-[24px] px-2.5 bg-[#0a0f1d] border border-[#1e293b] rounded flex items-center justify-between text-[9px] font-mono text-[#64748b] flex-shrink-0">
                <span>● SÜPERTOTO: ONLINE</span>
                <span className="hidden sm:inline">MOD 4: ALIGNED</span>
                <span>STRATEGY: {solution?.solver_mode ? (solution.solver_mode === 'base_only' ? 'EKONOMİK' : 'AKILLI + SÜRPRİZ') : 'OTOMATİK'}</span>
                {solution?.booster_columns ? (
                  <span className="text-[#38bdf8] font-bold">SÜRPRİZ: +{solution.booster_columns}</span>
                ) : null}
                <span className="text-emerald-400">5/5 RULES: PASSED</span>
              </div>
            </section>
          </div>
        )}

        {selectedTab === 'bulletin' && <BulletinStation />}
        {selectedTab === 'vault' && <VaultStation />}
        {selectedTab === 'live' && <LiveStation />}
      </main>

      {/* 4. Global Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-16 lg:bottom-5 right-4 z-50 max-w-md bg-[#0f2820] border border-emerald-500/80 text-emerald-200 px-4 py-2.5 rounded-lg shadow-2xl flex items-center justify-between gap-3 animate-slide-up">
          <div className="flex items-center gap-2 text-xs font-semibold">
            <span className="text-emerald-400 text-sm">⚡</span>
            <span>{toastMessage}</span>
          </div>
          <button
            onClick={clearToast}
            className="text-emerald-400 hover:text-white font-bold text-xs cursor-pointer ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* 5. Mobile Sticky Summary & Quick Action Footer (< 1024px, only on creator tab) */}
      {selectedTab === 'creator' && (
        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#0a0f1d]/95 backdrop-blur-md border-t border-[#1e293b] px-3 py-2 flex items-center justify-between gap-2 shadow-2xl">
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-1.5 text-[11px] font-mono">
              <span className="text-[#94a3b8] text-[10px]">Normal:</span>
              <span className="text-[#f8fafc] font-bold">{(rawPoolSize * 10).toLocaleString()} TL</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-mono">
              <span className="text-[#94a3b8] text-[10px]">Sistem:</span>
              <span className="text-emerald-400 font-extrabold">{totCost.toLocaleString()} TL</span>
              <span className="text-[10px] text-[#38bdf8]">({totCols} K)</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            <button
              onClick={() => solveWithStrategy('base_only')}
              disabled={isSolving}
              className="px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-lg border bg-[#0b1b15] border-[#10b981]/70 text-[#34d399] hover:text-white font-extrabold text-[11px] active:scale-95 transition disabled:opacity-50 cursor-pointer"
            >
              {isSolving ? '...' : `🛡️ ${selectedMode}`}
            </button>
            <button
              onClick={() => solveWithStrategy('auto_boost')}
              disabled={isSolving}
              className="px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-lg border bg-[#0d1829] border-[#38bdf8]/70 text-[#38bdf8] hover:text-white font-extrabold text-[11px] active:scale-95 transition disabled:opacity-50 cursor-pointer"
            >
              {isSolving ? '...' : '🚀 Sürpriz'}
            </button>
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
        }}
      />

      {/* Nesine Direct 10-Batch Export Modal */}
      {solution && (
        <NesineExportModal
          isOpen={isNesineModalOpen}
          onClose={() => setIsNesineModalOpen(false)}
          columns={solution.compact_columns || solution.columns.map(c => c.join(''))}
          pno={programInfo?.pNo}
        />
      )}
    </div>
  );
};



export default function Page() {
  return (
    <PinGate>
      <TotoProvider>
        <DashboardContent />
      </TotoProvider>
    </PinGate>
  );
}
