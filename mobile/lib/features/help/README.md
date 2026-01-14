# Help & Support Screen

## Overview
The Help & Support screen provides users with comprehensive assistance and resources for using the EduQuest AR app.

## Features

### 1. **FAQ Section** 📚
- Expandable FAQ items using `ExpansionTile`
- Beautiful glass container styling
- Pre-populated with common questions:
  - How to explore 3D models
  - How XP points are calculated
  - How to achieve higher ranks
  - Offline learning capabilities
  - Progress tracking

### 2. **Contact Support** 💬
- **Email Support**: Opens email client with pre-filled support email
- **Bug Report**: Allows users to report issues
- Direct email to: `support@eduquest.vn`

### 3. **Resources** 📖
- **Tutorial Videos**: Links to YouTube channel
- **Documentation**: Links to detailed PDF guides
- External links open in browser

### 4. **Social Media** 🌐
- Facebook link
- YouTube link
- Zalo messenger link
- Beautiful icon buttons with labels

## Design System

### Glass Morphism
All sections use `GlassContainer` with:
- Semi-transparent backgrounds
- Elegant borders
- Soft shadows
- Smooth animations

### Color Scheme
- Primary accent: Gold gradient
- Secondary accent: Imperial red
- Success: Green (for help icon)
- Accent: Orange (for resources)

### Layout
- Responsive single-scroll layout
- Proper spacing between sections
- SafeArea for device compatibility
- Gradient background

## Navigation

### Route
```dart
path: '/help'
name: 'help'
```

### Access Points
- Profile screen → "Trợ giúp & Hỗ trợ" button

### Navigation Example
```dart
context.push('/help');
```

## File Structure

```
mobile/lib/features/help/
└── presentation/
    └── screens/
        └── help_support_screen.dart
```

## Dependencies

### Required Packages
- `url_launcher: ^6.2.3` - For opening email and web links
- `flutter_riverpod` - State management
- `go_router` - Navigation

## Implementation Details

### FAQ Data Model
```dart
class FAQItem {
  final String question;
  final String answer;
}
```

### URL Launching
```dart
Future<void> _launchEmail() async {
  final Uri emailUri = Uri(
    scheme: 'mailto',
    path: 'support@eduquest.vn',
    query: 'subject=Hỗ trợ EduQuest AR',
  );
  
  if (await canLaunchUrl(emailUri)) {
    await launchUrl(emailUri);
  }
}
```

## Screenshots Sections

### 1. FAQ Section
- Expandable accordion-style questions
- Gold accent icon
- Smooth expand/collapse animation

### 2. Support Section
- Email support button
- Bug report button
- Imperial red accent icon

### 3. Resources Section
- Tutorial video link
- Documentation link
- Orange accent icon

### 4. Social Media Section
- Three social platforms
- Icon buttons with labels
- Multi-color gradient icon

## Customization

### Adding New FAQs
```dart
final List<FAQItem> _faqs = [
  FAQItem(
    question: 'Your question here?',
    answer: 'Your detailed answer here.',
  ),
  // ... more FAQs
];
```

### Changing Contact Email
Update the email path in `_launchEmail()`:
```dart
path: 'your-email@domain.com',
```

### Adding Social Media Links
Update URLs in social button callbacks:
```dart
_buildSocialButton(
  icon: Icons.your_icon,
  label: 'Platform',
  onTap: () => _launchURL('https://your-link.com'),
),
```

## User Experience

### Accessibility
- Clear section headers
- High contrast text
- Touch-friendly buttons
- Readable font sizes

### Error Handling
- Graceful fallback if email client unavailable
- SnackBar notifications for errors
- Clear error messages

### Performance
- Lazy loading of expandable items
- Optimized rendering
- Smooth animations

## Future Enhancements

- [ ] Live chat integration
- [ ] In-app FAQ search
- [ ] Video tutorials embed
- [ ] Multilingual support
- [ ] User feedback form
- [ ] Dark/Light theme toggle

## Testing

### Manual Testing Checklist
- ✅ FAQ items expand/collapse correctly
- ✅ Email button opens email client
- ✅ Bug report button opens email client
- ✅ Social media links open in browser
- ✅ Back button navigates correctly
- ✅ All text is readable
- ✅ Glass effects render properly

## Localization

All text is in Vietnamese (vi-VN):
- Title: "Trợ Giúp & Hỗ Trợ"
- Sections: Vietnamese labels
- FAQ: Vietnamese Q&A

To add English support, implement i18n localization.

## Notes

- Uses `url_launcher` for external links
- Requires internet for external resources
- Email functionality depends on device mail client
- Social links are placeholder URLs (update in production)

---

**Created**: 2024
**Last Updated**: 2024
**Version**: 1.0.0

