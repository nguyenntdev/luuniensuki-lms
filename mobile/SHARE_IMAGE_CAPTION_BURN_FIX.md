# Share Image Caption Burn Implementation

## Overview
Successfully implemented caption overlay functionality for the motif share feature. The caption is now "burned" (permanently drawn) onto the image before sharing, instead of being sent as separate text.

## Changes Made

### File Modified
- **`/mobile/lib/features/lesson/presentation/screens/motif_detail_screen.dart`**

### Key Changes

#### 1. Added `dart:ui` Import
```dart
import 'dart:ui' as ui;
```
This provides access to low-level canvas drawing APIs for image manipulation.

#### 2. Replaced `_shareMotif` Method
The new implementation:
1. **Downloads the original image** from the server
2. **Creates a canvas** with the original image
3. **Draws a semi-transparent overlay bar** at the bottom (120px height, black with 87% opacity)
4. **Renders caption text** in two lines:
   - Line 1: `🏛️ {motif.name}` (bold, white, 42px)
   - Line 2: `📍 {urn.name} • Lưu Niên Sử Kí` (regular, 80% white, 32px)
5. **Converts the canvas to PNG** image
6. **Shares the final image** (without separate text caption)

### Technical Implementation Details

#### Image Processing Flow
```
Download Image → Decode to ui.Image → Draw on Canvas → Add Overlay Bar → 
Draw Text → Convert to PNG → Save to Temp → Share
```

#### Canvas Drawing
- Uses `ui.PictureRecorder` and `Canvas` for drawing
- Original image dimensions are preserved
- Overlay bar: 120px height, positioned at bottom
- Text rendering uses `ui.ParagraphBuilder` for proper layout

#### Text Styling
```dart
// Caption line 1 (motif name)
fontSize: 42
fontWeight: bold
color: #FFFFFF (100% white)

// Caption line 2 (location)
fontSize: 32
fontWeight: normal
color: #CCFFFFFF (80% white)
```

#### Layout Parameters
- Bar height: 120px
- Text padding: 20px from sides
- Line 1 offset: 15px from top of bar
- Line 2 offset: 65px from top of bar
- Text alignment: center

## User Experience Improvements

### Before
- Image shared with separate text caption below
- Different apps displayed caption differently
- Caption could be lost or ignored
- Less visual appeal

### After
- Caption permanently embedded in image
- Consistent appearance across all platforms
- Professional watermark-style branding
- More shareable and recognizable

## Loading Indicator
Updated the loading message to better reflect the process:
- **Before**: "Đang chuẩn bị ảnh..." (Preparing image...)
- **After**: "Đang tạo ảnh chia sẻ..." (Creating share image...)
- Duration extended to 15 seconds (from 10) to account for image processing

## Error Handling
- Graceful fallback to text-only share if no image URL available
- Error messages displayed in Vietnamese
- Loading indicator properly hidden on success or failure
- Debug logging for troubleshooting

## File Format
- **Output format**: PNG (preserves transparency and quality)
- **MIME type**: `image/png`
- **Temp file naming**: `share_{motif_id}.png`

## Testing Recommendations

1. **Test with different image sizes**
   - Small images (< 500px)
   - Medium images (500-1500px)
   - Large images (> 1500px)

2. **Test with different motif names**
   - Short names (< 10 characters)
   - Long names (> 30 characters)
   - Names with special characters/emojis

3. **Test with different URN names**
   - Various lengths
   - Different Vietnamese diacritics

4. **Share to different platforms**
   - Facebook
   - Instagram
   - WhatsApp
   - Zalo
   - File manager

5. **Network conditions**
   - Fast connection
   - Slow connection
   - Network interruption during download

## Performance Considerations
- Image download may take time on slow connections
- Canvas rendering is relatively fast (<1 second for typical images)
- PNG encoding may increase file size compared to original
- Temp files are automatically cleaned up by system

## What's Next?

You could consider:

1. **Make caption customizable**
   - Allow users to add personal message
   - Choose caption position (top/bottom)
   - Toggle caption on/off

2. **Add more visual elements**
   - App logo/watermark
   - QR code to app download
   - Decorative borders or frames

3. **Optimize performance**
   - Cache processed images
   - Use JPEG for smaller file sizes
   - Progressive loading indicator

4. **Analytics tracking**
   - Track share success rate
   - Monitor popular share platforms
   - Track which motifs are shared most

## Related Files
- `lib/core/utils/url_utils.dart` - Image URL utilities
- `lib/features/urn_viewer/data/models/urn_dtos.dart` - Data models

