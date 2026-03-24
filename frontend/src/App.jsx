import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { usePositions, useOrders } from './hooks/useApi';
import PriceDisplay from './components/PriceDisplay';
import OrderBook from './components/OrderBook';
import PriceChart from './components/PriceChart';
import OrderForm from './components/OrderForm';
import PositionsTable from './components/PositionsTable';
import OrdersTable from './components/OrdersTable';
import { api } from './utils/api';

const DEFAULT_SYMBOL = '161030023';
const DEFAULT_EXCHANGE = 2;
const MAX_HISTORY = 200;

export default function App() {
  const [board, setBoard] = useState(null);
  const [history, setHistory] = useState([]);
  const [kabuConnected, setKabuConnected] = useState(false);
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [exchange, setExchange] = useState(DEFAULT_EXCHANGE);
  const [toast, setToast] = useState(null);
  const [closePos, setClosePos] = useState(null);

  const { positions, refresh: refreshPos } = usePositions();
  const { orders, refresh: refreshOrd, cancel } = useOrders();

  const showToast = (type, text) => {
    setToast({ type, text });
    setTimeout(() => setToast(null), 4000);
  };

  // WebSocket メッセージハンドラ（board は setBoard だけ。history は下の effect で一元管理）
  const handleWsMsg = useCallback((msg) => {
    if (msg.type === 'kabu_connected') {
      setKabuConnected(true);
      api.register([{ Symbol: symbol, Exchange: Number(exchange) }]).catch(console.error);
    }
    if (msg.type === 'kabu_disconnected') setKabuConnected(false);
    if (msg.type === 'board' && msg.data) {
      setBoard(msg.data);
    }
  }, [symbol, exchange]);

  const { connected: wsConnected } = useWebSocket(handleWsMsg);

  // board が更新されたらチャート履歴に追記（REST/WS どちらの更新でも動く）
  useEffect(() => {
    if (!board?.CurrentPrice) return;
    const t = new Date(board.CurrentPriceTime);
    const time = isNaN(t)
      ? new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : t.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const ts = isNaN(t) ? Date.now() : t.getTime();
    setHistory((prev) => {
      // 直前と時刻・価格が同じなら重複追加しない
      const last = prev[prev.length - 1];
      if (last?.time === time && last?.price === board.CurrentPrice) return prev;
      const next = [...prev, { time, price: board.CurrentPrice, ts }];
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
    });
  }, [board]);

  // WebSocket 接続時にシンボル登録
  useEffect(() => {
    if (!wsConnected) return;
    api.register([{ Symbol: symbol, Exchange: Number(exchange) }]).catch(console.error);
  }, [wsConnected, symbol, exchange]);

  // シンボル変更時にリセット＆初回取得
  useEffect(() => {
    setBoard(null);
    setHistory([]);
    api.getBoard(symbol, exchange).then(setBoard).catch(console.error);
  }, [symbol, exchange]);

  // 板情報・ポジション・注文を定期更新（板は3秒、他は15秒）
  useEffect(() => {
    refreshPos();
    refreshOrd();
    const boardId = setInterval(() => {
      api.getBoard(symbol, exchange).then(setBoard).catch(console.error);
    }, 3000);
    const dataId = setInterval(() => { refreshPos(); refreshOrd(); }, 15000);
    return () => { clearInterval(boardId); clearInterval(dataId); };
  }, [symbol, exchange, refreshPos, refreshOrd]);

  const handleSendOrder = async (orderData) => {
    await api.sendOrder(orderData);
    showToast('success', '注文を送信しました');
    setClosePos(null);
    setTimeout(refreshOrd, 1000);
  };

  const handleCancel = async (orderId) => {
    try {
      await cancel(orderId);
      showToast('success', '注文をキャンセルしました');
    } catch (err) {
      showToast('error', `キャンセルエラー: ${err.message}`);
    }
  };

  return (
    <div className="app">
      {/* ヘッダー */}
      <header className="app-header">
        <div className="header-left">
          <span className="app-title">日経先物ダッシュボード</span>
          <div className="symbol-controls">
            <input
              className="symbol-input"
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="Symbol (例: 169)"
            />
            <select
              className="exchange-select"
              value={exchange}
              onChange={(e) => setExchange(Number(e.target.value))}
            >
              <option value={2}>OSE (2)</option>
              <option value={1}>TSE (1)</option>
            </select>
          </div>
        </div>
        <div className="header-right">
          <div className={`status-badge ${kabuConnected ? 'ok' : 'ng'}`}>
            kabu WS: {kabuConnected ? '接続中' : '未接続'}
          </div>
          <div className={`status-badge ${wsConnected ? 'ok' : 'ng'}`}>
            サーバー: {wsConnected ? '接続中' : '未接続'}
          </div>
        </div>
      </header>

      {/* トースト通知 */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.text}</div>
      )}

      {/* メインレイアウト */}
      <div className="main-grid">
        <div className="col-left">
          <PriceDisplay data={board} />
          <OrderBook data={board} />
        </div>
        <div className="col-center">
          <PriceChart data={history} />
        </div>
        <div className="col-right">
          <OrderForm
            onSubmit={handleSendOrder}
            currentPrice={board?.CurrentPrice}
            symbol={symbol}
            exchange={exchange}
            closePosition={closePos}
            onClearClose={() => setClosePos(null)}
          />
        </div>
      </div>

      {/* 下段 */}
      <div className="bottom-grid">
        <div className="bottom-section">
          <div className="section-title">ポジション</div>
          <PositionsTable positions={positions} onRefresh={refreshPos} onClose={setClosePos} />
        </div>
        <div className="bottom-section">
          <div className="section-title">注文一覧</div>
          <OrdersTable orders={orders} onCancel={handleCancel} onRefresh={refreshOrd} />
        </div>
      </div>
    </div>
  );
}
