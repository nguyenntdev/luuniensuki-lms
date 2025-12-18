# 🔧 AUGMENT TASKS - DevOps & Testing

## 📋 Assigned Tasks

### Phase 4: Testing

| # | Task | Priority |
|---|------|----------|
| 4.7 | Frontend E2E test setup (Playwright) | HIGH |
| 4.8 | Critical user flows E2E tests | HIGH |

### Phase 5: DevOps

| # | Task | Priority |
|---|------|----------|
| 5.2 | GitHub Actions CI pipeline | HIGH |
| 5.3 | Docker build optimization | MEDIUM |
| 5.4 | Production deployment checklist | MEDIUM |
| 3.8 | Optimize GLB files (Draco) | LOW |

---

## 📝 TASK DETAILS

### 4.7 Frontend E2E test setup

**Setup Playwright:**
```bash
cd frontend
npm init playwright@latest
```

**Config:** `frontend/playwright.config.ts`
```typescript
export default defineConfig({
  testDir: './e2e',
  baseURL: 'http://localhost:3000',
  use: {
    trace: 'on-first-retry',
  },
});
```

---

### 4.8 Critical user flows E2E tests

**Create:** `frontend/e2e/` folder

**Test scenarios:**
1. `auth.spec.ts` - Register, Login, Logout
2. `explore.spec.ts` - View urns, Open 3D viewer
3. `quiz.spec.ts` - Start quiz, Answer questions, See results
4. `collection.spec.ts` - View collection, Filter motifs

---

### 5.2 GitHub Actions CI pipeline

**Create:** `.github/workflows/ci.yml`

**Jobs:**
1. **Backend:**
   - Lint (ruff/flake8)
   - Type check (mypy)
   - Run pytest
   
2. **Frontend:**
   - Lint (eslint)
   - Build (next build)
   - E2E tests (playwright)

**Trigger:** Push/PR to main

---

### 5.3 Docker build optimization

**Improvements:**
1. Multi-stage builds (already have)
2. Layer caching optimization
3. Use .dockerignore effectively
4. Reduce image size

**Check current sizes:**
```bash
docker images | grep luuniensuki
```

---

### 5.4 Production deployment checklist

**Create:** `docs/PRODUCTION_CHECKLIST.md`

**Contents:**
- [ ] Environment variables documented
- [ ] Secrets management (DB password, JWT secret)
- [ ] SSL certificate auto-renewal
- [ ] Backup strategy
- [ ] Monitoring/alerts setup
- [ ] Log rotation

---

### 3.8 Optimize GLB files (Draco compression)

**Tool:** gltf-pipeline or gltf-transform

```bash
npm install -g gltf-pipeline
gltf-pipeline -i input.glb -o output.glb -d
```

**Target:** Reduce GLB sizes by 50-70%

---

## 🔧 EXISTING CODE REFERENCES

**Docker files:**
- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`

**Test files:**
- `tests/backend/` - pytest tests
- `tests/backend/conftest.py` - fixtures

---

## ✅ ACCEPTANCE CRITERIA

- [x] Playwright setup working
- [x] E2E tests for critical flows
- [x] CI pipeline runs on PR
- [x] Docker images optimized
- [x] Production checklist documented
- [ ] GLB files compressed (optional)

---

## 🚀 RUN COMMANDS

```bash
# Run E2E tests
cd frontend && npx playwright test

# Run CI locally
act -j test  # requires 'act' tool

# Check docker image sizes
docker images --format "table {{.Repository}}\t{{.Size}}"
```

