export const fmt = new Intl.NumberFormat('ja-JP');

export function fmtPrice(price, digits = 0) {
  if (price == null || price === 0) return '-';
  return new Intl.NumberFormat('ja-JP', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(price);
}

export function fmtChange(change, pct) {
  if (change == null) return '-';
  const sign = change >= 0 ? '+' : '';
  return `${sign}${fmtPrice(change)} (${sign}${(pct ?? 0).toFixed(2)}%)`;
}

export function fmtTime(isoStr) {
  if (!isoStr) return '-';
  return new Date(isoStr).toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function fmtVol(vol) {
  if (vol == null) return '-';
  if (vol >= 1_000_000) return `${(vol / 1_000_000).toFixed(1)}M`;
  if (vol >= 1_000) return `${(vol / 1_000).toFixed(1)}K`;
  return String(vol);
}

export function sideLabel(side) {
  return side === '1' ? '売り' : '買い';
}

export function orderTypeLabel(type) {
  if (type == null) return '-';
  const map = {
    // 株式
    1: '指値', 2: '成行', 13: '逆指値', 101: '逆指値(指)', 102: '逆指値(成)',
    // 先物
    20: '指値', 120: '成行', 18: '引成', 28: '引指', 30: '逆指値',
  };
  return map[Number(type)] ?? String(type);
}

export function orderStatusLabel(status) {
  const map = {
    1: '待機中', 2: '処理中', 3: '処理済', 4: '訂正取消送信中',
    5: '仮受付', 6: '受付', 7: '順番待ち', 8: '繰越注文', 9: '削除済',
  };
  return map[status] ?? String(status);
}
