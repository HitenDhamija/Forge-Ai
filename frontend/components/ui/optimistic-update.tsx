'use client';

import React, { useState, useCallback, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

export function useOptimisticUpdate<T>(
  currentData: T,
  updateFn: (old: T, optimistic: Partial<T>) => T
) {
  const [optimisticData, setOptimisticData] = useState<T>(currentData);
  const [isPending, setIsPending] = useState(false);

  const triggerUpdate = useCallback(
    async (optimisticUpdate: Partial<T>, asyncFn: () => Promise<T>) => {
      setOptimisticData((prev) => updateFn(prev, optimisticUpdate));
      setIsPending(true);
      try {
        const result = await asyncFn();
        setOptimisticData(result);
        return result;
      } catch (error) {
        setOptimisticData(currentData);
        throw error;
      } finally {
        setIsPending(false);
      }
    },
    [currentData, updateFn]
  );

  const reset = useCallback(() => {
    setOptimisticData(currentData);
  }, [currentData]);

  return { data: optimisticData, isPending, triggerUpdate, reset };
}

interface OptimisticWrapperProps {
  isPending?: boolean;
  children: ReactNode;
  loadingOverlay?: boolean;
  spinner?: boolean;
  className?: string;
}

export function OptimisticWrapper({
  isPending = false,
  children,
  loadingOverlay = true,
  spinner = true,
  className,
}: OptimisticWrapperProps) {
  return (
    <div className={`relative ${className || ''}`}>
      {children}
      {isPending && loadingOverlay && (
        <div className="absolute inset-0 bg-gray-950/50 backdrop-blur-[1px] flex items-center justify-center rounded-lg z-10">
          {spinner && (
            <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
          )}
        </div>
      )}
    </div>
  );
}
