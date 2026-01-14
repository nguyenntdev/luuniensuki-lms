# 🧪 Testing & Verification Guide

This guide helps you test and verify the model compression solution.

## Pre-Testing Checklist

- [ ] Node.js v14+ installed (`node --version`)
- [ ] npm v6+ installed (`npm --version`)
- [ ] Scripts directory accessible (`cd mobile/scripts`)
- [ ] Execute permissions set (`chmod +x *.sh`)

## Test 1: Script Permissions ✓

```bash
cd mobile/scripts

# Check if scripts are executable
ls -l *.sh

# Should show: -rwxr-xr-x (executable)
# If not, run: chmod +x *.sh
```

**Expected**: Scripts have execute permissions

## Test 2: Dependency Installation ✓

```bash
# Test automatic installation
./compress-models.sh --help 2>/dev/null || echo "Will install deps"

# Or manually install
npm install
```

**Expected**: 
- gltf-pipeline installed
- fs-extra installed
- No errors

**Verify**:
```bash
npm list gltf-pipeline
npm list fs-extra
```

## Test 3: Test Compression (Sample Model) ✓

```bash
# Run test compression with sample model
npm test

# Or directly:
node test-compression.js
```

**Expected Output**:
```
🧪 Model Compression Test

📥 Downloading test model...
   URL: https://raw.githubusercontent.com/...
   ✅ Downloaded to: ...

🚀 Running compression test...

📦 Processing: test-model.glb
   Original size: X.XX MB
   Compressed size: X.XX MB
   Size reduction: X.XX MB (XX.XX%)
   ✅ Saved to: test-model.compressed.glb

✨ Test completed successfully!
```

## Test 4: Compression on Actual Model ✓

```bash
# Create test directory
mkdir -p test-models

# Copy one actual model (if available)
cp ../assets/models/CAO-DINH-v1.glb test-models/ 2>/dev/null || echo "No model found, skip"

# Run compression
./compress-models.sh test-models

# Check results
ls -lh test-models/
```

**Expected**:
- Original and compressed files both present
- Compressed file 30-50% smaller
- No errors in output

## Test 5: Batch Processing ✓

```bash
# If you have multiple models
./compress-models.sh ../assets/models ./test-output
```

**Expected**:
- All GLB files processed
- Statistics summary shown
- Compression ratios reported
- All files in output directory

## Test 6: npm Scripts ✓

```bash
# Test all npm scripts
npm run compress-models -- ../assets/models
npm run compress -- ../assets/models
npm run compress:default
```

**Expected**: Each command runs without errors

## Test 7: Configuration Changes ✓

Edit `compress-models.js`:

```javascript
// Change compression level
compressionLevel: 5  // Try different levels
```

Run compression and compare results:

```bash
node compress-models.js test-models
```

**Expected**: Different compression ratios with different levels

## Test 8: Error Handling ✓

Test error scenarios:

```bash
# Non-existent directory
./compress-models.sh /nonexistent/path
# Expected: Error message, graceful exit

# Empty directory
mkdir empty-dir
./compress-models.sh empty-dir
# Expected: "No GLB files found" message

# Permission denied
mkdir no-write
chmod 000 no-write
./compress-models.sh ../assets/models no-write
# Expected: Error message about permissions
chmod 755 no-write
```

## Test 9: Output Verification ✓

Verify compressed files are valid:

```bash
# Check file exists and is not empty
ls -lh test-models/*.compressed.glb

# Verify it's a valid GLB file (should start with "glTF")
xxd test-models/*.compressed.glb | head -n 1
# Should show: "glTF" in hex dump

# Check file size
du -h test-models/*.glb
```

**Expected**:
- Files exist and have content
- Valid GLB format
- Smaller than originals

## Test 10: Quality Verification (Manual)

If you have the app running:

1. Load original model in app
2. Load compressed model in app
3. Compare side-by-side
4. Check for visual differences
5. Measure load times

**Expected**:
- No visible quality loss
- Faster load time
- Smooth rendering

## Benchmark Tests

### Performance Benchmark

```bash
# Time the compression
time ./compress-models.sh test-models

# Expected: ~10-15 seconds per 70MB file
```

### Size Benchmark

```bash
# Compare sizes
echo "=== Size Comparison ==="
du -h test-models/*.glb | grep -v compressed
du -h test-models/*.compressed.glb
```

**Expected Results**:
| Original | Compressed | Reduction |
|----------|------------|-----------|
| 60-80 MB | 30-50 MB   | 30-50%    |

## Integration Tests

### Test with Different File Types

```bash
# Should only process .glb files
touch test-models/test.txt
touch test-models/test.obj
./compress-models.sh test-models

# Expected: Only .glb files processed, others ignored
```

### Test with Already Compressed Files

```bash
# Run compression twice
./compress-models.sh test-models
./compress-models.sh test-models

# Expected: .compressed.glb files not re-compressed
```

## Server Deployment Test (Optional)

```bash
# Dry run deployment
./deploy-compressed-models.sh

# Follow prompts (can cancel before actual upload)
```

**Expected**: Script runs, shows configuration, allows cancellation

## Cleanup After Testing

```bash
# Remove test files
rm -rf test-models
rm -rf test-output
rm -rf test-compression/test-output
rm -rf empty-dir
rm -rf no-write

# Keep node_modules for future use
# Or remove if not needed:
# rm -rf node_modules package-lock.json
```

## Troubleshooting Test Failures

### Test 1 Failed: Permissions
```bash
chmod +x compress-models.sh deploy-compressed-models.sh
```

### Test 2 Failed: Dependencies
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Test 3 Failed: Network
```bash
# Check internet connection
ping -c 1 google.com

# Try test again
npm test
```

### Test 4-5 Failed: No Models
```bash
# Download sample model
mkdir -p test-models
curl -o test-models/sample.glb https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Box/glTF-Binary/Box.glb

# Run compression
./compress-models.sh test-models
```

### Test 9 Failed: Invalid GLB
```bash
# Verify original model is valid
file test-models/*.glb
# Should show: "glTF binary"
```

## Success Criteria

All tests should:
- ✅ Complete without errors
- ✅ Produce valid output files
- ✅ Show expected compression ratios
- ✅ Handle errors gracefully
- ✅ Report accurate statistics

## Final Verification Checklist

Before using in production:

- [ ] All tests passed
- [ ] Compression ratio is 30-50%
- [ ] Compressed models load correctly
- [ ] No visual quality loss
- [ ] Error handling works
- [ ] Documentation is clear
- [ ] Scripts are executable
- [ ] Dependencies install correctly
- [ ] Backups created before deployment
- [ ] Tested on actual mobile device

## Performance Validation

Expected benchmarks:
- **Processing speed**: 10-15s per 70MB file
- **Compression ratio**: 30-50% reduction
- **Quality**: 99%+ visual similarity
- **Memory usage**: <500MB during compression
- **CPU usage**: Moderate during compression

## Reporting Issues

If tests fail, collect:
1. Error messages
2. Node.js version (`node --version`)
3. npm version (`npm --version`)
4. Operating system
5. File sizes involved
6. Steps to reproduce

## Next Steps After Testing

1. **If all tests pass**:
   - Use on production models
   - Deploy to server
   - Monitor in production

2. **If tests fail**:
   - Check troubleshooting section
   - Review error messages
   - Verify prerequisites
   - Report issues

3. **For production deployment**:
   - Test with one model first
   - Verify in app
   - Deploy all models
   - Monitor performance

---

**Testing Complete?** → See `QUICKSTART.md` for production usage!

