import React, { useMemo, useState } from 'react';
import { useToto } from '../context/TotoContext';

export interface BookmarkletButtonProps {
  initialDelay?: number;
}

/**
 * Builds the minified bookmarklet code string injecting the dynamic NETWORK_DELAY.
 * Begins strictly with: javascript:(async function()
 * Includes clipboard fallback handling via prompt().
 */
export function generateBookmarkletCode(networkDelay: number = 750, compactCols?: string[]): string {
  const embeddedCols = compactCols && compactCols.length > 0 ? JSON.stringify(compactCols) : 'null';
  return `javascript:(async function(){const EMBEDDED=${embeddedCols};const NETWORK_DELAY=${networkDelay};const sleep=ms=>new Promise(r=>setTimeout(r,ms));const dispatch=el=>{if(!el)return;['mouseover','mousedown','click','mouseup','change'].forEach(e=>el.dispatchEvent(new MouseEvent(e,{bubbles:true,cancelable:true})));};function findAddBtn(){const els=Array.from(document.querySelectorAll('button,a,div[role="button"]'));const match=els.find(el=>{(el.innerText||'').toLocaleLowerCase('tr-TR').trim().includes('sepete ekle')||(el.innerText||'').toLocaleLowerCase('tr-TR').trim().includes('hemen oyna');});return match||document.querySelector('.btn-add-basket,#btnSaveCoupon,button[data-action="add-basket"]');}let payload=null;if(EMBEDDED&&Array.isArray(EMBEDDED)&&EMBEDDED.length>0){payload={compact:true,cols:EMBEDDED};}else{let raw='';try{raw=await navigator.clipboard.readText();}catch(err){raw=prompt('Panoya erisilemedi. Lutfen kupon JSON kodunu buraya yapistiriniz:');}if(!raw)return alert('Kupon verisi bulunamadi!');try{payload=JSON.parse(raw);}catch(e){return alert('Panodaki veri gecerli bir kupon JSONi degil!');}}let sheets=[];if(payload.sheets&&Array.isArray(payload.sheets)){sheets=payload.sheets;}else if(payload.compact&&Array.isArray(payload.cols)){const tot=Math.ceil(payload.cols.length/4);for(let s=0;s<tot;s++){sheets.push({A:payload.cols[s*4]||[],B:payload.cols[s*4+1]||[],C:payload.cols[s*4+2]||[],D:payload.cols[s*4+3]||[]});}}else if(Array.isArray(payload)){const tot=Math.ceil(payload.length/4);for(let s=0;s<tot;s++){sheets.push({A:payload[s*4]||[],B:payload[s*4+1]||[],C:payload[s*4+2]||[],D:payload[s*4+3]||[]});}}if(sheets.length===0)return alert('Kupon yapragi bulunamadi!');if(!confirm(sheets.length*40+' TL ('+(sheets.length*4)+' kolon) Nesine sepetine yuklensin mi?'))return;const letters=['A','B','C','D'];for(let s=0;s<sheets.length;s++){const sheet=sheets[s];for(let l=0;l<letters.length;l++){const char=letters[l];const picks=sheet[char];if(!picks)continue;for(let m=0;m<15;m++){const pick=picks[m];if(!pick)continue;const btn=document.querySelector('[data-mno="'+(m+1)+'"][data-col="'+char+'"][data-val="'+pick+'"]')||document.querySelector('input[data-m="'+(m+1)+'"][data-c="'+char+'"][data-v="'+pick+'"]')||document.querySelector('[data-match-index="'+m+'"][data-column="'+char+'"][data-choice="'+pick+'"]');if(btn){if(m===10)btn.scrollIntoView({behavior:'instant',block:'center'});dispatch(btn);await sleep(20);}}}await sleep(Math.floor(NETWORK_DELAY/2));if(s<sheets.length-1){const addBtn=findAddBtn();if(!addBtn)return alert('HATA: Sepete Ekle bulunamadi!');dispatch(addBtn);await sleep(NETWORK_DELAY);}}alert('✅ '+(sheets.length*40)+' TL kupon basariyla yuklendi!');})();`;
}

export const BookmarkletButton: React.FC<BookmarkletButtonProps> = ({ initialDelay }) => {
  const { networkDelay, setNetworkDelay, solution, setToastMessage, setSelectedTab } = useToto();
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  const activeDelay = initialDelay ?? networkDelay;

  const bookmarkletCode = useMemo(() => {
    return generateBookmarkletCode(activeDelay, solution?.compact_columns);
  }, [activeDelay, solution]);

  const handleCopyPlainText = () => {
    let textLines: string[] = [];
    if (solution?.compact_columns && solution.compact_columns.length > 0) {
      textLines = solution.compact_columns;
    } else if (solution?.columns && solution.columns.length > 0) {
      textLines = solution.columns.map(c => c.join(''));
    } else if (solution?.sheets && solution.sheets.length > 0) {
      for (const s of solution.sheets) {
        for (const l of ['A', 'B', 'C', 'D'] as const) {
          if (s[l]) textLines.push(s[l].join(''));
        }
      }
    }

    if (textLines.length === 0) {
      setToastMessage("Henüz üretilmiş kupon bulunmuyor!");
      return;
    }

    const plainText = textLines.join('\n');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(plainText).then(() => {
        setCopiedText(true);
        setToastMessage("Kolonlar panoya kopyalandı.");
        setTimeout(() => setCopiedText(false), 2500);
      }).catch(() => {
        setCopiedText(true);
        setToastMessage("Kolonlar panoya kopyalandı.");
        setTimeout(() => setCopiedText(false), 2500);
      });
    } else {
      prompt("Kupon metnini kopyalayın:", plainText);
      setToastMessage("Kolonlar panoya kopyalandı.");
    }
  };

  const handleCopyCode = () => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(bookmarkletCode)
        .then(() => {
          setCopiedCode(true);
          setTimeout(() => setCopiedCode(false), 2000);
        })
        .catch(() => prompt("Kodu kopyalamak için Ctrl+C yapın:", bookmarkletCode));
    } else {
      prompt("Kodu kopyalamak için Ctrl+C yapın:", bookmarkletCode);
    }
  };

  const handleCopyJson = () => {
    const payloadStr = JSON.stringify(solution || { note: "Kupon bulunamadı" });
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(payloadStr)
        .then(() => {
          setCopiedJson(true);
          setTimeout(() => setCopiedJson(false), 2000);
        })
        .catch(() => prompt("JSON kodunu kopyalayın:", payloadStr));
    } else {
      prompt("JSON kodunu kopyalayın:", payloadStr);
    }
  };

  return (
    <div className="bg-[#0a0f1d] border border-[#1e293b] rounded-lg p-3 select-none text-xs">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-[11px] font-extrabold text-[#38bdf8] flex items-center gap-1.5 uppercase tracking-wide">
          <span>📌</span> Eklentisiz Nesine Köprüsü (Bookmarklet)
        </h4>
        <span className="text-[9.5px] font-mono text-[#64748b] bg-[#06080e] px-1.5 py-0.5 rounded border border-[#1e293b]">
          v3.6 Native
        </span>
      </div>

      {/* Lag Shield (Micro-slider with badge) */}
      <div className="bg-[#06080e] border border-[#1e293b] rounded p-2 mb-2.5">
        <div className="flex items-center justify-between gap-2 mb-1">
          <label htmlFor="network-delay-slider" className="text-[10px] font-bold text-[#cbd5e1] flex items-center gap-1">
            <span>⚡ Ağ Gecikmesi (Lag Shield):</span>
          </label>
          <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-950/40 px-1.5 py-0.2 rounded border border-amber-800/40">
            {activeDelay} ms
          </span>
        </div>

        <input
          id="network-delay-slider"
          type="range"
          min={650}
          max={1200}
          step={25}
          value={activeDelay}
          onChange={(e) => setNetworkDelay(Number(e.target.value))}
          className="w-full h-1 bg-[#1e293b] rounded-lg appearance-none cursor-pointer accent-amber-400"
        />

        <p className="text-[9px] text-[#64748b] mt-1 leading-snug">
          💡 <i>Yavaş internet veya yoğun saatlerde sepetin kaçırılmaması için gecikmeyi artırabilirsiniz.</i>
        </p>
      </div>

      {/* Mobile-Friendly Plain Text Copy Button (< 1024px) */}
      <div className="flex lg:hidden mb-2">
        <button
          id="btn-copy-mobile-text"
          onClick={handleCopyPlainText}
          className="w-full h-[38px] bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-500 hover:to-teal-600 active:scale-98 text-white text-xs font-bold px-3 rounded-lg shadow-md border border-emerald-400/60 flex items-center justify-center gap-2 transition cursor-pointer"
        >
          <span>📱</span>
          <span>{copiedText ? "✓ Kolonlar Panoya Kopyalandı!" : "Kuponları Kopyala (Metin)"}</span>
        </button>
      </div>

      {/* Action Buttons Bar */}
      <div className="grid grid-cols-12 gap-1.5 items-center">
        {/* Desktop-Only Hardware Token Draggable Pill (>= 1024px) */}
        <a
          id="bookmarklet-link"
          href={bookmarkletCode}
          draggable="true"
          onClick={(e) => {
            e.preventDefault();
            alert("Bu butona doğrudan tıklamayın!\n\nFareyle tutup tarayıcınızın üstündeki Yer İmleri çubuğuna sürükleyip bırakın.");
          }}
          className="hidden lg:flex col-span-6 items-center justify-center gap-1.5 h-[30px] bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-500 hover:to-sky-600 text-white text-[11px] font-bold px-2 rounded-md shadow-md border border-sky-400/80 cursor-grab active:cursor-grabbing transition text-center tracking-tight"
          title="Yer İmleri çubuğuna sürükleyin"
        >
          <span>📌</span>
          <span>Nesine'ye Aktar</span>
        </a>

        {/* Copy JSON button with instant checkmark feedback */}
        <button
          id="btn-copy-json"
          onClick={handleCopyJson}
          className="col-span-6 lg:col-span-3 h-[32px] lg:h-[30px] bg-[#0f172a] hover:bg-[#1e293b] text-[#cbd5e1] hover:text-white text-xs lg:text-[10.5px] font-semibold rounded-md border border-[#1e293b] hover:border-[#38bdf8]/60 transition flex items-center justify-center gap-1 cursor-pointer"
          title="Kupon JSON kodunu kopyalar"
        >
          {copiedJson ? (
            <span className="text-emerald-400 font-bold flex items-center gap-0.5">
              ✓ Kopyalandı
            </span>
          ) : (
            <span>📄 JSON Kodu</span>
          )}
        </button>

        {/* Copy Bookmarklet Code button */}
        <button
          id="btn-copy-bookmarklet"
          onClick={handleCopyCode}
          className="col-span-6 lg:col-span-3 h-[32px] lg:h-[30px] bg-[#0f172a] hover:bg-[#1e293b] text-[#cbd5e1] hover:text-white text-xs lg:text-[10.5px] font-semibold rounded-md border border-[#1e293b] hover:border-[#38bdf8]/60 transition flex items-center justify-center gap-1 cursor-pointer"
          title="Yer imi kodunu kopyalar"
        >
          {copiedCode ? (
            <span className="text-emerald-400 font-bold flex items-center gap-0.5">
              ✓ Kopyalandı
            </span>
          ) : (
            <span>📋 Yer İmi Kodu</span>
          )}
        </button>
      </div>

      <div className="hidden lg:block text-[9px] text-[#64748b] mt-2 text-center">
        <b>3 Adımda:</b> 1. Yer İmlerine sürükle • 2. Kuponu hazırla • 3. Nesine sekmesinde tıkla!
      </div>
      <div className="block lg:hidden text-[9.5px] text-[#64748b] mt-1.5 text-center">
        💡 Kuponları kopyalayıp Nesine mobil sepetine kolayca yapıştırabilirsiniz.
      </div>
    </div>
  );
};
