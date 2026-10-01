"use client";

import React, { useEffect } from "react";
import { AlertOctagon, RotateCcw, Home } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global application execution error:", error);
  }, [error]);

  return (
    <html lang="en" className="dark h-full">
      <body className="h-full bg-black text-white flex items-center justify-center p-4 font-mono">
        <div className="max-w-md w-full bg-[#0D0D0D] border border-white/10 rounded-2xl p-8 shadow-2xl text-center">
          <div className="h-16 w-16 mx-auto rounded-2xl bg-black border border-[#FFD400]/40 flex items-center justify-center text-[#FFD400] mb-6">
            <AlertOctagon className="h-8 w-8" />
          </div>

          <div className="space-y-2 mb-6">
            <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-white/5 text-[#FFD400] border border-[#FFD400]/30">
              System Exception
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white uppercase font-mono">
              Application Error
            </h1>
            <p className="text-sm text-white/50 leading-relaxed font-sans">
              An unexpected critical error occurred. Please try reloading the console.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <button
              onClick={() => reset()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-black hover:bg-[#171717] text-white text-xs font-semibold border border-white/20 transition-colors font-mono"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Try Again</span>
            </button>
            <button
              onClick={() => (window.location.href = "/")}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[#FFD400] hover:bg-[#ffe14d] text-black text-xs font-bold transition-colors font-mono"
            >
              <Home className="h-4 w-4" />
              <span>Dashboard</span>
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
