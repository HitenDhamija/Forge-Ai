"use client";

import { Bot, Workflow, Cpu, Shield } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layouts/page-header";

const features = [
  {
    icon: Bot,
    title: "Autonomous Agents",
    description: "Deploy intelligent agents that can work independently on complex tasks.",
  },
  {
    icon: Workflow,
    title: "Multi-Agent Systems",
    description: "Coordinate multiple agents to work together on larger projects.",
  },
  {
    icon: Cpu,
    title: "Custom Tool Integration",
    description: "Connect agents to your existing tools and services seamlessly.",
  },
  {
    icon: Shield,
    title: "Controlled Execution",
    description: "Set boundaries and rules for agent behavior with full control.",
  },
];

export default function FutureAgentsPage() {
  return (
    <div>
      <PageHeader
        title="Agents"
        description="Autonomous AI agents for complex task automation"
      />

      <div className="flex flex-col items-center justify-center py-16">
        <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-2xl bg-accent/10">
          <Bot className="h-12 w-12 text-accent" />
        </div>

        <Badge variant="secondary" className="mb-4">
          Coming Soon
        </Badge>

        <h2 className="mb-4 text-3xl font-bold text-center">
          AI Agents are under development
        </h2>
        <p className="mb-12 max-w-2xl text-center text-text-muted">
          We&apos;re creating powerful autonomous agents that can handle complex workflows,
          make decisions, and execute tasks with minimal human intervention.
        </p>

        <div className="grid w-full max-w-4xl gap-6 md:grid-cols-2">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="opacity-60">
                <CardHeader>
                  <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-surface-hover">
                    <Icon className="h-5 w-5 text-text-muted" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
