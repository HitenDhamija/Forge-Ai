'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, Command, ArrowRight, Clock, TrendingUp } from 'lucide-react';
import { useExperienceStore } from '@/stores/experience-store';
import { useRouter } from 'next/navigation';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const {
    commandPaletteItems,
    fetchCommandPaletteItems,
    recentSearches,
    fetchRecentSearches,
    popularSearches,
    fetchPopularSearches,
  } = useExperienceStore();

  useEffect(() => {
    if (isOpen) {
      fetchCommandPaletteItems();
      fetchRecentSearches();
      fetchPopularSearches();
    }
  }, [isOpen, fetchCommandPaletteItems, fetchRecentSearches, fetchPopularSearches]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const navigateCommand = (item: any) => {
    const routeMap: Record<string, string> = {
      'open-repo': '/repositories',
      'search-workflows': '/workflows',
      'search-agents': '/agents',
      'run-workflow': '/workflows',
      'switch-model': '/settings',
      'open-settings': '/settings',
      'search-knowledge': '/memory',
      'go-dashboard': '/dashboard',
      'go-workflows': '/workflows',
      'go-agents': '/agents',
      'go-monitoring': '/monitoring',
      'go-studio': '/studio',
    };
    const route = routeMap[item.id];
    if (route) {
      router.push(route);
      onClose();
    }
  };

  const filteredItems = commandPaletteItems.filter(item =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, filteredItems.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && filteredItems[selectedIndex]) {
      navigateCommand(filteredItems[selectedIndex]);
    }
  };

  const handleClose = () => {
    onClose();
    setQuery('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />
      <div className="relative w-full max-w-2xl bg-gray-900 rounded-xl shadow-2xl border border-gray-800 overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-800">
          <Command className="w-5 h-5 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none"
            autoFocus
          />
          <kbd className="px-2 py-1 text-xs text-gray-500 bg-gray-800 rounded">ESC</kbd>
        </div>

        <div className="max-h-96 overflow-y-auto p-2">
          {query === '' && recentSearches.length > 0 && (
            <div className="mb-4">
              <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase">
                Recent
              </div>
              {recentSearches.map((item, i) => (
                <button
                  key={i}
                  className="w-full flex items-center gap-3 px-3 py-2 text-left text-gray-300 hover:bg-gray-800 rounded-lg"
                  onClick={() => {
                    setQuery(item.query);
                  }}
                >
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span>{item.query}</span>
                </button>
              ))}
            </div>
          )}

          {query === '' && popularSearches.length > 0 && (
            <div className="mb-4">
              <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase">
                Popular
              </div>
              {popularSearches.map((item, i) => (
                <button
                  key={i}
                  className="w-full flex items-center gap-3 px-3 py-2 text-left text-gray-300 hover:bg-gray-800 rounded-lg"
                  onClick={() => {
                    setQuery(item.query);
                  }}
                >
                  <TrendingUp className="w-4 h-4 text-gray-500" />
                  <span>{item.query}</span>
                  <span className="ml-auto text-xs text-gray-600">{item.count} searches</span>
                </button>
              ))}
            </div>
          )}

          <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase">
            {query ? 'Results' : 'Commands'}
          </div>

          {filteredItems.map((item, i) => (
            <button
              key={item.id}
              className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-lg ${
                i === selectedIndex
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
              onClick={() => navigateCommand(item)}
              onMouseEnter={() => setSelectedIndex(i)}
            >
              {item.icon && <span className="text-gray-500">{item.icon}</span>}
              <span className="flex-1">{item.label}</span>
              {item.shortcut && (
                <kbd className="px-2 py-1 text-xs text-gray-500 bg-gray-800 rounded">
                  {item.shortcut}
                </kbd>
              )}
              <ArrowRight className="w-4 h-4 text-gray-600" />
            </button>
          ))}

          {filteredItems.length === 0 && (
            <div className="px-3 py-8 text-center text-gray-500">
              No results found for &quot;{query}&quot;
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 px-4 py-3 border-t border-gray-800 text-xs text-gray-500">
          <span>
            <kbd className="px-1 py-0.5 bg-gray-800 rounded">↑↓</kbd> Navigate
          </span>
          <span>
            <kbd className="px-1 py-0.5 bg-gray-800 rounded">↵</kbd> Select
          </span>
          <span>
            <kbd className="px-1 py-0.5 bg-gray-800 rounded">Esc</kbd> Close
          </span>
        </div>
      </div>
    </div>
  );
}
