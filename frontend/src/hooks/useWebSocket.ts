import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_BASE_URL, WS_ENDPOINTS, DASHBOARD_CONFIG } from '../constants';
import type { WebSocketMessage, AllocationResult, LatencyMetric } from '../types';

export interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempts: number;
}

export interface WebSocketData {
  allocations: AllocationResult[];
  latency: number;
  lastUpdate: number;
  predictiveMessage?: {
    action: string;
    message: string;
  } | null;
}

export interface UseWebSocketReturn {
  data: WebSocketData;
  state: WebSocketState;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Custom hook for managing WebSocket connection to real-time allocation updates
 * Implements automatic reconnection logic and latency metrics handling
 * 
 * Requirements: 4.2, 4.5, 10.3
 */
export const useWebSocket = (endpoint: string = WS_ENDPOINTS.ALLOCATIONS): UseWebSocketReturn => {
  const [data, setData] = useState<WebSocketData>({
    allocations: [],
    latency: 0,
    lastUpdate: 0,
  });

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef<boolean>(true);

  const url = `${WS_BASE_URL}${endpoint}`;

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const clearHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Handle different message types
      if ('type' in message) {
        switch (message.type) {
          case 'latency':
            // Handle latency metric
            const latencyMessage = message as LatencyMetric;
            setData(prev => ({
              ...prev,
              latency: latencyMessage.value,
            }));
            break;
            
          case 'predictive_action':
            const predictiveData = message as any;
            setData(prev => ({
              ...prev,
              predictiveMessage: {
                action: predictiveData.action,
                message: predictiveData.message
              }
            }));
            
            // Clear message after 8 seconds
            setTimeout(() => {
              setData(prev => {
                if (prev.predictiveMessage?.message === predictiveData.message) {
                  return { ...prev, predictiveMessage: null };
                }
                return prev;
              });
            }, 8000);
            break;
            
          case 'allocation_results':
            // Handle allocation results broadcast
            const allocationData = message as any;
            if (allocationData.allocations && Array.isArray(allocationData.allocations)) {
              setData(prev => ({
                ...prev,
                allocations: allocationData.allocations.slice(0, DASHBOARD_CONFIG.MAX_STREAM_ROWS),
                lastUpdate: Date.now(),
              }));
            }
            break;
            
          case 'connection_established':
            console.log('WebSocket connection established:', message);
            break;
            
          case 'system_state':
            console.log('Received system state:', message);
            break;
            
          default:
            console.log('Unknown message type:', message);
        }
      } else {
        // Handle single allocation result (legacy format)
        const allocation = message as AllocationResult;
        if (allocation.node_id && allocation.allocated_power !== undefined) {
          setData(prev => ({
            ...prev,
            allocations: [allocation, ...prev.allocations].slice(0, DASHBOARD_CONFIG.MAX_STREAM_ROWS),
            lastUpdate: Date.now(),
          }));
        }
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to parse message data',
      }));
    }
  }, []);

  const handleOpen = useCallback(() => {
    console.log('WebSocket connected');
    setState(prev => ({
      ...prev,
      isConnected: true,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0,
    }));

    // Start heartbeat
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 10000); // 10 seconds
  }, []);

  const handleClose = useCallback((event: CloseEvent) => {
    console.log('WebSocket disconnected:', event.code, event.reason);
    
    clearHeartbeat();

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));

    // Attempt automatic reconnection if not manually disconnected
    if (shouldReconnectRef.current && event.code !== 1000) {
      setState(prev => {
        const newAttempts = prev.reconnectAttempts + 1;
        
        if (newAttempts <= DASHBOARD_CONFIG.MAX_RECONNECT_ATTEMPTS) {
          console.log(`Attempting reconnection ${newAttempts}/${DASHBOARD_CONFIG.MAX_RECONNECT_ATTEMPTS}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, DASHBOARD_CONFIG.RECONNECT_DELAY_MS * newAttempts); // Exponential backoff
          
          return {
            ...prev,
            reconnectAttempts: newAttempts,
            error: `Connection lost. Reconnecting... (${newAttempts}/${DASHBOARD_CONFIG.MAX_RECONNECT_ATTEMPTS})`,
          };
        } else {
          return {
            ...prev,
            error: 'Connection failed. Maximum reconnection attempts reached.',
          };
        }
      });
    }
  }, []);

  const handleError = useCallback((event: Event) => {
    console.error('WebSocket error:', event);
    setState(prev => ({
      ...prev,
      error: 'WebSocket connection error',
      isConnecting: false,
    }));
  }, []);

  const connect = useCallback(() => {
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    clearReconnectTimeout();
    shouldReconnectRef.current = true;

    setState(prev => ({
      ...prev,
      isConnecting: true,
      error: null,
    }));

    try {
      const ws = new WebSocket(url);
      
      ws.onopen = handleOpen;
      ws.onmessage = handleMessage;
      ws.onclose = handleClose;
      ws.onerror = handleError;
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: 'Failed to create WebSocket connection',
      }));
    }
  }, [url, handleOpen, handleMessage, handleClose, handleError, clearReconnectTimeout]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();
    clearHeartbeat();
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0,
    }));
  }, [clearReconnectTimeout]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    // Cleanup on unmount
    return () => {
      shouldReconnectRef.current = false;
      clearReconnectTimeout();
      clearHeartbeat();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect, clearReconnectTimeout, clearHeartbeat]);

  return {
    data,
    state,
    connect,
    disconnect,
  };
};

export default useWebSocket;