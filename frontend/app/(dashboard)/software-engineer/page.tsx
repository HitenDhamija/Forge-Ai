import { Metadata } from "next";
import { SoftwareEngineerWorkspace } from "@/components/software-engineer/SoftwareEngineerWorkspace";

export const metadata: Metadata = {
  title: "Software Engineer | ForgeAI",
  description: "AI Software Engineer for autonomous code implementation",
};

export default function SoftwareEngineerPage() {
  return <SoftwareEngineerWorkspace />;
}
