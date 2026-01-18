# App Icon and Splash Screen Configuration

## Current Status

### ✅ App Icon Configuration
- **Location**: `/android/app/src/main/res/mipmap-*/`
- **Status**: **Configured** 
- **Icon File**: `ic_launcher.png`
- **Densities**: All required densities are present:
  - mipmap-mdpi
  - mipmap-hdpi
  - mipmap-xhdpi
  - mipmap-xxhdpi
  - mipmap-xxxhdpi

The app icon is properly referenced in `AndroidManifest.xml`:
```xml
<application
    android:icon="@mipmap/ic_launcher"
    ...>
```

### ⚠️ Splash Screen Configuration
- **Location**: `/android/app/src/main/res/drawable/launch_background.xml`
- **Status**: **Basic Setup Only** (Default white screen)
- **Current Implementation**: Plain white background with no logo

#### Current `launch_background.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@android:color/white" />
    <!-- Image placeholder is commented out -->
</layer-list>
```

## Recommendations for Improvement

### 1. Custom Splash Screen with Brand Colors
Replace the white background with the app's brand colors from `app_colors.dart`:
- Background: Deep midnight blue (#0A0F1C)
- Accent: Imperial gold (#E8B44C)

### 2. Add App Logo to Splash Screen
Create a launch image and uncomment the logo section in `launch_background.xml`:
```xml
<item>
    <bitmap
        android:gravity="center"
        android:src="@mipmap/launch_image" />
</item>
```

### 3. Update Splash Screen for Modern Android
For Android 12+ support, consider using the new Splash Screen API:
- Create `res/values-v31/styles.xml` for Android 12+ styling
- Define windowSplashScreenBackground and windowSplashScreenAnimatedIcon

### 4. iOS Configuration
Current check was Android only. For complete configuration, also verify:
- **iOS App Icon**: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`
- **iOS Launch Screen**: `ios/Runner/Assets.xcassets/LaunchImage.imageset/`
- **iOS Info.plist**: Launch screen configuration

## Implementation Steps

### Step 1: Create Brand-Colored Splash Screen
1. Update `/android/app/src/main/res/drawable/launch_background.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- Background color matching app theme -->
    <item android:drawable="@color/splash_background" />
    
    <!-- Center logo -->
    <item>
        <bitmap
            android:gravity="center"
            android:src="@mipmap/launch_image" />
    </item>
</layer-list>
```

2. Create `/android/app/src/main/res/values/colors.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="splash_background">#0A0F1C</color>
</resources>
```

### Step 2: Design and Add Launch Image
1. Design a launch logo/icon (recommended size: 288x288 dp)
2. Export in multiple densities:
   - mdpi: 288×288 px
   - hdpi: 432×432 px
   - xhdpi: 576×576 px
   - xxhdpi: 864×864 px
   - xxxhdpi: 1152×1152 px
3. Place in respective mipmap folders as `launch_image.png`

### Step 3: Use flutter_native_splash Package (Optional)
For automated configuration across platforms:
```yaml
dev_dependencies:
  flutter_native_splash: ^2.3.0

flutter_native_splash:
  color: "#0A0F1C"
  image: assets/images/splash_logo.png
  android: true
  ios: true
```

Then run:
```bash
flutter pub run flutter_native_splash:create
```

## Current App Branding Colors
From `lib/core/theme/app_colors.dart`:
- **Primary Gold**: #E8B44C
- **Background**: #0A0F1C (Deep midnight blue)
- **Surface**: #0F1729 (Rich navy)

## Files Modified by This Task
- None yet (documentation only)

## Next Steps
1. Design splash screen logo matching the app's Vietnamese cultural heritage theme
2. Export logo in all required densities
3. Update `launch_background.xml` with brand colors
4. Test on different Android versions (especially Android 12+)
5. Verify iOS splash screen configuration

