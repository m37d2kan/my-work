const axios = require('axios');

class KabuClient {
  constructor(baseUrl, password) {
    this.baseUrl = baseUrl;
    this.password = password;
    this.token = null;
    this.tokenExpiry = null;
  }

  async authenticate() {
    const res = await axios.post(`${this.baseUrl}/token`, {
      APIPassword: this.password,
    });
    this.token = res.data.Token;
    // トークンは24時間有効。23時間後に期限切れ扱い
    this.tokenExpiry = Date.now() + 23 * 60 * 60 * 1000;
    console.log('kabu API 認証成功');
    return this.token;
  }

  async ensureToken() {
    if (!this.token || Date.now() >= this.tokenExpiry) {
      await this.authenticate();
    }
    return this.token;
  }

  async request(method, path, data = null, params = null) {
    const token = await this.ensureToken();
    const config = {
      method,
      url: `${this.baseUrl}${path}`,
      headers: { 'X-API-KEY': token },
    };
    // 文字列の場合は事前シリアライズ済みJSONとして扱う
    if (typeof data === 'string') {
      config.data = data;
      config.headers['Content-Type'] = 'application/json';
    } else if (data !== null) {
      config.data = data;
    }
    if (params !== null) config.params = params;

    try {
      const res = await axios(config);
      return res.data;
    } catch (err) {
      if (err.response?.status === 401) {
        await this.authenticate();
        config.headers['X-API-KEY'] = this.token;
        const res = await axios(config);
        return res.data;
      }
      throw err;
    }
  }

  getBoard(symbol, exchange = 2) {
    return this.request('GET', `/board/${symbol}@${exchange}`);
  }

  getPositions(params = {}) {
    return this.request('GET', '/positions', null, params);
  }

  getOrders(params = {}) {
    return this.request('GET', '/orders', null, params);
  }

  sendOrder(orderData) {
    const body = { ...orderData, Password: this.password };
    console.log('[sendOrder] ===== 最終送信ボディ =====');
    Object.entries(body).forEach(([k, v]) => {
      if (k !== 'Password') {
        console.log(`  ${k}: ${JSON.stringify(v)}  (${typeof v})`);
      }
    });
    // 価格フィールドをJSON上で小数形式にする（59000 → 59000.0）
    // JSON.stringifyは整数を小数点なしで出力するため正規表現で補正
    // ReverseLimitOrder内のTriggerPrice/AfterHitPriceも対象
    const serialized = JSON.stringify(body).replace(
      /"(Price|TriggerPrice|AfterHitPrice)":(\d+)(?!\d|\.)/g,
      (_, key, n) => `"${key}":${n}.0`
    );
    console.log('[sendOrder] JSON:', serialized.replace(/"Password":"[^"]*"/, '"Password":"***"'));
    console.log('[sendOrder] ==========================');
    return this.request('POST', '/sendorder/future', serialized)
      .then((res) => {
        console.log('[sendOrder] レスポンス:', JSON.stringify(res, null, 2));
        return res;
      })
      .catch((err) => {
        console.error('[sendOrder] エラーレスポンス:', JSON.stringify(err.response?.data ?? err.message, null, 2));
        throw err;
      });
  }

  cancelOrder(orderId) {
    return this.request('PUT', '/cancelorder', {
      OrderId: orderId,
      Password: this.password,
    });
  }

  registerSymbols(symbols) {
    return this.request('POST', '/register', { Symbols: symbols });
  }

  unregisterSymbols(symbols) {
    return this.request('DELETE', '/register', { Symbols: symbols });
  }
}

module.exports = { KabuClient };
