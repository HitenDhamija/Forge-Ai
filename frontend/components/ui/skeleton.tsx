import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
}

function Skeleton({ className, variant = "rectangular", ...props }: SkeletonProps) {
  const variantClasses = {
    text: "h-4 w-full rounded",
    circular: "h-12 w-12 rounded-full",
    rectangular: "h-12 w-full rounded-md",
  };

  return (
    <div
      className={cn("animate-pulse bg-surface-hover", variantClasses[variant], className)}
      {...props}
    />
  );
}

export { Skeleton };
