import { SavedCoupon, GuaranteeMode } from '../types';

export const SAVED_COUPONS_STORAGE_KEY = 'supertoto_saved_coupons';
export const SAVED_COUPONS_EVENT = 'supertoto_coupons_changed';

/**
 * Retrieves all saved coupons from localStorage, sorted by creation date descending.
 */
export function getSavedCoupons(): SavedCoupon[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(SAVED_COUPONS_STORAGE_KEY);
    if (!raw) return [];
    const list = JSON.parse(raw);
    if (!Array.isArray(list)) return [];
    return list;
  } catch (err) {
    console.warn('Failed to parse saved coupons from localStorage:', err);
    return [];
  }
}

/**
 * Saves a new coupon into localStorage and dispatches a change event.
 */
export function saveCoupon(payload: {
  name: string;
  week: string | number;
  columnsCount: number;
  columns: string[][];
  compact_columns?: string[];
  mode?: GuaranteeMode;
  total_cost?: number;
}): SavedCoupon {
  const newCoupon: SavedCoupon = {
    id: `coupon_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    name: payload.name.trim() || `Kupon - ${payload.columnsCount} Kolon`,
    createdAt: new Date().toISOString(),
    week: payload.week || '141236',
    columnsCount: payload.columnsCount,
    columns: payload.columns,
    compact_columns: payload.compact_columns,
    mode: payload.mode || '13G',
    total_cost: payload.total_cost || payload.columnsCount * 10
  };

  const current = getSavedCoupons();
  const updated = [newCoupon, ...current];

  try {
    localStorage.setItem(SAVED_COUPONS_STORAGE_KEY, JSON.stringify(updated));
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event(SAVED_COUPONS_EVENT));
    }
  } catch (err) {
    console.error('Failed to save coupon to localStorage:', err);
  }

  return newCoupon;
}

/**
 * Deletes a coupon by ID from localStorage and dispatches a change event.
 */
export function deleteSavedCoupon(id: string): SavedCoupon[] {
  const current = getSavedCoupons();
  const updated = current.filter(c => c.id !== id);

  try {
    localStorage.setItem(SAVED_COUPONS_STORAGE_KEY, JSON.stringify(updated));
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event(SAVED_COUPONS_EVENT));
    }
  } catch (err) {
    console.error('Failed to delete coupon from localStorage:', err);
  }

  return updated;
}
