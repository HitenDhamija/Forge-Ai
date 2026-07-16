'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, X, GitBranch, GitMerge, Bot, Database, Brain, FileText, Clock, TrendingUp } from 'lucide-react';
import { useExperienceStore } from '@/stores/experience-store';
import { useRouter } from 'next/navigation';

interface SearchOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchOverlay({ isOpen, onClose }: SearchOverlayProps) {
  const [query, setQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const { searchResults, recentSearches, popularSearches, search, fetchRecentSearches, fetchPopularSearches } = useExperienceStore();

  useEffect(() => {
    if (isOpen) {
      fetchRecentSearches();
      fetchPopularSearches();
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, fetchRecentSearches, fetchPopularSearches]);

  useEffect(() => {
    if (query.length >= 2) {
      const timeout = setTimeout(() => search(query), 300);
      return () => clearTimeout(timeout);
    }
  }, [query, search]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          onClose();
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const filters = [
    { id: 'all', label: 'All', icon: Search },
    { id: 'repositories', label: 'Repositories', icon: GitBranch },
    { id: 'workflows', label: 'Workflows', icon: GitMerge },
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'memory', label: 'Memory', icon: Database },
    { id: 'knowledge', label: 'Knowledge', icon: Brain },
    { id: 'prompts', label: 'Prompts', icon: FileText },
  ];

  const getFilteredResults = () => {
    if (activeFilter === 'all') return searchResults;
    return searchResults.filter(r => r.type === activeFilter);
  };

  const handleResultClick = (result: any) => {
    const routeMap: Record<string, string> = {
      repository: '/repositories',
      workflow: '/workflows',
      agent: '/agents',
      memory: '/memory',
      knowledge: '/memory',
      prompt: '/ai',
      template: '/studio',
    };
    const baseRoute = routeMap[result.type] || '/dashboard';
    router.push(baseRoute);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh]">
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-4xl bg-gray-900 rounded-2xl shadow-2xl border border-gray-800 overflow-hidden max-h-[80vh] flex flex-col">
        <div className="flex items-center gap-4 px-6 py-4 border-b border-gray-800">
          <Search className="w-6 h-6 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search everything..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-xl text-white placeholder-gray-500 focus:outline-none"
          />
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center gap-2 px-6 py-3 border-b border-gray-800 overflow-x-auto">
          {filters.map((filter) => (
            <button
              key={filter.id}
              onClick={() => setActiveFilter(filter.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
                activeFilter === filter.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <filter.icon className="w-4 h-4" />
              {filter.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {query.length < 2 ? (
            <div className="space-y-8">
              {recentSearches.length > 0 && (
                <div>
                  <h3 className="flex items-center gap-2 text-sm font-medium text-gray-400 mb-3">
                    <Clock className="w-4 h-4" />
                    Recent Searches
                  </h3>
                  <div className="space-y-2">
                    {recentSearches.map((item, i) => (
                      <button
                        key={i}
                        onClick={() => setQuery(item.query)}
                        className="w-full flex items-center gap-3 px-4 py-2 text-left text-gray-300 hover:bg-gray-800 rounded-lg"
                      >
                        <Clock className="w-4 h-4 text-gray-500" />
                        {item.query}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {popularSearches.length > 0 && (
                <div>
                  <h3 className="flex items-center gap-2 text-sm font-medium text-gray-400 mb-3">
                    <TrendingUp className="w-4 h-4" />
                    Popular Searches
                  </h3>
                  <div className="space-y-2">
                    {popularSearches.map((item, i) => (
                      <button
                        key={i}
                        onClick={() => setQuery(item.query)}
                        className="w-full flex items-center gap-3 px-4 py-2 text-left text-gray-300 hover:bg-gray-800 rounded-lg"
                      >
                        <TrendingUp className="w-4 h-4 text-gray-500" />
                        {item.query}
                        <span className="ml-auto text-xs text-gray-500">{item.count} searches</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {getFilteredResults().map((result) => (
                <div
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className="flex items-center gap-4 px-4 py-3 bg-gray-800/50 hover:bg-gray-800 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="w-10 h-10 rounded-lg bg-gray-700 flex items-center justify-center">
                    <Search className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium">{result.title}</p>
                    <p className="text-sm text-gray-400 truncate">{result.description}</p>
                  </div>
                  <span className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded">{result.type}</span>
                </div>
              ))}

              {getFilteredResults().length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No results found for &quot;{query}&quot;</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 px-6 py-3 border-t border-gray-800 text-xs text-gray-500">
          <span><kbd className="px-1.5 py-0.5 bg-gray-800 rounded">↑↓</kbd> Navigate</span>
          <span><kbd className="px-1.5 py-0.5 bg-gray-800 rounded">↵</kbd> Select</span>
          <span><kbd className="px-1.5 py-0.5 bg-gray-800 rounded">Esc</kbd> Close</span>
        </div>
      </div>
    </div>
  );
}
