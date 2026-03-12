import React from 'react';
import { Outlet } from 'react-router-dom';

interface LayoutProps {
  children?: React.ReactNode;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  isGridDown?: boolean;
  onGridToggle?: () => void;
  wsState?: { isConnected: boolean; isConnecting: boolean; error: string | null };
}

export const Layout: React.FC<LayoutProps> = ({ 
  children, 
  activeTab = 'dashboard', 
  onTabChange, 
  isGridDown = false, 
  onGridToggle,
  wsState
}) => {
  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'priority', name: 'Priority Settings', icon: '⚡' }
  ];

  return (
    <div className={`min-h-screen transition-colors duration-700 ease-in-out ${isGridDown ? 'bg-slate-950' : 'bg-slate-900'}`}>
      <header className={`border-b transition-colors duration-700 ease-in-out ${isGridDown ? 'bg-red-950/30 border-red-900/50' : 'bg-slate-800 border-slate-700'}`}>
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
              {/* Connection Status Indicator */}
              {wsState && (
                <div className="flex items-center space-x-2 bg-slate-800/50 rounded-full px-3 py-1 border border-slate-700" title={wsState.error || (wsState.isConnected ? 'Connected' : wsState.isConnecting ? 'Connecting...' : 'Disconnected')}>
                  <div className={`w-3 h-3 rounded-full ${
                    wsState.isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' :
                    wsState.isConnecting ? 'bg-yellow-500 animate-pulse' :
                    'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'
                  }`}></div>
                  <span className="text-xs font-medium text-slate-300 hidden sm:inline-block">
                    {wsState.isConnected ? 'Live' : wsState.isConnecting ? 'Connecting' : 'Offline'}
                  </span>
                </div>
              )}
              
              <div className="text-sm text-slate-400 hidden md:block">
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