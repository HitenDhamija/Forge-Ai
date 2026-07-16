'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { TaskInfo } from '@/types/workflows';
import { CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

interface TaskGraphProps {
  tasks: TaskInfo[];
}

export function TaskGraph({ tasks }: TaskGraphProps) {
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

  const taskMap = new Map(tasks.map((t) => [t.id, t]));
  const rootTasks = tasks.filter((t) => t.dependencies.length === 0);

  const buildLevels = (): TaskInfo[][] => {
    const levels: TaskInfo[][] = [];
    const visited = new Set<string>();

    const addLevel = (currentTasks: TaskInfo[]) => {
      if (currentTasks.length === 0) return;

      levels.push(currentTasks);
      currentTasks.forEach((t) => visited.add(t.id));

      const nextTasks: TaskInfo[] = [];
      for (const task of tasks) {
        if (!visited.has(task.id)) {
          const deps = task.dependencies;
          if (deps.every((d) => visited.has(d))) {
            nextTasks.push(task);
          }
        }
      }

      addLevel(nextTasks);
    };

    addLevel(rootTasks);
    return levels;
  };

  const levels = buildLevels();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Task Dependency Graph</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-8">
          {levels.map((level, levelIndex) => (
            <div key={levelIndex}>
              <p className="text-sm text-muted-foreground mb-3">
                Level {levelIndex + 1}
              </p>
              <div className="flex flex-wrap gap-4">
                {level.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center space-x-2 p-3 border rounded-lg min-w-[200px]"
                  >
                    {getTaskStatusIcon(task.status)}
                    <div className="flex-1">
                      <p className="font-medium text-sm">{task.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {task.priority}
                      </p>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {task.status}
                    </Badge>
                  </div>
                ))}
              </div>
              {levelIndex < levels.length - 1 && (
                <div className="flex justify-center my-2">
                  <div className="w-px h-6 bg-border" />
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
