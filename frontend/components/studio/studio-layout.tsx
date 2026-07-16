"use client";

import * as React from "react";
import {
  GitBranch,
  MessageSquare,
  Play,
  Bot,
  LayoutDashboard,
  Cpu,
  Database,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Search,
  Bell,
  Settings,
  X,
  Terminal,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useStudioStore } from "@/stores/studio-store";

type StudioSection =
  | "workflows"
  | "prompts"
  | "replay"
  | "agents"
  | "workspace"
  | "models"
  | "memory";

interface NavItem {
  id: StudioSection;
  label: string;
  icon: React.ElementType;
}

const NAV_ITEMS: NavItem[] = [
  { id: "workflows", label: "Workflows", icon: GitBranch },
  { id: "prompts", label: "Prompts", icon: MessageSquare },
  { id: "replay", label: "Replay", icon: Play },
  { id: "agents", label: "Agents", icon: Bot },
  { id: "workspace", label: "Workspace", icon: LayoutDashboard },
  { id: "models", label: "Models", icon: Cpu },
  { id: "memory", label: "Memory", icon: Database },
];

interface ConsoleEntry {
  id: string;
  type: "info" | "success" | "error";
  message: string;
  timestamp: string;
}

function StudioSidebar() {
  const { activeSection, setActiveSection, sidebarCollapsed, toggleSidebar } =
    useStudioStore();

  React.useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "b") {
        e.preventDefault();
        toggleSidebar();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleSidebar]);

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-border bg-surface transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-60"
      )}
    >
      <div
        className={cn(
          "flex h-12 items-center border-b border-border",
          sidebarCollapsed ? "justify-center px-2" : "justify-between px-4"
        )}
      >
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent">
              <span className="text-xs font-bold text-accent-text">F</span>
            </div>
            <span className="text-sm font-semibold text-text">Studio</span>
          </div>
        )}
        {sidebarCollapsed && (
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent">
            <span className="text-xs font-bold text-accent-text">F</span>
          </div>
        )}
        {!sidebarCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="h-7 w-7"
            title="Collapse sidebar (Ctrl+B)"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      <nav className="flex-1 space-y-0.5 p-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              className={cn(
                "flex w-full items-center rounded-md text-sm font-medium transition-colors",
                sidebarCollapsed ? "justify-center px-2 py-2.5" : "px-3 py-2",
                isActive
                  ? "bg-surface-active text-text"
                  : "text-text-muted hover:bg-surface-hover hover:text-text"
              )}
              title={sidebarCollapsed ? item.label : undefined}
              aria-label={item.label}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {!sidebarCollapsed && <span className="ml-3">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      <div className="border-t border-border p-2">
        {sidebarCollapsed ? (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="mx-auto h-8 w-8"
            title="Expand sidebar (Ctrl+B)"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        ) : (
          <div className="flex items-center justify-between px-2 py-1.5">
            <span className="text-xs text-text-muted">v1.0.0</span>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="h-6 w-6"
              title="Collapse sidebar (Ctrl+B)"
            >
              <ChevronLeft className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </aside>
  );
}

function StudioTopBar() {
  const { activeSection, sidebarCollapsed } = useStudioStore();

  const sectionLabel = React.useMemo(() => {
    const item = NAV_ITEMS.find((n) => n.id === activeSection);
    return item?.label ?? "Studio";
  }, [activeSection]);

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-surface/80 px-4 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <nav className="flex items-center gap-1 text-sm">
          <span className="text-text-muted">ForgeAI</span>
          <ChevronRight className="h-3 w-3 text-text-muted" />
          <span className="font-medium text-text">{sectionLabel}</span>
        </nav>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative hidden w-64 md:block">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Search..."
            className="h-8 w-full rounded-md border border-border bg-surface-active pl-8 pr-3 text-sm text-text placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
          <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rounded border border-border bg-surface px-1.5 py-0.5 font-mono text-[10px] text-text-muted">
            Ctrl+K
          </kbd>
        </div>

        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Bell className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}

function StudioBottomPanel() {
  const [bottomPanelOpen, setBottomPanelOpen] = React.useState(true);
  const [consoleEntries] = React.useState<ConsoleEntry[]>([
    {
      id: "1",
      type: "info",
      message: "Studio initialized",
      timestamp: "00:00:01",
    },
    {
      id: "2",
      type: "success",
      message: "Connected to ForgeAI runtime",
      timestamp: "00:00:02",
    },
  ]);

  React.useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "`") {
        e.preventDefault();
        setBottomPanelOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex flex-col border-t border-border bg-surface">
      <div className="flex h-8 items-center justify-between border-b border-border px-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setBottomPanelOpen(!bottomPanelOpen)}
            className="flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-text"
          >
            <Terminal className="h-3.5 w-3.5" />
            Console
            {bottomPanelOpen ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronUp className="h-3 w-3" />
            )}
          </button>
          <span className="text-xs text-text-muted">|</span>
          <span className="text-xs text-text-muted">Event Log</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-green-500" />
            Ready
          </span>
        </div>
      </div>

      {bottomPanelOpen && (
        <div className="h-36 overflow-y-auto bg-surface-active p-3 font-mono text-xs">
          {consoleEntries.length === 0 ? (
            <p className="text-text-muted">No output yet.</p>
          ) : (
            <div className="space-y-1">
              {consoleEntries.map((entry) => (
                <div key={entry.id} className="flex items-start gap-2">
                  <span className="text-text-muted">{entry.timestamp}</span>
                  {entry.type === "error" ? (
                    <AlertCircle className="mt-0.5 h-3 w-3 flex-shrink-0 text-danger" />
                  ) : entry.type === "success" ? (
                    <CheckCircle2 className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-500" />
                  ) : (
                    <span className="mt-0.5 h-3 w-3 flex-shrink-0" />
                  )}
                  <span
                    className={cn(
                      entry.type === "error" && "text-danger",
                      entry.type === "success" && "text-green-400",
                      entry.type === "info" && "text-text"
                    )}
                  >
                    {entry.message}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface StudioLayoutProps {
  children?: React.ReactNode;
}

function StudioLayout({ children }: StudioLayoutProps) {
  const { activeSection, isLoading } = useStudioStore();

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <StudioSidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <StudioTopBar />

        <main className="flex-1 overflow-y-auto bg-bg">
          {isLoading && (
            <div className="flex h-full items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
          )}
          {!isLoading && children}
        </main>

        <StudioBottomPanel />
      </div>
    </div>
  );
}

export { StudioLayout, StudioSidebar, StudioTopBar, StudioBottomPanel };
export type { StudioSection, NavItem };
