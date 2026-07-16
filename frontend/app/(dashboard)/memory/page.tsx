"use client";

import { MemoryWorkspace } from "@/components/memory/memory-workspace";

export default function MemoryPage() {
  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6">
      <MemoryWorkspace />
    </div>
  );
}
