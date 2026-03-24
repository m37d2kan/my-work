require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

const express = require('express');
const cors = require('cors');
const { createServer } = require('http');
const { WebSocketServer } = require('ws');
const { KabuClient } = require('./src/kabuClient');
const { WsProxy } = require('./src/wsProxy');

const app = express();

app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:3000'],
}));
app.use(express.json());

const kabu = new KabuClient(
  process.env.KABU_API_URL || 'http://localhost:18080/kabusapi',
  process.env.KABU_API_PASSWORD || '860622'
);

const wsProxy = new WsProxy(
  process.env.KABU_WS_URL || 'ws://localhost:18081/kabusapi/websocket'
);

// ─── Routes ───────────────────────────────────────────────────────────────────

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', kabuConnected: wsProxy.isKabuConnected() });
});

app.post('/api/auth', async (_req, res) => {
  try {
    const token = await kabu.authenticate();
    res.json({ token });
  } catch (err) {
    res.status(500).json({ error: err.response?.data ?? err.message });
  }
});

app.get('/api/board/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const exchange = req.query.exchange ?? '2';
    const data = await kabu.getBoard(symbol, exchange);
    res.json(data);
  } catch (err) {
    res.status(err.response?.status ?? 500).json({
      error: err.response?.data ?? err.message,
    });
  }
});

app.get('/api/positions', async (req, res) => {
  try {
    const data = await kabu.getPositions(req.query);
    res.json(data);
  } catch (err) {
    res.status(err.response?.status ?? 500).json({
      error: err.response?.data ?? err.message,
    });
  }
});

app.get('/api/orders', async (req, res) => {
  try {
    const data = await kabu.getOrders(req.query);
    res.json(data);
  } catch (err) {
    res.status(err.response?.status ?? 500).json({
      error: err.response?.data ?? err.message,
    });
  }
});

app.post('/api/orders/send', async (req, res) => {
  try {
    const data = await kabu.sendOrder(req.body);
    res.json(data);
  } catch (err) {
    res.status(err.response?.status ?? 500).json({
      error: err.response?.data ?? err.message,
    });
  }
});

app.put('/api/orders/cancel', async (req, res) => {
  try {
    const { orderId } = req.body;
    if (!orderId) return res.status(400).json({ error: 'orderId が必要です' });
    const data = await kabu.cancelOrder(orderId);
    res.json(data);
  } catch (err) {
    res.status(err.response?.status ?? 500).json({
      error: err.response?.data ?? err.message,
    });
  }
});

app.post('/api/register', async (req, res) => {
  try {
    const { symbols } = req.body;
    if (!Array.isArray(symbols)) return res.status(400).json({ error: 'symbols は配列が必要です' });
    const data = await kabu.registerSymbols(symbols);
    res.json(data);
  } catch (err) {
    res.status(err.response?.status ?? 500).json({
      error: err.response?.data ?? err.message,
    });
  }
});

app.delete('/api/register', async (req, res) => {
  try {
    const { symbols } = req.body;
    if (!Array.isArray(symbols)) return res.status(400).json({ error: 'symbols は配列が必要です' });
    const data = await kabu.unregisterSymbols(symbols);
    res.json(data);
  } catch (err) {
    res.status(err.response?.status ?? 500).json({
      error: err.response?.data ?? err.message,
    });
  }
});

// ─── Server setup ─────────────────────────────────────────────────────────────

const server = createServer(app);

const wss = new WebSocketServer({ server, path: '/ws' });
wss.on('connection', (ws, req) => wsProxy.addClient(ws, req));

const PORT = process.env.PORT || 3001;

server.listen(PORT, async () => {
  console.log(`バックエンドサーバー起動: http://localhost:${PORT}`);
  try {
    await kabu.authenticate();
  } catch (err) {
    console.error('kabu API 認証失敗（kabu ステーションが起動しているか確認してください）:', err.message);
  }
  wsProxy.connect();
});
