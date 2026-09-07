"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { FullPageSpinner } from "@/components/ui/spinner";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) return <FullPageSpinner label="Loading CoolGrid..." />;
  if (!user) return <FullPageSpinner label="Redirecting to login..." />;

  return <>{children}</>;
}

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  if (loading || !user) return <FullPageSpinner />;
  if (user.role !== "admin") return <FullPageSpinner label="Redirecting..." />;

  return <>{children}</>;
}
