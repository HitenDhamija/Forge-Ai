'use client';

import React, { useState, useEffect } from 'react';
import { Bell, Search, Activity, Settings, Sparkles, HelpCircle, Brain } from 'lucide-react';
import { CommandPalette } from '@/components/experience/command-palette';
import { NotificationCenter } from '@/components/experience/notification-center';
import { ActivityFeed } from '@/components/experience/activity-feed';
import { LearningFeed } from '@/components/experience/learning-feed';
import { SearchOverlay } from '@/components/experience/search-overlay';
import { WelcomeWizard } from '@/components/experience/welcome-wizard';
import { SettingsHub } from '@/components/experience/settings-hub';
import { useExperienceStore } from '@/stores/experience-store';

export default function ExperiencePage() {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isWelcomeOpen, setIsWelcomeOpen] = useState(false);
  const [view, setView] = useState<'activity' | 'learning' | 'settings'>('activity');

  const { unreadCount, fetchUnreadCount, onboardingState, fetchOnboardingState } = useExperienceStore();

  useEffect(() => {
    fetchUnreadCount();
    fetchOnboardingState();
  }, [fetchUnreadCount, fetchOnboardingState]);

  // Show welcome wizard for first-time users
  useEffect(() => {
    if (onboardingState && !onboardingState.is_complete) {
      const hasSeenWizard = sessionStorage.getItem('forgeai-wizard-seen');
      if (!hasSeenWizard) {
        setIsWelcomeOpen(true);
        sessionStorage.setItem('forgeai-wizard-seen', 'true');
      }
    }
  }, [onboardingState]);

  return (
    <div className="h-full bg-gray-950">
      {/* Page Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Experience Center</h1>
            <p className="text-gray-400 mt-1">Your unified workspace for notifications, activity, and settings</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
            >
              <Search className="w-4 h-4" />
              Search
              <kbd className="px-1.5 py-0.5 text-xs bg-gray-700 rounded">Ctrl+/</kbd>
            </button>
            <button
              onClick={() => setIsCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Commands
              <kbd className="px-1.5 py-0.5 text-xs bg-gray-700 rounded">Ctrl+K</kbd>
            </button>
            <button
              onClick={() => setIsNotificationOpen(true)}
              className="relative p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setIsWelcomeOpen(true)}
              className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
              title="Show onboarding guide"
            >
              <HelpCircle className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex items-center gap-1 px-6 py-3 border-b border-gray-800">
        <button
          onClick={() => setView('activity')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            view === 'activity' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Activity className="w-4 h-4" />
          Activity Feed
        </button>
        <button
          onClick={() => setView('learning')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            view === 'learning' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Brain className="w-4 h-4" />
          Learning Feed
        </button>
        <button
          onClick={() => setView('settings')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            view === 'settings' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Settings className="w-4 h-4" />
          Settings
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {view === 'activity' && (
          <div className="p-6">
            <ActivityFeed limit={50} showHeader={false} />
          </div>
        )}
        {view === 'learning' && (
          <div className="p-6">
            <LearningFeed limit={50} showHeader={false} />
          </div>
        )}
        {view === 'settings' && <SettingsHub />}
      </div>

      {/* Overlays */}
      {isCommandPaletteOpen && (
        <CommandPalette isOpen={isCommandPaletteOpen} onClose={() => setIsCommandPaletteOpen(false)} />
      )}
      <NotificationCenter isOpen={isNotificationOpen} onClose={() => setIsNotificationOpen(false)} />
      <SearchOverlay isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
      <WelcomeWizard isOpen={isWelcomeOpen} onClose={() => setIsWelcomeOpen(false)} />
    </div>
  );
}
