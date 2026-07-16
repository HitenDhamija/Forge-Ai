"use client";

import * as React from "react";
import { Route, Shield, ShieldOff } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { RouteInfo } from "@/types/repository";

interface RoutesTableProps {
  routes: RouteInfo[];
}

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-success/20 text-success",
  POST: "bg-accent/20 text-accent",
  PUT: "bg-warning/20 text-warning",
  PATCH: "bg-warning/20 text-warning",
  DELETE: "bg-danger/20 text-danger",
  OPTIONS: "bg-text-muted/20 text-text-muted",
  HEAD: "bg-text-muted/20 text-text-muted",
};

function RoutesTable({ routes }: RoutesTableProps) {
  const [sortField, setSortField] = React.useState<"method" | "path">("path");
  const [sortDir, setSortDir] = React.useState<"asc" | "desc">("asc");

  const sortedRoutes = React.useMemo(() => {
    return [...routes].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      return sortDir === "asc"
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    });
  }, [routes, sortField, sortDir]);

  const handleSort = (field: "method" | "path") => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  if (routes.length === 0) {
    return (
      <p className="text-sm text-text-muted">No routes detected</p>
    );
  }

  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead
              className="cursor-pointer hover:text-text"
              onClick={() => handleSort("method")}
            >
              Method
            </TableHead>
            <TableHead
              className="cursor-pointer hover:text-text"
              onClick={() => handleSort("path")}
            >
              Path
            </TableHead>
            <TableHead>Function</TableHead>
            <TableHead>File</TableHead>
            <TableHead>Auth</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedRoutes.map((route, idx) => (
            <TableRow key={`${route.method}-${route.path}-${idx}`}>
              <TableCell>
                <Badge
                  className={METHOD_COLORS[route.method] || "bg-text-muted/20 text-text-muted"}
                >
                  {route.method}
                </Badge>
              </TableCell>
              <TableCell>
                <code className="text-sm font-mono text-text">
                  {route.path}
                </code>
              </TableCell>
              <TableCell>
                <span className="text-sm text-text-muted">
                  {route.function_name}
                </span>
              </TableCell>
              <TableCell>
                <span className="font-mono text-xs text-text-muted">
                  {route.file_path}
                </span>
              </TableCell>
              <TableCell>
                {route.authentication_required ? (
                  <Shield className="h-4 w-4 text-success" />
                ) : (
                  <ShieldOff className="h-4 w-4 text-text-muted" />
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export { RoutesTable };
