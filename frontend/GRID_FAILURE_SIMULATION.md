# Grid Failure Simulation Feature

## ✅ Implementation Complete

Added a "Simulate Grid Failure" feature to the existing dashboard with minimal code changes.

### 🔧 Changes Made

#### 1. State Management (App.tsx)
```typescript
const [isGridDown, setIsGridDown] = useState(false);
```

#### 2. Header Update (Layout.tsx)
- Added **Red Button** in top header: "SIMULATE GRID FAILURE"
- Button toggles `isGridDown` state
- When `isGridDown = true`: Button becomes **Green** and shows "RESTORE GRID"
- Added props: `isGridDown`, `onGridToggle`

#### 3. UI Logic - Visual Impact

**Critical Loads (Tier 1) - Enhanced when grid is down:**
```css
className={isGridDown ? 'text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.8)]' : ''}
```
- Applied to Total Supply gauge (represents critical hospital/ICU stats)
- Creates emerald glow effect showing priority power routing

**Non-Essential Loads (Tier 3) - Dimmed when grid is down:**
```css
className={isGridDown ? 'opacity-30 grayscale' : ''}
```
- Applied to Total Demand gauge and Stream Table (represents residential/non-essential)
- Shows these loads are powered off during grid failure

**Power Map - Subtle grid failure indication:**
```css
className={isGridDown ? 'opacity-90 saturate-50' : ''}
```
- Slightly desaturated to show grid stress

#### 4. Notification System
- Toast notification: "🚨 Grid Failure Detected! Pathway AI rerouting power to Tier 1 nodes in 8.4ms."
- Restoration notification: "✅ Grid Restored! All systems operational."
- Currently using `alert()` - can be replaced with proper toast library

### 🎯 User Experience
1. **Normal State**: Red "SIMULATE GRID FAILURE" button in header
2. **Click Button**: 
   - Button turns green → "RESTORE GRID"
   - Critical loads glow emerald (showing priority)
   - Non-essential loads fade out (showing power cut)
   - Toast notification appears
3. **Click Again**: Everything returns to normal state

### 🚀 Technical Benefits
- **Minimal Code Changes**: Only modified 2 files
- **No Breaking Changes**: Existing functionality preserved
- **Visual Feedback**: Clear indication of grid failure state
- **Realistic Simulation**: Shows actual priority-based power allocation
- **Ready for Backend**: State can easily be connected to real grid failure API

The feature demonstrates how Pathway AI would handle real grid failures by prioritizing critical infrastructure (hospitals) while cutting non-essential loads (residential areas).