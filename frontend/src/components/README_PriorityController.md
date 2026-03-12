# Priority Controller Component

A professional drag-and-drop priority management interface for the Bharat-Grid AI dashboard.

## Features

✅ **Three Priority Tiers**: Critical, Essential, Non-Essential  
✅ **Drag & Drop**: Smooth animations with framer-motion and dnd-kit  
✅ **Industrial Design**: Clean Tailwind CSS styling with subtle glows  
✅ **Visual Feedback**: Color-coded tiers with hover effects  
✅ **Save Configuration**: Logs priority changes to console  
✅ **Responsive Layout**: Works on different screen sizes  

## Installation

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities framer-motion
   ```

2. **Import the Component**:
   ```tsx
   import PriorityController from './components/PriorityController';
   ```

## Usage

### Basic Integration

```tsx
import React from 'react';
import PriorityController from './components/PriorityController';

function App() {
  return (
    <div className="h-screen">
      <PriorityController />
    </div>
  );
}
```

### Integration with Router

```tsx
import { Routes, Route } from 'react-router-dom';
import PriorityController from './components/PriorityController';

function App() {
  return (
    <Routes>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/priority-settings" element={<PriorityController />} />
    </Routes>
  );
}
```

### Integration with Existing Layout

```tsx
import React, { useState } from 'react';
import Layout from './components/Layout';
import PriorityController from './components/PriorityController';

function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <Layout>
      {activeTab === 'priority-settings' ? (
        <PriorityController />
      ) : (
        <YourExistingDashboard />
      )}
    </Layout>
  );
}
```

## Component Structure

```
PriorityController/
├── PriorityController.tsx     # Main component
├── DraggableLoadCard         # Individual load cards
├── PriorityTierColumn        # Tier containers
└── README_PriorityController.md
```

## Data Structure

### Load Items
```typescript
interface LoadItem {
  id: string;
  name: string;
  type: 'hospital' | 'factory' | 'school' | 'society' | 'water_pump';
  description: string;
  icon: string;
}
```

### Priority Tiers
```typescript
interface PriorityTier {
  id: string;
  name: string;
  level: number;           // 1, 2, or 3
  description: string;
  bgColor: string;         // Tailwind background class
  borderColor: string;     // Tailwind border class
  glowColor: string;       // Tailwind shadow class
  items: LoadItem[];
}
```

## Customization

### Adding New Load Types

1. **Update the LoadItem type**:
   ```typescript
   type: 'hospital' | 'factory' | 'school' | 'society' | 'water_pump' | 'your_new_type';
   ```

2. **Add to initial data**:
   ```typescript
   const newLoad: LoadItem = {
     id: 'new-load-1',
     name: 'Your New Load',
     type: 'your_new_type',
     description: 'Description here',
     icon: '🔌'
   };
   ```

### Changing Tier Colors

```typescript
const customTier: PriorityTier = {
  // ... other properties
  bgColor: 'bg-purple-50',
  borderColor: 'border-purple-200',
  glowColor: 'shadow-purple-100',
};
```

### Backend Integration

Replace the console.log in `handleSaveConfiguration`:

```typescript
const handleSaveConfiguration = async () => {
  const configuration = tiers.map(tier => ({
    tier: tier.level,
    name: tier.name,
    items: tier.items.map(item => ({
      id: item.id,
      name: item.name,
      type: item.type
    }))
  }));

  try {
    // Send to your backend API
    await fetch('/api/priority-configuration', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(configuration)
    });
    
    setHasChanges(false);
    // Show success message
  } catch (error) {
    console.error('Failed to save configuration:', error);
  }
};
```

## Styling

The component uses Tailwind CSS classes. Key design elements:

- **Tier 1**: Red glow (`bg-red-50`, `border-red-200`, `shadow-red-100`)
- **Tier 2**: Yellow accent (`bg-yellow-50`, `border-yellow-200`)  
- **Tier 3**: Gray neutral (`bg-gray-50`, `border-gray-200`)
- **Cards**: White background with subtle shadows
- **Animations**: Framer Motion for smooth transitions

## Demo

Run the demo component to see the Priority Controller in action:

```tsx
import PriorityControllerDemo from './components/PriorityControllerDemo';

function App() {
  return <PriorityControllerDemo />;
}
```

## Performance

- **Optimized Rendering**: Uses React.memo and proper key props
- **Smooth Animations**: 60fps animations with framer-motion
- **Efficient Drag & Drop**: dnd-kit provides excellent performance
- **Minimal Re-renders**: State updates are optimized

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

```json
{
  "@dnd-kit/core": "^6.1.0",
  "@dnd-kit/sortable": "^8.0.0", 
  "@dnd-kit/utilities": "^3.2.2",
  "framer-motion": "^10.16.5"
}
```