import { defineConfig } from "vitest/config";

// Minimal Vitest config for the unit tests added in security-hardening task 16.3
// (route guard, exam-submit error surfacing, and the `.json` strip regex).
// Tests run in the Node environment because the units under test execute on the
// server/Edge runtime; browser-only globals are mocked per-test where needed.
export default defineConfig({
  test: {
    environment: "node",
    include: ["**/*.test.{js,ts}"],
    exclude: ["**/node_modules/**", "**/.next/**", "**/e2e/**"],
    globals: false,
  },
});
