export interface MetricsData {
  performance: ChartData[];
  resources: ChartData[];
  errors: ChartData[];
  loadTests: LoadTestResult[];
}

export interface ChartData {
  timestamp: string;
  value: number;
  [key: string]: any;
}

export interface LoadTestResult {
  name: string;
  timestamp: string;
  requestsPerSecond: number;
  p95ResponseTime: number;
  errorRate: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
}

export interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  metric?: string;
  value?: number;
  threshold?: number;
}

export interface WebSocketUpdate {
  type: keyof MetricsData;
  data: ChartData | LoadTestResult;
  alerts?: Alert[];
} 