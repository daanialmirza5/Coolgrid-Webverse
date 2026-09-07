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

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [organization, setOrganization] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await register(email, password, fullName, organization || undefined);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 dark:bg-slate-950">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-700 text-white">
            <Thermometer className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-bold">Create your account</h1>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Register</CardTitle>
            <CardDescription>New accounts start with viewer access.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <Alert variant="destructive">{error}</Alert>}
              <div className="space-y-1.5">
                <Label htmlFor="fullName">Full name</Label>
                <Input id="fullName" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="organization">Organization (optional)</Label>
                <Input id="organization" value={organization} onChange={(e) => setOrganization(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
                <p className="text-xs text-slate-400">At least 8 characters.</p>
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Creating account..." : "Create account"}
              </Button>
            </form>
            <p className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
              Already have an account?{" "}
              <Link href="/login" className="font-medium text-sky-700 hover:underline dark:text-sky-400">
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
