'use client';

import React from 'react';

function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(' ');
}

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn('animate-pulse rounded-md bg-gray-800', className)} />
  );
}

interface CardSkeletonProps {
  header?: boolean;
  lines?: number;
  footer?: boolean;
}

export function CardSkeleton({ header = true, lines = 3, footer = false }: CardSkeletonProps) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
      {header && (
        <div className="mb-4">
          <Skeleton className="h-5 w-1/3 mb-2" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      )}
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-full" />
        ))}
      </div>
      {footer && (
        <div className="mt-4 flex justify-end gap-2">
          <Skeleton className="h-8 w-20 rounded-md" />
          <Skeleton className="h-8 w-20 rounded-md" />
        </div>
      )}
    </div>
  );
}

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  header?: boolean;
}

export function TableSkeleton({ rows = 5, columns = 4, header = true }: TableSkeletonProps) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
      {header && (
        <div className="flex gap-4 border-b border-gray-800 p-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      )}
      <div className="divide-y divide-gray-800">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4 p-4">
            {Array.from({ length: columns }).map((_, j) => (
              <Skeleton key={j} className="h-3 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

interface ListSkeletonProps {
  items?: number;
  avatar?: boolean;
}

export function ListSkeleton({ items = 5, avatar = true }: ListSkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 rounded-lg border border-gray-800 bg-gray-900 p-4">
          {avatar && <Skeleton className="h-10 w-10 rounded-full shrink-0" />}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
          <Skeleton className="h-6 w-16 rounded-md" />
        </div>
      ))}
    </div>
  );
}

interface StatsSkeletonProps {
  count?: number;
}

export function StatsSkeleton({ count = 4 }: StatsSkeletonProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <Skeleton className="h-3 w-1/2 mb-3" />
          <Skeleton className="h-8 w-2/3 mb-2" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      ))}
    </div>
  );
}

interface ChartSkeletonProps {
  height?: number;
  bars?: number;
}

export function ChartSkeleton({ height = 250, bars = 8 }: ChartSkeletonProps) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
      <div className="mb-4">
        <Skeleton className="h-5 w-1/4 mb-2" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <div className="flex items-end gap-2" style={{ height }}>
        {Array.from({ length: bars }).map((_, i) => (
          <div
            key={i}
            className="flex-1 rounded-t-md"
            style={{ height: `${30 + Math.random() * 70}%` }}
          >
            <Skeleton className="h-full w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

interface FormSkeletonProps {
  fields?: number;
  actions?: boolean;
}

export function FormSkeleton({ fields = 4, actions = true }: FormSkeletonProps) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 space-y-5">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-3 w-1/4" />
          <Skeleton className="h-10 w-full rounded-md" />
        </div>
      ))}
      {actions && (
        <div className="flex justify-end gap-3 pt-2">
          <Skeleton className="h-10 w-24 rounded-md" />
          <Skeleton className="h-10 w-24 rounded-md" />
        </div>
      )}
    </div>
  );
}

interface PageSkeletonProps {
  header?: boolean;
  sidebar?: boolean;
  content?: 'card' | 'table' | 'list' | 'stats';
}

export function PageSkeleton({
  header = true,
  sidebar = false,
  content = 'card',
}: PageSkeletonProps) {
  return (
    <div className="min-h-screen bg-gray-950">
      {header && (
        <div className="border-b border-gray-800 bg-gray-900 px-6 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <Skeleton className="h-6 w-32" />
            <div className="flex items-center gap-4">
              <Skeleton className="h-8 w-8 rounded-full" />
              <Skeleton className="h-4 w-24" />
            </div>
          </div>
        </div>
      )}
      <div className="flex">
        {sidebar && (
          <div className="w-64 border-r border-gray-800 bg-gray-900 p-4 space-y-3 min-h-[calc(100vh-65px)]">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full rounded-md" />
            ))}
          </div>
        )}
        <div className="flex-1 p-6 max-w-7xl mx-auto">
          <Skeleton className="h-7 w-48 mb-6" />
          {content === 'card' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <CardSkeleton key={i} lines={2} />
              ))}
            </div>
          )}
          {content === 'table' && <TableSkeleton />}
          {content === 'list' && <ListSkeleton />}
          {content === 'stats' && <StatsSkeleton />}
        </div>
      </div>
    </div>
  );
}

interface TabSkeletonProps {
  tabs?: number;
  panels?: number;
}

export function TabSkeleton({ tabs = 4, panels = 1 }: TabSkeletonProps) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900">
      <div className="flex border-b border-gray-800">
        {Array.from({ length: tabs }).map((_, i) => (
          <Skeleton key={i} className="h-11 flex-1 first:rounded-tl-lg last:rounded-tr-lg" />
        ))}
      </div>
      <div className="p-6 space-y-4">
        {Array.from({ length: panels }).map((_, i) => (
          <div key={i} className="space-y-3">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-5/6" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        ))}
      </div>
    </div>
  );
}
