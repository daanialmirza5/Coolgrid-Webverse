"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Thermometer } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("demo@coolgrid.app");
  const [password, setPassword] = useState("CoolGrid#Demo2026");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-700 text-white">
            <Thermometer className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-bold">CoolGrid</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Urban Heat Intelligence Platform</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sign in</CardTitle>
            <CardDescription>Use the demo credentials below, or your own account.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <Alert variant="destructive">{error}</Alert>}
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Link href="/forgot-password" className="text-xs text-sky-700 hover:underline dark:text-sky-400">
                    Forgot password?
                  </Link>
                </div>
                <Input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Signing in..." : "Sign in"}
              </Button>
            </form>
            <p className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
              Demo credentials pre-filled. Don&apos;t have an account?{" "}
              <Link href="/register" className="font-medium text-sky-700 hover:underline dark:text-sky-400">
                Register
              </Link>
            </p>
          </CardContent>
        </Card>
        <p className="mt-6 text-center text-xs text-slate-400">
          <Link href="/" className="hover:underline">
            ← Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
