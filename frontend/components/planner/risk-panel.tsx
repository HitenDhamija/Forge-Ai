"use client";

import * as React from "react";
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Info,
  AlertCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Risk, RiskLevel } from "@/types/planner";

interface RiskPanelProps {
  risks: Risk[];
  onSelectRisk: (risk: Risk | null) => void;
  selectedRisk: Risk | null;
}

const RISK_LEVEL_CONFIG: Record<
  RiskLevel,
  {
    label: string;
    color: string;
    bgColor: string;
    icon: React.ReactNode;
  }
> = {
  low: {
    label: "Low",
    color: "text-success",
    bgColor: "bg-success/10",
    icon: <ShieldCheck className="h-4 w-4" />,
  },
  medium: {
    label: "Medium",
    color: "text-warning",
    bgColor: "bg-warning/10",
    icon: <Info className="h-4 w-4" />,
  },
  high: {
    label: "High",
    color: "text-danger",
    bgColor: "bg-danger/10",
    icon: <AlertTriangle className="h-4 w-4" />,
  },
  critical: {
    label: "Critical",
    color: "text-danger",
    bgColor: "bg-danger/20",
    icon: <ShieldAlert className="h-4 w-4" />,
  },
};

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  breaking_change: <AlertCircle className="h-4 w-4" />,
  dependency: <AlertCircle className="h-4 w-4" />,
  performance: <AlertCircle className="h-4 w-4" />,
  security: <ShieldAlert className="h-4 w-4" />,
  data_loss: <AlertTriangle className="h-4 w-4" />,
  default: <Info className="h-4 w-4" />,
};

function getRiskStats(risks: Risk[]) {
  const stats = { low: 0, medium: 0, high: 0, critical: 0, total: risks.length };
  risks.forEach((r) => {
    stats[r.level]++;
  });
  return stats;
}

export function RiskPanel({ risks, onSelectRisk, selectedRisk }: RiskPanelProps) {
  const stats = getRiskStats(risks);

  if (risks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-text-muted">
        <ShieldCheck className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-sm font-medium">No risks identified</p>
        <p className="text-xs mt-1">This plan has a clean risk profile</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-2">
        {(
          Object.entries(stats) as [
            "low" | "medium" | "high" | "critical" | "total",
            number,
          ][]
        ).map(([level, count]) => {
          if (level === "total") return null;
          const config = RISK_LEVEL_CONFIG[level];
          return (
            <div
              key={level}
              className={cn(
                "rounded-lg border p-2 text-center",
                config.bgColor,
                "border-transparent"
              )}
            >
              <div className={cn("flex items-center justify-center mb-1", config.color)}>
                {config.icon}
              </div>
              <p className={cn("text-lg font-semibold", config.color)}>
                {count}
              </p>
              <p className="text-xs text-text-muted">{config.label}</p>
            </div>
          );
        })}
      </div>

      <div className="space-y-2">
        {risks.map((risk, index) => {
          const levelConfig = RISK_LEVEL_CONFIG[risk.level];
          const categoryIcon =
            CATEGORY_ICONS[risk.category] || CATEGORY_ICONS.default;
          const isSelected = selectedRisk?.description === risk.description;

          return (
            <div
              key={`${risk.category}-${index}`}
              className={cn(
                "rounded-lg border p-3 transition-all cursor-pointer",
                isSelected
                  ? cn("border-accent", levelConfig.bgColor)
                  : "border-border bg-surface hover:bg-surface-hover"
              )}
              onClick={() => onSelectRisk(isSelected ? null : risk)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className={cn("mt-0.5", levelConfig.color)}>
                    {levelConfig.icon}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-xs",
                          levelConfig.bgColor,
                          levelConfig.color
                        )}
                      >
                        {levelConfig.label}
                      </Badge>
                      <span className="text-xs text-text-muted capitalize">
                        {risk.category.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-sm text-text">{risk.description}</p>
                  </div>
                </div>
              </div>

              {isSelected && (
                <div className="mt-3 ml-7 space-y-2 border-t border-border pt-3">
                  {risk.mitigation && (
                    <div>
                      <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
                        Mitigation
                      </span>
                      <p className="text-sm text-text-muted mt-1">
                        {risk.mitigation}
                      </p>
                    </div>
                  )}
                  {risk.affected_tasks.length > 0 && (
                    <div>
                      <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
                        Affected Tasks
                      </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {risk.affected_tasks.map((taskId) => (
                          <Badge
                            key={taskId}
                            variant="secondary"
                            className="text-xs font-mono"
                          >
                            {taskId}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
