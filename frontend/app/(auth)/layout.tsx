import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "ForgeAI - Authentication",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center space-x-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent">
              <span className="text-lg font-bold text-accent-text">F</span>
            </div>
            <span className="text-2xl font-bold">ForgeAI</span>
          </Link>
        </div>
        {children}
      </div>
    </div>
  );
}
