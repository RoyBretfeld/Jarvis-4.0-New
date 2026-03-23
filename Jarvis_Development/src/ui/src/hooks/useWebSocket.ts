/**
 * AWP-024 – useWebSocket
 * Verbindet sich mit dem FastAPI WebSocket /ws/logs und streamt Log-Lines.
 * Auto-reconnect mit exponential backoff.
 */
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export interface LogLine {
  ts: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  service: string;
  message: string;
}

interface UseWebSocketOptions {
  url?: string;
  maxLines?: number;
  enabled?: boolean;
}

interface UseWebSocketResult {
  lines: LogLine[];
  connected: boolean;
  error: string | null;
  clear: () => void;
}

const DEFAULT_WS_URL =
  typeof window !== 'undefined'
    ? `ws://${window.location.hostname}:8000/ws/logs`
    : 'ws://localhost:8000/ws/logs';

export function useWebSocket({
  url = DEFAULT_WS_URL,
  maxLines = 500,
  enabled = true,
}: UseWebSocketOptions = {}): UseWebSocketResult {
  const [lines, setLines] = useState<LogLine[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);

  const connect = useCallback(() => {
    if (!enabled) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        retryCountRef.current = 0;
      };

      ws.onmessage = (evt) => {
        try {
          const line: LogLine = JSON.parse(evt.data as string);
          setLines((prev) => {
            const next = [...prev, line];
            return next.length > maxLines ? next.slice(-maxLines) : next;
          });
        } catch {
          // Raw string fallback
          const line: LogLine = {
            ts: new Date().toISOString(),
            level: 'INFO',
            service: 'raw',
            message: evt.data as string,
          };
          setLines((prev) => [...prev.slice(-maxLines + 1), line]);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        scheduleReconnect();
      };

      ws.onerror = () => {
        setError('WebSocket error');
        ws.close();
      };
    } catch (err) {
      setError(String(err));
      scheduleReconnect();
    }
  }, [url, maxLines, enabled]);

  const scheduleReconnect = useCallback(() => {
    const delay = Math.min(1000 * 2 ** retryCountRef.current, 30000);
    retryCountRef.current += 1;
    retryRef.current = setTimeout(connect, delay);
  }, [connect]);

  useEffect(() => {
    if (enabled) connect();
    return () => {
      retryRef.current && clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, [enabled, connect]);

  const clear = useCallback(() => setLines([]), []);

  return { lines, connected, error, clear };
}
