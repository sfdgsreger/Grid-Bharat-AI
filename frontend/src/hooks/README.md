# WebSocket Hook Documentation

## useWebSocket Hook

The `useWebSocket` hook provides a robust WebSocket client for real-time communication with the Bharat-Grid AI backend. It handles automatic reconnection, latency metrics, and proper error handling.

### Features

- **Automatic Connection**: Connects to WebSocket endpoint on mount
- **Automatic Reconnection**: Reconnects automatically when connection drops (up to 5 attempts with exponential backoff)
- **Latency Tracking**: Displays real-time latency metrics from the server
- **Error Handling**: Graceful error handling with user-friendly messages
- **Data Management**: Manages allocation results with configurable limits
- **Manual Control**: Provides connect/disconnect methods for manual control

### Usage

```typescript
import { useWebSocket } from '../hooks/useWebSocket';

function MyComponent() {
  const { data, state, connect, disconnect } = useWebSocket();

  return (
    <div>
      {/* Connection Status */}
      <div>Status: {state.isConnected ? 'Connected' : 'Disconnected'}</div>
      
      {/* Latency Display */}
      <div>Latency: {data.latency}ms</div>
      
      {/* Recent Allocations */}
      {data.allocations.map(allocation => (
        <div key={allocation.node_id}>
          {allocation.node_id}: {allocation.allocated_power}kW
        </div>
      ))}
      
      {/* Manual Controls */}
      <button onClick={connect}>Connect</button>
      <button onClick={disconnect}>Disconnect</button>
    </div>
  );
}
```

### Return Values

#### `data: WebSocketData`
- `allocations: AllocationResult[]` - Array of recent allocation results (limited to MAX_STREAM_ROWS)
- `latency: number` - Current WebSocket latency in milliseconds
- `lastUpdate: number` - Timestamp of last received allocation

#### `state: WebSocketState`
- `isConnected: boolean` - Whether WebSocket is currently connected
- `isConnecting: boolean` - Whether WebSocket is attempting to connect
- `error: string | null` - Current error message, if any
- `reconnectAttempts: number` - Number of reconnection attempts made

#### Methods
- `connect()` - Manually initiate WebSocket connection
- `disconnect()` - Manually close WebSocket connection

### Configuration

The hook uses configuration from `constants/index.ts`:

- `WS_BASE_URL` - WebSocket server base URL (default: ws://localhost:8000)
- `WS_ENDPOINTS.ALLOCATIONS` - Allocation endpoint path (default: /ws/allocations)
- `DASHBOARD_CONFIG.MAX_STREAM_ROWS` - Maximum allocations to keep (default: 50)
- `DASHBOARD_CONFIG.RECONNECT_DELAY_MS` - Base reconnection delay (default: 1000ms)
- `DASHBOARD_CONFIG.MAX_RECONNECT_ATTEMPTS` - Maximum reconnection attempts (default: 5)

### Message Types

The hook handles two types of WebSocket messages:

#### Allocation Result
```typescript
{
  node_id: string;
  allocated_power: number;
  source_mix: { grid?: number; solar?: number; battery?: number; diesel?: number; };
  action: 'maintain' | 'reduce' | 'cutoff';
  latency_ms: number;
}
```

#### Latency Metric
```typescript
{
  type: 'latency';
  value: number; // milliseconds
}
```

### Error Handling

The hook handles various error scenarios:

- **Connection Errors**: Network issues, server unavailable
- **Message Parsing Errors**: Malformed JSON from server
- **Automatic Reconnection**: Connection drops, server restarts
- **Manual Disconnection**: User-initiated disconnection

### Performance Considerations

- **Memory Management**: Limits allocation history to prevent memory leaks
- **Reconnection Strategy**: Exponential backoff prevents server overload
- **Error Recovery**: Graceful degradation when connection fails
- **Cleanup**: Proper cleanup on component unmount

### Requirements Satisfied

- **Requirement 4.2**: WebSocket connection to /ws/allocations endpoint
- **Requirement 4.5**: Latency metrics display
- **Requirement 10.3**: Automatic reconnection when connection drops

### Testing

The hook includes comprehensive tests covering:

- Connection establishment and teardown
- Message handling (allocations and latency)
- Error scenarios and recovery
- Automatic reconnection logic
- Manual connect/disconnect operations
- Memory management (allocation limits)

Run tests with:
```bash
npm test useWebSocket.test.tsx
```