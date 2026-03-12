# PowerMap Component

## Overview

The PowerMap component is an interactive visualization that displays energy nodes connected to a central grid hub with real-time status updates. It's designed for the Bharat-Grid AI system to show power allocation decisions across different types of energy consumers.

## Features

### ✅ Interactive Node Visualization
- Circular layout of energy nodes around a central hub
- Color-coded nodes based on allocation actions:
  - 🟢 **Green**: Maintain (full power allocation)
  - 🟡 **Yellow**: Reduce (partial power allocation)
  - 🔴 **Red**: Cutoff (no power allocation)

### ✅ Real-time Status Updates
- Nodes update colors based on allocation results
- Connection lines change color to match node status
- Smooth transitions and animations for status changes
- Pulsing animation for cutoff nodes

### ✅ Node Positioning and Connection Lines
- Automatic circular positioning around central hub
- Dynamic connection lines from hub to each node
- Dashed lines for cutoff connections
- Responsive positioning for different screen sizes

### ✅ Priority-based Visual Differentiation
- Priority tier indicators (1, 2, 3) on each node
- Color legend showing priority types:
  - Priority 1: Hospital (Red indicator)
  - Priority 2: Factory (Yellow indicator)  
  - Priority 3: Residential (Blue indicator)

### ✅ Responsive Design
- Adapts to different screen sizes
- Maintains aspect ratio and readability
- Mobile-friendly hover interactions

## Component Props

```typescript
interface PowerMapProps {
  nodes: EnergyNode[];        // Array of energy nodes to display
  allocations: AllocationResult[];  // Current allocation results
}
```

## Usage

```tsx
import PowerMap from './components/PowerMap';

function Dashboard() {
  const nodes = [/* your energy nodes */];
  const allocations = [/* current allocations */];
  
  return (
    <PowerMap nodes={nodes} allocations={allocations} />
  );
}
```

## Interactive Features

### Hover Tooltips
Each node displays detailed information on hover:
- Node type (Hospital/Factory/Residential)
- Node ID
- Current load (kW)
- Source type (Grid/Solar/Battery/Diesel)
- Allocated power (kW)
- Allocation action
- Processing latency (ms)

### Visual Indicators
- **Central Hub**: Pulsing blue circle representing the grid hub
- **Connection Lines**: Color-coded lines showing power flow status
- **Node Animations**: Hover effects and status-based animations
- **Status Legend**: Real-time counts of maintain/reduce/cutoff actions

## Requirements Fulfilled

- **12.1**: Interactive node visualization ✅
- **12.5**: Node status changes update visual representation ✅
- **12.6**: Cutoff nodes displayed in red ✅
- **12.7**: Reduce nodes displayed in yellow ✅
- **12.8**: Maintain nodes displayed in green ✅

## Demo Mode

The component includes a `PowerMapDemo` that simulates real-time scenarios:
1. **Normal Operation**: All nodes maintained
2. **Moderate Shortage**: Factories and residential reduced
3. **Severe Shortage**: Residential cutoff, hospitals maintained

## Technical Implementation

- Built with React 18 and TypeScript
- Styled with Tailwind CSS
- SVG-based connection lines
- Circular positioning algorithm
- Optimized re-rendering with useMemo
- Smooth CSS transitions and animations

## Performance

- Efficient rendering with React.memo optimization
- Minimal re-renders using useMemo for calculations
- Smooth 60fps animations
- Responsive to real-time data updates

## Testing

Unit tests included in `PowerMap.test.tsx`:
- Component rendering
- Status count calculations
- Empty state handling
- Priority tier display
- Interactive features