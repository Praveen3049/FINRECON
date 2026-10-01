"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, Coins } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "success"
    | "warning"
    | "critical"
    | "info"
    | "crypto"
    | "neutral"
    | "matched"
    | "exception"
    | "yellow";
  size?: "xs" | "sm" | "md";
  showIcon?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "neutral",
  size = "sm",
  showIcon = true,
  children,
  ...props
}) => {
  const variantConfig = {
    yellow: {
      style: "bg-[#FFD400]/15 text-[#FFD400] border-[#FFD400]/30 font-semibold",
      icon: CheckCircle2,
    },
    success: {
      style: "bg-white/10 text-white border-white/20 font-medium",
      icon: CheckCircle2,
    },
    matched: {
      style: "bg-[#FFD400]/15 text-[#FFD400] border-[#FFD400]/35 font-semibold",
      icon: CheckCircle2,
    },
    warning: {
      style: "bg-[#FFD400]/10 text-[#FFD400] border-[#FFD400]/30",
      icon: AlertTriangle,
    },
    exception: {
      style: "bg-[#FFD400]/15 text-[#FFD400] border-[#FFD400]/40 font-semibold",
      icon: AlertTriangle,
    },
    critical: {
      style: "bg-[#FFD400] text-black border-[#FFD400] font-bold",
      icon: AlertCircle,
    },
    info: {
      style: "bg-white/5 text-white/90 border-white/15",
      icon: Info,
    },
    crypto: {
      style: "bg-[#FFD400]/10 text-white border-[#FFD400]/25",
      icon: Coins,
    },
    neutral: {
      style: "bg-[#111111] text-white/80 border-white/10",
      icon: null,
    },
  }[variant];

  const sizeStyle = {
    xs: "text-[10px] px-1.5 py-0.2 gap-1 rounded",
    sm: "text-[11px] px-2 py-0.5 gap-1.5 rounded-md",
    md: "text-xs px-2.5 py-1 gap-1.5 rounded-lg",
  }[size];

  const IconComp = variantConfig.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center font-mono font-medium border shrink-0 transition-colors select-none",
        variantConfig.style,
        sizeStyle,
        className
      )}
      {...props}
    >
      {showIcon && IconComp && <IconComp className="h-3 w-3 shrink-0" />}
      <span>{children}</span>
    </span>
  );
};
