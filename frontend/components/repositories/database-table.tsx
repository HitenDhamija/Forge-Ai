"use client";

import * as React from "react";
import { Database, Key, Link2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { DatabaseModelInfo } from "@/types/repository";

interface DatabaseTableProps {
  models: DatabaseModelInfo[];
}

function DatabaseTable({ models }: DatabaseTableProps) {
  if (models.length === 0) {
    return (
      <p className="text-sm text-text-muted">No database models detected</p>
    );
  }

  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Model</TableHead>
            <TableHead>Table</TableHead>
            <TableHead>Fields</TableHead>
            <TableHead>Relationships</TableHead>
            <TableHead>Primary Key</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {models.map((model) => (
            <TableRow key={model.name}>
              <TableCell>
                <div className="flex items-center space-x-2">
                  <Database className="h-4 w-4 text-accent" />
                  <span className="font-medium text-text">{model.name}</span>
                </div>
              </TableCell>
              <TableCell>
                <code className="text-sm text-text-muted">
                  {model.table_name || "-"}
                </code>
              </TableCell>
              <TableCell>
                <Badge variant="default">
                  {model.fields.length} fields
                </Badge>
              </TableCell>
              <TableCell>
                {model.relationships.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {model.relationships.map((rel) => (
                      <Badge
                        key={rel}
                        variant="secondary"
                        className="gap-1 text-xs"
                      >
                        <Link2 className="h-2 w-2" />
                        {rel}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-text-muted">None</span>
                )}
              </TableCell>
              <TableCell>
                {model.primary_key ? (
                  <div className="flex items-center space-x-1">
                    <Key className="h-3 w-3 text-warning" />
                    <code className="text-sm text-text-muted">
                      {model.primary_key}
                    </code>
                  </div>
                ) : (
                  <span className="text-xs text-text-muted">-</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export { DatabaseTable };
