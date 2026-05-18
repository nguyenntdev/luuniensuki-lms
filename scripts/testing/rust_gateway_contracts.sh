#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://lms.histolab.icu}"
BASE_URL="${BASE_URL%/}"
CURL_INSECURE="${CURL_INSECURE:-1}"

curl_args=(-sS)
if [[ "$CURL_INSECURE" == "1" ]]; then
  curl_args+=(-k)
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

request() {
  local path="$1"
  local out="$2"
  curl "${curl_args[@]}" -o "$out" -w "%{http_code}" "$BASE_URL$path"
}

assert_status() {
  local path="$1"
  local expected="$2"
  local out="$tmp_dir/$(echo "$path" | tr '/?' '__').json"
  local status
  status="$(request "$path" "$out")"
  [[ "$status" == "$expected" ]] || fail "$path expected $expected got $status body=$(cat "$out")"
  echo "OK $path $status"
}

assert_body_contains() {
  local file="$1"
  local needle="$2"
  grep -Fq "$needle" "$file" || fail "$file missing $needle"
}

health_body="$tmp_dir/health.json"
status="$(request "/health" "$health_body")"
[[ "$status" == "200" ]] || fail "/health expected 200 got $status"
assert_body_contains "$health_body" '"status":"ok"'
assert_body_contains "$health_body" '"mode":"gateway"'
echo "OK /health 200"

ratings_body="$tmp_dir/content-ratings.json"
status="$(request "/api/v1/content/ratings" "$ratings_body")"
[[ "$status" == "200" ]] || fail "/api/v1/content/ratings expected 200 got $status"
assert_body_contains "$ratings_body" '"ratings":['
assert_body_contains "$ratings_body" '"rating":"everyone"'
assert_body_contains "$ratings_body" '"rating":"teen"'
assert_body_contains "$ratings_body" '"rating":"mature"'
echo "OK /api/v1/content/ratings 200"

db_health_body="$tmp_dir/db-health.json"
status="$(request "/api/v1/internal/db-health" "$db_health_body")"
[[ "$status" == "200" ]] || fail "/api/v1/internal/db-health expected 200 got $status"
assert_body_contains "$db_health_body" '"database":"ok"'
echo "OK /api/v1/internal/db-health 200"

tags_body="$tmp_dir/tags.json"
status="$(request "/api/v1/tags" "$tags_body")"
[[ "$status" == "200" ]] || fail "/api/v1/tags expected 200 got $status"
grep -Eq '^\[.*\]$' "$tags_body" || fail "/api/v1/tags response is not JSON array body=$(cat "$tags_body")"
echo "OK /api/v1/tags 200"

ranks_unauth_body="$tmp_dir/ranks-unauth.json"
status="$(request "/api/v1/ranks" "$ranks_unauth_body")"
[[ "$status" == "401" ]] || fail "/api/v1/ranks unauth expected 401 got $status"
assert_body_contains "$ranks_unauth_body" '"HTTP_ERROR"'
echo "OK /api/v1/ranks unauth 401"

badges_unauth_body="$tmp_dir/badges-unauth.json"
status="$(request "/api/v1/badges" "$badges_unauth_body")"
[[ "$status" == "401" ]] || fail "/api/v1/badges unauth expected 401 got $status"
assert_body_contains "$badges_unauth_body" '"HTTP_ERROR"'
echo "OK /api/v1/badges unauth 401"

streak_unauth_body="$tmp_dir/streak-unauth.json"
status="$(request "/api/v1/users/me/streak" "$streak_unauth_body")"
[[ "$status" == "401" ]] || fail "/api/v1/users/me/streak unauth expected 401 got $status"
assert_body_contains "$streak_unauth_body" '"HTTP_ERROR"'
echo "OK /api/v1/users/me/streak unauth 401"

if [[ -n "${AUTH_EMAIL:-}" && -n "${AUTH_PASSWORD:-}" ]]; then
  cookie_jar="$tmp_dir/cookies.txt"
  login_body="$tmp_dir/login.json"
  status="$(
    curl "${curl_args[@]}" \
      -c "$cookie_jar" \
      -H "content-type: application/json" \
      -d "{\"email\":\"$AUTH_EMAIL\",\"password\":\"$AUTH_PASSWORD\"}" \
      -o "$login_body" \
      -w "%{http_code}" \
      "$BASE_URL/api/v1/auth/login"
  )"
  [[ "$status" == "200" ]] || fail "/api/v1/auth/login expected 200 got $status body=$(cat "$login_body")"
  echo "OK /api/v1/auth/login 200"

  ranks_auth_body="$tmp_dir/ranks-auth.json"
  status="$(
    curl "${curl_args[@]}" \
      -b "$cookie_jar" \
      -o "$ranks_auth_body" \
      -w "%{http_code}" \
      "$BASE_URL/api/v1/ranks"
  )"
  [[ "$status" == "200" ]] || fail "/api/v1/ranks auth expected 200 got $status body=$(cat "$ranks_auth_body")"
  assert_body_contains "$ranks_auth_body" '"level":1'
  assert_body_contains "$ranks_auth_body" '"xp":80000'
  echo "OK /api/v1/ranks auth 200"

  badges_auth_body="$tmp_dir/badges-auth.json"
  status="$(
    curl "${curl_args[@]}" \
      -b "$cookie_jar" \
      -o "$badges_auth_body" \
      -w "%{http_code}" \
      "$BASE_URL/api/v1/badges"
  )"
  [[ "$status" == "200" ]] || fail "/api/v1/badges auth expected 200 got $status body=$(cat "$badges_auth_body")"
  grep -Eq '^\[.*\]$' "$badges_auth_body" || fail "/api/v1/badges response is not JSON array body=$(cat "$badges_auth_body")"
  echo "OK /api/v1/badges auth 200"

  streak_auth_body="$tmp_dir/streak-auth.json"
  status="$(
    curl "${curl_args[@]}" \
      -b "$cookie_jar" \
      -o "$streak_auth_body" \
      -w "%{http_code}" \
      "$BASE_URL/api/v1/users/me/streak"
  )"
  [[ "$status" == "200" ]] || fail "/api/v1/users/me/streak auth expected 200 got $status body=$(cat "$streak_auth_body")"
  assert_body_contains "$streak_auth_body" '"current_streak":'
  assert_body_contains "$streak_auth_body" '"longest_streak":'
  assert_body_contains "$streak_auth_body" '"streak_freezes":'
  assert_body_contains "$streak_auth_body" '"days_since_last_active":'
  echo "OK /api/v1/users/me/streak auth 200"
else
  echo "SKIP auth contract: set AUTH_EMAIL and AUTH_PASSWORD"
fi

echo "PASS rust gateway contracts"
