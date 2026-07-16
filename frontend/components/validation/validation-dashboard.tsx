'use client';

import React, { useState, useEffect } from 'react';
import {
  Shield,
  Activity,
  Gauge,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Download,
  Play,
} from 'lucide-react';
import type {
  ValidationReport,
  BenchmarkReport,
  GateReport,
  SecurityAuditReport,
} from '@/types/validation';

type Tab = 'overview' | 'system' | 'benchmarks' | 'quality' | 'security';

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'overview', label: 'Overview', icon: <Activity className="w-4 h-4" /> },
  { id: 'system', label: 'System Validation', icon: <CheckCircle className="w-4 h-4" /> },
  { id: 'benchmarks', label: 'Benchmarks', icon: <Gauge className="w-4 h-4" /> },
  { id: 'quality', label: 'Quality Gates', icon: <AlertTriangle className="w-4 h-4" /> },
  { id: 'security', label: 'Security Audit', icon: <Shield className="w-4 h-4" /> },
];

const MOCK_VALIDATION: ValidationReport = {
  timestamp: new Date().toISOString(),
  overall_status: 'pass',
  passed: 14,
  failed: 1,
  skipped: 1,
  results: [
    { subsystem: 'API Gateway', status: 'pass', message: 'All endpoints healthy', duration_ms: 234 },
    { subsystem: 'Auth Service', status: 'pass', message: 'JWT validation working', duration_ms: 189 },
    { subsystem: 'Database', status: 'pass', message: 'Connection pool optimal', duration_ms: 56 },
    { subsystem: 'Cache Layer', status: 'pass', message: 'Redis cluster healthy', duration_ms: 12 },
    { subsystem: 'Message Queue', status: 'pass', message: 'RabbitMQ responsive', duration_ms: 78 },
    { subsystem: 'ML Pipeline', status: 'fail', message: 'Model inference timeout', duration_ms: 5023 },
    { subsystem: 'File Storage', status: 'pass', message: 'S3 bucket accessible', duration_ms: 145 },
    { subsystem: 'Logging', status: 'pass', message: 'ELK stack operational', duration_ms: 34 },
    { subsystem: 'Monitoring', status: 'pass', message: 'Prometheus scraping', duration_ms: 67 },
    { subsystem: 'CDN', status: 'pass', message: 'Edge nodes healthy', duration_ms: 89 },
    { subsystem: 'Rate Limiter', status: 'pass', message: 'Thresholds configured', duration_ms: 23 },
    { subsystem: 'Circuit Breaker', status: 'pass', message: 'Fallbacks ready', duration_ms: 15 },
    { subsystem: 'Config Service', status: 'skip', message: 'Skipped - external dependency', duration_ms: 0 },
    { subsystem: 'Webhook Handler', status: 'pass', message: 'Payload validation OK', duration_ms: 112 },
    { subsystem: 'Email Service', status: 'pass', message: 'SMTP connection verified', duration_ms: 234 },
    { subsystem: 'Search Index', status: 'warning', message: 'Index latency elevated', duration_ms: 456 },
  ],
};

const MOCK_BENCHMARKS: BenchmarkReport = {
  timestamp: new Date().toISOString(),
  benchmarks: [
    { name: 'API Response Time', duration_ms: 45, operations_per_second: 12500, memory_mb: 256, cpu_percent: 42, status: 'pass' },
    { name: 'Database Query', duration_ms: 12, operations_per_second: 35000, memory_mb: 128, cpu_percent: 28, status: 'pass' },
    { name: 'Cache Lookup', duration_ms: 2, operations_per_second: 98000, memory_mb: 64, cpu_percent: 15, status: 'pass' },
    { name: 'Auth Validation', duration_ms: 8, operations_per_second: 45000, memory_mb: 96, cpu_percent: 32, status: 'pass' },
    { name: 'File Upload', duration_ms: 230, operations_per_second: 850, memory_mb: 512, cpu_percent: 65, status: 'pass' },
    { name: 'ML Inference', duration_ms: 150, operations_per_second: 1200, memory_mb: 1024, cpu_percent: 78, status: 'fail' },
  ],
  summary: {
    total_benchmarks: 6,
    passed: 5,
    avg_latency_ms: 74.5,
    avg_memory_mb: 346.67,
  },
  recommendations: [
    'ML Inference: Consider model quantization to reduce memory usage',
    'File Upload: Implement chunked upload for large files',
    'API Response: Add response caching for read-heavy endpoints',
  ],
};

const MOCK_GATES: GateReport = {
  timestamp: new Date().toISOString(),
  overall_pass: false,
  pass_count: 7,
  fail_count: 2,
  gates: [
    { name: 'Code Coverage', threshold: 80, actual: 87, status: 'pass', message: 'Coverage meets threshold' },
    { name: 'Test Pass Rate', threshold: 95, actual: 98, status: 'pass', message: 'All critical tests passing' },
    { name: 'Build Success', threshold: 100, actual: 100, status: 'pass', message: 'Builds successful' },
    { name: 'Lint Score', threshold: 90, actual: 94, status: 'pass', message: 'Code quality acceptable' },
    { name: 'Bundle Size', threshold: 500, actual: 423, status: 'pass', message: 'Within budget' },
    { name: 'Lighthouse Score', threshold: 90, actual: 92, status: 'pass', message: 'Performance excellent' },
    { name: 'API Response Time', threshold: 200, actual: 45, status: 'pass', message: 'Within latency budget' },
    { name: 'Error Rate', threshold: 0.1, actual: 0.3, status: 'fail', message: 'Error rate exceeds threshold' },
    { name: 'Memory Usage', threshold: 80, actual: 85, status: 'fail', message: 'Memory usage too high' },
  ],
};

const MOCK_SECURITY: SecurityAuditReport = {
  timestamp: new Date().toISOString(),
  overall_score: 78,
  critical_count: 1,
  high_count: 2,
  medium_count: 4,
  checks: [
    { name: 'SQL Injection', category: 'Input Validation', severity: 'critical', status: 'fail', description: 'Unparameterized query detected', recommendation: 'Use parameterized queries' },
    { name: 'XSS Prevention', category: 'Input Validation', severity: 'high', status: 'pass', description: 'Output encoding applied', recommendation: 'N/A' },
    { name: 'CSRF Protection', category: 'Authentication', severity: 'high', status: 'pass', description: 'Tokens validated', recommendation: 'N/A' },
    { name: 'Auth Bypass', category: 'Authentication', severity: 'high', status: 'fail', description: 'Endpoint missing auth middleware', recommendation: 'Add authentication guard' },
    { name: 'Rate Limiting', category: 'API Security', severity: 'medium', status: 'pass', description: 'Limits configured', recommendation: 'N/A' },
    { name: 'CORS Policy', category: 'API Security', severity: 'medium', status: 'pass', description: 'Origins restricted', recommendation: 'N/A' },
    { name: 'Secrets in Code', category: 'Configuration', severity: 'critical', status: 'fail', description: 'API key found in source', recommendation: 'Move to environment variables' },
    { name: 'Dependency Audit', category: 'Dependencies', severity: 'medium', status: 'fail', description: '2 vulnerable packages', recommendation: 'Update dependencies' },
    { name: 'Transport Security', category: 'Network', severity: 'medium', status: 'pass', description: 'TLS 1.3 enforced', recommendation: 'N/A' },
    { name: 'Error Handling', category: 'Logging', severity: 'low', status: 'pass', description: 'No sensitive data in errors', recommendation: 'N/A' },
  ],
};

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    fail: 'bg-red-500/20 text-red-400 border-red-500/30',
    warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    skip: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status] || styles.skip}`}>
      {status.toUpperCase()}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[severity] || ''}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4">
      <p className="text-xs text-gray-400 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function ValidationDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [validation, setValidation] = useState<ValidationReport>(MOCK_VALIDATION);
  const [benchmarks, setBenchmarks] = useState<BenchmarkReport>(MOCK_BENCHMARKS);
  const [gates, setGates] = useState<GateReport>(MOCK_GATES);
  const [security, setSecurity] = useState<SecurityAuditReport>(MOCK_SECURITY);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1200);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Running validation checks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
              <Shield className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Release Candidate Validation</h1>
              <p className="text-sm text-gray-400">ForgeAI Platform - v1.0.0-rc1</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              v1.0.0-rc1
            </span>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${
                validation.overall_status === 'pass'
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                  : 'bg-red-500/20 text-red-400 border-red-500/30'
              }`}
            >
              {validation.overall_status === 'pass' ? 'Ready' : 'Not Ready'}
            </span>
            <button
              onClick={handleRefresh}
              className="p-2 rounded-lg bg-gray-800 border border-gray-700 hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button className="p-2 rounded-lg bg-gray-800 border border-gray-700 hover:bg-gray-700 transition-colors">
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-lg p-1 mb-8">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Passed" value={validation.passed} sub="checks" />
              <MetricCard label="Failed" value={validation.failed} sub="checks" />
              <MetricCard label="Skipped" value={validation.skipped} sub="checks" />
              <MetricCard label="Total Time" value={`${validation.results.reduce((a, r) => a + r.duration_ms, 0)}ms`} sub="execution" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div
                className={`p-4 rounded-xl border cursor-pointer transition-colors hover:bg-gray-800/80 ${
                  validation.overall_status === 'pass'
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-red-500/10 border-red-500/30'
                }`}
                onClick={() => setActiveTab('system')}
              >
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <span className="font-medium">System Validation</span>
                </div>
                <p className="text-sm text-gray-400">{validation.passed}/{validation.passed + validation.failed} subsystems</p>
              </div>

              <div
                className={`p-4 rounded-xl border cursor-pointer transition-colors hover:bg-gray-800/80 ${
                  benchmarks.summary.passed === benchmarks.summary.total_benchmarks
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-amber-500/10 border-amber-500/30'
                }`}
                onClick={() => setActiveTab('benchmarks')}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Gauge className="w-5 h-5 text-blue-400" />
                  <span className="font-medium">Benchmarks</span>
                </div>
                <p className="text-sm text-gray-400">{benchmarks.summary.passed}/{benchmarks.summary.total_benchmarks} passed</p>
              </div>

              <div
                className={`p-4 rounded-xl border cursor-pointer transition-colors hover:bg-gray-800/80 ${
                  gates.overall_pass
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-red-500/10 border-red-500/30'
                }`}
                onClick={() => setActiveTab('quality')}
              >
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  <span className="font-medium">Quality Gates</span>
                </div>
                <p className="text-sm text-gray-400">{gates.pass_count}/{gates.pass_count + gates.fail_count} gates</p>
              </div>

              <div
                className={`p-4 rounded-xl border cursor-pointer transition-colors hover:bg-gray-800/80 ${
                  security.overall_score >= 80
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-red-500/10 border-red-500/30'
                }`}
                onClick={() => setActiveTab('security')}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-5 h-5 text-purple-400" />
                  <span className="font-medium">Security Audit</span>
                </div>
                <p className="text-sm text-gray-400">Score: {security.overall_score}/100</p>
              </div>
            </div>
          </div>
        )}

        {/* System Validation Tab */}
        {activeTab === 'system' && (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <MetricCard label="Passed" value={validation.passed} />
              <MetricCard label="Failed" value={validation.failed} />
              <MetricCard label="Warnings" value={validation.results.filter((r) => r.status === 'warning').length} />
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-800/50 text-xs font-medium text-gray-400 uppercase tracking-wider">
                <div className="col-span-3">Subsystem</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-5">Message</div>
                <div className="col-span-2 text-right">Duration</div>
              </div>
              {validation.results.map((result, i) => (
                <div
                  key={i}
                  className={`grid grid-cols-12 gap-4 px-6 py-4 items-center border-t border-gray-800/50 hover:bg-gray-800/30 transition-colors ${
                    i % 2 === 0 ? 'bg-gray-900/50' : ''
                  }`}
                >
                  <div className="col-span-3 font-medium">{result.subsystem}</div>
                  <div className="col-span-2">
                    <StatusBadge status={result.status} />
                  </div>
                  <div className="col-span-5 text-sm text-gray-400">{result.message}</div>
                  <div className="col-span-2 text-right text-sm text-gray-500 font-mono">{result.duration_ms}ms</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Benchmarks Tab */}
        {activeTab === 'benchmarks' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Total" value={benchmarks.summary.total_benchmarks} sub="benchmarks" />
              <MetricCard label="Passed" value={benchmarks.summary.passed} />
              <MetricCard label="Avg Latency" value={`${benchmarks.summary.avg_latency_ms}ms`} />
              <MetricCard label="Avg Memory" value={`${benchmarks.summary.avg_memory_mb.toFixed(0)}MB`} />
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-800/50 text-xs font-medium text-gray-400 uppercase tracking-wider">
                <div className="col-span-3">Benchmark</div>
                <div className="col-span-2">Latency</div>
                <div className="col-span-2">Ops/sec</div>
                <div className="col-span-2">Memory</div>
                <div className="col-span-2">CPU</div>
                <div className="col-span-1">Status</div>
              </div>
              {benchmarks.benchmarks.map((b, i) => (
                <div
                  key={i}
                  className={`grid grid-cols-12 gap-4 px-6 py-4 items-center border-t border-gray-800/50 hover:bg-gray-800/30 transition-colors ${
                    i % 2 === 0 ? 'bg-gray-900/50' : ''
                  }`}
                >
                  <div className="col-span-3 font-medium">{b.name}</div>
                  <div className="col-span-2 text-sm font-mono text-gray-300">{b.duration_ms}ms</div>
                  <div className="col-span-2 text-sm font-mono text-gray-300">{b.operations_per_second.toLocaleString()}</div>
                  <div className="col-span-2 text-sm font-mono text-gray-300">{b.memory_mb}MB</div>
                  <div className="col-span-2 text-sm font-mono text-gray-300">{b.cpu_percent}%</div>
                  <div className="col-span-1">
                    <StatusBadge status={b.status} />
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h3 className="font-semibold mb-4">Recommendations</h3>
              <ul className="space-y-3">
                {benchmarks.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-gray-400">
                    <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Quality Gates Tab */}
        {activeTab === 'quality' && (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <MetricCard label="Gates Passed" value={gates.pass_count} />
              <MetricCard label="Gates Failed" value={gates.fail_count} />
              <MetricCard
                label="Overall"
                value={gates.overall_pass ? 'PASS' : 'FAIL'}
                sub={gates.overall_pass ? 'All gates satisfied' : 'Some gates failed'}
              />
            </div>

            <div className="space-y-3">
              {gates.gates.map((gate, i) => (
                <div
                  key={i}
                  className={`bg-gray-900 border rounded-xl p-5 ${
                    gate.status === 'pass' ? 'border-emerald-500/20' : 'border-red-500/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {gate.status === 'pass' ? (
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-400" />
                      )}
                      <span className="font-medium">{gate.name}</span>
                    </div>
                    <StatusBadge status={gate.status} />
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <span className="text-gray-400">
                      Threshold: <span className="text-white font-mono">{gate.threshold}</span>
                    </span>
                    <span className="text-gray-400">
                      Actual: <span className={`font-mono ${gate.status === 'pass' ? 'text-emerald-400' : 'text-red-400'}`}>{gate.actual}</span>
                    </span>
                    <span className="text-gray-500">{gate.message}</span>
                  </div>
                  <div className="mt-3 h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        gate.status === 'pass' ? 'bg-emerald-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(100, (gate.actual / gate.threshold) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Security Audit Tab */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Security Score" value={`${security.overall_score}/100`} />
              <MetricCard label="Critical" value={security.critical_count} sub="issues" />
              <MetricCard label="High" value={security.high_count} sub="issues" />
              <MetricCard label="Medium" value={security.medium_count} sub="issues" />
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h3 className="font-semibold mb-4">Security Score Breakdown</h3>
              <div className="h-4 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    security.overall_score >= 80 ? 'bg-emerald-500' : security.overall_score >= 60 ? 'bg-amber-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${security.overall_score}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-gray-500">
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-800/50 text-xs font-medium text-gray-400 uppercase tracking-wider">
                <div className="col-span-3">Check</div>
                <div className="col-span-2">Category</div>
                <div className="col-span-2">Severity</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-3">Recommendation</div>
              </div>
              {security.checks.map((check, i) => (
                <div
                  key={i}
                  className={`grid grid-cols-12 gap-4 px-6 py-4 items-center border-t border-gray-800/50 hover:bg-gray-800/30 transition-colors ${
                    i % 2 === 0 ? 'bg-gray-900/50' : ''
                  }`}
                >
                  <div className="col-span-3">
                    <div className="font-medium">{check.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{check.description}</div>
                  </div>
                  <div className="col-span-2 text-sm text-gray-400">{check.category}</div>
                  <div className="col-span-2">
                    <SeverityBadge severity={check.severity} />
                  </div>
                  <div className="col-span-2">
                    <StatusBadge status={check.status} />
                  </div>
                  <div className="col-span-3 text-sm text-gray-400">{check.recommendation}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
