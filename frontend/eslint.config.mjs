import path from "node:path";
import { fileURLToPath } from "node:url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

export default [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "out/**",
      "build/**",
      "coverage/**",
      "next-env.d.ts",
      "eslint.config.mjs",
      "playwright-report/**",
      "test-results/**",
    ],
  },
  ...compat.config({
    extends: ["next/core-web-vitals"],
    rules: {
      "@next/next/no-img-element": "off",
    },
  }),
];
