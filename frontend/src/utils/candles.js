export const TIMEFRAMES = [
  { key: 'tick', label: 'Tick' },
  { key: '1m',   label: '1分' },
  { key: '5m',   label: '5分' },
  { key: '15m',  label: '15分' },
  { key: '30m',  label: '30分' },
  { key: '60m',  label: '60分' },
];

const INTERVAL_MS = {
  '1m':  60_000,
  '5m':  5  * 60_000,
  '15m': 15 * 60_000,
  '30m': 30 * 60_000,
  '60m': 60 * 60_000,
};

// tick 配列 → OHLC ローソク足配列
export function aggregateCandles(ticks, timeframeKey) {
  const ms = INTERVAL_MS[timeframeKey];
  if (!ms || !ticks.length) return [];

  const buckets = new Map();
  for (const tick of ticks) {
    const bucketTs = Math.floor(tick.ts / ms) * ms;
    if (!buckets.has(bucketTs)) {
      buckets.set(bucketTs, {
        ts: bucketTs,
        time: new Date(bucketTs).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }),
        open:  tick.price,
        high:  tick.price,
        low:   tick.price,
        close: tick.price,
      });
    } else {
      const c = buckets.get(bucketTs);
      if (tick.price > c.high) c.high = tick.price;
      if (tick.price < c.low)  c.low  = tick.price;
      c.close = tick.price;
    }
  }
  return Array.from(buckets.values()).sort((a, b) => a.ts - b.ts);
}

// ローソク足 → recharts 用スタックバーデータに変換
// 積み上げバー構造: invisible(底上げ) + lowerWick + body + upperWick
export function toCandleChartData(candles) {
  if (!candles.length) return { chartData: [], visibleMin: 0, domainMax: 1 };

  const allPrices = candles.flatMap(c => [c.high, c.low]);
  const dataMin = Math.min(...allPrices);
  const dataMax = Math.max(...allPrices);
  const padding = Math.max((dataMax - dataMin) * 0.1, 5);

  // visibleMin をベースに相対値へ変換（recharts スタックバーは 0 起点のため）
  const visibleMin = Math.floor(dataMin - padding);
  const domainMax  = Math.ceil(dataMax - visibleMin + padding);

  const chartData = candles.map(c => {
    const isUp       = c.close >= c.open;
    const bodyBottom = Math.min(c.open, c.close);
    const bodyTop    = Math.max(c.open, c.close);
    return {
      time:       c.time,
      isUp,
      open:  c.open,
      close: c.close,
      high:  c.high,
      low:   c.low,
      // スタックバー各セグメント（visibleMin 相対）
      invisible:  c.low - visibleMin,
      lowerWick:  bodyBottom - c.low,
      body:       Math.max(bodyTop - bodyBottom, 1), // doji は最低 1px
      upperWick:  c.high - bodyTop,
    };
  });

  return { chartData, visibleMin, domainMax };
}
