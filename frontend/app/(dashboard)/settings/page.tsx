"use client";

import * as React from "react";
import { Save, Send, Check, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layouts/page-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useThemeStore } from "@/stores/theme-store";
import { Switch } from "@/components/ui/switch";
import { notificationService } from "@/services/notification.service";

const generalSchema = z.object({
  appName: z.string().min(1, "App name is required"),
  apiUrl: z.string().url("Please enter a valid URL"),
});
type GeneralFormData = z.infer<typeof generalSchema>;

const EMAIL_TOGGLES = [
  { key: "email_task_complete", label: "Task completed", desc: "When an agent finishes a task" },
  { key: "email_task_failed", label: "Task failed", desc: "When a task encounters an error" },
  { key: "email_workflow_approved", label: "Workflow approved", desc: "When a workflow is approved" },
  { key: "email_deployment", label: "Deployment updates", desc: "Deployment status changes" },
  { key: "email_security", label: "Security alerts", desc: "Critical security notifications" },
];

const INAPP_TOGGLES = [
  { key: "inapp_agent_updates", label: "Agent activity", desc: "Real-time agent status updates" },
  { key: "inapp_mentions", label: "Mentions", desc: "When someone mentions you" },
  { key: "inapp_system", label: "System messages", desc: "Platform updates and maintenance" },
];

export default function SettingsPage() {
  const { theme, setTheme } = useThemeStore();
  const [isSaving, setIsSaving] = React.useState(false);
  const [prefs, setPrefs] = React.useState<Record<string, boolean>>({});
  const [smtpConfigured, setSmtpConfigured] = React.useState(false);
  const [testEmail, setTestEmail] = React.useState("");
  const [testStatus, setTestStatus] = React.useState<"idle" | "sending" | "sent" | "error">("idle");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<GeneralFormData>({
    resolver: zodResolver(generalSchema),
    defaultValues: { appName: "ForgeAI", apiUrl: "http://localhost:8000" },
  });

  React.useEffect(() => {
    notificationService.getPreferences().then(setPrefs).catch(() => {});
    notificationService.getSMTPStatus().then((s) => setSmtpConfigured(s.configured)).catch(() => {});
  }, []);

  const togglePref = async (key: string) => {
    const updated = { ...prefs, [key]: !prefs[key] };
    setPrefs(updated);
    try {
      await notificationService.updatePreferences({ [key]: updated[key] });
    } catch {}
  };

  const onSubmit = async (data: GeneralFormData) => {
    setIsSaving(true);
    await new Promise((r) => setTimeout(r, 1000));
    setIsSaving(false);
    alert("Settings saved!");
  };

  const handleTestEmail = async () => {
    if (!testEmail) return;
    setTestStatus("sending");
    try {
      const result = await notificationService.sendTestEmail(testEmail);
      setTestStatus(result.status === "success" ? "sent" : "error");
    } catch {
      setTestStatus("error");
    }
    setTimeout(() => setTestStatus("idle"), 3000);
  };

  return (
    <div>
      <PageHeader title="Settings" description="Manage your application settings and preferences" />

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
        </TabsList>

        {/* General */}
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>Configure your application settings</CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit(onSubmit)}>
              <CardContent className="space-y-4">
                <Input label="Application Name" placeholder="ForgeAI" error={errors.appName?.message} {...register("appName")} />
                <Input label="API URL" placeholder="http://localhost:8000" error={errors.apiUrl?.message} {...register("apiUrl")} />
              </CardContent>
              <CardFooter>
                <Button type="submit" isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>Save Changes</Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>

        {/* Appearance */}
        <TabsContent value="appearance">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Customize the look and feel of your application</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Theme</label>
                <div className="flex space-x-2">
                  {(["dark", "light", "system"] as const).map((t) => (
                    <Button key={t} variant={theme === t ? "default" : "outline"} onClick={() => setTheme(t)}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-4">
          {/* SMTP Status */}
          <Card>
            <CardHeader>
              <CardTitle>Email Service (SMTP)</CardTitle>
              <CardDescription>Configure and test your email delivery</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${smtpConfigured ? "bg-success" : "bg-warning"}`} />
                <span className="text-sm">
                  {smtpConfigured ? "SMTP configured — emails are live" : "SMTP not configured — emails are disabled"}
                </span>
              </div>
              {!smtpConfigured && (
                <p className="text-xs text-text-muted">
                  Set environment variables before starting the backend. For Gmail, use an{" "}
                  <a href="https://myaccount.google.com/apppasswords" target="_blank" className="text-accent hover:underline">App Password</a>.
                  See the <code className="rounded bg-surface px-1 py-0.5">backend/.env.smtp.example</code> file for all options.
                </p>
              )}
              <div className="flex items-end space-x-2">
                <Input
                  label="Send test email to"
                  placeholder="your@email.com"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  className="max-w-sm"
                />
                <Button
                  variant="outline"
                  onClick={handleTestEmail}
                  disabled={!testEmail || testStatus === "sending"}
                  leftIcon={
                    testStatus === "sending" ? <Loader2 className="h-4 w-4 animate-spin" /> :
                    testStatus === "sent" ? <Check className="h-4 w-4" /> :
                    <Send className="h-4 w-4" />
                  }
                >
                  {testStatus === "sent" ? "Sent!" : testStatus === "error" ? "Failed" : "Send Test"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Email toggles */}
          <Card>
            <CardHeader>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>Choose which emails you want to receive</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {EMAIL_TOGGLES.map((item) => (
                <div key={item.key} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-text-muted">{item.desc}</p>
                  </div>
                  <Switch checked={!!prefs[item.key]} onCheckedChange={() => togglePref(item.key)} />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* In-app toggles */}
          <Card>
            <CardHeader>
              <CardTitle>In-App Notifications</CardTitle>
              <CardDescription>Control what appears in the notification center</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {INAPP_TOGGLES.map((item) => (
                <div key={item.key} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-text-muted">{item.desc}</p>
                  </div>
                  <Switch checked={!!prefs[item.key]} onCheckedChange={() => togglePref(item.key)} />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys */}
        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage your API keys for external integrations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { name: "OpenAI", key: "sk-...****", added: "2 days ago" },
                { name: "Ollama (Local)", key: "http://localhost:11434", added: "1 week ago" },
              ].map((item) => (
                <div key={item.name} className="flex items-center justify-between rounded-md border border-border p-3">
                  <div>
                    <p className="text-sm font-medium">{item.name}</p>
                    <p className="text-xs text-text-muted font-mono">{item.key}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-text-muted">Added {item.added}</span>
                    <Button variant="ghost" size="sm">Remove</Button>
                  </div>
                </div>
              ))}
              <Button variant="outline" size="sm">Add API Key</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
