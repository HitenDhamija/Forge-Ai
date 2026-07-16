import { Loader2 } from "lucide-react";

function LoadingScreen() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-bg">
      <div className="flex flex-col items-center space-y-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent">
          <span className="text-xl font-bold text-accent-text">F</span>
        </div>
        <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
        <p className="text-sm text-text-muted">Loading...</p>
      </div>
    </div>
  );
}

export { LoadingScreen };
