import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Vendored/static assets (maplibre-gl's own worker bundle, copied
    // verbatim by scripts/copy-maplibre-worker.js) -- not our source.
    "public/**",
    // Playwright output, not source.
    "test-results/**",
    "playwright-report/**",
    // Plain Node/CommonJS setup scripts run standalone via `node`, not
    // part of the Next.js app bundle -- they intentionally use require().
    "scripts/**",
  ]),
]);

export default eslintConfig;
