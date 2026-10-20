import { defineConfig } from "vitest/config";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Minimal Vitest config for the unit tests added in security-hardening task 16.3
// (route guard, exam-submit error surfacing, and the `.json` strip regex).
// Tests run in the Node environment because the units under test execute on the
// server/Edge runtime; browser-only globals are mocked per-test where needed.
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(path.dirname(fileURLToPath(import.meta.url)), "src"),
    },
  },
  test: {
    environment: "node",
    include: ["**/*.test.{js,ts,jsx,tsx}"],
    exclude: ["**/node_modules/**", "**/.next/**", "**/e2e/**"],
    globals: false,
  },
});
