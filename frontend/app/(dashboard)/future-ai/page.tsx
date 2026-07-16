"use client";

import { Brain, Sparkles, Zap, Lock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layouts/page-header";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Workflows",
    description: "Automate complex tasks with intelligent AI workflows that learn and adapt.",
  },
  {
    icon: Sparkles,
    title: "Natural Language Processing",
    description: "Understand and process human language for smarter interactions.",
  },
  {
    icon: Zap,
    title: "Real-time Analytics",
    description: "Get insights and analytics powered by AI in real-time.",
  },
  {
    icon: Lock,
    title: "Enterprise Security",
    description: "Bank-grade security for your AI operations and data.",
  },
];

export default function FutureAIPage() {
  return (
    <div>
      <PageHeader
        title="AI Employees"
        description="Intelligent AI assistants to supercharge your workflow"
      />

      <div className="flex flex-col items-center justify-center py-16">
        <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-2xl bg-accent/10">
          <Brain className="h-12 w-12 text-accent" />
        </div>

        <Badge variant="secondary" className="mb-4">
          Coming Soon
        </Badge>

        <h2 className="mb-4 text-3xl font-bold text-center">
          AI Employees are on the way
        </h2>
        <p className="mb-12 max-w-2xl text-center text-text-muted">
          We&apos;re building powerful AI assistants that will help you automate tasks,
          make decisions, and boost your productivity. Stay tuned for updates.
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
