export interface ValidationResult {
  subsystem: string;
  status: 'pass' | 'fail' | 'skip' | 'warning';
  message: string;
  duration_ms: number;
  details?: Record<string, unknown>;
}

export interface ValidationReport {
  timestamp: string;
  overall_status: string;
  passed: number;
  failed: number;
  skipped: number;
  results: ValidationResult[];
}

export interface BenchmarkResult {
  name: string;
  duration_ms: number;
  operations_per_second: number;
  memory_mb: number;
  cpu_percent: number;
  status: 'pass' | 'fail';
}

export interface BenchmarkReport {
  timestamp: string;
  benchmarks: BenchmarkResult[];
  summary: {
    total_benchmarks: number;
    passed: number;
    avg_latency_ms: number;
    avg_memory_mb: number;
  };
  recommendations: string[];
}

export interface QualityGate {
  name: string;
  threshold: number;
  actual: number;
  status: 'pass' | 'fail';
  message: string;
}

export interface GateReport {
  timestamp: string;
  overall_pass: boolean;
  pass_count: number;
  fail_count: number;
  gates: QualityGate[];
}

export interface SecurityCheck {
  name: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'pass' | 'fail';
  description: string;
  recommendation: string;
}

export interface SecurityAuditReport {
  timestamp: string;
  overall_score: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  checks: SecurityCheck[];
}

export interface E2EScenario {
  id: string;
  name: string;
  description: string;
  status: 'pass' | 'fail';
  steps_passed: number;
  steps_failed: number;
  duration_ms: number;
  steps: Array<{
    action: string;
    status: 'pass' | 'fail';
    duration_ms: number;
  }>;
}
