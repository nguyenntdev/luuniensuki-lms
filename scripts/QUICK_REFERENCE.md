# Quick Reference: Script Locations

## 🚀 Common Tasks

### Deploy to Production
```bash
./scripts/deployment/deploy-to-server.sh
```

### Safe Production Deploy
```bash
./scripts/deployment/deploy-safe.sh --password='your-ssh-password'
```

### Update Running Server
```bash
./scripts/deployment/update-server.sh
```

### Install Mobile App for Testing
```bash
./scripts/testing/install-apk.sh
```

### Generate Flutter Code
```bash
./scripts/build/generate_hearts_code.sh
```

### Test RAG API
```bash
export ADMIN_TOKEN="your_jwt_token"
./scripts/testing/P0-RAG-02_API_TESTING.sh
```

---

## 📂 All Scripts by Category

### Deployment (scripts/deployment/)
| Script | Purpose |
|--------|---------|
| `deploy-to-server.sh` | Full deployment from local to production |
| `deploy-safe.sh` | Safer deploy with preflight checks + migration + health check |
| `update-server.sh` | Quick update without rebuild |
| `deploy-lms.sh` | LMS deployment (run on server) |
| `deploy-cors.sh` | Deploy CORS configuration |
| `deploy-cors-auto.sh` | Deploy CORS with sshpass |
| `get-ssl.sh` | Setup SSL certificates |

### Server Management (scripts/server/)
| Script | Purpose |
|--------|---------|
| `remote-setup.sh` | Initial server setup |
| `server-hardening.sh` | Security hardening |
| `resource-monitor.sh` | Resource + service monitoring checks |
| `install-resource-monitor.sh` | Install monitor systemd timer |
| `security-ioc-audit.sh` | IOC/persistence scan and neutralization |
| `install-security-audit-timer.sh` | Install daily security-audit timer |

### Build & Code Generation (scripts/build/)
| Script | Purpose |
|--------|---------|
| `generate_hearts_code.sh` | Flutter code generation |
| `run_collection_fix.sh` | Regenerate collection DTOs |

### Testing (scripts/testing/)
| Script | Purpose |
|--------|---------|
| `install-apk.sh` | Install app via ADB |
| `adb_automated_test.sh` | Automated mobile testing |
| `P0-RAG-02_API_TESTING.sh` | Test RAG API |
| `verify_migration.sh` | Verify database migrations |

---

## 🔄 Migration Guide

If you have bookmarks or aliases to old script locations, update them:

```bash
# OLD LOCATIONS → NEW LOCATIONS

./deploy-to-server.sh     → ./scripts/deployment/deploy-to-server.sh
./update-server.sh        → ./scripts/deployment/update-server.sh
./install-apk.sh          → ./scripts/testing/install-apk.sh
./generate_hearts_code.sh → ./scripts/build/generate_hearts_code.sh
```

### Creating Aliases (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias lms-deploy='./scripts/deployment/deploy-to-server.sh'
alias lms-update='./scripts/deployment/update-server.sh'
alias lms-install='./scripts/testing/install-apk.sh'
alias lms-gen='./scripts/build/generate_hearts_code.sh'
```
