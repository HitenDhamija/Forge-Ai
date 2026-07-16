"use client";

import * as React from "react";
import { Camera, Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarStatus } from "@/components/ui/avatar";
import { PageHeader } from "@/components/layouts/page-header";
import { useAuthStore } from "@/stores/auth-store";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  bio: z.string().optional(),
  company: z.string().optional(),
  website: z.string().url("Please enter a valid URL").optional().or(z.literal("")),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [isSaving, setIsSaving] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name || "",
      email: user?.email || "",
      bio: "",
      company: "",
      website: "",
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    setIsSaving(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
    alert("Profile saved successfully!");
  };

  return (
    <div>
      <PageHeader
        title="Profile"
        description="Manage your personal information and preferences"
      />

      <div className="max-w-2xl space-y-6">
        {/* Avatar Section */}
        <Card>
          <CardHeader>
            <CardTitle>Profile Picture</CardTitle>
            <CardDescription>Update your profile photo</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-6">
              <Avatar size="xl">
                <AvatarFallback>{user?.name?.charAt(0) || "U"}</AvatarFallback>
                <AvatarStatus status="online" />
              </Avatar>
              <div>
                <Button variant="outline" leftIcon={<Camera className="h-4 w-4" />}>
                  Upload Photo
                </Button>
                <p className="mt-2 text-xs text-text-muted">
                  JPG, GIF or PNG. Max size 2MB.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Personal Information */}
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Update your personal details</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label="Name"
                  placeholder="Your name"
                  error={errors.name?.message}
                  {...register("name")}
                />
                <Input
                  label="Email"
                  type="email"
                  placeholder="your@email.com"
                  error={errors.email?.message}
                  {...register("email")}
                />
              </div>
              <Input
                label="Company"
                placeholder="Your company"
                {...register("company")}
              />
              <Input
                label="Website"
                placeholder="https://example.com"
                error={errors.website?.message}
                {...register("website")}
              />
              <Textarea
                label="Bio"
                placeholder="Tell us about yourself"
                rows={4}
                {...register("bio")}
              />
            </CardContent>
            <CardFooter>
              <Button type="submit" isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>
                Save Changes
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
