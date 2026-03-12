import React, { useEffect, useRef, useState } from 'react';
import type { LiveGaugeProps } from '../types';

/**
 * Real-time gauge component with smooth animations
 * 
 * Features:
 * - Smooth value transitions using CSS animations
 * - 60fps performance during updates
 * - Customizable colors and styling
 * - Responsive design
 * 
 * Requirements: 4.4, 12.2
 */
export const LiveGauge: React.FC<LiveGaugeProps> = ({
  title,
  value,
  max,
  unit,
  color = 'blue'
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const [animatedValue, setAnimatedValue] = useState(0);
  const animationRef = useRef<number>();
  const startTimeRef = useRef<number>();
  const startValueRef = useRef<number>(0);

  // Color configurations
  const colorConfig = {
    blue: {
      primary: 'text-blue-400',
      secondary: 'text-blue-300',
      gradient: 'from-blue-500 to-blue-600',
      ring: 'ring-blue-500/20',
      glow: 'shadow-blue-500/20'
    },
    green: {
      primary: 'text-green-400',
      secondary: 'text-green-300',
      gradient: 'from-green-500 to-green-600',
      ring: 'ring-green-500/20',
      glow: 'shadow-green-500/20'
    },
    yellow: {
      primary: 'text-yellow-400',
      secondary: 'text-yellow-300',
      gradient: 'from-yellow-500 to-yellow-600',
      ring: 'ring-yellow-500/20',
      glow: 'shadow-yellow-500/20'
    },
    red: {
      primary: 'text-red-400',
      secondary: 'text-red-300',
      gradient: 'from-red-500 to-red-600',
      ring: 'ring-red-500/20',
      glow: 'shadow-red-500/20'
    }
  };

  const colors = colorConfig[color];

  // Smooth animation using requestAnimationFrame for 60fps
  const animateValue = (targetValue: number) => {
    const duration = 800; // 800ms animation duration
    
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    startTimeRef.current = performance.now();
    startValueRef.current = animatedValue;

    const animate = (currentTime: number) => {
      if (!startTimeRef.current) return;

      const elapsed = currentTime - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function for smooth animation (ease-out)
      const easeOut = 1 - Math.pow(1 - progress, 3);
      
      const currentValue = startValueRef.current + (targetValue - startValueRef.current) * easeOut;
      setAnimatedValue(currentValue);
      setDisplayValue(Math.round(currentValue));

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);
  };

  // Update animated value when value prop changes
  useEffect(() => {
    animateValue(value);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [value]);

  // Calculate percentage for visual representation
  const percentage = Math.min((animatedValue / max) * 100, 100);
  const safePercentage = Math.max(0, percentage);

  // Calculate stroke dash array for circular progress
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (safePercentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center space-y-4 p-4">
      {/* Title */}
      <h3 className="text-lg font-semibold text-white text-center">
        {title}
      </h3>

      {/* Circular Gauge */}
      <div className="relative">
        {/* Background circle */}
        <svg
          className="transform -rotate-90 w-32 h-32"
          viewBox="0 0 100 100"
        >
          {/* Background track */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            className="text-slate-700"
          />
          
          {/* Progress circle */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={`${colors.primary} transition-all duration-300 ease-out`}
            style={{
              filter: 'drop-shadow(0 0 6px currentColor)'
            }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`text-2xl font-bold ${colors.primary}`}>
            {displayValue.toLocaleString()}
          </div>
          <div className={`text-sm ${colors.secondary}`}>
            {unit}
          </div>
        </div>

        {/* Glow effect */}
        <div 
          className={`absolute inset-0 rounded-full bg-gradient-to-br ${colors.gradient} opacity-10 blur-xl`}
          style={{
            transform: 'scale(1.2)',
            zIndex: -1
          }}
        />
      </div>

      {/* Value details */}
      <div className="text-center space-y-1">
        <div className="flex items-center justify-center space-x-2 text-sm text-slate-400">
          <span>Max:</span>
          <span className="font-medium">{max.toLocaleString()} {unit}</span>
        </div>
        
        <div className="flex items-center justify-center space-x-2 text-sm text-slate-400">
          <span>Usage:</span>
          <span className={`font-medium ${colors.secondary}`}>
            {safePercentage.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Status indicator */}
      <div className="flex items-center space-x-2">
        <div 
          className={`w-2 h-2 rounded-full ${
            percentage > 90 ? 'bg-red-400 animate-pulse' :
            percentage > 75 ? 'bg-yellow-400' :
            'bg-green-400'
          }`}
        />
        <span className="text-xs text-slate-400">
          {percentage > 90 ? 'Critical' :
           percentage > 75 ? 'High' :
           'Normal'}
        </span>
      </div>
    </div>
  );
};

export default LiveGauge;