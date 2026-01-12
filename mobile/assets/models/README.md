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

## Compression (Optional)

If file sizes are too large, you can compress the models using:

```bash
# Using gltf-pipeline
npm install -g gltf-pipeline
gltf-pipeline -i CAO-DINH-v1.glb -o CAO-DINH-v1-compressed.glb -d
```

This can reduce file size by 30-50% with minimal quality loss.