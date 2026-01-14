#!/bin/bash

###############################################################################
# Model Compression Shell Script
# 
# This script automates the compression of GLB model files using gltf-pipeline
# with Draco compression for optimal mobile performance.
#
# Usage:
#   ./compress-models.sh [input_dir] [output_dir]
#
# Examples:
#   ./compress-models.sh                              # Uses default paths
#   ./compress-models.sh ./models                     # Custom input directory
#   ./compress-models.sh ./models ./compressed        # Custom input and output
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default paths
DEFAULT_INPUT_DIR="$PROJECT_ROOT/assets/models"
INPUT_DIR="${1:-$DEFAULT_INPUT_DIR}"
OUTPUT_DIR="${2:-}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          GLB Model Compression Utility                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Check Node.js installation
###############################################################################
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed.${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v)
echo -e "${GREEN}✓${NC} Node.js ${NODE_VERSION} is installed"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed.${NC}"
    exit 1
fi

NPM_VERSION=$(npm -v)
echo -e "${GREEN}✓${NC} npm ${NPM_VERSION} is installed"

###############################################################################
# Check and install dependencies
###############################################################################
echo ""
echo -e "${YELLOW}📦 Checking dependencies...${NC}"

# Navigate to script directory for package management
cd "$SCRIPT_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${YELLOW}⚠️  Creating package.json...${NC}"
    npm init -y > /dev/null 2>&1
fi

# Function to check if package is installed
check_package() {
    npm list "$1" > /dev/null 2>&1
}

# Install gltf-pipeline if not present
if ! check_package "gltf-pipeline"; then
    echo -e "${YELLOW}📥 Installing gltf-pipeline...${NC}"
    npm install gltf-pipeline --save
else
    echo -e "${GREEN}✓${NC} gltf-pipeline is already installed"
fi

# Install fs-extra if not present
if ! check_package "fs-extra"; then
    echo -e "${YELLOW}📥 Installing fs-extra...${NC}"
    npm install fs-extra --save
else
    echo -e "${GREEN}✓${NC} fs-extra is already installed"
fi

###############################################################################
# Verify input directory
###############################################################################
echo ""
echo -e "${YELLOW}📁 Verifying directories...${NC}"

if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}❌ Input directory does not exist: $INPUT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Input directory: $INPUT_DIR"

# Count GLB files
GLB_COUNT=$(find "$INPUT_DIR" -maxdepth 1 -iname "*.glb" ! -name "*compressed*" | wc -l | tr -d ' ')

if [ "$GLB_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No GLB files found in $INPUT_DIR${NC}"
    echo "Nothing to compress."
    exit 0
fi

echo -e "${GREEN}✓${NC} Found $GLB_COUNT GLB file(s) to compress"

if [ -n "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
    echo -e "${GREEN}✓${NC} Output directory: $OUTPUT_DIR"
fi

###############################################################################
# Run compression
###############################################################################
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Starting compression...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Run the Node.js compression script
if [ -n "$OUTPUT_DIR" ]; then
    node "$SCRIPT_DIR/compress-models.js" "$INPUT_DIR" "$OUTPUT_DIR"
else
    node "$SCRIPT_DIR/compress-models.js" "$INPUT_DIR"
fi

COMPRESS_EXIT_CODE=$?

###############################################################################
# Final summary
###############################################################################
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $COMPRESS_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Compression completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Test the compressed models in your application"
    echo "  2. Verify visual quality is acceptable"
    echo "  3. Replace original models with compressed versions if satisfied"
    echo "  4. Keep backups of original files"
else
    echo -e "${RED}❌ Compression failed with errors.${NC}"
    echo "Please check the error messages above."
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

exit $COMPRESS_EXIT_CODE

