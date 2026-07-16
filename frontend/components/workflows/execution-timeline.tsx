'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { WorkflowEvent } from '@/types/workflows';
import {
  CheckCircle,
  XCircle,
  Clock,
  Play,
  Pause,
  X,
  AlertCircle,
} from 'lucide-react';

interface ExecutionTimelineProps {
  events: WorkflowEvent[];
}

export function ExecutionTimeline({ events }: ExecutionTimelineProps) {
  const getEventIcon = (eventType: string) => {
    if (eventType.includes('completed')) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    if (eventType.includes('failed')) {
      return <XCircle className="h-4 w-4 text-red-500" />;
    }
    if (eventType.includes('started') || eventType.includes('resumed')) {
      return <Play className="h-4 w-4 text-blue-500" />;
    }
    if (eventType.includes('paused')) {
      return <Pause className="h-4 w-4 text-yellow-500" />;
    }
    if (eventType.includes('cancelled')) {
      return <X className="h-4 w-4 text-gray-500" />;
    }
    if (eventType.includes('approval')) {
      return <AlertCircle className="h-4 w-4 text-orange-500" />;
    }
    return <Clock className="h-4 w-4" />;
  };

  const formatEventType = (eventType: string) => {
    return eventType
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const sortedEvents = [...events].sort(
    (a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Execution Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        {sortedEvents.length > 0 ? (
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />
            <div className="space-y-4">
              {sortedEvents.map((event) => (
                <div key={event.id} className="flex items-start space-x-4 relative">
                  <div className="relative z-10 p-1 bg-background border rounded-full">
                    {getEventIcon(event.event_type)}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{formatEventType(event.event_type)}</p>
                    {event.task_id && (
                      <p className="text-sm text-muted-foreground">
                        Task: {event.task_id}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-muted-foreground text-center py-8">
            No events recorded yet
          </p>
        )}
      </CardContent>
    </Card>
  );
}
