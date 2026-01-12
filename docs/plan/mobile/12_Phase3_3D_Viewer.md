# 12_Phase3_3D_Viewer.md — 3D Urn Viewer & Motif Discovery

## Overview

Phase 3 implements the core 3D urn viewer with GLB model loading, touch interactions, hotspot rendering, and motif discovery flow.

**Duration:** 2 weeks  
**Priority:** P0 (Critical Path)  
**Prerequisites:** Phase 2 (Core Screens) completed

---

## Technology Options

### Option A: model_viewer_plus (Recommended)

```yaml
dependencies:
  model_viewer_plus: ^1.6.0
```

**Pros:**
- Based on Google's model-viewer (battle-tested)
- WebView-based (works on all devices)
- Built-in AR support
- Good performance for our model sizes (~10MB GLB)
- Automatic lighting and shadows

**Cons:**
- Limited customization
- Hotspots require HTML/JS bridge
- WebView overhead

### Option B: flutter_3d_controller

```yaml
dependencies:
  flutter_3d_controller: ^1.3.1
```

**Pros:**
- Native Flutter rendering
- More control over interactions
- Better performance for complex scenes

**Cons:**
- Less mature
- More complex setup
- Manual lighting configuration

### Decision: Start with model_viewer_plus, migrate to flutter_3d_controller if needed

---

## Week 1: 3D Model Loading & Basic Interaction

### Task 3.1: Create Urn Viewer Screen

**Estimated Time:** 4 hours

**File: `lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

class UrnViewerScreen extends ConsumerStatefulWidget {
  final String urnSlug;
  
  const UrnViewerScreen({super.key, required this.urnSlug});
  
  @override
  ConsumerState<UrnViewerScreen> createState() => _UrnViewerScreenState();
}

class _UrnViewerScreenState extends ConsumerState<UrnViewerScreen> {
  bool _isLoading = true;
  bool _showHotspots = true;
  Motif? _selectedMotif;
  
  @override
  Widget build(BuildContext context) {
    final urnAsync = ref.watch(urnDetailProvider(widget.urnSlug));
    
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: Icon(
              _showHotspots ? Icons.visibility : Icons.visibility_off,
              color: Colors.white,
            ),
            onPressed: () => setState(() => _showHotspots = !_showHotspots),
          ),
          IconButton(
            icon: const Icon(Icons.info_outline, color: Colors.white),
            onPressed: () => _showUrnInfo(context),
          ),
        ],
      ),
      body: urnAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, s) => ErrorWidget(message: e.toString()),
        data: (urn) => Stack(
          children: [
            // 3D Model Viewer
            Positioned.fill(
              child: _build3DViewer(urn),
            ),
            
            // Loading overlay
            if (_isLoading)
              const Positioned.fill(
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('Đang tải mô hình 3D...'),
                    ],
                  ),
                ),
              ),
            
            // Hotspot overlays
            if (_showHotspots && !_isLoading)
              ...urn.motifs.map((motif) => _buildHotspotOverlay(motif)),
            
            // Bottom info bar
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: _buildBottomBar(urn),
            ),
            
            // Motif sidebar
            if (_selectedMotif != null)
              Positioned(
                right: 0,
                top: 0,
                bottom: 0,
                width: MediaQuery.of(context).size.width * 0.85,
                child: MotifSidebar(
                  motif: _selectedMotif!,
                  onClose: () => setState(() => _selectedMotif = null),
                  onStartLesson: () => _navigateToLesson(_selectedMotif!),
                ),
              ),
          ],
        ),
      ),
    );
  }
  
  Widget _build3DViewer(UrnDetail urn) {
    return ModelViewer(
      src: urn.modelUrl ?? 'https://lms.histolab.icu/assets/models/${urn.slug.toUpperCase()}-v1.glb',
      alt: urn.name,
      ar: false, // Disable AR for now
      autoRotate: false,
      cameraControls: true,
      disableZoom: false,
      backgroundColor: const Color(0xFF1A1A1A),
      loading: Loading.eager,
      reveal: Reveal.auto,
      onProgress: (progress) {
        if (progress == 1.0 && _isLoading) {
          setState(() => _isLoading = false);
        }
      },
      // Hotspot handling via JavaScript
      innerModelViewerHtml: _generateHotspotHtml(urn.motifs),
      relatedJs: _generateHotspotJs(),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] GLB model loads from server
- [ ] Loading indicator shown during load
- [ ] Touch to rotate/pan/zoom works
- [ ] Back button returns to previous screen

---

### Task 3.2: Implement Hotspot System

**Estimated Time:** 6 hours

**Hotspot Rendering Strategy:**

Since model_viewer_plus uses WebView, we have two options:
1. **HTML hotspots** - Use model-viewer's built-in hotspot feature
2. **Flutter overlays** - Calculate screen positions from 3D coords

**Approach: Hybrid** - Use model-viewer hotspots for click detection, Flutter overlays for UI.

**File: `lib/features/urn_viewer/presentation/widgets/hotspot_overlay.dart`**

```dart
class HotspotOverlay extends StatefulWidget {
  final Motif motif;
  final bool isDiscovered;
  final VoidCallback onTap;
  
  const HotspotOverlay({
    super.key,
    required this.motif,
    required this.isDiscovered,
    required this.onTap,
  });
  
  @override
  State<HotspotOverlay> createState() => _HotspotOverlayState();
}

class _HotspotOverlayState extends State<HotspotOverlay>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  
  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
    
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    final color = widget.isDiscovered
        ? AppColors.discovered
        : AppColors.primary;
    
    return GestureDetector(
      onTap: widget.onTap,
      child: AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (context, child) => Transform.scale(
          scale: widget.isDiscovered ? 1.0 : _pulseAnimation.value,
          child: Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: color.withOpacity(0.8),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
              boxShadow: [
                BoxShadow(
                  color: color.withOpacity(0.5),
                  blurRadius: 8,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Icon(
              widget.isDiscovered ? Icons.check : Icons.touch_app,
              color: Colors.white,
              size: 16,
            ),
          ),
        ),
      ),
    );
  }
}
```

**JavaScript Bridge for Hotspot Clicks:**

```dart
String _generateHotspotJs() {
  return '''
    document.querySelectorAll('.hotspot').forEach(hotspot => {
      hotspot.addEventListener('click', () => {
        const motifId = hotspot.dataset.motifId;
        window.flutter_inappwebview.callHandler('onHotspotClick', motifId);
      });
    });
  ''';
}

String _generateHotspotHtml(List<Motif> motifs) {
  final buffer = StringBuffer();
  
  for (final motif in motifs) {
    buffer.writeln('''
      <button class="hotspot"
        slot="hotspot-${motif.id}"
        data-motif-id="${motif.id}"
        data-position="${motif.posX} ${motif.posY} ${motif.posZ}"
        data-normal="0 1 0">
      </button>
    ''');
  }
  
  return buffer.toString();
}
```

**Acceptance Criteria:**
- [ ] Hotspots visible on 3D model
- [ ] Undiscovered hotspots pulse
- [ ] Discovered hotspots show checkmark
- [ ] Tap detection works

---

### Task 3.3: Implement Motif Discovery Flow

**Estimated Time:** 4 hours

**File: `lib/features/urn_viewer/presentation/providers/discovery_provider.dart`**

```dart
@riverpod
class DiscoveryNotifier extends _$DiscoveryNotifier {
  @override
  FutureOr<void> build() {}
  
  Future<UnlockResult?> unlockMotif(String motifId) async {
    state = const AsyncLoading();
    
    final repository = ref.read(progressRepositoryProvider);
    final result = await repository.unlockMotif(motifId);
    
    return result.fold(
      (failure) {
        state = AsyncError(failure, StackTrace.current);
        return null;
      },
      (unlockResult) {
        state = const AsyncData(null);
        
        // Invalidate related providers
        ref.invalidate(urnDetailProvider);
        ref.invalidate(collectionProvider);
        ref.invalidate(dashboardProvider);
        
        return unlockResult;
      },
    );
  }
}
```

**Discovery Animation:**

```dart
class DiscoveryAnimation extends StatefulWidget {
  final Motif motif;
  final int xpEarned;
  final VoidCallback onComplete;
  
  const DiscoveryAnimation({
    super.key,
    required this.motif,
    required this.xpEarned,
    required this.onComplete,
  });
  
  @override
  State<DiscoveryAnimation> createState() => _DiscoveryAnimationState();
}

class _DiscoveryAnimationState extends State<DiscoveryAnimation>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _opacityAnimation;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    );
    
    _scaleAnimation = TweenSequence<double>([
      TweenSequenceItem(tween: Tween(begin: 0.0, end: 1.2), weight: 30),
      TweenSequenceItem(tween: Tween(begin: 1.2, end: 1.0), weight: 20),
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 1.0), weight: 30),
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 0.0), weight: 20),
    ]).animate(_controller);
    
    _controller.forward().then((_) => widget.onComplete());
  }
  
  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => Transform.scale(
        scale: _scaleAnimation.value,
        child: Container(
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: Colors.black87,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.celebration, color: AppColors.xpGold, size: 48),
              const SizedBox(height: 16),
              Text(
                'Đã khám phá!',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                widget.motif.name,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(height: 16),
              XpBadge(amount: widget.xpEarned, size: XpBadgeSize.large),
            ],
          ),
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Tap on undiscovered hotspot triggers unlock
- [ ] Discovery animation plays
- [ ] XP awarded shown
- [ ] Hotspot updates to discovered state
- [ ] Progress saved to backend

---

## Week 2: Sidebar & Lesson Integration

### Task 3.4: Implement Motif Sidebar

**Estimated Time:** 6 hours

**File: `lib/features/urn_viewer/presentation/widgets/motif_sidebar.dart`**

```dart
class MotifSidebar extends ConsumerWidget {
  final Motif motif;
  final VoidCallback onClose;
  final VoidCallback onStartLesson;
  
  const MotifSidebar({
    super.key,
    required this.motif,
    required this.onClose,
    required this.onStartLesson,
  });
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final progressAsync = ref.watch(motifProgressProvider(motif.id));
    final theme = Theme.of(context);
    
    return Material(
      elevation: 16,
      child: Container(
        color: theme.colorScheme.surface,
        child: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header
              _buildHeader(context),
              
              // Content
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Thumbnail
                      if (motif.thumbnailUrl != null)
                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: CachedNetworkImage(
                            imageUrl: motif.thumbnailUrl!,
                            height: 200,
                            width: double.infinity,
                            fit: BoxFit.cover,
                          ),
                        ),
                      
                      const SizedBox(height: 16),
                      
                      // Motif name
                      Text(
                        motif.name,
                        style: theme.textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      
                      const SizedBox(height: 8),
                      
                      // Category and rarity
                      Row(
                        children: [
                          CategoryChip(category: motif.category),
                          const SizedBox(width: 8),
                          RarityChip(rarity: motif.rarity),
                        ],
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Progress stepper
                      progressAsync.when(
                        loading: () => const LinearProgressIndicator(),
                        error: (e, s) => const SizedBox(),
                        data: (progress) => ProgressStepper(
                          status: progress?.status ?? 'hidden',
                        ),
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Description
                      if (motif.description != null)
                        Text(
                          motif.description!,
                          style: theme.textTheme.bodyMedium,
                        ),
                    ],
                  ),
                ),
              ),
              
              // Action button
              Padding(
                padding: const EdgeInsets.all(16),
                child: progressAsync.when(
                  loading: () => const SizedBox(),
                  error: (e, s) => const SizedBox(),
                  data: (progress) => _buildActionButton(context, progress),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildActionButton(BuildContext context, Progress? progress) {
    final status = progress?.status ?? 'discovered';
    
    switch (status) {
      case 'discovered':
        return ElevatedButton.icon(
          onPressed: onStartLesson,
          icon: const Icon(Icons.school),
          label: const Text('Bắt đầu bài học'),
        );
      case 'learned':
        return ElevatedButton.icon(
          onPressed: () => _startQuiz(context),
          icon: const Icon(Icons.quiz),
          label: const Text('Làm trắc nghiệm'),
        );
      case 'mastered':
        return OutlinedButton.icon(
          onPressed: onStartLesson,
          icon: const Icon(Icons.replay),
          label: const Text('Xem lại bài học'),
        );
      default:
        return const SizedBox();
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Sidebar slides in from right
- [ ] Shows motif details
- [ ] Progress stepper visible
- [ ] Action button changes based on status
- [ ] Can close sidebar

---

### Task 3.5: Implement Progress Stepper

**Estimated Time:** 3 hours

**File: `lib/features/urn_viewer/presentation/widgets/progress_stepper.dart`**

```dart
class ProgressStepper extends StatelessWidget {
  final String status;
  
  const ProgressStepper({super.key, required this.status});
  
  static const _steps = [
    _Step(
      status: 'discovered',
      label: 'Khám Phá',
      icon: Icons.explore,
      xp: 25,
    ),
    _Step(
      status: 'learned',
      label: 'Bài Học',
      icon: Icons.school,
      xp: 50,
    ),
    _Step(
      status: 'mastered',
      label: 'Trắc Nghiệm',
      icon: Icons.emoji_events,
      xp: 75,
    ),
  ];
  
  int get _currentStepIndex {
    switch (status) {
      case 'hidden': return -1;
      case 'discovered': return 0;
      case 'learned': return 1;
      case 'mastered': return 2;
      default: return -1;
    }
  }
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Row(
      children: List.generate(_steps.length * 2 - 1, (index) {
        if (index.isOdd) {
          // Connector line
          final stepIndex = index ~/ 2;
          final isCompleted = stepIndex < _currentStepIndex;
          
          return Expanded(
            child: Container(
              height: 2,
              color: isCompleted
                  ? AppColors.discovered
                  : theme.colorScheme.outlineVariant,
            ),
          );
        }
        
        // Step circle
        final stepIndex = index ~/ 2;
        final step = _steps[stepIndex];
        final isCompleted = stepIndex <= _currentStepIndex;
        final isCurrent = stepIndex == _currentStepIndex;
        
        return _StepCircle(
          step: step,
          isCompleted: isCompleted,
          isCurrent: isCurrent,
        );
      }),
    );
  }
}

class _Step {
  final String status;
  final String label;
  final IconData icon;
  final int xp;
  
  const _Step({
    required this.status,
    required this.label,
    required this.icon,
    required this.xp,
  });
}

class _StepCircle extends StatelessWidget {
  final _Step step;
  final bool isCompleted;
  final bool isCurrent;
  
  const _StepCircle({
    required this.step,
    required this.isCompleted,
    required this.isCurrent,
  });
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    Color backgroundColor;
    Color iconColor;
    IconData icon;
    
    if (isCompleted) {
      backgroundColor = AppColors.discovered;
      iconColor = Colors.white;
      icon = Icons.check;
    } else if (isCurrent) {
      backgroundColor = theme.colorScheme.primary;
      iconColor = Colors.white;
      icon = step.icon;
    } else {
      backgroundColor = theme.colorScheme.surfaceVariant;
      iconColor = theme.colorScheme.onSurfaceVariant;
      icon = Icons.lock;
    }
    
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: backgroundColor,
            shape: BoxShape.circle,
            boxShadow: isCurrent ? [
              BoxShadow(
                color: backgroundColor.withOpacity(0.4),
                blurRadius: 8,
                spreadRadius: 2,
              ),
            ] : null,
          ),
          child: Icon(icon, color: iconColor, size: 20),
        ),
        const SizedBox(height: 4),
        Text(
          step.label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: isCompleted || isCurrent
                ? theme.colorScheme.onSurface
                : theme.colorScheme.onSurfaceVariant,
            fontWeight: isCurrent ? FontWeight.bold : null,
          ),
        ),
        Text(
          '+${step.xp} XP',
          style: theme.textTheme.labelSmall?.copyWith(
            color: AppColors.xpGold,
          ),
        ),
      ],
    );
  }
}
```

**Acceptance Criteria:**
- [ ] 3-step progress indicator
- [ ] Completed steps show checkmark
- [ ] Current step highlighted
- [ ] Locked steps show lock icon
- [ ] XP values displayed

---

### Task 3.6: Implement Alternative 3D Viewer (flutter_3d_controller)

**Estimated Time:** 4 hours (contingency)

If model_viewer_plus has performance issues, implement fallback:

```dart
class Native3DViewer extends StatefulWidget {
  final String modelUrl;
  final List<Motif> motifs;
  final Function(String motifId) onHotspotTap;
  
  const Native3DViewer({
    super.key,
    required this.modelUrl,
    required this.motifs,
    required this.onHotspotTap,
  });
  
  @override
  State<Native3DViewer> createState() => _Native3DViewerState();
}

class _Native3DViewerState extends State<Native3DViewer> {
  late Flutter3DController _controller;
  
  @override
  void initState() {
    super.initState();
    _controller = Flutter3DController();
  }
  
  @override
  Widget build(BuildContext context) {
    return Flutter3DViewer(
      controller: _controller,
      src: widget.modelUrl,
      enableTouch: true,
      onProgress: (progress) {
        // Handle loading progress
      },
      onLoad: (model) {
        // Model loaded, setup hotspots
        _setupHotspots();
      },
      onError: (error) {
        // Handle error
      },
    );
  }
  
  void _setupHotspots() {
    // Add hotspot markers at motif positions
    for (final motif in widget.motifs) {
      if (motif.posX != null && motif.posY != null && motif.posZ != null) {
        _controller.addMarker(
          position: Vector3(motif.posX!, motif.posY!, motif.posZ!),
          onTap: () => widget.onHotspotTap(motif.id),
        );
      }
    }
  }
}
```

---

## Performance Optimizations

### Model Loading

```dart
class ModelCache {
  static final Map<String, String> _localPaths = {};
  
  static Future<String> getModelPath(String url) async {
    if (_localPaths.containsKey(url)) {
      return _localPaths[url]!;
    }
    
    // Download and cache
    final cacheDir = await getTemporaryDirectory();
    final fileName = url.split('/').last;
    final filePath = '${cacheDir.path}/models/$fileName';
    
    final file = File(filePath);
    if (!await file.exists()) {
      final response = await Dio().download(url, filePath);
    }
    
    _localPaths[url] = filePath;
    return filePath;
  }
}
```

### Memory Management

```dart
@override
void dispose() {
  // Clear model from memory
  _controller.dispose();
  
  // Clear texture cache if needed
  imageCache.clear();
  
  super.dispose();
}
```

---

## Phase 3 Checklist

### 3D Viewer
- [ ] P3-V1: GLB model loads from server
- [ ] P3-V2: Touch controls (rotate, zoom, pan) work
- [ ] P3-V3: Loading indicator during model load
- [ ] P3-V4: Error handling for failed loads

### Hotspots
- [ ] P3-H1: Hotspots render at correct positions
- [ ] P3-H2: Undiscovered hotspots pulse
- [ ] P3-H3: Discovered hotspots show checkmark
- [ ] P3-H4: Tap detection triggers discovery

### Discovery Flow
- [ ] P3-D1: Unlock API call on tap
- [ ] P3-D2: Discovery animation plays
- [ ] P3-D3: XP awarded displayed
- [ ] P3-D4: Progress updates in real-time

### Sidebar
- [ ] P3-S1: Sidebar slides in on selection
- [ ] P3-S2: Motif details displayed
- [ ] P3-S3: Progress stepper visible
- [ ] P3-S4: Action button changes by status
- [ ] P3-S5: Navigation to lesson/quiz works

### Performance
- [ ] P3-P1: Model loads in < 5 seconds on 4G
- [ ] P3-P2: Smooth 60fps rotation
- [ ] P3-P3: Memory usage < 300MB
- [ ] P3-P4: Models cached locally

---

## Testing Checklist

### Manual Testing
- [ ] Test on low-end device (Android Go)
- [ ] Test on tablet
- [ ] Test with slow network (throttled)
- [ ] Test model rotation gestures
- [ ] Test pinch-to-zoom
- [ ] Test hotspot tap accuracy
- [ ] Test discovery flow end-to-end

### Automated Testing
- [ ] Widget test for ProgressStepper
- [ ] Widget test for MotifSidebar
- [ ] Integration test for discovery flow
- [ ] Golden test for hotspot states