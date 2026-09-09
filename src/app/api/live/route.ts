import { NextResponse } from 'next/server';

const USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
];

export async function GET() {
  try {
    const ua = USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
    const res = await fetch("https://st.nesine.com/v1/Program", {
      headers: {
        'User-Agent': ua,
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.nesine.com',
        'Referer': 'https://www.nesine.com/sportoto',
      },
      next: { revalidate: 10 }
    });

    if (res.ok) {
      const data = await res.json();
      const d = data.d || {};
      const matches = d.matches || [];

      if (matches && matches.length >= 15) {
        const liveDetails = matches.slice(0, 15).map((m: any, idx: number) => {
          const resVal = String(m.result ?? '').trim().toUpperCase();
          const hs = m.homeScore;
          const as_ = m.awayScore;
          const minVal = m.minute || m.liveMinute || m.min || '-';

          let outcome: '1' | 'X' | '2' | '-' = '-';
          let status: 'NS' | 'LIVE' | 'HT' | 'FT' = 'NS';
          let minuteStr = minVal;
          let scoreStr = hs !== undefined && hs !== null && as_ !== undefined && as_ !== null ? `${hs} - ${as_}` : '- - -';

          if (['1', 'X', '2', '0'].includes(resVal)) {
            outcome = (resVal === '0' || resVal === 'X') ? 'X' : (resVal as any);
            status = 'FT';
            minuteStr = 'MS';
          } else if (hs !== undefined && as_ !== undefined && (hs > 0 || as_ > 0 || minVal !== '-')) {
            status = 'LIVE';
            if (hs > as_) outcome = '1';
            else if (hs < as_) outcome = '2';
            else outcome = 'X';
          }

          return {
            no: m.matchNo || (idx + 1),
            home: (m.homeTeam || '').replace(/[\r\n]+/g, ' ').trim(),
            away: (m.awayTeam || '').replace(/[\r\n]+/g, ' ').trim(),
            date: m.eventDate && m.eventTime ? `${m.eventDate.split('.').slice(0, 2).join('.')} ${m.eventTime}` : '',
            status,
            minute: minuteStr,
            score: scoreStr,
            current_outcome: outcome,
            is_official: status === 'FT'
          };
        });

        return NextResponse.json({
          success: true,
          matches: liveDetails,
          is_live: true
        });
      }
    }
  } catch (err: any) {
    console.warn("Live scores fetch error:", err?.message);
  }

  // Fallback default state
  const fallback = Array.from({ length: 15 }, (_, i) => ({
    no: i + 1,
    home: `Maç ${i + 1}`,
    away: `Rakip ${i + 1}`,
    date: '11.09 20:00',
    status: 'NS' as const,
    minute: '-',
    score: '- - -',
    current_outcome: '-' as const,
    is_official: false
  }));

  return NextResponse.json({
    success: true,
    matches: fallback,
    is_live: false
  });
}
