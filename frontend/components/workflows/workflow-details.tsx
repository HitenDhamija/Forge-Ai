'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { WorkflowInfo } from '@/types/workflows';
import {
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Pause,
  Play,
  X,
} from 'lucide-react';

interface WorkflowDetailsProps {
  workflow: WorkflowInfo;
  onApprove?: () => void;
  onStart?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
}

export function WorkflowDetails({
  workflow,
  onApprove,
  onStart,
  onPause,
  onResume,
  onCancel,
}: WorkflowDetailsProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'paused':
        return <Pause className="h-5 w-5 text-yellow-500" />;
      default:
        return <Clock className="h-5 w-5" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'running':
        return <Badge className="bg-blue-500">Running</Badge>;
      case 'paused':
        return <Badge className="bg-yellow-500">Paused</Badge>;
      case 'waiting_approval':
        return <Badge className="bg-orange-500">Waiting Approval</Badge>;
      case 'ready':
        return <Badge className="bg-purple-500">Ready</Badge>;
      case 'cancelled':
        return <Badge variant="secondary">Cancelled</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const getTaskStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const completedTasks = workflow.tasks.filter(
    (t) => t.status === 'completed'
  ).length;
  const totalTasks = workflow.tasks.length;
  const progress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon(workflow.status)}
              <CardTitle>{workflow.title}</CardTitle>
            </div>
            <div className="flex items-center space-x-2">
              {getStatusBadge(workflow.status)}
              {workflow.status === 'waiting_approval' && onApprove && (
                <Button onClick={onApprove}>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Approve
                </Button>
              )}
              {workflow.status === 'ready' && onStart && (
                <Button onClick={onStart}>
                  <Play className="mr-2 h-4 w-4" />
                  Start
                </Button>
              )}
              {workflow.status === 'running' && onPause && (
                <Button variant="outline" onClick={onPause}>
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </Button>
              )}
              {workflow.status === 'paused' && onResume && (
                <Button onClick={onResume}>
                  <Play className="mr-2 h-4 w-4" />
                  Resume
                </Button>
              )}
              {(workflow.status === 'running' ||
                workflow.status === 'paused') &&
                onCancel && (
                  <Button variant="destructive" onClick={onCancel}>
                    <X className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">{workflow.description}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-muted-foreground">Tasks</p>
              <p className="text-2xl font-bold">
                {completedTasks}/{totalTasks}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Progress</p>
              <p className="text-2xl font-bold">{progress.toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <Badge>{workflow.risk_level}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="text-sm">
                {new Date(workflow.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="w-full bg-muted rounded-full h-2 mb-6">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tasks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {workflow.tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  {getTaskStatusIcon(task.status)}
                  <div>
                    <p className="font-medium">{task.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {task.priority} priority
                      {task.dependencies.length > 0 &&
                        ` • Depends on ${task.dependencies.length} task(s)`}
                    </p>
                  </div>
                </div>
                <Badge variant="outline">{task.status}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
