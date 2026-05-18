# Implementation Examples for Future Development

## How to Use AppSpacing

### Basic Usage
```dart
import 'package:your_app/core/theme/app_spacing.dart';

// Using constants
Container(
  padding: EdgeInsets.all(AppSpacing.md),
  child: Column(
    children: [
      Text('Hello'),
      AppSpacing.verticalSpaceMD,  // Pre-built SizedBox
      Text('World'),
    ],
  ),
)

// Using radius
Container(
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
  ),
)
```

### Advanced Usage
```dart
// Custom padding with spacing constants
Container(
  padding: EdgeInsets.symmetric(
    horizontal: AppSpacing.lg,
    vertical: AppSpacing.md,
  ),
)

// Margin with spacing
Container(
  margin: EdgeInsets.only(
    top: AppSpacing.xl,
    bottom: AppSpacing.sm,
  ),
)
```

## How to Add Animations

### Screen Entry Animation
```dart
class MyScreen extends ConsumerStatefulWidget {
  @override
  State<MyScreen> createState() => _MyScreenState();
}

class _MyScreenState extends ConsumerState<MyScreen> 
    with SingleTickerProviderStateMixin {
  
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 600),
    );
    
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
    
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();  // IMPORTANT!
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: YourContent(),
    );
  }
}
```

### Press Animation
```dart
class AnimatedCard extends StatefulWidget {
  final VoidCallback? onTap;
  
  @override
  State<AnimatedCard> createState() => _AnimatedCardState();
}

class _AnimatedCardState extends State<AnimatedCard> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap?.call();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedScale(
        scale: _isPressed ? 0.95 : 1.0,
        duration: Duration(milliseconds: 150),
        curve: Curves.easeOut,
        child: YourCard(),
      ),
    );
  }
}
```

### Staggered List Animation
```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: Duration(milliseconds: 400 + (index * 100)),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.scale(
          scale: value,
          child: Opacity(
            opacity: value,
            child: child,
          ),
        );
      },
      child: YourListItem(items[index]),
    );
  },
)
```

## How to Create Glassmorphism Cards

### Basic Glass Card
```dart
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        Colors.white.withOpacity(0.12),
        Colors.white.withOpacity(0.06),
      ],
    ),
    borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
    border: Border.all(
      color: Colors.white.withOpacity(0.2),
      width: 1.5,
    ),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.2),
        blurRadius: 20,
        offset: Offset(0, 10),
      ),
    ],
  ),
  child: YourContent(),
)
```

### Glass Card with Glow Effect
```dart
Container(
  decoration: BoxDecoration(
    // ... gradient and border as above ...
    boxShadow: [
      // Base shadow
      BoxShadow(
        color: Colors.black.withOpacity(0.2),
        blurRadius: 20,
        offset: Offset(0, 10),
      ),
      // Glow effect (conditional)
      if (isHighlighted)
        BoxShadow(
          color: Color(0xFFD4A84B).withOpacity(0.4),
          blurRadius: 30,
          spreadRadius: -5,
        ),
    ],
  ),
)
```

## How to Add Form Fields

### Standard Input Field
```dart
Container(
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.1),
        blurRadius: 10,
        offset: Offset(0, 4),
      ),
    ],
  ),
  child: TextField(
    style: TextStyle(color: Colors.white, fontSize: 15),
    decoration: InputDecoration(
      hintText: 'Enter text...',
      hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
      filled: true,
      fillColor: Colors.white.withOpacity(0.12),
      contentPadding: EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.md,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        borderSide: BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        borderSide: BorderSide(color: Color(0xFFD4A84B), width: 2),
      ),
      prefixIcon: Icon(
        Icons.email_outlined,
        color: Colors.white.withOpacity(0.6),
      ),
    ),
  ),
)
```

## How to Add Buttons

### Primary Button
```dart
SizedBox(
  height: 56,
  child: ElevatedButton(
    onPressed: _handlePress,
    style: ElevatedButton.styleFrom(
      backgroundColor: Color(0xFFD4A84B),
      foregroundColor: Color(0xFF1A1A2E),
      elevation: 8,
      shadowColor: Color(0xFFD4A84B).withOpacity(0.4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      ),
    ),
    child: Text(
      'Button Text',
      style: TextStyle(
        fontSize: 17,
        fontWeight: FontWeight.bold,
        letterSpacing: 0.5,
      ),
    ),
  ),
)
```

### Button with Loading State
```dart
ElevatedButton(
  onPressed: _isLoading ? null : _handlePress,
  style: ElevatedButton.styleFrom(
    backgroundColor: Color(0xFFD4A84B),
    disabledBackgroundColor: Color(0xFFD4A84B).withOpacity(0.5),
    // ... other styles ...
  ),
  child: _isLoading
      ? Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                valueColor: AlwaysStoppedAnimation(Color(0xFF1A1A2E)),
              ),
            ),
            AppSpacing.horizontalSpaceMD,
            Text('Loading...'),
          ],
        )
      : Text('Button Text'),
)
```

