#!/bin/bash

###############################################################################
# Example Usage Scenarios for Model Compression
# 
# This file shows various ways to use the compression scripts
###############################################################################

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Model Compression - Usage Examples                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Example 1: Basic compression with defaults
echo "Example 1: Basic Compression (Default Settings)"
echo "────────────────────────────────────────────────────────────"
echo "$ ./compress-models.sh"
echo ""
echo "This will:"
echo "  • Use default input directory: ../assets/models"
echo "  • Output to same directory with .compressed.glb suffix"
echo "  • Use compression level 7 (recommended)"
echo ""

# Example 2: Custom input directory
echo "Example 2: Compress Models from Custom Directory"
echo "────────────────────────────────────────────────────────────"
echo "$ ./compress-models.sh /path/to/downloaded/models"
echo ""
echo "This will:"
echo "  • Read GLB files from /path/to/downloaded/models"
echo "  • Output compressed files to the same directory"
echo ""

# Example 3: Custom input and output directories
echo "Example 3: Separate Input and Output Directories"
echo "────────────────────────────────────────────────────────────"
echo "$ ./compress-models.sh /srv/original-models /srv/compressed-models"
echo ""
echo "This will:"
echo "  • Read from /srv/original-models"
echo "  • Write to /srv/compressed-models"
echo "  • Keep original files untouched"
echo ""

# Example 4: Using Node.js directly for more control
echo "Example 4: Direct Node.js Execution with Custom Settings"
echo "────────────────────────────────────────────────────────────"
echo "$ node compress-models.js ../assets/models ./output"
echo ""
echo "This will:"
echo "  • Run the Node.js script directly"
echo "  • Skip dependency auto-installation"
echo "  • Faster if dependencies already installed"
echo ""

# Example 5: Production server workflow
echo "Example 5: Production Server Compression Workflow"
echo "────────────────────────────────────────────────────────────"
echo "# Step 1: SSH to server"
echo "$ ssh user@lms.histolab.icu"
echo ""
echo "# Step 2: Navigate to project"
echo "$ cd /path/to/luuniensuki-lms/mobile/scripts"
echo ""
echo "# Step 3: Run compression"
echo "$ ./compress-models.sh /srv/assets/models /srv/assets/models-compressed"
echo ""
echo "# Step 4: Backup originals"
echo "$ mv /srv/assets/models /srv/assets/models-original"
echo ""
echo "# Step 5: Replace with compressed"
echo "$ mv /srv/assets/models-compressed /srv/assets/models"
echo ""
echo "# Step 6: Rename compressed files to remove suffix"
echo "$ cd /srv/assets/models"
echo "$ for f in *.compressed.glb; do mv \"\$f\" \"\${f%.compressed.glb}.glb\"; done"
echo ""

# Example 6: Test with a single model first
echo "Example 6: Test Compression on Single Model"
echo "────────────────────────────────────────────────────────────"
echo "$ mkdir test-compress"
echo "$ cp ../assets/models/CAO-DINH-v1.glb test-compress/"
echo "$ ./compress-models.sh test-compress"
echo "$ # Compare the results before processing all models"
echo ""

# Example 7: Compare compression levels
echo "Example 7: Testing Different Compression Levels"
echo "────────────────────────────────────────────────────────────"
echo "Edit compress-models.js and change compressionLevel:"
echo ""
echo "  Level 5: const CONFIG = { dracoOptions: { compressionLevel: 5 }}"
echo "  Level 7: const CONFIG = { dracoOptions: { compressionLevel: 7 }}"
echo "  Level 9: const CONFIG = { dracoOptions: { compressionLevel: 9 }}"
echo ""
echo "Then run and compare results"
echo ""

# Example 8: Batch processing workflow
echo "Example 8: Complete Batch Processing Workflow"
echo "────────────────────────────────────────────────────────────"
echo "#!/bin/bash"
echo ""
echo "# Download all models"
echo "cd mobile/assets/models"
echo "curl -o CAO-DINH-v1.glb https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb"
echo "curl -o CHUONG-DINH-v1.glb https://lms.histolab.icu/assets/models/CHUONG-DINH-v1.glb"
echo "# ... download other models ..."
echo ""
echo "# Compress all models"
echo "cd ../../scripts"
echo "./compress-models.sh ../assets/models ./compressed-output"
echo ""
echo "# Test in app with compressed models"
echo "# If satisfied, deploy to server"
echo "scp compressed-output/*.glb user@lms.histolab.icu:/srv/assets/models/"
echo ""

# Example 9: CI/CD Integration
echo "Example 9: Automated Compression in CI/CD"
echo "────────────────────────────────────────────────────────────"
echo "Add to your deployment script:"
echo ""
echo "  deploy:"
echo "    script:"
echo "      - cd mobile/scripts"
echo "      - npm install"
echo "      - node compress-models.js /models /compressed"
echo "      - rsync -av /compressed/ user@server:/srv/models/"
echo ""

# Example 10: Quick test
echo "Example 10: Quick Test Run"
echo "────────────────────────────────────────────────────────────"
echo "$ npm run compress-models"
echo ""
echo "Uses npm script defined in package.json"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo "💡 Tips:"
echo "  • Always keep backups of original models"
echo "  • Test compressed models in the app before deployment"
echo "  • Start with compression level 7 (best balance)"
echo "  • Process one model first to verify quality"
echo "  • Monitor actual load times on real devices"
echo ""
echo "📖 For more information, see README.md"
echo ""

