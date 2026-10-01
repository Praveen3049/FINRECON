"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "success" | "destructive" | "outline" | "ghost" | "yellow";
  size?: "xs" | "sm" | "md" | "lg";
  isLoading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      children,
      iconLeft,
      iconRight,
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      primary:
        "bg-[#FFD400] hover:bg-[#E6BE00] text-black font-bold shadow-md shadow-[#FFD400]/15 border border-[#FFD400]",
      yellow:
        "bg-[#FFD400] hover:bg-[#E6BE00] text-black font-bold shadow-md shadow-[#FFD400]/15 border border-[#FFD400]",
      secondary:
        "bg-[#111111] hover:bg-[#1a1a1a] text-white border border-white/15",
      success:
        "bg-white hover:bg-neutral-200 text-black font-bold border border-white",
      destructive:
        "bg-[#0D0D0D] hover:bg-[#1a1a1a] text-[#FFD400] border border-[#FFD400]/40 font-semibold",
      outline:
        "bg-transparent hover:bg-white/5 text-white border border-white/20",
      ghost:
        "bg-transparent hover:bg-white/5 text-neutral-400 hover:text-white border-transparent",
    }[variant];

    const sizeStyles = {
      xs: "px-2 py-1 text-[11px] gap-1 rounded",
      sm: "px-2.5 py-1.5 text-xs gap-1.5 rounded-md",
      md: "px-3.5 py-2 text-xs font-semibold gap-2 rounded-lg",
      lg: "px-5 py-2.5 text-sm font-semibold gap-2.5 rounded-xl",
    }[size];

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-all duration-150 select-none active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100",
          variantStyles,
          sizeStyles,
          className
        )}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          iconLeft && <span className="shrink-0">{iconLeft}</span>
        )}
        <span>{children}</span>
        {!isLoading && iconRight && <span className="shrink-0">{iconRight}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";
