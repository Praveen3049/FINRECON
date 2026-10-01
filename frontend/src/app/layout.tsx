import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "FinRecon — Multi-Source Financial Reconciliation Platform",
  description:
    "Enterprise-grade intelligent reconciliation engine across Banks, Payment Gateways, ERP/Accounting, Invoices, and Blockchain ledgers. Reconcile every financial record. Investigate every exception.",
  keywords: "financial reconciliation, transaction matching, exception investigation, crypto reconciliation, audit trail, fintech",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full">
      <body className="h-full bg-background antialiased font-sans">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
