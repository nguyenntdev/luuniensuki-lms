# Quick Reference Guide - Model Compression

## 🚀 Quick Start (3 Steps)

```bash
# 1. Go to scripts directory
cd mobile/scripts

# 2. Make executable (first time only)
chmod +x compress-models.sh

# 3. Run compression
./compress-models.sh
```

## 📋 Common Commands

### Compress with Defaults
```bash
./compress-models.sh
```

### Compress from Specific Directory
```bash
./compress-models.sh /path/to/models
```

### Compress with Separate Output
```bash
./compress-models.sh /path/to/input /path/to/output
```

### Use npm Scripts
```bash
npm install
npm run compress          # Default directory
npm run compress:default  # ../assets/models
npm test                  # Run test compression
```

## ⚙️ Configuration Quick Reference

Edit `compress-models.js` line ~15:

```javascript
const CONFIG = {
  dracoOptions: {
    compressionLevel: 7,      // 0-10 (default: 7)
  },
  outputSuffix: '.compressed', // Output filename suffix
  skipExisting: false          // Skip if output exists
};
```

## 📊 Compression Levels

| Level | Size Reduction | Quality | Speed |
|-------|----------------|---------|-------|
| 5     | ~40%          | Excellent | Fast |
| 7     | ~50%          | Very Good | Medium ⭐ Recommended |
| 9     | ~55%          | Good    | Slow |

## 🔧 Troubleshooting

### Script won't run
```bash
chmod +x compress-models.sh
```

### Out of memory
```bash
NODE_OPTIONS=--max-old-space-size=4096 node compress-models.js
```

### Dependencies not found
```bash
npm install
```

## 📁 File Locations

- **Script**: `mobile/scripts/compress-models.sh`
- **Node script**: `mobile/scripts/compress-models.js`
- **Input (default)**: `mobile/assets/models/`
- **Output**: Same as input (with `.compressed.glb` suffix)

## 📖 Expected Results

- **Original size**: 60-80 MB per file
- **Compressed size**: 30-50 MB per file
- **Reduction**: 30-50%
- **Quality**: 99%+ visual similarity
- **Processing time**: ~10-15s per file

## 🎯 Production Workflow

```bash
# 1. Test on one model
mkdir test
cp ../assets/models/CAO-DINH-v1.glb test/
./compress-models.sh test

# 2. Compare quality (load both in app)

# 3. If satisfied, compress all
./compress-models.sh ../assets/models ./compressed

# 4. Deploy to server
scp compressed/*.glb user@server:/srv/assets/models/
```

## 📞 Need Help?

- Full documentation: `README.md`
- Usage examples: `EXAMPLES.md`
- Model info: `../assets/models/README.md`

## ✅ Checklist Before Production

- [ ] Tested compression on one model
- [ ] Verified visual quality in app
- [ ] Backed up original files
- [ ] Tested on actual mobile device
- [ ] Measured actual load time improvement
- [ ] Updated server with compressed files

