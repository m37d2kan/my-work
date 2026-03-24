const WebSocket = require('ws');

class WsProxy {
  constructor(kabuWsUrl) {
    this.kabuWsUrl = kabuWsUrl;
    this.kabuWs = null;
    this.clients = new Set();
    this.reconnectDelay = 2000;
    this.reconnectTimer = null;
    this.isConnecting = false;
  }

  connect() {
    if (this.isConnecting) return;
    this.isConnecting = true;

    console.log(`kabu WebSocket に接続中: ${this.kabuWsUrl}`);
    this.kabuWs = new WebSocket(this.kabuWsUrl);

    this.kabuWs.on('open', () => {
      console.log('kabu WebSocket 接続完了');
      this.isConnecting = false;
      this.reconnectDelay = 2000;
      this.broadcast({ type: 'kabu_connected' });
    });

    this.kabuWs.on('message', (data) => {
      try {
        const parsed = JSON.parse(data.toString());
        this.broadcast({ type: 'board', data: parsed });
      } catch (err) {
        console.error('kabu WS メッセージ解析エラー:', err.message);
      }
    });

    this.kabuWs.on('close', () => {
      console.log('kabu WebSocket 切断');
      this.isConnecting = false;
      this.broadcast({ type: 'kabu_disconnected' });
      this.scheduleReconnect();
    });

    this.kabuWs.on('error', (err) => {
      console.error('kabu WebSocket エラー:', err.message);
      this.isConnecting = false;
    });
  }

  scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    console.log(`${this.reconnectDelay}ms 後に再接続します`);
    this.reconnectTimer = setTimeout(() => {
      this.connect();
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    }, this.reconnectDelay);
  }

  isKabuConnected() {
    return this.kabuWs?.readyState === WebSocket.OPEN;
  }

  addClient(ws, req) {
    this.clients.add(ws);
    console.log(`フロントエンド接続 (合計: ${this.clients.size})`);

    // 現在の接続状態を通知
    ws.send(JSON.stringify({
      type: this.isKabuConnected() ? 'kabu_connected' : 'kabu_disconnected',
    }));

    ws.on('close', () => {
      this.clients.delete(ws);
      console.log(`フロントエンド切断 (合計: ${this.clients.size})`);
    });

    ws.on('error', (err) => {
      console.error('フロントエンド WS エラー:', err.message);
      this.clients.delete(ws);
    });
  }

  broadcast(message) {
    const data = JSON.stringify(message);
    this.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(data);
      }
    });
  }
}

module.exports = { WsProxy };
