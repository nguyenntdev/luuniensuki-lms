# Personal Info Settings Screen

## Overview
A beautiful glass morphism-styled screen for users to view and edit their personal information, featuring smooth animations and an intuitive user interface.

## File Location
`mobile/lib/features/profile/presentation/screens/personal_info_screen.dart`

## Features

### 1. **Avatar Management**
- Displays user avatar with a beautiful glass circle design
- Shows first letter of display name if no avatar is set
- Camera icon button for changing avatar (placeholder - ready for future implementation)
- Gradient border with golden glow effect

### 2. **Display Name Field**
- Glass container with editable text field
- Real-time validation (cannot be empty)
- Helper text indicating it's publicly visible
- Icon indicator for better UX

### 3. **Username Field**
- Optional username for profile sharing
- Glass container styling
- Helper text explaining its purpose
- Icon indicator (@) for username context

### 4. **Email Field (Read-only)**
- Displays user email in a dimmed glass container
- Lock icon indicating it cannot be changed
- Reduced opacity to show it's read-only

### 5. **Profile Visibility Toggle**
- Beautiful animated switch to toggle public/private profile
- Dynamic icon (🌐 public / 🔒 private)
- Info box with context-sensitive message
- Glowing effect when enabled

### 6. **Save Button**
- Primary glass button with gradient
- Only enabled when changes are detected
- Loading state with spinner
- Success/error notifications with snackbars

## UI Components Used

### Glass Components
- `AnimatedGradientBackground` - Animated gradient backdrop
- `GlassContainer` - Semi-transparent containers for sections
- `GlassTextField` - Beautiful input fields with glass effect
- `GlassButton` - Gradient button for saving changes

### Theme
- Uses `AppColors` for consistent color scheme
- Uses `AppSpacing` for consistent padding/margins
- Vietnamese imperial gold accent color
- Dark navy background with glass morphism

## Navigation

### From Profile Screen
```dart
// In profile_screen.dart, line 877-883
Navigator.of(context).push(
  MaterialPageRoute(
    builder: (context) => const PersonalInfoScreen(),
  ),
);
```

### Back Navigation
- Back button in the app bar (top-left)
- Standard iOS/Material back gesture support

## State Management

### Provider Integration
- Uses `authNotifierProvider` to read current user
- Calls `updateProfile()` method to save changes
- Automatically updates UI when save is successful

### Local State
- `_isLoading` - Tracks save operation
- `_hasChanges` - Detects when fields are modified
- `_isProfilePublic` - Tracks visibility toggle
- Text controllers for name and username fields

## Animations

### Entry Animations
- **Fade In**: Content fades in smoothly (600ms)
- **Slide Up**: Content slides up from below (Cubic ease-out curve)
- Staggered timing for elegant appearance

### Interactive Animations
- Switch glow effect when profile is public
- Button opacity changes based on `_hasChanges`
- Smooth state transitions

## Validation

### Display Name
- Required field - cannot be empty
- Shows error snackbar if submitted empty

### Username
- Optional field
- Only sent to API if changed and not empty

### Profile Visibility
- Boolean toggle - no validation needed

## API Integration

### Update Profile Method
```dart
final success = await authNotifier.updateProfile(
  displayName: displayName != user.displayName ? displayName : null,
  username: username.isNotEmpty && username != user.username ? username : null,
  isProfilePublic: _isProfilePublic != user.isProfilePublic ? _isProfilePublic : null,
);
```

Only sends changed fields to the API for efficiency.

## Future Enhancements

### Avatar Upload (TODO)
Currently shows placeholder message. To implement:
1. Add image picker dependency
2. Implement file upload to backend
3. Update avatar URL in user profile
4. Show upload progress

### Additional Fields
Could add in the future:
- Bio/description
- Social media links
- Preferred language
- Timezone

## Code Structure

### Main Sections
1. **State & Controllers** (lines 23-31)
2. **Lifecycle Methods** (lines 33-95)
3. **Build Method** (lines 97-213)
4. **Avatar Section** (lines 215-292)
5. **Form Fields** (lines 294-469)
6. **Visibility Toggle** (lines 471-574)
7. **Save Button** (lines 576-638)

### Key Methods
- `_onFieldChanged()` - Detects changes for save button
- `_saveChanges()` - Validates and saves to API
- `_showSuccessSnackbar()` - Shows success message
- `_showErrorSnackbar()` - Shows error message

## Design Philosophy

### Glass Morphism
- Semi-transparent containers with blur
- Light borders for depth
- Subtle shadows for elevation
- Gradient accents for visual interest

### Vietnamese Cultural Theme
- Imperial gold color (#E8B44C)
- Deep navy background
- Elegant and sophisticated design

### User Experience
- Clear visual hierarchy
- Helpful micro-copy
- Instant feedback
- Smooth animations
- Accessibility considerations

## Testing Checklist

- [x] Screen loads without errors
- [x] User data populates correctly
- [x] Text fields are editable
- [x] Email field is read-only
- [x] Toggle switch works
- [x] Save button enables/disables based on changes
- [ ] API integration works (requires backend)
- [ ] Success message shows after save
- [ ] Error handling works
- [ ] Back navigation preserves changes prompt
- [ ] Avatar upload (future feature)

## Screenshots

The screen features:
- **Top**: Golden avatar circle with camera icon
- **Middle**: Three glass containers for name, username, and email
- **Bottom**: Visibility toggle with info box and save button

All wrapped in an animated gradient background with smooth transitions.

