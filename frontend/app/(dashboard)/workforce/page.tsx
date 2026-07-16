'use client';

import { useEffect } from 'react';
import { useWorkforceStore } from '@/stores/workforce-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Users,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Brain,
  Code,
  TestTube,
  FileText,
  Server,
  Database,
  Search,
} from 'lucide-react';

export default function WorkforcePage() {
  const { agents, statusSummary, isLoading, fetchAgents, fetchStatusSummary } =
    useWorkforceStore();

  useEffect(() => {
    fetchAgents();
    fetchStatusSummary();
  }, [fetchAgents, fetchStatusSummary]);

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
        return <Users className="h-5 w-5" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'executing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
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

  const formatRole = (role: string) => {
    return role
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Enterprise AI Workforce</h1>
        <p className="text-muted-foreground">
          Manage and monitor your AI employees
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : statusSummary ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statusSummary.total_agents}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Idle Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">
                {statusSummary.idle_agents}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Busy Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-500">
                {statusSummary.busy_agents}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Unavailable
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">
                {statusSummary.unavailable_agents}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>AI Employees</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                  <Skeleton className="h-6 w-20" />
                </div>
              ))}
            </div>
          ) : agents.length > 0 ? (
            <div className="space-y-4">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-muted rounded-full">
                      {getRoleIcon(agent.role)}
                    </div>
                    <div>
                      <p className="font-medium">{agent.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {agent.description}
                      </p>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge variant="outline">{formatRole(agent.role)}</Badge>
                        <span className="text-xs text-muted-foreground">
                          v{agent.version}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Capabilities</p>
                      <p className="font-medium">{agent.capabilities.length}</p>
                    </div>
                    {getStatusIcon(agent.status)}
                    {getStatusBadge(agent.status)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No agents registered
            </p>
          )}
        </CardContent>
      </Card>

      {statusSummary && Object.keys(statusSummary.agents_by_role).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Agents by Role</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(statusSummary.agents_by_role).map(([role, count]) => (
                <div key={role} className="flex items-center space-x-2 p-3 border rounded-lg">
                  {getRoleIcon(role)}
                  <div>
                    <p className="font-medium">{formatRole(role)}</p>
                    <p className="text-sm text-muted-foreground">{count} agent(s)</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
