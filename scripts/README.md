# Scripts Directory

This directory contains all shell scripts for the Luuniensuki LMS project, organized by purpose.

## Directory Structure

### 📦 `deployment/`
Scripts for deploying the application to production servers.

- **`deploy-cors-auto.sh`** - Deploy CORS configuration using sshpass
- **`deploy-cors.sh`** - Deploy CORS configuration (manual SSH)
- **`deploy-lms.sh`** - Full LMS deployment to production
- **`deploy-to-server.sh`** - Deploy from local machine to server
- **`update-server.sh`** - Quick update without full rebuild
- **`get-ssl.sh`** - Setup Let's Encrypt SSL certificates

**Usage Example:**
```bash
# Deploy to production
./scripts/deployment/deploy-to-server.sh

# Update running server
./scripts/deployment/update-server.sh
```

### 🖥️ `server/`
Scripts for server setup and maintenance.

- **`remote-setup.sh`** - Initial server setup (run on server)
- **`server-hardening.sh`** - Security hardening (run on server)

**Usage Example:**
```bash
# On the server after initial setup
./scripts/server/remote-setup.sh
./scripts/server/server-hardening.sh
```

### 🔨 `build/`
Scripts for building and code generation.

- **`generate_hearts_code.sh`** - Generate Flutter freezed/riverpod code
- **`run_collection_fix.sh`** - Regenerate collection screen DTOs
- **`build_v1.5.0.sh.obsolete`** - Archived version-specific build script

**Usage Example:**
```bash
# Regenerate Flutter code
./scripts/build/generate_hearts_code.sh
```

### 🧪 `testing/`
Scripts for testing and verification.

- **`P0-RAG-02_API_TESTING.sh`** - Test RAG document management API
- **`adb_automated_test.sh`** - Automated mobile app testing
- **`install-apk.sh`** - Install mobile app via ADB
- **`verify_migration.sh`** - Verify database migrations

**Usage Example:**
```bash
# Test RAG API
export ADMIN_TOKEN="your_jwt_token"
./scripts/testing/P0-RAG-02_API_TESTING.sh

# Install mobile app
./scripts/testing/install-apk.sh
```

## Root Level Scripts

The following scripts remain at the project root for convenience:

- **`setup.sh`** - Primary setup script (entry point for new installations)

## Notes

- All scripts use `set -e` for fail-fast behavior
- Deployment scripts target server: `36.50.26.18` (lms.histolab.icu)
- Mobile scripts require Flutter and ADB to be installed
- Backend scripts may require Docker or local Python environment

## Migration Notes

This organization was created to clean up the root directory and provide better structure for script management. Version-specific scripts (e.g., `commit_v1.4.0.sh`, `commit_v1.5.0.sh`) have been removed as they are no longer needed.

