import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../hooks/useWebSocket';
import { DASHBOARD_CONFIG } from '../constants';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      const closeEvent = new CloseEvent('close', { code: code || 1000, reason });
      this.onclose(closeEvent);
    }
  }

  send(data: string) {
    // Mock send - could be extended for testing
  }
}

// Mock global WebSocket
const originalWebSocket = global.WebSocket;

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllTimers();
    vi.useFakeTimers();
    global.WebSocket = MockWebSocket as any;
  });

  afterEach(() => {
    vi.useRealTimers();
    global.WebSocket = originalWebSocket;
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.data).toEqual({
      allocations: [],
      latency: 0,
      lastUpdate: 0,
    });

    expect(result.current.state).toEqual({
      isConnected: false,
      isConnecting: true, // Should be connecting on mount
      error: null,
      reconnectAttempts: 0,
    });
  });

  it('should connect successfully', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Initially connecting
    expect(result.current.state.isConnecting).toBe(true);
    expect(result.current.state.isConnected).toBe(false);

    // Wait for connection to establish
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(result.current.state.isConnected).toBe(true);
    expect(result.current.state.isConnecting).toBe(false);
    expect(result.current.state.error).toBe(null);
  });

  it('should handle allocation messages', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Wait for connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const mockAllocation = {
      node_id: 'test-node-1',
      allocated_power: 100,
      source_mix: { solar: 100 },
      action: 'maintain' as const,
      latency_ms: 5,
    };

    // Simulate receiving allocation message
    await act(async () => {
      const ws = (global.WebSocket as any).mock.instances[0];
      if (ws && ws.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: JSON.stringify(mockAllocation)
        }));
      }
    });

    expect(result.current.data.allocations).toHaveLength(1);
    expect(result.current.data.allocations[0]).toEqual(mockAllocation);
    expect(result.current.data.lastUpdate).toBeGreaterThan(0);
  });

  it('should handle latency messages', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Wait for connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const mockLatency = {
      type: 'latency' as const,
      value: 25,
    };

    // Simulate receiving latency message
    await act(async () => {
      const ws = (global.WebSocket as any).mock.instances[0];
      if (ws && ws.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: JSON.stringify(mockLatency)
        }));
      }
    });

    expect(result.current.data.latency).toBe(25);
  });

  it('should limit allocations to MAX_STREAM_ROWS', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Wait for connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    // Send more allocations than the limit
    const allocationsToSend = DASHBOARD_CONFIG.MAX_STREAM_ROWS + 10;
    
    await act(async () => {
      const ws = (global.WebSocket as any).mock.instances[0];
      if (ws && ws.onmessage) {
        for (let i = 0; i < allocationsToSend; i++) {
          const mockAllocation = {
            node_id: `test-node-${i}`,
            allocated_power: 100,
            source_mix: { solar: 100 },
            action: 'maintain' as const,
            latency_ms: 5,
          };
          
          ws.onmessage(new MessageEvent('message', {
            data: JSON.stringify(mockAllocation)
          }));
        }
      }
    });

    expect(result.current.data.allocations).toHaveLength(DASHBOARD_CONFIG.MAX_STREAM_ROWS);
    // Should have the most recent allocations (highest indices)
    expect(result.current.data.allocations[0].node_id).toBe(`test-node-${allocationsToSend - 1}`);
  });

  it('should handle connection errors gracefully', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Wait for connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    // Simulate connection error
    await act(async () => {
      const ws = (global.WebSocket as any).mock.instances[0];
      if (ws && ws.onerror) {
        ws.onerror(new Event('error'));
      }
    });

    expect(result.current.state.error).toBe('WebSocket connection error');
    expect(result.current.state.isConnecting).toBe(false);
  });

  it('should handle malformed messages gracefully', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Wait for connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    // Simulate malformed message
    await act(async () => {
      const ws = (global.WebSocket as any).mock.instances[0];
      if (ws && ws.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: 'invalid json'
        }));
      }
    });

    expect(result.current.state.error).toBe('Failed to parse message data');
  });

  it('should disconnect manually', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Wait for connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(result.current.state.isConnected).toBe(true);

    // Manual disconnect
    act(() => {
      result.current.disconnect();
    });

    expect(result.current.state.isConnected).toBe(false);
    expect(result.current.state.isConnecting).toBe(false);
    expect(result.current.state.error).toBe(null);
  });

  it('should reconnect manually', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Wait for initial connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    // Disconnect
    act(() => {
      result.current.disconnect();
    });

    expect(result.current.state.isConnected).toBe(false);

    // Reconnect
    act(() => {
      result.current.connect();
    });

    expect(result.current.state.isConnecting).toBe(true);

    // Wait for reconnection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(result.current.state.isConnected).toBe(true);
  });
});