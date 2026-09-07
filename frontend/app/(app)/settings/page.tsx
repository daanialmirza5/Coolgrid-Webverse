"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [organization, setOrganization] = useState(user?.organization ?? "");
  const [profileMsg, setProfileMsg] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [savingPassword, setSavingPassword] = useState(false);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setProfileMsg(null);
    setProfileError(null);
    setSavingProfile(true);
    try {
      await api.users.updateProfile({ full_name: fullName, organization });
      await refreshUser();
      setProfileMsg("Profile updated.");
    } catch (err) {
      setProfileError(err instanceof ApiError ? err.message : "Could not update profile");
    } finally {
      setSavingProfile(false);
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setPasswordMsg(null);
    setPasswordError(null);
    setSavingPassword(true);
    try {
      await api.users.changePassword(currentPassword, newPassword);
      setPasswordMsg("Password changed.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setPasswordError(err instanceof ApiError ? err.message : "Could not change password");
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <div className="max-w-xl space-y-4">
      <h1 className="text-xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>
            {user?.email} · <Badge variant="secondary">{user?.role}</Badge>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={saveProfile} className="space-y-3">
            {profileMsg && <Alert variant="success">{profileMsg}</Alert>}
            {profileError && <Alert variant="destructive">{profileError}</Alert>}
            <div className="space-y-1.5">
              <Label htmlFor="fullName">Full name</Label>
              <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="organization">Organization</Label>
              <Input id="organization" value={organization} onChange={(e) => setOrganization(e.target.value)} />
            </div>
            <Button type="submit" disabled={savingProfile}>
              {savingProfile ? "Saving..." : "Save profile"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={changePassword} className="space-y-3">
            {passwordMsg && <Alert variant="success">{passwordMsg}</Alert>}
            {passwordError && <Alert variant="destructive">{passwordError}</Alert>}
            <div className="space-y-1.5">
              <Label htmlFor="currentPassword">Current password</Label>
              <Input id="currentPassword" type="password" required value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="newPassword">New password</Label>
              <Input id="newPassword" type="password" required minLength={8} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </div>
            <Button type="submit" disabled={savingPassword}>
              {savingPassword ? "Updating..." : "Change password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
