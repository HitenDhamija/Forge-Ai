"use client";

import * as React from "react";
import { Cpu, Sparkles, FileSearch } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { FrameworkInfo } from "@/types/repository";

interface TechnologyCardsProps {
  frameworks: FrameworkInfo[];
  configFiles?: string[];
}

function TechnologyCards({
  frameworks,
  configFiles = [],
}: TechnologyCardsProps) {
  return (
    <div className="space-y-4">
      {frameworks.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {frameworks.map((fw) => (
            <Card key={fw.name}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-base">
                  <div className="flex items-center space-x-2">
                    <Cpu className="h-4 w-4 text-accent" />
                    <span>{fw.name}</span>
                  </div>
                  {fw.version && (
                    <Badge variant="secondary">{fw.version}</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-text-muted">Confidence</span>
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-surface-hover">
                      <div
                        className="h-full bg-accent transition-all"
                        style={{ width: `${fw.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-text">
                      {(fw.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                {fw.evidence.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {fw.evidence.slice(0, 3).map((ev) => (
                      <Badge
                        key={ev}
                        variant="default"
                        className="gap-1 text-xs"
                      >
                        <Sparkles className="h-2 w-2" />
                        {ev}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {configFiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-base">
              <FileSearch className="h-5 w-5 text-accent" />
              <span>Configuration Files</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1">
              {configFiles.map((file) => (
                <Badge key={file} variant="default" className="font-mono text-xs">
                  {file}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {frameworks.length === 0 && configFiles.length === 0 && (
        <p className="text-sm text-text-muted">
          No frameworks or configuration files detected.
        </p>
      )}
    </div>
  );
}

export { TechnologyCards };
