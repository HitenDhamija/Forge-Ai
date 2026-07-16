'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AgentInfo } from '@/types/agents';
import {
  Bot,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Wrench,
} from 'lucide-react';

interface AgentStatusProps {
  agent: AgentInfo;
}

export function AgentStatus({ agent }: AgentStatusProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'idle':
        return <Clock className="h-5 w-5 text-muted-foreground" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Bot className="h-5 w-5" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'idle':
        return <Badge variant="secondary">Idle</Badge>;
      case 'running':
        return <Badge className="bg-blue-500">Running</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{agent.name}</CardTitle>
          {getStatusBadge(agent.status)}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            {getStatusIcon(agent.status)}
            <span className="text-sm text-muted-foreground">
              {agent.description}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <Badge variant="outline">{agent.agent_type}</Badge>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Available Tools:</p>
            <div className="flex flex-wrap gap-2">
              {agent.available_tools.map((tool) => (
                <Badge key={tool} variant="secondary" className="text-xs">
                  <Wrench className="h-3 w-3 mr-1" />
                  {tool}
                </Badge>
              ))}
            </div>
          </div>

          <div className="text-xs text-muted-foreground">
            Created: {new Date(agent.created_at).toLocaleString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
