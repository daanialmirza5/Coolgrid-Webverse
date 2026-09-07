"use client";

import { AuthGuard } from "@/components/layout/auth-guard";
import { AppShell } from "@/components/layout/app-shell";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
