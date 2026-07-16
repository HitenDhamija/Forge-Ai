"use client";

import * as React from "react";
import {
  Layers,
  DoorOpen,
  Package,
  Shield,
  Database,
  Globe,
  Monitor,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ArchitectureSummary as ArchitectureSummaryType } from "@/types/repository";

interface ArchitectureSummaryProps {
  architecture: ArchitectureSummaryType;
}

const STYLE_LABELS: Record<string, string> = {
  mvc: "MVC (Model-View-Controller)",
  clean: "Clean Architecture",
  layered: "Layered Architecture",
  microservices: "Microservices",
  monolith: "Monolithic",
  serverless: "Serverless",
  unknown: "Unknown",
};

function ArchitectureSummary({ architecture }: ArchitectureSummaryProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-base">
            <Layers className="h-5 w-5 text-accent" />
            <span>Architecture Style</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Badge variant="default" className="text-sm">
              {STYLE_LABELS[architecture.style] || architecture.style}
            </Badge>
          </div>
          <p className="text-sm text-text-muted">{architecture.description}</p>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <DetectionIndicator
              icon={<Shield className="h-4 w-4" />}
              label="Authentication"
              detected={architecture.authentication_detected}
            />
            <DetectionIndicator
              icon={<Database className="h-4 w-4" />}
              label="Database"
              detected={architecture.database_detected}
            />
            <DetectionIndicator
              icon={<Globe className="h-4 w-4" />}
              label="API"
              detected={architecture.api_detected}
            />
            <DetectionIndicator
              icon={<Monitor className="h-4 w-4" />}
              label="Frontend"
              detected={architecture.frontend_detected}
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-base">
              <DoorOpen className="h-5 w-5 text-accent" />
              <span>Entry Points</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {architecture.entry_points.length > 0 ? (
              <ul className="space-y-1">
                {architecture.entry_points.map((ep) => (
                  <li
                    key={ep}
                    className="font-mono text-sm text-text-muted"
                  >
                    {ep}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-text-muted">No entry points detected</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-base">
              <Package className="h-5 w-5 text-accent" />
              <span>Main Modules</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {architecture.main_modules.length > 0 ? (
              <div className="flex flex-wrap gap-1">
                {architecture.main_modules.map((mod) => (
                  <Badge key={mod} variant="secondary">
                    {mod}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted">No modules detected</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DetectionIndicator({
  icon,
  label,
  detected,
}: {
  icon: React.ReactNode;
  label: string;
  detected: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center space-x-2 rounded-md border p-2",
        detected
          ? "border-success/30 bg-success/5 text-success"
          : "border-border bg-surface text-text-muted"
      )}
    >
      {icon}
      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}

export { ArchitectureSummary };
