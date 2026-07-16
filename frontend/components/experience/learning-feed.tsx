'use client';

import React, { useEffect } from 'react';
import { useLearningStore } from '@/stores/learning-store';
import { BookOpen, Lightbulb, AlertTriangle, Target, Brain, CheckCircle, XCircle, Minus, Clock } from 'lucide-react';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  architecture: <BookOpen className="w-4 h-4" />,
  bug_fix: <XCircle className="w-4 h-4" />,
  deployment: <Target className="w-4 h-4" />,
  database: <BookOpen className="w-4 h-4" />,
  testing: <Target className="w-4 h-4" />,
  performance: <Target className="w-4 h-4" />,
  security: <Target className="w-4 h-4" />,
  documentation: <BookOpen className="w-4 h-4" />,
  refactoring: <BookOpen className="w-4 h-4" />,
};

function formatRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffHours < 1) return 'just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getOutcomeIcon(outcome: string) {
  switch (outcome) {
    case 'success':
      return <CheckCircle className="w-3.5 h-3.5 text-green-400" />;
    case 'failure':
      return <XCircle className="w-3.5 h-3.5 text-red-400" />;
    case 'partial':
      return <Minus className="w-3.5 h-3.5 text-yellow-400" />;
    default:
      return <Clock className="w-3.5 h-4 text-gray-400" />;
  }
}

interface LearningFeedProps {
  limit?: number;
  showHeader?: boolean;
}

export function LearningFeed({ limit = 50, showHeader = true }: LearningFeedProps) {
  const {
    tasks,
    experiences,
    patterns,
    lessons,
    stats,
    fetchTasks,
    fetchExperiences,
    fetchPatterns,
    fetchStats,
    isLoading,
  } = useLearningStore();

  useEffect(() => {
    fetchTasks();
    fetchExperiences({ limit });
    fetchPatterns({ limit: 20 });
    fetchStats();
  }, [fetchTasks, fetchExperiences, fetchPatterns, fetchStats, limit]);

  const recentExperiences = experiences.slice(0, limit);
  const recentTasks = tasks.slice(0, limit);

  return (
    <div className="space-y-6">
      {showHeader && (
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Learning Feed</h2>
            <p className="text-sm text-gray-400">Recent experiences, patterns, and lessons from processed workflows</p>
          </div>
        </div>
      )}

      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <BookOpen className="w-4 h-4" />
              Experiences
            </div>
            <p className="text-2xl font-bold text-white">{stats.total_experiences}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Lightbulb className="w-4 h-4" />
              Patterns
            </div>
            <p className="text-2xl font-bold text-white">{stats.total_patterns}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <AlertTriangle className="w-4 h-4" />
              Lessons
            </div>
            <p className="text-2xl font-bold text-white">{stats.total_lessons}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Target className="w-4 h-4" />
              Tasks
            </div>
            <p className="text-2xl font-bold text-white">{stats.total_tasks}</p>
          </div>
        </div>
      )}

      {/* Recent Experiences */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg">
        <div className="px-4 py-3 border-b border-gray-800">
          <h3 className="text-sm font-medium text-white flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-400" />
            Recent Experiences
          </h3>
        </div>
        {recentExperiences.length > 0 ? (
          <div className="divide-y divide-gray-800">
            {recentExperiences.map((exp) => (
              <div key={exp.id} className="px-4 py-3 hover:bg-gray-800/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      {getOutcomeIcon(exp.outcome)}
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-white">{exp.title}</p>
                      {exp.description && (
                        <p className="text-xs text-gray-400 line-clamp-2">{exp.description}</p>
                      )}
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                          {TYPE_ICONS[exp.experience_type] || <BookOpen className="w-3.5 h-3.5" />}
                          {exp.experience_type}
                        </span>
                        <span className="text-xs text-gray-600">·</span>
                        <span className="text-xs text-gray-500">{Math.round(exp.confidence * 100)}% confidence</span>
                        {exp.technologies.length > 0 && (
                          <>
                            <span className="text-xs text-gray-600">·</span>
                            <span className="text-xs text-gray-500">{exp.technologies.slice(0, 3).join(', ')}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                    {formatRelativeTime(exp.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-4 py-8 text-center text-gray-500">
            <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No experiences yet</p>
            <p className="text-xs text-gray-600 mt-1">Process a workflow to start collecting experiences</p>
          </div>
        )}
      </div>

      {/* Recent Learning Tasks */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg">
        <div className="px-4 py-3 border-b border-gray-800">
          <h3 className="text-sm font-medium text-white flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-400" />
            Processing Tasks
          </h3>
        </div>
        {recentTasks.length > 0 ? (
          <div className="divide-y divide-gray-800">
            {recentTasks.map((task) => (
              <div key={task.task_id} className="px-4 py-3 hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-500/20">
                      <Brain className="w-4 h-4 text-purple-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        {task.workflow_id || `Task ${task.task_id.slice(0, 8)}`}
                      </p>
                      <p className="text-xs text-gray-500">
                        {task.experiences_count} exp · {task.patterns_count} patterns · {task.lessons_count} lessons
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      task.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      task.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {task.status === 'completed' ? <CheckCircle className="w-3 h-3" /> :
                       task.status === 'failed' ? <XCircle className="w-3 h-3" /> :
                       <Clock className="w-3 h-3" />}
                      {task.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatRelativeTime(task.started_at)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-4 py-8 text-center text-gray-500">
            <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No tasks processed yet</p>
            <p className="text-xs text-gray-600 mt-1">Run a workflow and process it to start learning</p>
          </div>
        )}
      </div>

      {/* Recent Patterns */}
      {patterns.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg">
          <div className="px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-white flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-yellow-400" />
              Detected Patterns
            </h3>
          </div>
          <div className="divide-y divide-gray-800">
            {patterns.slice(0, 5).map((pattern) => (
              <div key={pattern.id} className="px-4 py-3 hover:bg-gray-800/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-white">{pattern.name}</p>
                    <p className="text-xs text-gray-400 line-clamp-1">{pattern.description}</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">{pattern.pattern_type}</span>
                      <span className="text-xs text-gray-600">·</span>
                      <span className="text-xs text-gray-500">{pattern.usage_count} uses</span>
                      <span className="text-xs text-gray-600">·</span>
                      <span className="text-xs text-gray-500">{Math.round(pattern.confidence * 100)}% confidence</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
