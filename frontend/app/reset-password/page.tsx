"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Thermometer } from "lucide-react";
import { api, ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FullPageSpinner } from "@/components/ui/spinner";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [token, setToken] = useState(searchParams.get("token") ?? "");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.auth.resetPassword(token, newPassword);
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reset password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Set a new password</CardTitle>
        <CardDescription>Paste the reset token from the previous step.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <Alert variant="destructive">{error}</Alert>}
        {done ? (
          <>
            <Alert variant="success">Password updated. You can sign in now.</Alert>
            <Button className="w-full" onClick={() => router.push("/login")}>
              Go to sign in
            </Button>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="token">Reset token</Label>
              <Input id="token" required value={token} onChange={(e) => setToken(e.target.value)} className="font-mono text-xs" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="newPassword">New password</Label>
              <Input id="newPassword" type="password" required minLength={8} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Updating..." : "Update password"}
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
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-700 text-white">
            <Thermometer className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-bold">Reset password</h1>
        </div>
        <Suspense fallback={<FullPageSpinner />}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
