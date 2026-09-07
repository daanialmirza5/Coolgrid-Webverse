# End-to-End Tests

The actual Playwright E2E suite lives in `frontend/e2e/` (Playwright convention colocates tests with the app they drive; `frontend/playwright.config.ts` configures it). It covers:

- `auth.spec.ts` — landing page, register, login, wrong password, protected-route redirect, logout, forgot/reset password.
- `navigation.spec.ts` — every sidebar page loads without console/page errors; admin nav item hidden for non-admins.
- `map.spec.ts` — heat map renders ward polygons, all 5 layer toggles work, ward click selection; a dark-mode regression test asserting the legend stacks above the map canvas.
- `simulation.spec.ts` — ward picker, running a simulation, validation error on all-zero coverage.
- `optimization.spec.ts` — running the optimizer, ranked strategies, infeasible-budget empty state.
- `responsive.spec.ts` — no horizontal overflow at mobile/tablet viewports on 6 key pages; mobile hamburger drawer opens/closes.
- `full-journey.spec.ts` — the complete required flow: **LOGIN → DASHBOARD → SELECT AREA → HOTSPOT → DRIVER ANALYSIS → PREDICTION → SIMULATION → OPTIMIZATION → REPORT → LOGOUT**, asserting zero console/page errors across the whole run.

## Running

Requires the backend + PostgreSQL already running with demo data seeded (see the root [README.md](../../README.md#local-installation)), **and** a Next.js dev server running:

```powershell
# terminal 1
cd frontend
pnpm dev
# note which port it prints ("Local: http://localhost:XXXX" -- it falls
# back from 3000 if that port is already in use on your machine)

# terminal 2, once it says "Ready"
cd frontend
pnpm test:e2e
# if it picked a port other than 3000:
#   $env:PLAYWRIGHT_BASE_URL = "http://localhost:XXXX"; pnpm test:e2e
```

Playwright deliberately does not manage the dev server's lifecycle itself here: Next.js 16 refuses to start a second dev server in the same project directory at all while one is already running, which made Playwright's built-in `webServer` option unreliable in practice — starting it yourself and pointing Playwright at it via `baseURL`/`PLAYWRIGHT_BASE_URL` is the pattern that's actually been verified working.
