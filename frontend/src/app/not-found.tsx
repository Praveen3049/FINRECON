"use client";

import React from "react";
import Link from "next/link";
import { FileQuestion, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4 font-mono">
      <div className="max-w-md w-full bg-[#0D0D0D] border border-white/10 rounded-2xl p-8 shadow-2xl text-center relative overflow-hidden">
        <div className="h-16 w-16 mx-auto rounded-2xl bg-black border border-[#FFD400]/40 flex items-center justify-center text-[#FFD400] mb-6">
          <FileQuestion className="h-8 w-8" />
        </div>

        <div className="space-y-2 mb-6">
          <Badge variant="neutral" size="sm">
            HTTP 404
          </Badge>
          <h1 className="text-2xl font-bold tracking-tight text-white uppercase font-mono">
            Page Not Found
          </h1>
          <p className="text-sm text-white/50 leading-relaxed font-sans">
            The financial reconciliation view or endpoint you requested does not exist or has been moved.
          </p>
        </div>

        <Link href="/">
          <Button variant="primary" className="w-full" iconLeft={<ArrowLeft className="h-4 w-4 text-black" />}>
            Return to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
}
