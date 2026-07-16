"use client";

import * as React from "react";
import type { LanguageInfo } from "@/types/repository";

interface LanguageBreakdownProps {
  languages: LanguageInfo[];
}

const LANGUAGE_COLORS: Record<string, string> = {
  TypeScript: "#3178c6",
  JavaScript: "#f7df1e",
  Python: "#3572a5",
  Java: "#b07219",
  "C++": "#f34b7d",
  C: "#555555",
  "C#": "#178600",
  Go: "#00add8",
  Rust: "#dea584",
  Ruby: "#701516",
  PHP: "#4f5d95",
  Swift: "#ffac45",
  Kotlin: "#a97bff",
  Dart: "#00b4ab",
  HTML: "#e34c26",
  CSS: "#563d7c",
  SCSS: "#c6538c",
  Shell: "#89e051",
  SQL: "#e38c00",
  Markdown: "#083fa1",
  JSON: "#292929",
  YAML: "#cb171e",
  TOML: "#9c4221",
  Dockerfile: "#384d54",
  Makefile: "#427819",
};

function getLanguageColor(name: string): string {
  return LANGUAGE_COLORS[name] || "#6b7280";
}

function LanguageBreakdown({ languages }: LanguageBreakdownProps) {
  if (languages.length === 0) {
    return (
      <p className="text-sm text-text-muted">No language data available</p>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stacked bar */}
      <div className="flex h-4 overflow-hidden rounded-full bg-surface-hover">
        {languages.map((lang) => (
          <div
            key={lang.name}
            style={{
              width: `${lang.percentage}%`,
              backgroundColor: getLanguageColor(lang.name),
            }}
            className="transition-all duration-300"
            title={`${lang.name}: ${lang.percentage.toFixed(1)}%`}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="space-y-2">
        {languages.map((lang) => (
          <div key={lang.name} className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: getLanguageColor(lang.name) }}
              />
              <span className="text-sm font-medium text-text">{lang.name}</span>
            </div>
            <div className="flex items-center space-x-4 text-xs text-text-muted">
              <span>{lang.file_count} files</span>
              <span>{lang.total_lines.toLocaleString()} lines</span>
              <span className="w-12 text-right font-medium text-text">
                {lang.percentage.toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export { LanguageBreakdown };
