import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

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
      cache: 'no-store'
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
          program_info: {
            pNo: d.pNo,
            week: d.week,
            status: d.status
          },
          is_live: true
        });
      }
    }
  } catch (err: any) {
    console.warn("Live scores fetch error:", err?.message);
  }

  // Fallback for new week 358
  const fallback = [
    { no: 1, home: "Kasımpaşa A.Ş.", away: "Konyaspor", date: "18.09 20:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 2, home: "Kocaelispor", away: "Gaziantep F.K. A.Ş.", date: "18.09 20:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 3, home: "Çorum FK", away: "Alanyaspor", date: "19.09 17:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 4, home: "Başakşehir FK", away: "Gençlerbirliği", date: "19.09 17:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 5, home: "Trabzonspor A.Ş.", away: "Galatasaray A.Ş.", date: "19.09 20:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 6, home: "Erzurumspor FK", away: "Samsunspor A.Ş.", date: "19.09 20:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 7, home: "Fenerbahçe A.Ş.", away: "Eyüpspor", date: "20.09 17:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 8, home: "Amed Sportif Faliyetler", away: "Beşiktaş A.Ş.", date: "20.09 20:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 9, home: "Göztepe A.Ş.", away: "Çaykur Rizespor A.Ş.", date: "20.09 20:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 10, home: "Stuttgart", away: "B. Dortmund", date: "19.09 16:30", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 11, home: "B. Leverkusen", away: "Leipzig", date: "19.09 19:30", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 12, home: "Tottenham", away: "Aston Villa", date: "20.09 16:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 13, home: "Newcastle United", away: "Hull City", date: "20.09 18:30", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 14, home: "Atletico Madrid", away: "Real Madrid", date: "20.09 22:00", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
    { no: 15, home: "AS Roma", away: "Inter", date: "20.09 21:45", status: "NS" as const, minute: "-", score: "- - -", current_outcome: "-" as const, is_official: false },
  ];

  return NextResponse.json({
    success: true,
    matches: fallback,
    is_live: false
  });
}
