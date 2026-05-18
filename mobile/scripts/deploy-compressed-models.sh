#!/bin/bash

###############################################################################
# Server Deployment Script for Model Compression
#
# This script guides you through deploying compressed models to the
# production server. It includes safety checks and backup procedures.
#
# Usage:
#   ./deploy-compressed-models.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVER_USER="your-username"
SERVER_HOST="lms.histolab.icu"
SERVER_MODELS_PATH="/srv/assets/models"
LOCAL_COMPRESSED_DIR="./compressed-output"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Model Compression - Server Deployment Guide           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Pre-flight checks
###############################################################################
echo -e "${YELLOW}📋 Pre-flight Checklist${NC}"
echo "────────────────────────────────────────────────────────────"

# Check if compressed files exist
if [ ! -d "$LOCAL_COMPRESSED_DIR" ] || [ -z "$(ls -A $LOCAL_COMPRESSED_DIR/*.glb 2>/dev/null)" ]; then
    echo -e "${RED}❌ No compressed files found in $LOCAL_COMPRESSED_DIR${NC}"
    echo ""
    echo "Please run compression first:"
    echo "  ./compress-models.sh ../assets/models $LOCAL_COMPRESSED_DIR"
    exit 1
fi

echo -e "${GREEN}✓${NC} Compressed files found"

# Count compressed files
COMPRESSED_COUNT=$(ls -1 $LOCAL_COMPRESSED_DIR/*.compressed.glb 2>/dev/null | wc -l | tr -d ' ')
echo -e "${GREEN}✓${NC} Found $COMPRESSED_COUNT compressed model(s)"

###############################################################################
# Interactive configuration
###############################################################################
echo ""
echo -e "${YELLOW}⚙️  Configuration${NC}"
echo "────────────────────────────────────────────────────────────"

read -p "Server username [$SERVER_USER]: " input_user
SERVER_USER=${input_user:-$SERVER_USER}

read -p "Server hostname [$SERVER_HOST]: " input_host
SERVER_HOST=${input_host:-$SERVER_HOST}

read -p "Server models path [$SERVER_MODELS_PATH]: " input_path
SERVER_MODELS_PATH=${input_path:-$SERVER_MODELS_PATH}

echo ""
echo -e "${CYAN}Configuration:${NC}"
echo "  • User:    $SERVER_USER"
echo "  • Host:    $SERVER_HOST"
echo "  • Path:    $SERVER_MODELS_PATH"
echo "  • Files:   $COMPRESSED_COUNT model(s)"

###############################################################################
# Confirm deployment
###############################################################################
echo ""
echo -e "${YELLOW}⚠️  Warning${NC}"
echo "────────────────────────────────────────────────────────────"
echo "This will:"
echo "  1. Create backup of existing models on server"
echo "  2. Upload compressed models to server"
echo "  3. Optionally replace original files"
echo ""

read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

###############################################################################
# Deployment steps
###############################################################################
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Starting Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Test SSH connection
echo -e "${YELLOW}Step 1/5: Testing SSH connection...${NC}"
if ssh -q "$SERVER_USER@$SERVER_HOST" exit; then
    echo -e "${GREEN}✓${NC} SSH connection successful"
else
    echo -e "${RED}❌ Cannot connect to server${NC}"
    echo "Please check your SSH configuration and try again."
    exit 1
fi

# Step 2: Create backup on server
echo ""
echo -e "${YELLOW}Step 2/5: Creating backup on server...${NC}"
BACKUP_DIR="$SERVER_MODELS_PATH.backup.$(date +%Y%m%d_%H%M%S)"
ssh "$SERVER_USER@$SERVER_HOST" "mkdir -p $BACKUP_DIR && cp -r $SERVER_MODELS_PATH/*.glb $BACKUP_DIR/ 2>/dev/null || true"
echo -e "${GREEN}✓${NC} Backup created at: $BACKUP_DIR"

# Step 3: Create temporary directory on server
echo ""
echo -e "${YELLOW}Step 3/5: Creating temporary directory...${NC}"
TEMP_DIR="$SERVER_MODELS_PATH.temp.$(date +%s)"
ssh "$SERVER_USER@$SERVER_HOST" "mkdir -p $TEMP_DIR"
echo -e "${GREEN}✓${NC} Created: $TEMP_DIR"

# Step 4: Upload compressed files
echo ""
echo -e "${YELLOW}Step 4/5: Uploading compressed models...${NC}"
scp $LOCAL_COMPRESSED_DIR/*.compressed.glb "$SERVER_USER@$SERVER_HOST:$TEMP_DIR/"
echo -e "${GREEN}✓${NC} Upload complete"

# Step 5: Ask about file replacement
echo ""
echo -e "${YELLOW}Step 5/5: File placement${NC}"
echo "────────────────────────────────────────────────────────────"
echo "How would you like to deploy the compressed models?"
echo ""
echo "1) Keep .compressed.glb suffix (safe - allows A/B testing)"
echo "2) Replace original files (remove .compressed suffix)"
echo "3) Cancel and clean up"
echo ""
read -p "Choose option (1/2/3): " deploy_option

case $deploy_option in
    1)
        # Copy with .compressed suffix
        echo ""
        echo -e "${CYAN}Copying files with .compressed suffix...${NC}"
        ssh "$SERVER_USER@$SERVER_HOST" "cp $TEMP_DIR/*.compressed.glb $SERVER_MODELS_PATH/"
        echo -e "${GREEN}✓${NC} Files deployed with .compressed.glb suffix"
        ;;
    2)
        # Replace originals (remove .compressed suffix)
        echo ""
        echo -e "${CYAN}Replacing original files...${NC}"
        ssh "$SERVER_USER@$SERVER_HOST" "
            cd $TEMP_DIR
            for f in *.compressed.glb; do
                new_name=\${f%.compressed.glb}.glb
                cp \"\$f\" $SERVER_MODELS_PATH/\"\$new_name\"
            done
        "
        echo -e "${GREEN}✓${NC} Original files replaced with compressed versions"
        ;;
    3)
        echo ""
        echo -e "${YELLOW}Cleaning up...${NC}"
        ssh "$SERVER_USER@$SERVER_HOST" "rm -rf $TEMP_DIR"
        echo "Deployment cancelled. Backup remains at: $BACKUP_DIR"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

# Cleanup temp directory
ssh "$SERVER_USER@$SERVER_HOST" "rm -rf $TEMP_DIR"

###############################################################################
# Summary
###############################################################################
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Summary:${NC}"
echo "  • Compressed models deployed to server"
echo "  • Backup created at: $BACKUP_DIR"
echo "  • Files deployed: $COMPRESSED_COUNT model(s)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Test the compressed models in your app"
echo "  2. Monitor performance and load times"
echo "  3. If satisfied, you can remove the backup"
echo "  4. If issues occur, restore from backup:"
echo "     ssh $SERVER_USER@$SERVER_HOST 'cp $BACKUP_DIR/*.glb $SERVER_MODELS_PATH/'"
echo ""
echo -e "${CYAN}Backup cleanup (after testing):${NC}"
echo "  ssh $SERVER_USER@$SERVER_HOST 'rm -rf $BACKUP_DIR'"
echo ""

