#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://lms.histolab.icu}"
FIXTURE="${FIXTURE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/live-ai-prompt-regression.json}"
MIN_PASS_RATIO="${MIN_PASS_RATIO:-0.9}"

if [[ -z "${LIVE_SESSION_ID:-}" ]]; then
  echo "LIVE_SESSION_ID is required." >&2
  exit 2
fi

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "AUTH_TOKEN is required. Use a staff/teacher learner token that can access the live session." >&2
  exit 2
fi

node - "$BASE_URL" "$LIVE_SESSION_ID" "$AUTH_TOKEN" "$FIXTURE" "$MIN_PASS_RATIO" <<'NODE'
const fs = require("fs");

const [baseUrl, sessionId, token, fixturePath, minPassRatioRaw] = process.argv.slice(2);
const scenarios = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const minPassRatio = Number(minPassRatioRaw || 0.9);

function hasVietnameseDiacritic(text) {
  return /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(text);
}

function cleanText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

async function runScenario(scenario) {
  const response = await fetch(`${baseUrl.replace(/\/+$/, "")}/api/v1/live-sessions/${encodeURIComponent(sessionId)}/ai-teacher/reply`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: scenario.message,
      mode: scenario.mode || "hint-first",
      grade_level: scenario.grade_level || "middle_school",
      history: [],
    }),
  });

  const raw = await response.text();
  let payload = null;
  try {
    payload = JSON.parse(raw);
  } catch {
    payload = { raw };
  }

  const answer = cleanText(payload.answer || payload.message || payload.content || payload.raw);
  const required = Array.isArray(scenario.must_contain_any) ? scenario.must_contain_any : [];
  const containsRequired = required.length === 0 || required.some((item) =>
    answer.toLowerCase().includes(String(item).toLowerCase()),
  );
  const checks = [
    { name: "http_ok", ok: response.ok },
    { name: "non_empty", ok: answer.length >= 50 },
    { name: "vietnamese_diacritics", ok: hasVietnameseDiacritic(answer) },
    { name: "no_raw_markdown_bold", ok: !answer.includes("**") },
    { name: "contains_expected_concept", ok: containsRequired },
  ];

  return {
    id: scenario.id,
    ok: checks.every((check) => check.ok),
    status: response.status,
    failed: checks.filter((check) => !check.ok).map((check) => check.name),
    sample: answer.slice(0, 180),
  };
}

(async () => {
  const results = [];
  for (const scenario of scenarios) {
    const result = await runScenario(scenario);
    results.push(result);
    const label = result.ok ? "PASS" : "FAIL";
    console.log(`${label} ${result.id} status=${result.status}${result.failed.length ? ` failed=${result.failed.join(",")}` : ""}`);
    if (!result.ok) console.log(`  sample=${result.sample}`);
  }

  const passed = results.filter((item) => item.ok).length;
  const ratio = passed / Math.max(1, results.length);
  console.log(`\nsummary passed=${passed}/${results.length} ratio=${ratio.toFixed(3)} min=${minPassRatio}`);
  if (ratio < minPassRatio) process.exit(1);
})();
NODE
