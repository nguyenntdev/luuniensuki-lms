# Panoramas (360° equirectangular images)

Drop equirectangular `.jpg` panoramas here. They are served at `/panoramas/<file>`.

Scenes wired in the self-hosted viewer (`SelfHostedTour.jsx`):

| File | Scene |
|------|-------|
| `kinh-thanh.jpg` | Kinh thành Huế |
| `ngo-mon.jpg` | Ngọ Môn |
| `the-mieu.jpg` | Thế Miếu |
| `cuu-dinh.jpg` | Sân Cửu Đỉnh |

Requirements:
- Equirectangular projection, 2:1 aspect ratio (e.g. 4096×2048 or 8192×4096).
- **Only use images the project has the rights to use.** Do not rehost third-party
  copyrighted panoramas without permission.

To add a new scene: place `<slug>.jpg` here and add an entry to the `SCENES`
array in `frontend/src/components/vr360/SelfHostedTour.jsx`.
