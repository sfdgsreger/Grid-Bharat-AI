/**
 * Dashboard Performance Monitor
 * 
 * Monitors and optimizes dashboard performance to ensure 60fps target
 * Requirements: 4.4, 7.5
 */

export interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  renderTime: number;
  updateTime: number;
  memoryUsage: number;
  timestamp: number;
}

export interface PerformanceTarget {
  name: string;
  target: number;
  current: number;
  status: 'pass' | 'warning' | 'fail';
}

class DashboardPerformanceMonitor {
  private frameCount = 0;
  private lastFrameTime = performance.now();
  private frameTimeHistory: number[] = [];
  private renderTimeHistory: number[] = [];
  private updateTimeHistory: number[] = [];
  private isMonitoring = false;
  private animationFrameId: number | null = null;
  
  // Performance targets
  private readonly TARGET_FPS = 60;
  private readonly TARGET_FRAME_TIME = 16.67; // 1000ms / 60fps
  private readonly WARNING_THRESHOLD = 0.8; // 80% of target
  
  // Optimization flags
  private optimizations = {
    requestAnimationFrame: true,
    memoryOptimization: true,
    batchUpdates: true,
    virtualScrolling: false,
    componentMemoization: true
  };
  
  // Performance history (keep last 100 measurements)
  private readonly HISTORY_SIZE = 100;
  
  constructor() {
    this.bindMethods();
  }
  
  private bindMethods() {
    this.measureFrame = this.measureFrame.bind(this);
    this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
  }
  
  /**
   * Start performance monitoring
   */
  startMonitoring(): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.frameCount = 0;
    this.lastFrameTime = performance.now();
    
    // Start frame measurement loop
    this.measureFrame();
    
    // Listen for visibility changes to pause monitoring when tab is hidden
    document.addEventListener('visibilitychange', this.handleVisibilityChange);
    
    console.log('📊 Dashboard performance monitoring started');
  }
  
  /**
   * Stop performance monitoring
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) return;
    
    this.isMonitoring = false;
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    
    console.log('📊 Dashboard performance monitoring stopped');
  }
  
  /**
   * Measure frame performance
   */
  private measureFrame(): void {
    if (!this.isMonitoring) return;
    
    const currentTime = performance.now();
    const frameTime = currentTime - this.lastFrameTime;
    
    // Record frame time
    this.frameTimeHistory.push(frameTime);
    if (this.frameTimeHistory.length > this.HISTORY_SIZE) {
      this.frameTimeHistory.shift();
    }
    
    // Update counters
    this.frameCount++;
    this.lastFrameTime = currentTime;
    
    // Check for performance issues
    if (frameTime > this.TARGET_FRAME_TIME * 1.5) {
      console.warn(`⚠️ Slow frame detected: ${frameTime.toFixed(2)}ms (target: ${this.TARGET_FRAME_TIME}ms)`);
    }
    
    // Schedule next measurement
    this.animationFrameId = requestAnimationFrame(this.measureFrame);
  }
  
  /**
   * Measure render time for a component update
   */
  measureRender<T>(renderFunction: () => T, componentName?: string): T {
    const startTime = performance.now();
    const result = renderFunction();
    const renderTime = performance.now() - startTime;
    
    // Record render time
    this.renderTimeHistory.push(renderTime);
    if (this.renderTimeHistory.length > this.HISTORY_SIZE) {
      this.renderTimeHistory.shift();
    }
    
    // Log slow renders
    if (renderTime > 5) { // 5ms threshold for component renders
      console.warn(`⚠️ Slow render in ${componentName || 'component'}: ${renderTime.toFixed(2)}ms`);
    }
    
    return result;
  }
  
  /**
   * Measure update time for data processing
   */
  measureUpdate<T>(updateFunction: () => T, operationName?: string): T {
    const startTime = performance.now();
    const result = updateFunction();
    const updateTime = performance.now() - startTime;
    
    // Record update time
    this.updateTimeHistory.push(updateTime);
    if (this.updateTimeHistory.length > this.HISTORY_SIZE) {
      this.updateTimeHistory.shift();
    }
    
    // Log slow updates
    if (updateTime > 2) { // 2ms threshold for data updates
      console.warn(`⚠️ Slow update in ${operationName || 'operation'}: ${updateTime.toFixed(2)}ms`);
    }
    
    return result;
  }
  
  /**
   * Get current performance metrics
   */
  getMetrics(): PerformanceMetrics {
    const currentFps = this.calculateFPS();
    const avgFrameTime = this.calculateAverage(this.frameTimeHistory);
    const avgRenderTime = this.calculateAverage(this.renderTimeHistory);
    const avgUpdateTime = this.calculateAverage(this.updateTimeHistory);
    
    return {
      fps: currentFps,
      frameTime: avgFrameTime,
      renderTime: avgRenderTime,
      updateTime: avgUpdateTime,
      memoryUsage: this.getMemoryUsage(),
      timestamp: Date.now()
    };
  }
  
  /**
   * Get performance targets with current status
   */
  getPerformanceTargets(): PerformanceTarget[] {
    const metrics = this.getMetrics();
    
    return [
      {
        name: 'Frame Rate',
        target: this.TARGET_FPS,
        current: metrics.fps,
        status: this.getStatus(metrics.fps, this.TARGET_FPS, false) // Higher is better
      },
      {
        name: 'Frame Time',
        target: this.TARGET_FRAME_TIME,
        current: metrics.frameTime,
        status: this.getStatus(metrics.frameTime, this.TARGET_FRAME_TIME, true) // Lower is better
      },
      {
        name: 'Render Time',
        target: 5, // 5ms target for component renders
        current: metrics.renderTime,
        status: this.getStatus(metrics.renderTime, 5, true) // Lower is better
      },
      {
        name: 'Update Time',
        target: 2, // 2ms target for data updates
        current: metrics.updateTime,
        status: this.getStatus(metrics.updateTime, 2, true) // Lower is better
      }
    ];
  }
  
  /**
   * Calculate current FPS
   */
  private calculateFPS(): number {
    if (this.frameTimeHistory.length < 10) return 0;
    
    const recentFrames = this.frameTimeHistory.slice(-30); // Last 30 frames
    const avgFrameTime = this.calculateAverage(recentFrames);
    
    return avgFrameTime > 0 ? 1000 / avgFrameTime : 0;
  }
  
  /**
   * Calculate average of an array
   */
  private calculateAverage(values: number[]): number {
    if (values.length === 0) return 0;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }
  
  /**
   * Get memory usage (if available)
   */
  private getMemoryUsage(): number {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / 1024 / 1024; // MB
    }
    return 0;
  }
  
  /**
   * Get status based on target comparison
   */
  private getStatus(current: number, target: number, lowerIsBetter: boolean): 'pass' | 'warning' | 'fail' {
    const ratio = lowerIsBetter ? current / target : target / current;
    
    if (ratio <= 1) return 'pass';
    if (ratio <= 1.2) return 'warning'; // 20% tolerance
    return 'fail';
  }
  
  /**
   * Handle visibility change to pause monitoring when tab is hidden
   */
  private handleVisibilityChange(): void {
    if (document.hidden) {
      // Pause monitoring when tab is hidden
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
    } else {
      // Resume monitoring when tab becomes visible
      if (this.isMonitoring && !this.animationFrameId) {
        this.lastFrameTime = performance.now();
        this.measureFrame();
      }
    }
  }
  
  /**
   * Enable or disable specific optimization
   */
  enableOptimization(optimization: keyof typeof this.optimizations, enabled: boolean): void {
    this.optimizations[optimization] = enabled;
    console.log(`${enabled ? 'Enabled' : 'Disabled'} ${optimization} optimization`);
  }
  
  /**
   * Get optimization status
   */
  getOptimizations(): Record<string, boolean> {
    return { ...this.optimizations };
  }
  
  /**
   * Generate performance report
   */
  generateReport(): string {
    const metrics = this.getMetrics();
    const targets = this.getPerformanceTargets();
    
    const report = [
      'DASHBOARD PERFORMANCE REPORT',
      '=' .repeat(40),
      '',
      'CURRENT METRICS',
      '-'.repeat(20),
      `FPS: ${metrics.fps.toFixed(1)} (target: ${this.TARGET_FPS})`,
      `Frame Time: ${metrics.frameTime.toFixed(2)}ms (target: ${this.TARGET_FRAME_TIME}ms)`,
      `Render Time: ${metrics.renderTime.toFixed(2)}ms (target: 5ms)`,
      `Update Time: ${metrics.updateTime.toFixed(2)}ms (target: 2ms)`,
      `Memory Usage: ${metrics.memoryUsage.toFixed(1)}MB`,
      '',
      'TARGET STATUS',
      '-'.repeat(15),
      ...targets.map(target => {
        const status = target.status === 'pass' ? '✓' : target.status === 'warning' ? '⚠' : '✗';
        return `${status} ${target.name}: ${target.current.toFixed(2)} / ${target.target}`;
      }),
      '',
      'OPTIMIZATIONS',
      '-'.repeat(15),
      ...Object.entries(this.optimizations).map(([name, enabled]) => {
        const status = enabled ? '✓ Enabled' : '✗ Disabled';
        return `${name}: ${status}`;
      }),
      '',
      `Report generated at: ${new Date().toISOString()}`
    ];
    
    return report.join('\n');
  }
  
  /**
   * Run performance test
   */
  async runPerformanceTest(duration: number = 10000): Promise<PerformanceMetrics[]> {
    console.log(`🧪 Running dashboard performance test for ${duration}ms`);
    
    const results: PerformanceMetrics[] = [];
    const startTime = Date.now();
    
    // Start monitoring if not already started
    const wasMonitoring = this.isMonitoring;
    if (!wasMonitoring) {
      this.startMonitoring();
    }
    
    // Collect metrics every second
    const interval = setInterval(() => {
      results.push(this.getMetrics());
    }, 1000);
    
    // Wait for test duration
    await new Promise(resolve => setTimeout(resolve, duration));
    
    // Clean up
    clearInterval(interval);
    if (!wasMonitoring) {
      this.stopMonitoring();
    }
    
    // Calculate test summary
    const avgFps = results.reduce((sum, m) => sum + m.fps, 0) / results.length;
    const minFps = Math.min(...results.map(m => m.fps));
    const maxFrameTime = Math.max(...results.map(m => m.frameTime));
    
    console.log(`🧪 Performance test completed:`);
    console.log(`   Average FPS: ${avgFps.toFixed(1)}`);
    console.log(`   Minimum FPS: ${minFps.toFixed(1)}`);
    console.log(`   Maximum Frame Time: ${maxFrameTime.toFixed(2)}ms`);
    
    const testPassed = avgFps >= this.TARGET_FPS * 0.9 && minFps >= this.TARGET_FPS * 0.7;
    console.log(`   Test Result: ${testPassed ? '✓ PASS' : '✗ FAIL'}`);
    
    return results;
  }
}

// Global performance monitor instance
export const performanceMonitor = new DashboardPerformanceMonitor();

// React hook for performance monitoring
export function usePerformanceMonitor() {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics | null>(null);
  const [isMonitoring, setIsMonitoring] = React.useState(false);
  
  React.useEffect(() => {
    if (isMonitoring) {
      performanceMonitor.startMonitoring();
      
      // Update metrics every second
      const interval = setInterval(() => {
        setMetrics(performanceMonitor.getMetrics());
      }, 1000);
      
      return () => {
        clearInterval(interval);
        performanceMonitor.stopMonitoring();
      };
    }
  }, [isMonitoring]);
  
  return {
    metrics,
    isMonitoring,
    startMonitoring: () => setIsMonitoring(true),
    stopMonitoring: () => setIsMonitoring(false),
    getTargets: () => performanceMonitor.getPerformanceTargets(),
    generateReport: () => performanceMonitor.generateReport(),
    runTest: (duration?: number) => performanceMonitor.runPerformanceTest(duration)
  };
}

// Performance measurement decorators
export function measureRender(componentName: string) {
  return function<T extends (...args: any[]) => any>(target: T): T {
    return ((...args: any[]) => {
      return performanceMonitor.measureRender(() => target(...args), componentName);
    }) as T;
  };
}

export function measureUpdate(operationName: string) {
  return function<T extends (...args: any[]) => any>(target: T): T {
    return ((...args: any[]) => {
      return performanceMonitor.measureUpdate(() => target(...args), operationName);
    }) as T;
  };
}

// Utility functions for performance optimization
export const PerformanceUtils = {
  /**
   * Debounce function to limit update frequency
   */
  debounce<T extends (...args: any[]) => any>(func: T, delay: number): T {
    let timeoutId: NodeJS.Timeout;
    return ((...args: any[]) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func(...args), delay);
    }) as T;
  },
  
  /**
   * Throttle function to limit execution frequency
   */
  throttle<T extends (...args: any[]) => any>(func: T, delay: number): T {
    let lastCall = 0;
    return ((...args: any[]) => {
      const now = Date.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        return func(...args);
      }
    }) as T;
  },
  
  /**
   * Request animation frame wrapper for smooth updates
   */
  requestAnimationFrame(callback: () => void): number {
    return requestAnimationFrame(callback);
  },
  
  /**
   * Batch DOM updates to minimize reflows
   */
  batchDOMUpdates(updates: (() => void)[]): void {
    requestAnimationFrame(() => {
      updates.forEach(update => update());
    });
  }
};

export default performanceMonitor;