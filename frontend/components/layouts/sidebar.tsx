"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight, LogOut, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarStatus } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";
import { useAuth } from "@/hooks/use-auth";
import { mainNavigation, bottomNavigation } from "@/config/navigation";
import { ROUTES } from "@/config/constants";

function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { user, logout } = useAuth();

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-black/50 transition-opacity lg:hidden",
          sidebarCollapsed ? "opacity-0 pointer-events-none" : "opacity-100"
        )}
        onClick={toggleSidebar}
      />

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-full flex-col border-r border-border bg-surface transition-all duration-300",
          sidebarCollapsed ? "w-[70px]" : "w-[260px]",
          "lg:relative"
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          {!sidebarCollapsed && (
            <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-accent">
                <span className="text-sm font-bold text-accent-text">F</span>
              </div>
              <span className="text-lg font-semibold">ForgeAI</span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="hidden lg:flex"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Main navigation */}
        <nav className="flex-1 min-h-0 overflow-y-auto space-y-1 p-3">
          {mainNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.disabled ? "#" : item.href}
                className={cn(
                  "flex items-center rounded-md px-3 py-2 text-[15px] font-medium transition-colors",
                  isActive
                    ? "bg-surface-active text-text"
                    : "text-text-muted hover:bg-surface-hover hover:text-text",
                  item.disabled && "opacity-50 cursor-not-allowed",
                  sidebarCollapsed && "justify-center"
                )}
                title={sidebarCollapsed ? item.label : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {!sidebarCollapsed && (
                  <>
                    <span className="ml-3">{item.label}</span>
                    {item.badge && (
                      <span className="ml-auto rounded-full bg-accent/20 px-2 py-0.5 text-xs text-accent">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom navigation */}
        <div className="border-t border-border p-3 space-y-1">
          {bottomNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center rounded-md px-3 py-2 text-[15px] font-medium transition-colors",
                  isActive
                    ? "bg-surface-active text-text"
                    : "text-text-muted hover:bg-surface-hover hover:text-text",
                  sidebarCollapsed && "justify-center"
                )}
                title={sidebarCollapsed ? item.label : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {!sidebarCollapsed && <span className="ml-3">{item.label}</span>}
              </Link>
            );
          })}

          {/* User info */}
          <div
            className={cn(
              "flex items-center rounded-md px-3 py-2 text-[15px]",
              sidebarCollapsed && "justify-center"
            )}
          >
            <Avatar size="sm">
              <AvatarFallback>{user?.name?.charAt(0) || "U"}</AvatarFallback>
              <AvatarStatus status="online" />
            </Avatar>
            {!sidebarCollapsed && (
              <div className="ml-3 flex-1 overflow-hidden">
                <p className="truncate font-medium">{user?.name || "User"}</p>
                <p className="truncate text-xs text-text-muted">
                  {user?.email || "user@example.com"}
                </p>
              </div>
            )}
            {!sidebarCollapsed && (
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                className="flex-shrink-0"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

export { Sidebar };
