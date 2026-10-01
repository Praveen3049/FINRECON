"use client";

import React from "react";
import { FolderOpen } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-dashed border-border/80 bg-card/40 my-3",
        className
      )}
    >
      <div className="h-12 w-12 rounded-xl bg-secondary/50 border border-border flex items-center justify-center text-muted-foreground mb-3.5 shadow-sm">
        {icon || <FolderOpen className="h-6 w-6 text-muted-foreground" />}
      </div>
      <h4 className="text-sm font-semibold text-white tracking-tight">{title}</h4>
      <p className="text-xs text-muted-foreground mt-1 max-w-sm leading-relaxed">
        {description}
      </p>
      {action && (
        <div className="mt-4">
          <Button
            size="sm"
            variant="secondary"
            onClick={action.onClick}
            iconLeft={action.icon}
          >
            {action.label}
          </Button>
        </div>
      )}
    </div>
  );
};
