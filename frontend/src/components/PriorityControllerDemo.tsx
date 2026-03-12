import React, { useState } from 'react';
import { Settings, ArrowLeft } from 'lucide-react';
import PriorityController from './PriorityController';

/**
 * Demo component showing how to integrate Priority Controller
 * into your existing Bharat-Grid AI dashboard
 */
export const PriorityControllerDemo: React.FC = () => {
  const [showPriorityController, setShowPriorityController] = useState(false);

  if (showPriorityController) {
    return (
      <div className="h-screen bg-slate-50">
        {/* Simple Header */}
        <div className="bg-white border-b border-slate-200 px-6 py-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowPriorityController(false)}
              className="flex items-center space-x-2 text-slate-600 hover:text-slate-800 transition-colors"
            >
              <ArrowLeft size={20} />
              <span>Back to Dashboard</span>
            </button>
            <div className="h-6 w-px bg-slate-300"></div>
            <h1 className="text-xl font-semibold text-slate-800">Bharat-Grid AI</h1>
          </div>
        </div>

        {/* Priority Controller */}
        <PriorityController />
      </div>
    );
  }

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-800 mb-8">
          Bharat-Grid AI Dashboard
        </h1>
        
        {/* Demo Card */}
        <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-800">Priority Management</h2>
              <p className="text-slate-600 mt-1">
                Configure load priorities for optimal power allocation
              </p>
            </div>
            <Settings className="text-slate-400" size={24} />
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="font-semibold text-red-800">Tier 1 - Critical</div>
                <div className="text-red-600">1 load assigned</div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="font-semibold text-yellow-800">Tier 2 - Essential</div>
                <div className="text-yellow-600">2 loads assigned</div>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="font-semibold text-gray-800">Tier 3 - Non-Essential</div>
                <div className="text-gray-600">2 loads assigned</div>
              </div>
            </div>
            
            <button
              onClick={() => setShowPriorityController(true)}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              Open Priority Controller
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PriorityControllerDemo;