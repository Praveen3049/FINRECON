"use client";

import React, { useEffect } from "react";
import { AlertOctagon, RotateCcw, Home } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application execution error:", error);
  }, [error]);

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4 font-mono">
      <div className="max-w-md w-full bg-[#0D0D0D] border border-white/10 rounded-2xl p-8 shadow-2xl text-center relative overflow-hidden">
        <div className="h-16 w-16 mx-auto rounded-2xl bg-black border border-[#FFD400]/40 flex items-center justify-center text-[#FFD400] mb-6">
          <AlertOctagon className="h-8 w-8" />
        </div>

        <div className="space-y-2 mb-6">
          <Badge variant="critical" size="sm">
            HTTP 500 • Exception
          </Badge>
          <h1 className="text-2xl font-bold tracking-tight text-white uppercase font-mono">
            Application Error
          </h1>
          <p className="text-sm text-white/50 leading-relaxed font-sans">
            An unexpected error occurred while processing this reconciliation module.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <Button
            variant="outline"
            className="w-full"
            iconLeft={<RotateCcw className="h-4 w-4" />}
            onClick={() => reset()}
          >
            Try Again
          </Button>
          <Button
            variant="primary"
            className="w-full"
            iconLeft={<Home className="h-4 w-4 text-black" />}
            onClick={() => (window.location.href = "/")}
          >
            Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
