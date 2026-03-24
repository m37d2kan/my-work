const API_BASE = '/api';

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(
      typeof err.error === 'object' ? JSON.stringify(err.error) : (err.error ?? `HTTP ${res.status}`)
    );
  }
  return res.json();
}

export const api = {
  getBoard: (symbol, exchange = 2) =>
    fetchJson(`${API_BASE}/board/${encodeURIComponent(symbol)}?exchange=${exchange}`),

  getPositions: (params = {}) => {
    const q = new URLSearchParams({ product: 0, ...params }).toString();
    return fetchJson(`${API_BASE}/positions?${q}`);
  },

  getOrders: (params = {}) => {
    const q = new URLSearchParams({ product: 0, ...params }).toString();
    return fetchJson(`${API_BASE}/orders?${q}`);
  },

  sendOrder: (orderData) =>
    fetchJson(`${API_BASE}/orders/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData),
    }),

  cancelOrder: (orderId) =>
    fetchJson(`${API_BASE}/orders/cancel`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ orderId }),
    }),

  register: (symbols) =>
    fetchJson(`${API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbols }),
    }),
};
