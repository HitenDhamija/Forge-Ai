'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AgentInfo } from '@/types/workforce';
import {
  Brain,
  Code,
  TestTube,
  CheckCircle,
  FileText,
  Server,
  Database,
  Search,
  Wrench,
} from 'lucide-react';

interface AgentDetailsProps {
  agent: AgentInfo;
}

export function AgentDetails({ agent }: AgentDetailsProps) {
  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'supervisor':
        return <Brain className="h-5 w-5" />;
      case 'software_engineer':
        return <Code className="h-5 w-5" />;
      case 'qa_engineer':
        return <TestTube className="h-5 w-5" />;
      case 'code_reviewer':
        return <CheckCircle className="h-5 w-5" />;
      case 'technical_writer':
        return <FileText className="h-5 w-5" />;
      case 'devops_engineer':
        return <Server className="h-5 w-5" />;
      case 'database_engineer':
        return <Database className="h-5 w-5" />;
      case 'research_engineer':
        return <Search className="h-5 w-5" />;
      default:
        return <Brain className="h-5 w-5" />;
    }
  };

  const formatRole = (role: string) => {
    return role
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'idle':
        return <Badge className="bg-green-500">Idle</Badge>;
      case 'executing':
        return <Badge className="bg-blue-500">Executing</Badge>;
      case 'assigned':
        return <Badge className="bg-yellow-500">Assigned</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'offline':
        return <Badge variant="secondary">Offline</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getRoleIcon(agent.role)}
              <div>
                <CardTitle>{agent.name}</CardTitle>
                <p className="text-muted-foreground">{agent.description}</p>
              </div>
            </div>
            {getStatusBadge(agent.status)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-muted-foreground">Role</p>
              <Badge variant="outline">{formatRole(agent.role)}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Version</p>
              <p className="font-medium">{agent.version}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Capabilities</p>
              <p className="font-medium">{agent.capabilities.length}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Max Concurrent</p>
              <p className="font-medium">{agent.policies.max_concurrent_tasks}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {agent.capabilities.map((cap) => (
              <div key={cap.name} className="p-3 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium">{cap.name}</p>
                  <Badge variant="outline">Level {cap.level}/10</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-2">{cap.description}</p>
                <div className="flex flex-wrap gap-2">
                  {cap.tools.map((tool) => (
                    <Badge key={tool} variant="secondary" className="text-xs">
                      <Wrench className="h-3 w-3 mr-1" />
                      {tool}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Policies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Allowed Tasks</p>
              <div className="flex flex-wrap gap-2">
                {agent.policies.allowed_tasks.length > 0 ? (
                  agent.policies.allowed_tasks.map((task) => (
                    <Badge key={task} variant="outline">
                      {task}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">All tasks</p>
                )}
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-2">Allowed Tools</p>
              <div className="flex flex-wrap gap-2">
                {agent.policies.allowed_tools.length > 0 ? (
                  agent.policies.allowed_tools.map((tool) => (
                    <Badge key={tool} variant="outline">
                      {tool}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">All tools</p>
                )}
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Max Retries</p>
              <p className="font-medium">{agent.policies.max_retries}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Timeout</p>
              <p className="font-medium">{agent.policies.timeout_seconds}s</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Memory</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Short-Term Memory</p>
              <p className="font-medium">{agent.memory.short_term.length} items</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Task Memory</p>
              <p className="font-medium">{agent.memory.task_memory.length} tasks</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
