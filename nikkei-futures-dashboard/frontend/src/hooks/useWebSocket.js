import { useEffect, useRef, useState, useCallback } from 'react';

export function useWebSocket(onMessage) {
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const onMsgRef = useRef(onMessage);
  onMsgRef.current = onMessage;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const url = `ws://${window.location.host}/ws`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      setTimeout(connect, 3000);
    };
    ws.onerror = (e) => console.error('WebSocket エラー:', e);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onMsgRef.current(data);
      } catch (err) {
        console.error('WS メッセージ解析失敗:', err);
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
