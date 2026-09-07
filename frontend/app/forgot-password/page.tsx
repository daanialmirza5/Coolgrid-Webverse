"use client";

import Link from "next/link";
import { useState } from "react";
import { Thermometer } from "lucide-react";
import { api, ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ message: string; demo_note?: string; reset_token?: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await api.auth.forgotPassword(email);
      setResult(resp);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
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
          <h1 className="text-xl font-bold">Reset your password</h1>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Forgot password</CardTitle>
            <CardDescription>We&apos;ll issue a reset token for your account.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && <Alert variant="destructive">{error}</Alert>}
            {result ? (
              <div className="space-y-3">
                <Alert variant="success">{result.message}</Alert>
                {result.demo_note && <Alert variant="warning">{result.demo_note}</Alert>}
                {result.reset_token && (
                  <div className="space-y-1.5">
                    <Label>Reset token (demo mode)</Label>
                    <Input readOnly value={result.reset_token} onFocus={(e) => e.target.select()} className="font-mono text-xs" />
                    <Link href={`/reset-password?token=${encodeURIComponent(result.reset_token)}`} className="text-sm font-medium text-sky-700 hover:underline dark:text-sky-400">
                      Continue to reset password →
                    </Link>
                  </div>
                )}
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
                </div>
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Sending..." : "Send reset link"}
                </Button>
              </form>
            )}
            <p className="text-center text-xs text-slate-500 dark:text-slate-400">
              <Link href="/login" className="font-medium text-sky-700 hover:underline dark:text-sky-400">
                ← Back to sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
