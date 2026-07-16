'use client';

import React, { useEffect, useState } from 'react';
import { Settings, User, Brain, Palette, Bell, Shield, Code, Database, Save, RotateCcw, Check } from 'lucide-react';
import { useExperienceStore } from '@/stores/experience-store';

const categories = [
  { id: 'general', label: 'General', icon: Settings },
  { id: 'models', label: 'AI Models', icon: Brain },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'developer', label: 'Developer', icon: Code },
];

export function SettingsHub() {
  const [activeCategory, setActiveCategory] = useState('general');
  const { settings, fetchSettings, updateSetting } = useExperienceStore();
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const categorySettings = Object.values(settings).filter(
    s => s.category === activeCategory
  );

  const handleValueChange = (key: string, value: string) => {
    updateSetting(key, value);
  };

  const handleSave = async () => {
    setSaveState('saving');
    // Settings auto-save on each change, so this just confirms
    await new Promise(resolve => setTimeout(resolve, 500));
    setSaveState('saved');
    setTimeout(() => setSaveState('idle'), 2000);
  };

  const handleReset = () => {
    fetchSettings(activeCategory);
  };

  const renderSettingInput = (setting: any) => {
    switch (setting.type) {
      case 'boolean':
        return (
          <button
            onClick={() => handleValueChange(setting.key, String(!setting.value))}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              setting.value === 'true' || setting.value === true ? 'bg-blue-600' : 'bg-gray-700'
            }`}
          >
            <span
              className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                setting.value === 'true' || setting.value === true ? 'left-7' : 'left-1'
              }`}
            />
          </button>
        );
      case 'select':
        return (
          <select
            value={setting.value || setting.default}
            onChange={(e) => handleValueChange(setting.key, e.target.value)}
            className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-blue-500"
          >
            {setting.options?.map((opt: string) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      case 'color':
        return (
          <div className="flex items-center gap-3">
            <input
              type="color"
              value={setting.value || setting.default}
              onChange={(e) => handleValueChange(setting.key, e.target.value)}
              className="w-10 h-10 rounded-lg border border-gray-700 cursor-pointer"
            />
            <input
              type="text"
              value={setting.value || setting.default}
              onChange={(e) => handleValueChange(setting.key, e.target.value)}
              className="flex-1 bg-gray-800 text-white rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-blue-500"
            />
          </div>
        );
      default:
        return (
          <input
            type={setting.type === 'number' ? 'number' : 'text'}
            value={setting.value || setting.default || ''}
            onChange={(e) => handleValueChange(setting.key, e.target.value)}
            className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-blue-500"
          />
        );
    }
  };

  return (
    <div className="flex h-full bg-gray-950">
      <div className="w-64 bg-gray-900 border-r border-gray-800 p-4">
        <h2 className="text-lg font-semibold text-white mb-6">Settings</h2>
        <nav className="space-y-1">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                activeCategory === cat.id
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <cat.icon className="w-5 h-5" />
              {cat.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-2xl font-bold text-white">
              {categories.find(c => c.id === activeCategory)?.label}
            </h1>
            <div className="flex items-center gap-3">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
              >
                <RotateCcw className="w-4 h-4" />
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={saveState === 'saving'}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
              >
                {saveState === 'saved' ? (
                  <>
                    <Check className="w-4 h-4" />
                    Saved
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    {saveState === 'saving' ? 'Saving...' : 'Save Changes'}
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="space-y-6">
            {categorySettings.map((setting) => (
              <div key={setting.key} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-white font-medium">{setting.label}</label>
                    {setting.description && (
                      <p className="text-sm text-gray-400 mt-1">{setting.description}</p>
                    )}
                  </div>
                  <div className="w-64">
                    {renderSettingInput(setting)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
