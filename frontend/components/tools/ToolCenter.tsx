"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Wrench,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Terminal,
  Database,
  Globe,
  FolderTree,
  GitBranch,
  Box,
} from "lucide-react";
import { TOOL_ENDPOINTS, API_URL } from "@/config/constants";

interface Tool {
  tool_id: string;
  name: string;
  description: string;
  type: string;
  provider: string;
  status: string;
  version: string;
  supported_operations: string[];
}

interface ToolExecution {
  execution_id: string;
  tool_id: string;
  success: boolean;
  duration_ms: number;
  error: string | null;
}

const TOOL_ICONS: Record<string, React.ReactNode> = {
  filesystem: <FolderTree className="h-5 w-5" />,
  git: <GitBranch className="h-5 w-5" />,
  terminal: <Terminal className="h-5 w-5" />,
  docker: <Box className="h-5 w-5" />,
  database: <Database className="h-5 w-5" />,
  browser: <Globe className="h-5 w-5" />,
};

export function ToolCenter() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [executions, setExecutions] = useState<ToolExecution[]>([]);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [operation, setOperation] = useState("");
  const [parameters, setParameters] = useState("{}");
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    fetchTools();
    fetchExecutions();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await fetch(`${API_URL}${TOOL_ENDPOINTS.BASE}`);
      if (response.ok) {
        const json = await response.json();
        const data = json.data || json;
        setTools(data.tools || data || []);
      }
    } catch (error) {
      console.error("Failed to fetch tools:", error);
    }
  };

  const fetchExecutions = async () => {
    try {
      const response = await fetch(`${API_URL}${TOOL_ENDPOINTS.EXECUTIONS}`);
      if (response.ok) {
        const json = await response.json();
        const data = json.data || json;
        setExecutions(data.executions || data || []);
      }
    } catch (error) {
      console.error("Failed to fetch executions:", error);
    }
  };

  const executeTool = async () => {
    if (!selectedTool || !operation) return;

    setIsExecuting(true);
    setResult(null);

    try {
      let parsedParams = {};
      try {
        parsedParams = JSON.parse(parameters);
      } catch {
        parsedParams = { raw: parameters };
      }

      const response = await fetch(`${API_URL}${TOOL_ENDPOINTS.EXECUTE}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool_id: selectedTool.tool_id,
          operation,
          parameters: parsedParams,
        }),
      });

      const data = await response.json();
      setResult(data);
      fetchExecutions();
    } catch (error) {
      setResult({ success: false, error: "Execution failed" });
    } finally {
      setIsExecuting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "unhealthy":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tool Center</h1>
          <p className="text-muted-foreground">
            Manage and execute tools for your workflows
          </p>
        </div>
        <Button onClick={fetchTools} variant="outline">
          <Wrench className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="tools">
        <TabsList>
          <TabsTrigger value="tools">Tools</TabsTrigger>
          <TabsTrigger value="execute">Execute</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="tools" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tools.map((tool) => (
              <Card
                key={tool.tool_id}
                className={`cursor-pointer transition-colors ${
                  selectedTool?.tool_id === tool.tool_id
                    ? "border-primary"
                    : "hover:border-muted-foreground/50"
                }`}
                onClick={() => setSelectedTool(tool)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {TOOL_ICONS[tool.tool_id] || <Wrench className="h-5 w-5" />}
                      <CardTitle className="text-lg">{tool.name}</CardTitle>
                    </div>
                    {getStatusIcon(tool.status)}
                  </div>
                  <CardDescription>{tool.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1">
                    {tool.supported_operations.slice(0, 3).map((op) => (
                      <Badge key={op} variant="secondary" className="text-xs">
                        {op}
                      </Badge>
                    ))}
                    {tool.supported_operations.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{tool.supported_operations.length - 3}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="execute" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Execute Tool</CardTitle>
              <CardDescription>
                {selectedTool
                  ? `Executing: ${selectedTool.name}`
                  : "Select a tool from the Tools tab"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Operation</label>
                <Input
                  placeholder="e.g., read, write, list, execute"
                  value={operation}
                  onChange={(e) => setOperation(e.target.value)}
                  disabled={!selectedTool}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Parameters (JSON)</label>
                <Textarea
                  placeholder='{"path": "./"}'
                  value={parameters}
                  onChange={(e) => setParameters(e.target.value)}
                  disabled={!selectedTool}
                  rows={4}
                />
              </div>
              <Button
                onClick={executeTool}
                disabled={!selectedTool || !operation || isExecuting}
              >
                {isExecuting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                Execute
              </Button>

              {result && (
                <div className="mt-4 p-4 rounded-lg bg-muted">
                  <div className="flex items-center gap-2 mb-2">
                    {result.success ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="font-medium">
                      {result.success ? "Success" : "Failed"}
                    </span>
                    {result.duration_ms && (
                      <Badge variant="secondary">
                        {result.duration_ms.toFixed(0)}ms
                      </Badge>
                    )}
                  </div>
                  <pre className="text-sm overflow-auto max-h-64">
                    {JSON.stringify(result.data || result.error, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Execution History</CardTitle>
              <CardDescription>Recent tool executions</CardDescription>
            </CardHeader>
            <CardContent>
              {executions.length === 0 ? (
                <p className="text-muted-foreground">No executions yet</p>
              ) : (
                <div className="space-y-2">
                  {executions.slice(0, 10).map((exec) => (
                    <div
                      key={exec.execution_id}
                      className="flex items-center justify-between p-2 rounded-lg bg-muted"
                    >
                      <div className="flex items-center gap-2">
                        {exec.success ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className="font-medium">{exec.tool_id}</span>
                        <Badge variant="secondary" className="text-xs">
                          {exec.duration_ms.toFixed(0)}ms
                        </Badge>
                      </div>
                      {exec.error && (
                        <span className="text-sm text-destructive">
                          {exec.error}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
