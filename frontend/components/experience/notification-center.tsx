'use client';

import React, { useState, useEffect } from 'react';
import { Bell, Check, CheckCheck, Filter, GitMerge, Bot, Rocket, AlertTriangle, Info, X } from 'lucide-react';
import { useExperienceStore } from '@/stores/experience-store';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationCenter({ isOpen, onClose }: NotificationCenterProps) {
  const { notifications, unreadCount, fetchNotifications, markNotificationRead, markAllNotificationsRead } = useExperienceStore();
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, fetchNotifications]);

  if (!isOpen) return null;

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'workflow_started':
      case 'workflow_finished':
        return <GitMerge className="w-5 h-5 text-blue-500" />;
      case 'agent_failed':
        return <Bot className="w-5 h-5 text-red-500" />;
      case 'deployment_ready':
        return <Rocket className="w-5 h-5 text-green-500" />;
      case 'approval_required':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-blue-500';
      default: return 'bg-gray-500';
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

  const groupByDate = (notifications: any[]) => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterdayStart = new Date(todayStart);
    yesterdayStart.setDate(yesterdayStart.getDate() - 1);

    const groups: Record<string, any[]> = {
      Today: [],
      Yesterday: [],
      Earlier: [],
    };

    notifications.forEach((n) => {
      const date = new Date(n.created_at);
      if (date >= todayStart) {
        groups.Today.push(n);
      } else if (date >= yesterdayStart) {
        groups.Yesterday.push(n);
      } else {
        groups.Earlier.push(n);
      }
    });

    return groups;
  };

  const filteredNotifications = filter === 'all'
    ? notifications
    : notifications.filter(n => n.type.startsWith(filter));

  const grouped = groupByDate(filteredNotifications);

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-gray-900 border-l border-gray-800 shadow-2xl z-50 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-white" />
          <h2 className="text-lg font-semibold text-white">Notifications</h2>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={markAllNotificationsRead}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
            title="Mark all read"
          >
            <CheckCheck className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="px-4 py-2 border-b border-gray-800">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-blue-500"
        >
          <option value="all">All Notifications</option>
          <option value="workflow">Workflows</option>
          <option value="agent">Agents</option>
          <option value="deployment">Deployments</option>
          <option value="approval">Approvals</option>
        </select>
      </div>

      {/* Notifications List */}
      <div className="flex-1 overflow-y-auto">
        {filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bell className="w-12 h-12 mb-4 opacity-50" />
            <p>No notifications</p>
          </div>
        ) : (
          <div className="p-2 space-y-4">
            {Object.entries(grouped).map(([group, items]) =>
              items.length > 0 ? (
                <div key={group}>
                  <h4 className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {group}
                  </h4>
                  <div className="space-y-1">
                    {items.map((notification) => (
                      <div
                        key={notification.id}
                        onClick={() => markNotificationRead(notification.id)}
                        className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                          notification.status === 'unread'
                            ? 'bg-blue-600/10 hover:bg-blue-600/20'
                            : 'hover:bg-gray-800'
                        }`}
                      >
                        <div className="flex-shrink-0 mt-1">
                          {getNotificationIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className={`text-sm font-medium ${notification.status === 'unread' ? 'text-white' : 'text-gray-300'}`}>
                              {notification.title}
                            </p>
                            <span className={`w-2 h-2 rounded-full ${getPriorityColor(notification.priority)}`} />
                          </div>
                          <p className="text-sm text-gray-400 mt-1 line-clamp-2">{notification.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {getTimeAgo(notification.created_at)}
                          </p>
                        </div>
                        {notification.status === 'unread' && (
                          <div className="flex-shrink-0">
                            <div className="w-2 h-2 bg-blue-500 rounded-full" />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null
            )}
          </div>
        )}
      </div>
    </div>
  );
}
