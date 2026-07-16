"use client";

import * as React from "react";
import { Search, X, Command } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onClear?: () => void;
  className?: string;
  shortcut?: boolean;
}

function SearchBar({
  placeholder = "Search...",
  value,
  onChange,
  onClear,
  className,
  shortcut = true,
}: SearchBarProps) {
  const [internalValue, setInternalValue] = React.useState(value || "");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInternalValue(e.target.value);
    onChange?.(e.target.value);
  };

  const handleClear = () => {
    setInternalValue("");
    onChange?.("");
    onClear?.();
  };

  React.useEffect(() => {
    if (value !== undefined) {
      setInternalValue(value);
    }
  }, [value]);

  return (
    <div className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
      <input
        type="text"
        placeholder={placeholder}
        value={internalValue}
        onChange={handleChange}
        className="h-9 w-full rounded-md border border-border bg-surface pl-9 pr-20 text-sm text-text placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      />
      {internalValue && (
        <button
          onClick={handleClear}
          className="absolute right-12 top-1/2 -translate-y-1/2 rounded p-1 text-text-muted hover:text-text"
        >
          <X className="h-3 w-3" />
        </button>
      )}
      {shortcut && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center space-x-0.5 text-text-muted">
          <Command className="h-3 w-3" />
          <span className="text-xs">K</span>
        </div>
      )}
    </div>
  );
}

export { SearchBar };
