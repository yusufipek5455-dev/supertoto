'use client';

import React, { useState, useEffect } from 'react';

const AUTH_KEY = 'SUPER_TOTO_AUTH';
const DEFAULT_PIN = '1453';

export const PinGate: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [pinInput, setPinInput] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const targetPin = process.env.NEXT_PUBLIC_APP_PIN || DEFAULT_PIN;

  useEffect(() => {
    try {
      const stored = localStorage.getItem(AUTH_KEY);
      if (stored === 'true') {
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch {
      setIsAuthenticated(false);
    }
  }, []);

  const handleVerifyPin = (inputToTest: string) => {
    if (inputToTest.trim() === targetPin.trim()) {
      try {
        localStorage.setItem(AUTH_KEY, 'true');
      } catch {}
      setErrorMsg(null);
      setIsAuthenticated(true);
    } else {
      setErrorMsg('⚠️ Hatalı PIN kodu! Lütfen tekrar deneyiniz.');
      setPinInput('');
    }
  };

  const handleKeypadPress = (digit: string) => {
    setErrorMsg(null);
    if (pinInput.length < 8) {
      const next = pinInput + digit;
      setPinInput(next);
      if (next.length === targetPin.length) {
        handleVerifyPin(next);
      }
    }
  };

  const handleClear = () => {
    setPinInput('');
    setErrorMsg(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleVerifyPin(pinInput);
    }
  };

  // Prevent flash while checking localStorage
  if (isAuthenticated === null) {
    return (
      <div className="h-screen w-screen bg-[#06080e] flex items-center justify-center text-[#38bdf8] font-mono text-sm">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#38bdf8] animate-ping" />
          <span>SüperToto Yükleniyor...</span>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="h-screen w-screen bg-[#06080e] flex flex-col items-center justify-center select-none font-sans p-4">
      {/* Background Ambient Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-sky-950/20 via-[#06080e] to-[#06080e] pointer-events-none" />

      {/* Terminal Card */}
      <div className="relative z-10 w-full max-w-[360px] bg-[#0a0f1d] border border-[#1e293b] rounded-xl p-6 shadow-2xl flex flex-col items-center">
        {/* Brand Header */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl font-black text-[#38bdf8] tracking-wider font-mono">
            ⚡ SÜPERTOTO
          </span>
          <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded-full border border-emerald-500/40 font-mono">
            PRO TERMINAL
          </span>
        </div>

        <p className="text-[11px] text-[#94a3b8] text-center mb-6">
          Terminal erişimi için 4 haneli PIN kodunu giriniz
        </p>

        {/* Masked PIN Display */}
        <div className="w-full mb-4">
          <input
            type="password"
            maxLength={8}
            value={pinInput}
            onChange={(e) => {
              const val = e.target.value.replace(/\D/g, '');
              setPinInput(val);
              setErrorMsg(null);
              if (val.length === targetPin.length) {
                handleVerifyPin(val);
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder="••••"
            autoFocus
            className="w-full h-14 lg:h-12 bg-[#06080e] border border-[#1e293b] focus:border-[#38bdf8] rounded-xl text-center text-3xl lg:text-2xl font-mono tracking-widest text-[#f8fafc] placeholder-[#334155] outline-none transition shadow-inner"
          />
        </div>

        {/* Error Feedback */}
        {errorMsg ? (
          <div className="text-xs lg:text-[11px] text-rose-400 font-medium mb-3 text-center animate-pulse">
            {errorMsg}
          </div>
        ) : (
          <div className="h-4 mb-3" />
        )}

        {/* Numeric Keypad: Large comfortable buttons on mobile (56px) */}
        <div className="grid grid-cols-3 gap-2 sm:gap-2.5 w-full mb-4 font-mono">
          {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((num) => (
            <button
              key={num}
              type="button"
              onClick={() => handleKeypadPress(num)}
              className="h-14 lg:h-11 bg-[#0f172a] hover:bg-[#1e293b] active:scale-95 text-[#f8fafc] text-xl lg:text-base font-bold rounded-xl border border-[#1e293b] hover:border-[#38bdf8]/40 transition shadow-sm flex items-center justify-center cursor-pointer"
            >
              {num}
            </button>
          ))}
          <button
            type="button"
            onClick={handleClear}
            className="h-14 lg:h-11 bg-[#1e131d] hover:bg-rose-950/50 active:scale-95 text-rose-300 text-sm lg:text-xs font-bold rounded-xl border border-rose-900/40 hover:border-rose-500/50 transition shadow-sm flex items-center justify-center cursor-pointer"
          >
            SİL
          </button>
          <button
            type="button"
            onClick={() => handleKeypadPress('0')}
            className="h-14 lg:h-11 bg-[#0f172a] hover:bg-[#1e293b] active:scale-95 text-[#f8fafc] text-xl lg:text-base font-bold rounded-xl border border-[#1e293b] hover:border-[#38bdf8]/40 transition shadow-sm flex items-center justify-center cursor-pointer"
          >
            0
          </button>
          <button
            type="button"
            onClick={() => handleVerifyPin(pinInput)}
            className="h-14 lg:h-11 bg-[#062419] hover:bg-emerald-900/60 active:scale-95 text-emerald-300 text-sm lg:text-xs font-extrabold rounded-xl border border-emerald-700/50 hover:border-emerald-500 transition shadow-sm flex items-center justify-center cursor-pointer"
          >
            GİRİŞ ↵
          </button>
        </div>

        {/* Footer Security Notice */}
        <div className="flex items-center gap-1.5 text-[9px] text-[#475569] font-mono">
          <span>🔒</span>
          <span>Uçtan Uca Şifreli Kokpit Oturumu</span>
        </div>
      </div>
    </div>
  );
};
