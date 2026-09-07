"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Database,
  FileText,
  FlaskConical,
  LayoutDashboard,
  Lightbulb,
  ListChecks,
  LogOut,
  Map as MapIcon,
  Menu,
  Settings as SettingsIcon,
  ShieldCheck,
  Target,
  Thermometer,
  TrendingUp,
  X,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { CityProvider, useCity } from "@/lib/city-context";
import { Badge } from "@/components/ui/badge";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/map", label: "Heat Map", icon: MapIcon },
  { href: "/hotspots", label: "Hotspots", icon: Thermometer },
  { href: "/drivers", label: "Driver Analysis", icon: Lightbulb },
  { href: "/predictions", label: "Predictions", icon: TrendingUp },
  { href: "/simulation", label: "Simulation", icon: FlaskConical },
  { href: "/optimization", label: "Optimization", icon: Target },
  { href: "/recommendations", label: "Recommendations", icon: ListChecks },
  { href: "/comparison", label: "Ward Comparison", icon: BarChart3 },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/datasources", label: "Data Sources", icon: Database },
  { href: "/settings", label: "Settings", icon: SettingsIcon },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = user?.role === "admin" ? [...NAV_ITEMS, { href: "/admin", label: "Admin", icon: ShieldCheck }] : NAV_ITEMS;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-5 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-700 text-white">
          <Thermometer className="h-4 w-4" />
        </div>
        <span className="text-base font-bold tracking-tight">CoolGrid</span>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-sky-50 text-sky-800 dark:bg-sky-950 dark:text-sky-300"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { user, logout } = useAuth();
  const { city } = useCity();
  const router = useRouter();

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} aria-label="Open menu" className="rounded-md p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden">
          <Menu className="h-5 w-5" />
        </button>
        {city && (
          <div className="hidden items-center gap-2 sm:flex">
            <span className="text-sm font-medium">{city.name}</span>
            {city.is_demo && <Badge variant="secondary">DEMO DATA</Badge>}
          </div>
        )}
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium leading-none">{user?.full_name}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{user?.role}</p>
        </div>
        <button
          onClick={async () => {
            await logout();
            router.push("/login");
          }}
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          title="Log out"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Log out</span>
        </button>
      </div>
    </header>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <CityProvider>
      <div className="flex h-screen overflow-hidden">
        <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 lg:block">
          <SidebarContent />
        </aside>

        {mobileOpen && (
          <div className="fixed inset-0 z-40 lg:hidden" data-testid="mobile-sidebar">
            <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
            <div className="absolute left-0 top-0 h-full w-64 bg-white shadow-xl dark:bg-slate-900">
              <div className="flex justify-end p-2">
                <button onClick={() => setMobileOpen(false)} aria-label="Close menu" className="rounded-md p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <SidebarContent onNavigate={() => setMobileOpen(false)} />
            </div>
          </div>
        )}

        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar onMenuClick={() => setMobileOpen(true)} />
          <main className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-50 p-4 dark:bg-slate-950 sm:p-6">{children}</main>
        </div>
      </div>
    </CityProvider>
  );
}
