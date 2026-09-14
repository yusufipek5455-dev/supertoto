/**
 * Gerçekçi ve Veriye Dayalı Spor Toto İkramiye Hesaplama Motoru (Pari-Mutuel Havuz Modeli)
 *
 * Formülasyon ve Kurallar:
 * 1. Hasılat ve Havuz Mantığı:
 *    - Toplam hasılatın %55'i ikramiye havuzudur (Kolon bedeli: 10 TL).
 *    - Kategori Dağılımları:
 *      * 15 Bilenler: %35 (+ Varsa devir tutarı)
 *      * 14 Bilenler: %20
 *      * 13 Bilenler: %20
 *      * 12 Bilenler: %25
 * 2. Dinamik Hacim (Pazar Büyüklüğü):
 *    - Normal Hafta (Devirsiz): ~4.5 Milyon kolon (45 Milyon TL hasılat)
 *    - 1 Devirli Hafta: ~8 Milyon kolon (80 Milyon TL hasılat)
 *    - 2+ Devirli Rekor Hafta: ~13 Milyon kolon (130 Milyon TL hasılat)
 * 3. Kupon Popülerliği ve Kazanan Sayısı Tahmini:
 *    - Maçların halk tercih yüzdeleri çarpılarak kuponun oynanma olasılığı P(Kupon) = ∏ P_i
 *    - Beklenen 15 bilen sayısı: λ_15 = Toplam Kolon × P(Kupon)
 *    - Kişi başı ikramiye: Kategori Havuzu / max(1, Beklenen Kazanan)
 *    - Eğer λ_15 < 0.5 ise "Devir Olasılığı Yüksek" rozeti çıkar.
 *    - 14, 13 ve 12 kademeleri popülerlik sapmasına dayalı kombinatorik dağılımla hesaplanır.
 */

export interface MatchProbability {
  '1': number;
  'X': number;
  '2': number;
}

export type VolumePresetKey = 'normal' | 'single_devir' | 'record_devir' | 'custom';

export interface VolumePreset {
  key: VolumePresetKey;
  label: string;
  badge: string;
  columns: number;
  revenue: number;
  defaultCarryover: number;
  description: string;
}

export const VOLUME_PRESETS: Record<Exclude<VolumePresetKey, 'custom'>, VolumePreset> = {
  normal: {
    key: 'normal',
    label: 'Normal Hafta',
    badge: '45M',
    columns: 4500000,
    revenue: 45000000,
    defaultCarryover: 0,
    description: 'Devirsiz • ~4.5M Kolon (45M TL Hasılat)'
  },
  single_devir: {
    key: 'single_devir',
    label: '1 Devirli Hafta',
    badge: '80M',
    columns: 8000000,
    revenue: 80000000,
    defaultCarryover: 7500000,
    description: '1 Devir • ~8M Kolon (80M TL Hasılat + 7.5M Devir)'
  },
  record_devir: {
    key: 'record_devir',
    label: '2+ Devirli Rekor',
    badge: '130M',
    columns: 13000000,
    revenue: 130000000,
    defaultCarryover: 25000000,
    description: '2+ Devir • ~13M Kolon (130M TL Hasılat + 25M Devir)'
  }
};

export interface RealisticPrizeTier {
  expectedWinners: string;
  rawWinners: number;
  estimatedPrize: string;
  rawPrize: number;
  isDevir?: boolean;
}

export interface RealisticPrizeResult {
  couponPopularityScore: string;
  couponProbability: number;
  totalColumnsPlayed: number;
  totalPrizePool: number;
  pools: {
    15: number;
    14: number;
    13: number;
    12: number;
  };
  tier15: RealisticPrizeTier;
  tier14: RealisticPrizeTier;
  tier13: RealisticPrizeTier;
  tier12: RealisticPrizeTier;
  climateBadge: string;
  climateColor: string;
  isHighDevirRisk: boolean;
}

export interface CalculateRealisticPrizeParams {
  couponChoices: string;                 // 15 karakter string: "121121212221222"
  matchProbabilities: MatchProbability[]; // 15 elemanlı dizi: [{ '1': 0.65, 'X': 0.20, '2': 0.15 }, ...]
  totalRevenue?: number;                 // Haftalık hasılat (TL) - Varsayılan: 45.000.000 TL
  carryover?: number;                    // 15 devir tutarı (TL) - Varsayılan: 0 TL
}

export function formatPrizeTL(val: number): string {
  return new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 }).format(Math.round(val)) + " TL";
}

export function calculateRealisticPrize({
  couponChoices,
  matchProbabilities,
  totalRevenue = 45000000,
  carryover = 0
}: CalculateRealisticPrizeParams): RealisticPrizeResult {
  const columnPrice = 10; // Kolon bedeli (TL)
  const totalColumnsPlayed = Math.max(1, totalRevenue / columnPrice); // Oynanan toplam kolon
  const totalPrizePool = totalRevenue * 0.55; // İkramiye havuzu (%55)

  // Kategori havuzları
  const pools = {
    15: (totalPrizePool * 0.35) + carryover,
    14: totalPrizePool * 0.20,
    13: totalPrizePool * 0.20,
    12: totalPrizePool * 0.25
  };

  // Kuponun gerçekleşme olasılığı (Halk tercih yüzdelerinin çarpımı: P(Kupon) = ∏ P_i)
  let couponPopularity = 1;
  const probs: number[] = [];

  for (let i = 0; i < 15; i++) {
    const choice = (couponChoices[i] || '1') as '1' | 'X' | '2';
    const matchProbs = matchProbabilities[i] || { '1': 0.33, 'X': 0.33, '2': 0.34 };
    const p = matchProbs[choice] || 0.33;
    probs.push(p);
    couponPopularity *= p;
  }

  // Beklenen 15 bilen sayısı (λ_15 = Toplam Kolon × P(Kupon))
  const expectedWinners15 = Math.max(0.01, totalColumnsPlayed * couponPopularity);
  const isHighDevirRisk = expectedWinners15 < 0.5;

  // 14, 13, 12 kademeleri kombinatorik tahminleri
  const avgP = probs.reduce((a, b) => a + b, 0) / 15;
  const expectedWinners14 = Math.max(1, totalColumnsPlayed * (couponPopularity / avgP) * (1 - avgP) * 15);
  const expectedWinners13 = Math.max(10, expectedWinners14 * 12);
  const expectedWinners12 = Math.max(100, expectedWinners13 * 10);

  // İklim Başlığı ve Renk Belirleme
  let climateBadge = '⚖️ DENGELİ HAVUZ';
  let climateColor = 'text-[#38bdf8]';

  if (isHighDevirRisk) {
    climateBadge = '🔥 DEVİR OLASILIĞI YÜKSEK';
    climateColor = 'text-rose-400 animate-pulse';
  } else if (expectedWinners15 < 5) {
    climateBadge = '⚡ ÇOK YÜKSEK İKRAMİYE';
    climateColor = 'text-amber-400';
  } else if (expectedWinners15 < 50) {
    climateBadge = '✨ YÜKSEK İKRAMİYE POTANSİYELİ';
    climateColor = 'text-yellow-400';
  } else if (expectedWinners15 < 500) {
    climateBadge = '⚖️ DENGELİ HAVUZ';
    climateColor = 'text-[#38bdf8]';
  } else {
    climateBadge = '📉 POPÜLER / DÜŞÜK HAVUZ';
    climateColor = 'text-slate-400';
  }

  return {
    couponPopularityScore: (couponPopularity * 1e8).toFixed(2),
    couponProbability: couponPopularity,
    totalColumnsPlayed,
    totalPrizePool,
    pools,
    climateBadge,
    climateColor,
    isHighDevirRisk,
    tier15: {
      expectedWinners: isHighDevirRisk ? "0 - 1 (Devir Olasılığı Yüksek)" : Math.round(expectedWinners15).toLocaleString('tr-TR'),
      rawWinners: expectedWinners15,
      estimatedPrize: formatPrizeTL(pools[15] / Math.max(1, expectedWinners15)),
      rawPrize: pools[15] / Math.max(1, expectedWinners15),
      isDevir: isHighDevirRisk
    },
    tier14: {
      expectedWinners: Math.round(expectedWinners14).toLocaleString('tr-TR'),
      rawWinners: expectedWinners14,
      estimatedPrize: formatPrizeTL(pools[14] / Math.max(1, expectedWinners14)),
      rawPrize: pools[14] / Math.max(1, expectedWinners14)
    },
    tier13: {
      expectedWinners: Math.round(expectedWinners13).toLocaleString('tr-TR'),
      rawWinners: expectedWinners13,
      estimatedPrize: formatPrizeTL(pools[13] / Math.max(1, expectedWinners13)),
      rawPrize: pools[13] / Math.max(1, expectedWinners13)
    },
    tier12: {
      expectedWinners: Math.round(expectedWinners12).toLocaleString('tr-TR'),
      rawWinners: expectedWinners12,
      estimatedPrize: formatPrizeTL(pools[12] / Math.max(1, expectedWinners12)),
      rawPrize: pools[12] / Math.max(1, expectedWinners12)
    }
  };
}
