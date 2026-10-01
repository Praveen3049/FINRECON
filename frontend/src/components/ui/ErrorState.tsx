"use client";

import React, { useState } from "react";
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

export interface ErrorStateProps {
  title?: string;
  message?: string;
  technicalDetails?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Unable to load data",
  message = "A network or service issue prevented retrieving the requested financial records. Please verify the backend connection and try again.",
  technicalDetails,
  onRetry,
  className,
}) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center rounded-xl border border-[#FFD400]/30 bg-[#0D0D0D] my-4 shadow-sm",
        className
      )}
      role="alert"
    >
      <div className="h-11 w-11 rounded-xl bg-[#FFD400]/15 border border-[#FFD400]/30 flex items-center justify-center text-[#FFD400] mb-3 shadow-sm">
        <AlertTriangle className="h-5 w-5" />
      </div>

      <h4 className="text-sm font-semibold text-white tracking-tight">{title}</h4>
      <p className="text-xs text-muted-foreground mt-1 max-w-md leading-relaxed">{message}</p>

      {onRetry && (
        <div className="mt-4">
          <Button
            size="sm"
            variant="secondary"
            onClick={onRetry}
            iconLeft={<RefreshCw className="h-3.5 w-3.5 text-[#FFD400]" />}
          >
            Retry Request
          </Button>
        </div>
      )}

      {technicalDetails && (
        <div className="mt-3 text-left w-full max-w-md">
          <button
            type="button"
            onClick={() => setShowDetails((p) => !p)}
            className="text-[11px] text-muted-foreground hover:text-white flex items-center gap-1 mx-auto"
          >
            <span>{showDetails ? "Hide technical diagnostic" : "Show technical diagnostic"}</span>
            {showDetails ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
          {showDetails && (
            <pre className="mt-2 p-2.5 rounded-lg bg-black/60 border border-border/80 text-[10px] font-mono text-[#FFD400] overflow-x-auto whitespace-pre-wrap">
              {technicalDetails}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};
