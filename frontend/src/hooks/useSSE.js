import { useState, useEffect, useRef } from 'react';

export const useSSE = (url) => {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('connecting'); // connecting, connected, error
  const [error, setError] = useState(null);
  const eventSource = useRef(null);
  const reconnectTimeout = useRef(null);

  useEffect(() => {
    let mounted = true;

    const connect = () => {
      // Avoid multiple connections
      if (eventSource.current && eventSource.current.readyState !== EventSource.CLOSED) {
          return;
      }

      setStatus('connecting');
      console.log(`[SSE] Connecting to ${url}...`);

      const es = new EventSource(url);
      eventSource.current = es;

      es.onopen = () => {
        if (mounted) {
            console.log('[SSE] Connected');
            setStatus('connected');
            setError(null);
        }
      };

      es.onmessage = (event) => {
        if (mounted) {
            try {
                const parsed = JSON.parse(event.data);
                setData(parsed);
            } catch (err) {
                console.error('[SSE] JSON Parse Error:', err);
            }
        }
      };

      es.onerror = (err) => {
        console.error('[SSE] Error:', err);
        if (mounted) {
            setStatus('error');
            setError(err);
        }
        es.close();
        
        // Reconnect strategy: exponential backoff or fixed 3s
        reconnectTimeout.current = setTimeout(() => {
            if (mounted) connect();
        }, 3000);
      };
    };

    connect();

    return () => {
      mounted = false;
      if (eventSource.current) {
          eventSource.current.close();
      }
      if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
      }
    };
  }, [url]);

  return { data, status, error };
};
