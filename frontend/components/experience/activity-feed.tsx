'use client';

import React, { useEffect, useState } from 'react';
import { Activity as ActivityIcon, GitMerge, GitBranch, Bot, Terminal, Building2, Clock, ChevronDown } from 'lucide-react';
import { useExperienceStore } from '@/stores/experience-store';

interface ActivityFeedProps {
  limit?: number;
  showHeader?: boolean;
}

export function ActivityFeed({ limit = 20, showHeader = true }: ActivityFeedProps) {
  const { activities, fetchActivities } = useExperienceStore();
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetchActivities(limit);
  }, [fetchActivities, limit]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'workflow': return <GitMerge className="w-4 h-4 text-blue-500" />;
      case 'repository': return <GitBranch className="w-4 h-4 text-green-500" />;
      case 'agent': return <Bot className="w-4 h-4 text-purple-500" />;
      case 'execution': return <Terminal className="w-4 h-4 text-orange-500" />;
      case 'organization': return <Building2 className="w-4 h-4 text-cyan-500" />;
      default: return <ActivityIcon className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTimeAgo = (dateStr: string) => {
    const now = new Date();
    const date = new Date(dateStr);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const filteredActivities = filter === 'all'
    ? activities
    : activities.filter(a => a.type === filter);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800">
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">Activity</h3>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-gray-800 text-white text-sm rounded-lg px-3 py-1 border border-gray-700 focus:outline-none"
          >
            <option value="all">All</option>
            <option value="workflow">Workflows</option>
            <option value="repository">Repositories</option>
            <option value="agent">Agents</option>
            <option value="execution">Executions</option>
          </select>
        </div>
      )}

      <div className="p-4">
        {filteredActivities.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <ActivityIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No recent activity</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredActivities.map((activity, index) => (
              <div key={activity.id} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center">
                    {getActivityIcon(activity.type)}
                  </div>
                  {index < filteredActivities.length - 1 && (
                    <div className="w-0.5 h-full bg-gray-800 mt-2" />
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <p className="text-sm text-white font-medium">{activity.title}</p>
                  {activity.description && (
                    <p className="text-sm text-gray-400 mt-1">{activity.description}</p>
                  )}
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{getTimeAgo(activity.timestamp)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
