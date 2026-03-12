import React, { useState } from 'react';
import { DndContext, DragEndEvent, DragOverlay, DragStartEvent } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { motion, AnimatePresence } from 'framer-motion';

// Types
interface LoadItem {
  id: string;
  name: string;
  type: 'hospital' | 'factory' | 'school' | 'society' | 'water_pump';
  description: string;
  icon: string;
}

interface PriorityTier {
  id: string;
  name: string;
  level: number;
  description: string;
  bgColor: string;
  borderColor: string;
  glowColor: string;
  items: LoadItem[];
}

// Initial data
const initialLoads: LoadItem[] = [
  {
    id: 'hospital-1',
    name: 'City Hospital',
    type: 'hospital',
    description: 'ICU & Emergency Services',
    icon: '🏥'
  },
  {
    id: 'factory-1',
    name: 'Manufacturing Plant',
    type: 'factory',
    description: 'Production Line 1',
    icon: '🏭'
  },
  {
    id: 'school-1',
    name: 'Primary School',
    type: 'school',
    description: 'Educational Facility',
    icon: '🏫'
  },
  {
    id: 'society-1',
    name: 'Residential Complex',
    type: 'society',
    description: 'Housing Society A',
    icon: '🏘️'
  },
  {
    id: 'water-pump-1',
    name: 'Water Treatment',
    type: 'water_pump',
    description: 'Main Water Pump Station',
    icon: '💧'
  }
];

const initialTiers: PriorityTier[] = [
  {
    id: 'tier-1',
    name: 'Tier 1 - Critical',
    level: 1,
    description: 'Never Cut - Essential Services',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    glowColor: 'shadow-red-100',
    items: [initialLoads[0]] // Hospital starts in Tier 1
  },
  {
    id: 'tier-2',
    name: 'Tier 2 - Essential',
    level: 2,
    description: 'Reduce if Necessary',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    glowColor: 'shadow-yellow-100',
    items: [initialLoads[1], initialLoads[4]] // Factory and Water Pump
  },
  {
    id: 'tier-3',
    name: 'Tier 3 - Non-Essential',
    level: 3,
    description: 'First to Cut',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    glowColor: 'shadow-gray-100',
    items: [initialLoads[2], initialLoads[3]] // School and Society
  }
];
// Draggable Load Card Component
const DraggableLoadCard: React.FC<{ 
  item: LoadItem; 
  isDragging?: boolean;
}> = ({ item, isDragging = false }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isSortableDragging,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        bg-white rounded-lg border-2 border-slate-200 p-4 cursor-grab active:cursor-grabbing
        shadow-sm hover:shadow-md transition-all duration-200
        ${isDragging || isSortableDragging ? 'opacity-50 rotate-2 shadow-lg' : ''}
        ${isDragging ? 'z-50' : ''}
      `}
    >
      <div className="flex items-center space-x-3">
        <div className="text-2xl">{item.icon}</div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-slate-800 truncate">{item.name}</h4>
          <p className="text-sm text-slate-500 truncate">{item.description}</p>
        </div>
        <div className="flex-shrink-0">
          <div className="w-2 h-8 bg-slate-300 rounded-full opacity-50"></div>
        </div>
      </div>
    </motion.div>
  );
};

// Priority Tier Column Component
const PriorityTierColumn: React.FC<{
  tier: PriorityTier;
  isOver?: boolean;
}> = ({ tier, isOver = false }) => {
  return (
    <div className="flex-1 min-h-0">
      <motion.div
        layout
        className={`
          h-full rounded-xl border-2 p-6 transition-all duration-300
          ${tier.bgColor} ${tier.borderColor} ${tier.glowColor}
          ${isOver ? 'shadow-lg scale-[1.02] border-blue-400' : 'shadow-sm'}
        `}
      >
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-bold text-slate-800">{tier.name}</h3>
            <span className="bg-slate-800 text-white text-xs px-2 py-1 rounded-full">
              {tier.items.length}
            </span>
          </div>
          <p className="text-sm text-slate-600">{tier.description}</p>
        </div>

        {/* Drop Zone */}
        <SortableContext items={tier.items.map(item => item.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-3 min-h-[200px]">
            <AnimatePresence>
              {tier.items.map((item) => (
                <DraggableLoadCard key={item.id} item={item} />
              ))}
            </AnimatePresence>
            
            {/* Empty State */}
            {tier.items.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center justify-center h-32 border-2 border-dashed border-slate-300 rounded-lg"
              >
                <p className="text-slate-400 text-sm">Drop items here</p>
              </motion.div>
            )}
          </div>
        </SortableContext>
      </motion.div>
    </div>
  );
};
// Main Priority Controller Component
export const PriorityController: React.FC = () => {
  const [tiers, setTiers] = useState<PriorityTier[]>(initialTiers);
  const [activeItem, setActiveItem] = useState<LoadItem | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const item = findItemById(active.id as string);
    setActiveItem(item);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveItem(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Find source and destination tiers
    const sourceTier = tiers.find(tier => tier.items.some(item => item.id === activeId));
    const destinationTier = tiers.find(tier => tier.id === overId || tier.items.some(item => item.id === overId));

    if (!sourceTier || !destinationTier) return;

    // If moving to a different tier
    if (sourceTier.id !== destinationTier.id) {
      const item = sourceTier.items.find(item => item.id === activeId);
      if (!item) return;

      setTiers(prevTiers => {
        const newTiers = prevTiers.map(tier => {
          if (tier.id === sourceTier.id) {
            return {
              ...tier,
              items: tier.items.filter(item => item.id !== activeId)
            };
          }
          if (tier.id === destinationTier.id) {
            return {
              ...tier,
              items: [...tier.items, item]
            };
          }
          return tier;
        });
        return newTiers;
      });

      setHasChanges(true);
    }
  };

  const findItemById = (id: string): LoadItem | null => {
    for (const tier of tiers) {
      const item = tier.items.find(item => item.id === id);
      if (item) return item;
    }
    return null;
  };

  const handleSaveConfiguration = () => {
    const configuration = tiers.map(tier => ({
      tier: tier.level,
      name: tier.name,
      items: tier.items.map(item => ({
        id: item.id,
        name: item.name,
        type: item.type
      }))
    }));

    console.log('🔧 Priority Configuration Saved:', configuration);
    
    // Here you would typically send this to your backend API
    // Example: await savePriorityConfiguration(configuration);
    
    setHasChanges(false);
    
    // Show success feedback
    alert('Priority configuration saved successfully!');
  };

  const handleResetConfiguration = () => {
    setTiers(initialTiers);
    setHasChanges(false);
  };

  return (
    <div className="h-full bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-800">Priority Controller</h1>
            <p className="text-slate-600 mt-1">
              Drag and drop loads to configure priority tiers for power allocation
            </p>
          </div>
          
          {/* Action Buttons */}
          <div className="flex space-x-3">
            <button
              onClick={handleResetConfiguration}
              className="px-4 py-2 text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Reset
            </button>
            <motion.button
              onClick={handleSaveConfiguration}
              disabled={!hasChanges}
              whileHover={{ scale: hasChanges ? 1.05 : 1 }}
              whileTap={{ scale: hasChanges ? 0.95 : 1 }}
              className={`
                px-6 py-2 rounded-lg font-semibold transition-all duration-200
                ${hasChanges 
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg' 
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }
              `}
            >
              {hasChanges ? 'Save Configuration' : 'No Changes'}
            </motion.button>
          </div>
        </div>

        {/* Status Indicator */}
        {hasChanges && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-amber-100 border border-amber-300 text-amber-800 px-4 py-2 rounded-lg text-sm"
          >
            ⚠️ You have unsaved changes to the priority configuration
          </motion.div>
        )}
      </div>

      {/* Drag and Drop Context */}
      <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div className="flex space-x-6 h-[calc(100vh-280px)]">
          {tiers.map((tier) => (
            <PriorityTierColumn key={tier.id} tier={tier} />
          ))}
        </div>

        {/* Drag Overlay */}
        <DragOverlay>
          {activeItem ? (
            <DraggableLoadCard item={activeItem} isDragging />
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Legend */}
      <div className="mt-6 bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="font-semibold text-slate-800 mb-3">Priority Levels</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-200 border border-red-300 rounded"></div>
            <span><strong>Tier 1:</strong> Critical loads that are never cut off</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-200 border border-yellow-300 rounded"></div>
            <span><strong>Tier 2:</strong> Essential loads that may be reduced</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gray-200 border border-gray-300 rounded"></div>
            <span><strong>Tier 3:</strong> Non-essential loads cut first</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PriorityController;