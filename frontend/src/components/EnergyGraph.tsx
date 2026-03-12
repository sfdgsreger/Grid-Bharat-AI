import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface EnergyGraphProps {
  totalSupply: number;
  totalDemand: number;
  decisionLatency?: number; // Prop for Task 5: Latency Counter
}

interface DataPoint {
  time: string;
  Supply: number;
  Demand: number;
  timestamp: number;
}

export const EnergyGraph: React.FC<EnergyGraphProps> = React.memo(({ totalSupply, totalDemand, decisionLatency }) => {
  const [data, setData] = useState<DataPoint[]>([]);

  useEffect(() => {
    const now = Date.now();
    const newDataPoint: DataPoint = {
      time: new Date(now).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' }),
      Supply: totalSupply,
      Demand: totalDemand,
      timestamp: now,
    };

    setData((prev) => {
      // Keep only last 60 seconds of data to form a rolling window (~600 points max at 100ms intervals)
      const cutoff = now - 60000;
      const recentData = prev.filter(p => p.timestamp >= cutoff);
      return [...recentData, newDataPoint];
    });
  }, [totalSupply, totalDemand]);

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 shadow-xl overflow-hidden">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-xl font-semibold text-white">Real-Time Performance</h2>
          <p className="text-sm text-slate-400">Total Supply vs Demand (Rolling 60s)</p>
        </div>
        
        {/* Task 5: Latency Counter for O(n) decision */}
        {decisionLatency !== undefined && (
          <div className="flex items-center space-x-3 bg-slate-900 px-4 py-2 rounded-lg border border-slate-700 shadow-inner">
            <span className="text-sm font-medium text-slate-400">Allocation Latency:</span>
            <div className="flex items-center space-x-2">
              <span className={`text-base font-mono font-bold ${
                decisionLatency < 10 ? 'text-emerald-400' : 
                decisionLatency < 20 ? 'text-amber-400' : 'text-red-400'
              }`}>
                {decisionLatency.toFixed(1)}ms
              </span>
              <div className={`w-2.5 h-2.5 rounded-full ${
                decisionLatency < 10 ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 
                decisionLatency < 20 ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]'
              } ${decisionLatency < 15 ? 'animate-pulse' : ''}`}></div>
            </div>
          </div>
        )}
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorSupply" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis 
              dataKey="time" 
              stroke="#94a3b8" 
              fontSize={12}
              tickMargin={10}
              minTickGap={40}
            />
            <YAxis 
              stroke="#94a3b8" 
              fontSize={12}
              tickFormatter={(value) => `${value}kW`} 
              width={65}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
              itemStyle={{ fontSize: '14px', fontWeight: 600 }}
              labelStyle={{ color: '#94a3b8', marginBottom: '6px' }}
            />
            <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ paddingBottom: '20px' }} />
            <Area 
              type="monotone" 
              dataKey="Demand" 
              stroke="#ef4444" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorDemand)" 
              isAnimationActive={false} // Prevents re-render lag at 60fps
            />
            <Area 
              type="monotone" 
              dataKey="Supply" 
              stroke="#3b82f6" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorSupply)" 
              isAnimationActive={false} // Prevents re-render lag at 60fps
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

export default EnergyGraph;
