# 3D Models Directory

This directory contains the 3D GLB models for the Nine Urns (Cửu Đỉnh).

## Models List

The following models should be placed in this directory:

1. `CAO-DINH-v1.glb` - Cao Đỉnh (The Urn of Height)
2. `NHAN-DINH-v1.glb` - Nhân Đỉnh (The Urn of Humanity)
3. `CHUONG-DINH-v1.glb` - Chương Đỉnh (The Urn of Chapters)
4. `ANH-DINH-v1.glb` - Anh Đỉnh (The Urn of Heroes)
5. `NGHI-DINH-v1.glb` - Nghị Đỉnh (The Urn of议)
6. `THUAN-DINH-v1.glb` - Thuần Đỉnh (The Urn of Purity)
7. `TUYEN-DINH-v1.glb` - Tuyên Đỉnh (The Urn of Proclamation)
8. `DU-DINH-v1.glb` - Dụ Đỉnh (The Urn of Education)
9. `HUYEN-DINH-v1.glb` - Huyền Đỉnh (The Urn of Mystery)

## Download Instructions

To download models from the production server:

```bash
cd mobile/assets/models

# Download CAO-DINH model (primary model)
curl -o CAO-DINH-v1.glb https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb

# Download other available models
curl -o CHUONG-DINH-v1.glb https://lms.histolab.icu/assets/models/CHUONG-DINH-v1.glb
curl -o NGHI-DINH-v1.glb https://lms.histolab.icu/assets/models/NGHI-DINH-v1.glb
curl -o THUAN-DINH-v1.glb https://lms.histolab.icu/assets/models/THUAN-DINH-v1.glb
curl -o TUYEN-DINH-v1.glb https://lms.histolab.icu/assets/models/TUYEN-DINH-v1.glb
curl -o HUYEN-DINH-v1.glb https://lms.histolab.icu/assets/models/HUYEN-DINH-v1.glb
```

## File Sizes

Each model is approximately 60-80MB in size. Total size for all models: ~600-700MB.

**Note:** Due to the large file sizes, models are NOT included in the repository. You must download them separately using the commands above or from the production server.

## Local Development

For local development, you only need to download the CAO-DINH model initially, as it's the demo urn with full coordinates data.

## Usage

**As of January 2026, models are now loaded directly from remote URLs for better compatibility with model_viewer_plus:**

```dart
// The app loads models from remote server:
'https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb'

// Local assets are no longer used due to path compatibility issues
// with the model_viewer_plus package.
```

**Note:** This directory is maintained for reference and potential future use, but the app currently loads all models from the remote server.

## Model Format

- **Format:** GLB (Binary glTF 2.0)
- **Texture:** Embedded in GLB file
- **Lighting:** PBR materials
- **Optimization:** Models are optimized for mobile viewing

## Model Compression

GLB models can be quite large (60-80MB each). To optimize for mobile performance and reduce bandwidth usage, we provide automated compression scripts using Draco compression.

### Why Compress?

- **Reduced Download Size:** 30-50% smaller files
- **Faster Loading:** Less data to transfer over network
- **Better Performance:** Reduced memory footprint on mobile devices
- **Cost Savings:** Lower bandwidth costs for users

### Compression Methods

#### Method 1: Automated Script (Recommended)

Use our compression utility that processes all models in batch:

```bash
cd mobile/scripts

# Make the script executable
chmod +x compress-models.sh

# Run compression (uses default paths)
./compress-models.sh

# Or specify custom input/output directories
./compress-models.sh /path/to/models /path/to/output
```

The script will:
- ✅ Automatically install required dependencies (gltf-pipeline, fs-extra)
- ✅ Process all GLB files in the directory
- ✅ Report before/after sizes and compression ratios
- ✅ Output compressed files with `.compressed.glb` suffix
- ✅ Provide detailed statistics and summary

#### Method 2: Direct Node.js Script

For more control, run the Node.js script directly:

```bash
cd mobile/scripts

# Install dependencies first
npm install

# Compress models from default directory
node compress-models.js

# Specify input directory
node compress-models.js ../assets/models

# Specify both input and output directories
node compress-models.js ../assets/models ./compressed-output
```

#### Method 3: Manual Compression

For single files or manual control:

```bash
# Install gltf-pipeline globally
npm install -g gltf-pipeline

# Compress a single model
gltf-pipeline -i CAO-DINH-v1.glb -o CAO-DINH-v1.compressed.glb -d

# With custom Draco compression level (0-10)
gltf-pipeline -i CAO-DINH-v1.glb -o CAO-DINH-v1.compressed.glb --draco.compressionLevel=7
```

### Compression Settings

Our scripts use optimized Draco compression settings:

```javascript
{
  compressionLevel: 7,          // Balance between size and quality (0-10)
  quantizePositionBits: 14,     // Vertex position precision
  quantizeNormalBits: 10,       // Normal vector precision
  quantizeTexcoordBits: 12,     // Texture coordinate precision
  quantizeColorBits: 8,         // Vertex color precision
  quantizeGenericBits: 12       // Generic attribute precision
}
```

### Expected Results

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| File Size | 60-80 MB | 30-50 MB | 30-50% |
| Quality | Original | Near-identical | Minimal loss |
| Load Time (4G) | 15-20s | 7-12s | ~50% faster |

### Quality Considerations

**Draco compression is lossy but optimized for 3D models:**

✅ **Preserves:**
- Overall model geometry
- Texture quality
- Material properties
- Visual appearance

⚠️ **Minor changes:**
- Slight vertex quantization (imperceptible at typical viewing distances)
- Minor precision reduction in normals (no visible artifacts)

**Recommended testing:**
1. Compress a single model first
2. View side-by-side with original in the app
3. Verify quality is acceptable
4. If satisfied, compress all models
5. Always keep backups of original files

### Compression Levels Guide

| Level | Compression | Quality | Use Case |
|-------|-------------|---------|----------|
| 0-3 | Low | Best | Archives, master copies |
| 4-7 | Medium | Excellent | **Production (recommended)** |
| 8-10 | High | Good | Extreme optimization |

**We use level 7** as it provides excellent compression while maintaining near-perfect visual quality.

### File Naming Convention

Compressed files are automatically named with a suffix:

- Original: `CAO-DINH-v1.glb`
- Compressed: `CAO-DINH-v1.compressed.glb`

This allows you to keep both versions for comparison.

### Server Deployment

To deploy compressed models to the server:

```bash
# 1. Compress all models
cd mobile/scripts
./compress-models.sh ../assets/models ./compressed-output

# 2. Test compressed models locally
# (Update app to use compressed files temporarily)

# 3. Upload to server (replace originals or use new names)
scp compressed-output/*.glb user@lms.histolab.icu:/path/to/assets/models/

# 4. Update model URLs in app if using different names
```

### Troubleshooting

**Issue: "gltf-pipeline not found"**
- Solution: Run `./compress-models.sh` which auto-installs dependencies

**Issue: "Out of memory" error**
- Solution: Process models one at a time
- Increase Node.js memory: `NODE_OPTIONS=--max-old-space-size=4096 node compress-models.js`

**Issue: Compressed model looks incorrect**
- Solution: Lower compression level to 5 or 6
- Check original model for errors
- Ensure textures are embedded in GLB

**Issue: File size didn't reduce much**
- Models may already be optimized
- Some models compress better than others
- Try higher compression level (8-9)

### Additional Resources

- [glTF Pipeline Documentation](https://github.com/CesiumGS/gltf-pipeline)
- [Draco Compression Guide](https://google.github.io/draco/)
- [glTF Specification](https://www.khronos.org/gltf/)

### Best Practices

1. **Always backup originals** before replacing with compressed versions
2. **Test thoroughly** on actual mobile devices, not just desktop
3. **Monitor metrics** - track actual load times and file sizes
4. **Iterate if needed** - adjust compression level based on results
5. **Document changes** - note which compression settings were used