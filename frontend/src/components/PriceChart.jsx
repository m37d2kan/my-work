import { useState } from 'react';
import {
  AreaChart, Area,
  BarChart, Bar, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { fmtPrice } from '../utils/format';
import { TIMEFRAMES, aggregateCandles, toCandleChartData } from '../utils/candles';

// ─── Tick ツールチップ ─────────────────────────────────────────────────────────
const TickTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div>{payload[0]?.payload?.time}</div>
      <div className="chart-tooltip-price">{fmtPrice(payload[0]?.value)}</div>
    </div>
  );
};

// ─── ローソク足ツールチップ ────────────────────────────────────────────────────
const CandleTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  const col = d.isUp ? 'var(--green)' : 'var(--red)';
  return (
    <div className="chart-tooltip">
      <div>{d.time}</div>
      <div style={{ color: col }}>始: {fmtPrice(d.open)}</div>
      <div style={{ color: 'var(--green)' }}>高: {fmtPrice(d.high)}</div>
      <div style={{ color: 'var(--red)' }}>安: {fmtPrice(d.low)}</div>
      <div className="chart-tooltip-price" style={{ color: col }}>終: {fmtPrice(d.close)}</div>
    </div>
  );
};

// ─── ヒゲを細い線で描画するカスタムシェイプ ─────────────────────────────────────
const WickShape = ({ x, y, width, height, payload }) => {
  if (!height || height <= 0) return null;
  const cx = Math.round(x + width / 2);
  const color = payload?.isUp ? '#3fb950' : '#f85149';
  return (
    <line
      x1={cx} y1={Math.round(y)}
      x2={cx} y2={Math.round(y + height)}
      stroke={color} strokeWidth={1.5}
    />
  );
};

// ─── メインコンポーネント ──────────────────────────────────────────────────────
export default function PriceChart({ data }) {
  const [timeframe, setTimeframe] = useState('tick');

  const isCandle = timeframe !== 'tick';
  const candles = isCandle ? aggregateCandles(data, timeframe) : [];
  const { chartData, visibleMin, domainMax } = isCandle
    ? toCandleChartData(candles)
    : { chartData: [], visibleMin: 0, domainMax: 1 };

  // ── Tick チャート用 ─────────────────────────────────────────────────────────
  const prices = data.map(d => d.price);
  const pMin = prices.length ? Math.min(...prices) : 0;
  const pMax = prices.length ? Math.max(...prices) : 0;
  const pPad = Math.max((pMax - pMin) * 0.1, 5);
  const tickDomain = [Math.floor(pMin - pPad), Math.ceil(pMax + pPad)];
  const tickInterval = Math.max(1, Math.floor(data.length / 8));

  // ── ローソク足チャート用 ────────────────────────────────────────────────────
  const candleInterval = Math.max(1, Math.floor(chartData.length / 6));

  const isEmpty = isCandle ? !chartData.length : !data.length;

  return (
    <div className="card price-chart">
      <div className="card-title">
        価格チャート
        <span className="chart-count">
          {isCandle ? ` ${candles.length}本` : ` ${data.length} tick`}
        </span>
        <div className="tf-buttons">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf.key}
              className={`tf-btn${timeframe === tf.key ? ' active' : ''}`}
              onClick={() => setTimeframe(tf.key)}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {isEmpty ? (
        <div className="loading">データ待ち...</div>
      ) : isCandle ? (
        /* ── ローソク足チャート ──────────────────────────────────────────────── */
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 4 }} barCategoryGap="20%">
            <XAxis
              dataKey="time"
              tick={{ fill: '#8b949e', fontSize: 10 }}
              interval={candleInterval}
              tickLine={false}
              axisLine={{ stroke: '#30363d' }}
            />
            <YAxis
              domain={[0, domainMax]}
              tick={{ fill: '#8b949e', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => fmtPrice(v + visibleMin)}
              width={65}
            />
            <Tooltip content={<CandleTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
            {/* 底上げ（透明スペーサー） */}
            <Bar dataKey="invisible" stackId="c" fill="transparent" isAnimationActive={false} />
            {/* 下ヒゲ */}
            <Bar dataKey="lowerWick" stackId="c" isAnimationActive={false} shape={<WickShape />} />
            {/* ボディ */}
            <Bar dataKey="body" stackId="c" isAnimationActive={false} minPointSize={1}>
              {chartData.map((d, i) => (
                <Cell key={i} fill={d.isUp ? '#3fb950' : '#f85149'} />
              ))}
            </Bar>
            {/* 上ヒゲ */}
            <Bar dataKey="upperWick" stackId="c" isAnimationActive={false} shape={<WickShape />} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        /* ── Tick エリアチャート ─────────────────────────────────────────────── */
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 4 }}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#58a6ff" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#58a6ff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              tick={{ fill: '#8b949e', fontSize: 10 }}
              interval={tickInterval}
              tickLine={false}
              axisLine={{ stroke: '#30363d' }}
            />
            <YAxis
              domain={tickDomain}
              tick={{ fill: '#8b949e', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => fmtPrice(v)}
              width={65}
            />
            <Tooltip content={<TickTooltip />} />
            <ReferenceLine y={(pMin + pMax) / 2} stroke="#30363d" strokeDasharray="3 3" />
            <Area
              type="monotone"
              dataKey="price"
              stroke="#58a6ff"
              strokeWidth={1.5}
              fill="url(#priceGradient)"
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
