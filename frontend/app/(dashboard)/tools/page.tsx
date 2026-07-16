import { Metadata } from "next";
import { ToolCenter } from "@/components/tools/ToolCenter";

export const metadata: Metadata = {
  title: "Tool Center | ForgeAI",
  description: "Manage and execute tools for your workflows",
};

export default function ToolsPage() {
  return <ToolCenter />;
}
