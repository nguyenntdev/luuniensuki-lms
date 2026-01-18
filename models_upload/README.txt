Compressed GLB assets for upload to Cloudflare R2 (store.histolab.icu)

Upload files:
- CAO-DINH-v1-512.glb (ultra low / 512 textures + simplified mesh)
- CAO-DINH-v1-1k.glb  (medium quality / 1k textures)
- CAO-DINH-v1-2k.glb  (high quality / 2k textures)

Notes:
- Keep filenames exactly as above.
- The app selects based on device RAM (<=3GB uses -512, <=4GB uses -1k, >4GB uses -2k).
- The -512 file is simplified to ~78k vertices and ~5MB to avoid black screens on low-end GPUs.
- Original CAO-DINH-v1.glb should remain on the server for fallback.
