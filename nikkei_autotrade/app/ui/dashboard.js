// ── ステータスポーリング ──
async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const d = await res.json();
    updateHeader(d);
    updateStrategy(d);
    updatePosition(d);
  } catch (e) {
    console.error('fetchStatus error', e);
  }
}

function updateHeader(d) {
  setBadge('badge-api', d.api_connected, 'API');
  setBadge('badge-push', d.push_connected, 'PUSH');

  const autoEl = document.getElementById('badge-auto');
  autoEl.textContent = 'AUTO: ' + (d.auto_enabled ? 'ON' : 'OFF');
  autoEl.className = 'badge ' + (d.auto_enabled ? 'badge-ok' : 'badge-info');

  const estopEl = document.getElementById('badge-estop');
  if (d.emergency_stop) {
    estopEl.style.display = '';
    estopEl.className = 'badge badge-ng';
    estopEl.textContent = 'EMERGENCY STOP';
  } else {
    estopEl.style.display = 'none';
  }

  // データギャップ警告バナー
  const gapBanner = document.getElementById('gap-banner');
  if (gapBanner) {
    if (d.data_gap_detected && !d.strategy_ready) {
      gapBanner.style.display = 'block';
      gapBanner.textContent = `⚠ DATA GAP: ${d.data_gap_minutes}分の欠損 — 戦略再蓄積中（発注停止）`;
      gapBanner.className = 'gap-banner warning';
    } else if (d.data_gap_detected && d.strategy_ready) {
      gapBanner.style.display = 'block';
      gapBanner.textContent = '✓ 再蓄積完了 — 戦略判定再開';
      gapBanner.className = 'gap-banner recovered';
      setTimeout(() => { gapBanner.style.display = 'none'; }, 30000);
    } else {
      gapBanner.style.display = 'none';
    }
  }
}

function setBadge(id, ok, label) {
  const el = document.getElementById(id);
  el.textContent = label + ': ' + (ok ? 'OK' : 'OFF');
  el.className = 'badge ' + (ok ? 'badge-ok' : 'badge-ng');
}

function updateStrategy(d) {
  setText('val-price', d.current_price != null ? d.current_price.toLocaleString() : '---');
  setText('val-trend', d.trend_status1 || '---');
  setText('val-pbstate', d.pbState1 || '---');
  setText('val-prevpeak', fmt(d.prevPeak1));
  setText('val-prevbot', fmt(d.prevBot1));
  setText('val-modori', fmt(d.modoriTakane1));
  setText('val-oshi', fmt(d.oshiYasune1));
  setText('val-peakfall', d.peakFalling1 ? 'YES' : 'NO');
  setText('val-botrise', d.botRising1 ? 'YES' : 'NO');

  const plan = d.plan;
  if (plan) {
    setText('val-ma', fmt(plan.entry_ma));
    setText('val-atr', fmt(plan.atr_value));
    setText('val-maok', plan.ma_deviation_ok ? 'OK' : 'NG');
    setText('val-timeok', plan.signal_time_ok ? 'OK' : 'NG');

    setText('val-buyactive', plan.buy_setup_active ? 'ACTIVE' : '---');
    setText('val-buyprice', fmt(plan.buy_stop_price));
    setText('val-sellactive', plan.sell_setup_active ? 'ACTIVE' : '---');
    setText('val-sellprice', fmt(plan.sell_stop_price));

    const buyBox = document.getElementById('setup-buy');
    buyBox.className = 'setup-box' + (plan.buy_setup_active ? ' buy-active' : '');
    const sellBox = document.getElementById('setup-sell');
    sellBox.className = 'setup-box' + (plan.sell_setup_active ? ' sell-active' : '');
  }

  setText('val-buyorder', d.buy_order_active ? `PLACED @${fmt(d.last_buy_order_price)}` : '---');
  setText('val-sellorder', d.sell_order_active ? `PLACED @${fmt(d.last_sell_order_price)}` : '---');
}

function updatePosition(d) {
  const box = document.getElementById('position-box');
  const sideEl = document.getElementById('val-posside');

  if (d.position_side) {
    box.className = 'position-info has-position';
    sideEl.textContent = d.position_side;
    sideEl.className = 'pos-side ' + (d.position_side === 'BUY' ? 'buy' : 'sell');
    setText('val-posentry', `Entry: ${fmt(d.entry_price)}`);
    setText('val-possl', `SL: ${fmt(d.sl_price)}`);
    const tpLabel = d.tp_is_software ? 'TP(SW):' : 'TP:';
    setText('val-postp', `${tpLabel} ${fmt(d.tp_price)}`);

    const beEl = document.getElementById('val-be');
    beEl.textContent = d.be_moved ? 'BE MOVED' : '';
    beEl.className = 'be-status' + (d.be_moved ? ' be-active' : '');

    if (d.current_price != null && d.entry_price != null) {
      const pnl = d.position_side === 'BUY'
        ? (d.current_price - d.entry_price) * d.position_qty
        : (d.entry_price - d.current_price) * d.position_qty;
      const pnlEl = document.getElementById('val-pospnl');
      pnlEl.textContent = `P&L: ${pnl >= 0 ? '+' : ''}${pnl.toLocaleString()}`;
      pnlEl.className = 'pnl-value ' + (pnl >= 0 ? 'positive' : 'negative');
    }
  } else {
    box.className = 'position-info';
    sideEl.textContent = 'NONE';
    sideEl.className = 'pos-side';
    setText('val-posentry', '---');
    setText('val-possl', '---');
    setText('val-postp', '---');
    setText('val-pospnl', '---');
    document.getElementById('val-be').textContent = '';
  }

  // Risk
  setText('val-dailypnl', d.daily_pnl != null ? (d.daily_pnl >= 0 ? '+' : '') + d.daily_pnl.toLocaleString() : '---');
  setText('val-conloss', d.consecutive_losses != null ? d.consecutive_losses : '---');
}

// ── ログポーリング ──
async function fetchLogs() {
  try {
    const res = await fetch('/api/logs');
    const logs = await res.json();
    const container = document.getElementById('log-entries');
    container.innerHTML = logs.slice(-50).reverse().map(l => {
      const catClass = {
        BAR: 'log-cat-bar',
        PLAN: 'log-cat-plan',
        ORDER: 'log-cat-order',
        CONTROL: 'log-cat-control',
      }[l.category] || 'log-cat';
      const time = l.time ? l.time.split('T')[1]?.split('.')[0] || '' : '';
      return `<div class="log-entry"><span class="log-time">${time}</span> <span class="${catClass}">[${l.category}]</span> ${l.message}</div>`;
    }).join('');
  } catch (e) {
    console.error('fetchLogs error', e);
  }
}

// ── チャートポーリング ──
let chartCanvas, chartCtx;

async function fetchChart() {
  try {
    const res = await fetch('/api/chart/5m');
    const candles = await res.json();
    drawChart(candles);
  } catch (e) {
    console.error('fetchChart error', e);
  }
}

function drawChart(candles) {
  if (!chartCanvas) {
    chartCanvas = document.getElementById('chart-canvas');
    chartCtx = chartCanvas.getContext('2d');
  }

  const container = document.getElementById('chart-container');
  chartCanvas.width = container.clientWidth;
  chartCanvas.height = container.clientHeight;

  const ctx = chartCtx;
  const W = chartCanvas.width;
  const H = chartCanvas.height;

  ctx.fillStyle = '#0a0e17';
  ctx.fillRect(0, 0, W, H);

  if (candles.length < 2) {
    ctx.fillStyle = '#475569';
    ctx.font = '14px Consolas';
    ctx.textAlign = 'center';
    ctx.fillText('Waiting for candle data...', W / 2, H / 2);
    return;
  }

  const maxShow = Math.min(candles.length, 120);
  const data = candles.slice(-maxShow);

  const highs = data.map(c => c.high);
  const lows = data.map(c => c.low);
  const maxPrice = Math.max(...highs);
  const minPrice = Math.min(...lows);
  const range = maxPrice - minPrice || 1;
  const pad = 40;

  const barWidth = Math.max(2, (W - pad * 2) / maxShow);
  const bodyWidth = Math.max(1, barWidth * 0.6);

  function yPos(price) {
    return pad + (1 - (price - minPrice) / range) * (H - pad * 2);
  }

  // グリッド
  ctx.strokeStyle = '#1e2a3a';
  ctx.lineWidth = 0.5;
  const step = Math.pow(10, Math.floor(Math.log10(range))) || 50;
  for (let p = Math.floor(minPrice / step) * step; p <= maxPrice + step; p += step) {
    const y = yPos(p);
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(W - pad, y);
    ctx.stroke();
    ctx.fillStyle = '#475569';
    ctx.font = '10px Consolas';
    ctx.textAlign = 'right';
    ctx.fillText(p.toLocaleString(), pad - 4, y + 3);
  }

  // ローソク足
  for (let i = 0; i < data.length; i++) {
    const c = data[i];
    const x = pad + i * barWidth + barWidth / 2;
    const isUp = c.close >= c.open;

    // ヒゲ
    ctx.strokeStyle = isUp ? '#34d399' : '#f87171';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, yPos(c.high));
    ctx.lineTo(x, yPos(c.low));
    ctx.stroke();

    // 実体
    const top = yPos(Math.max(c.open, c.close));
    const bot = yPos(Math.min(c.open, c.close));
    const h = Math.max(1, bot - top);

    ctx.fillStyle = isUp ? '#065f46' : '#7f1d1d';
    ctx.fillRect(x - bodyWidth / 2, top, bodyWidth, h);

    ctx.strokeStyle = isUp ? '#34d399' : '#f87171';
    ctx.lineWidth = 0.5;
    ctx.strokeRect(x - bodyWidth / 2, top, bodyWidth, h);
  }

  // 最新価格ライン
  const lastPrice = data[data.length - 1].close;
  const ly = yPos(lastPrice);
  ctx.strokeStyle = '#60a5fa';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(pad, ly);
  ctx.lineTo(W - pad, ly);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#60a5fa';
  ctx.font = '11px Consolas';
  ctx.textAlign = 'left';
  ctx.fillText(lastPrice.toLocaleString(), W - pad + 4, ly + 3);
}

// ── ヘルパ ──
function setText(id, text) {
  document.getElementById(id).textContent = text;
}

function fmt(v) {
  if (v == null) return '---';
  return typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 1 }) : String(v);
}

async function post(url) {
  await fetch(url, { method: 'POST' });
  await fetchStatus();
}

// ── ポーリング開始 ──
setInterval(fetchStatus, 1000);
setInterval(fetchLogs, 2000);
setInterval(fetchChart, 3000);
fetchStatus();
fetchLogs();
fetchChart();
