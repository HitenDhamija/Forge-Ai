"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, FolderKanban } from "lucide-react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useProjectStore } from "@/stores/project-store";
import { ROUTES } from "@/config/constants";

const projectSchema = z.object({
  name: z.string().min(1, "Project name is required"),
  description: z.string().optional(),
});

type ProjectFormData = z.infer<typeof projectSchema>;

export default function NewProjectPage() {
  const router = useRouter();
  const { addProject } = useProjectStore();
  const [isCreating, setIsCreating] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: { name: "", description: "" },
  });

  const onSubmit = async (data: ProjectFormData) => {
    setIsCreating(true);
    await new Promise((r) => setTimeout(r, 500));

    const newProject = {
      id: crypto.randomUUID(),
      name: data.name,
      description: data.description || "",
      status: "active" as const,
      createdAt: new Date().toISOString().split("T")[0],
      updatedAt: new Date().toISOString().split("T")[0],
      userId: "user-1",
    };

    addProject(newProject);
    router.push(ROUTES.PROJECTS);
  };

  return (
    <div>
      <Link href={ROUTES.PROJECTS} className="mb-4 inline-flex items-center text-sm text-text-muted hover:text-text">
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to Projects
      </Link>

      <div className="mx-auto max-w-lg">
        <Card>
          <CardHeader>
            <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10">
              <FolderKanban className="h-6 w-6 text-accent" />
            </div>
            <CardTitle className="text-2xl">Create New Project</CardTitle>
            <CardDescription>Give your project a name and optional description.</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <Input
                label="Project Name"
                placeholder="e.g. Website Redesign"
                error={errors.name?.message}
                {...register("name")}
              />
              <Textarea
                label="Description (optional)"
                placeholder="What is this project about?"
                rows={3}
                {...register("description")}
              />
            </CardContent>
            <CardFooter className="flex justify-end space-x-2">
              <Link href={ROUTES.PROJECTS}>
                <Button variant="ghost" type="button">Cancel</Button>
              </Link>
              <Button type="submit" isLoading={isCreating}>Create Project</Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
