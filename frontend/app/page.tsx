import Link from "next/link";
import {
  ArrowRight,
  FlaskConical,
  Lightbulb,
  Search,
  Target,
  Thermometer,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const PIPELINE = [
  { icon: Search, label: "Detect", description: "XGBoost heat detection surfaces hotspots from urban & environmental features." },
  { icon: Lightbulb, label: "Explain", description: "SHAP attributes each hotspot to built-up density, vegetation, albedo & weather." },
  { icon: TrendingUp, label: "Predict", description: "Physics-informed 1/7/30-day LST forecasts with confidence ranges." },
  { icon: FlaskConical, label: "Simulate", description: "What-if intervention modeling: trees, cool/green roofs, blue infrastructure." },
  { icon: Target, label: "Optimize", description: "Constraint-aware search ranks interventions by cooling, cost & population benefit." },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-700 text-white">
            <Thermometer className="h-4 w-4" />
          </div>
          <span className="text-lg font-bold tracking-tight">CoolGrid</span>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/login">
            <Button variant="ghost">Sign in</Button>
          </Link>
          <Link href="/register">
            <Button>Get started</Button>
          </Link>
        </div>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-5xl px-6 py-20 text-center">
          <Badge variant="secondary" className="mb-4">
            Webverse 2026 · AI &amp; Physics-Informed Urban Heat Intelligence
          </Badge>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Turn urban heat into a <span className="text-sky-700 dark:text-sky-400">ranked, testable</span> city decision
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
            CoolGrid detects heat hotspots, explains their drivers, predicts future risk, simulates cooling
            interventions, and optimizes the plan — so planners can act with confidence, not guesswork.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link href="/register">
              <Button size="lg" className="gap-2">
                Explore the demo <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                Sign in
              </Button>
            </Link>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-20">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {PIPELINE.map((step) => (
              <Card key={step.label}>
                <CardHeader>
                  <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-400">
                    <step.icon className="h-4 w-4" />
                  </div>
                  <CardTitle>{step.label}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{step.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="border-t border-slate-200 bg-white py-16 dark:border-slate-800 dark:bg-slate-900">
          <div className="mx-auto max-w-4xl px-6 text-center">
            <h2 className="text-2xl font-bold">Built for city planners, ULBs & researchers</h2>
            <p className="mt-3 text-slate-600 dark:text-slate-400">
              CoolGrid runs on a fully interactive demo dataset for Pune, India — labeled DEMO DATA throughout —
              with a provider architecture ready to plug in real Landsat, Sentinel-2, ERA5, and census data.
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 px-6 py-6 text-center text-xs text-slate-400 dark:border-slate-800">
        CoolGrid — Webverse 2026 Hackathon
      </footer>
    </div>
  );
}
