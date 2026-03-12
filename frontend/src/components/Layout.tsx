import React from 'react';
import { Outlet } from 'react-router-dom';

interface LayoutProps {
  children?: React.ReactNode;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  isGridDown?: boolean;
  onGridToggle?: () => void;
}

export const Layout: React.FC<LayoutProps> = ({ 
  children, 
  activeTab = 'dashboard', 
  onTabChange, 
  isGridDown = false, 
  onGridToggle 
}) => {
  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'priority', name: 'Priority Settings', icon: '⚡' }
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-white">
                Bharat-Grid AI
              </h1>
              <span className="ml-3 px-2 py-1 text-xs font-medium bg-primary-600 text-white rounded-full">
                v1.0.0
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-slate-400">
                Real-time Energy Distribution
              </div>
              {/* Grid Failure Simulation Button */}
              {onGridToggle && (
                <button
                  onClick={onGridToggle}
                  className={`
                    px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-200 shadow-lg
                    ${isGridDown 
                      ? 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-emerald-500/25' 
                      : 'bg-red-600 text-white hover:bg-red-700 shadow-red-500/25'
                    }
                  `}
                >
                  {isGridDown ? 'RESTORE GRID' : 'SIMULATE GRID FAILURE'}
                </button>
              )}
            </div>
          </div>
          
          {/* Tab Navigation */}
          {onTabChange && (
            <div className="border-t border-slate-700">
              <nav className="flex space-x-8" aria-label="Tabs">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => onTabChange(tab.id)}
                    className={`
                      flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                      ${activeTab === tab.id
                        ? 'border-primary-500 text-primary-400'
                        : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300'
                      }
                    `}
                  >
                    <span>{tab.icon}</span>
                    <span>{tab.name}</span>
                  </button>
                ))}
              </nav>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children || <Outlet />}
      </main>
    </div>
  );
};

export default Layout;