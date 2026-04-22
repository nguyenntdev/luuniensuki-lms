# 13_Phase4_Learning_Flow.md — Learning Flow: Lessons & Quizzes

## Overview

Phase 4 implements the complete learning flow: lesson content display with multimedia support (audio, video, images), quiz system with all question types, and progress tracking.

**Duration:** 2 weeks  
**Priority:** P0 (Critical Path)  
**Prerequisites:** Phase 3 (3D Viewer) completed

---

## Week 1: Lesson Content Display

### Task 4.1: Create Motif Detail Screen

**Estimated Time:** 4 hours

**File: `lib/features/lesson/presentation/screens/motif_detail_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MotifDetailScreen extends ConsumerStatefulWidget {
  final String motifId;
  
  const MotifDetailScreen({super.key, required this.motifId});
  
  @override
  ConsumerState<MotifDetailScreen> createState() => _MotifDetailScreenState();
}

class _MotifDetailScreenState extends ConsumerState<MotifDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }
  
  @override
  Widget build(BuildContext context) {
    final motifAsync = ref.watch(motifDetailProvider(widget.motifId));
    
    return Scaffold(
      body: motifAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, s) => ErrorWidget(
          message: e.toString(),
          onRetry: () => ref.invalidate(motifDetailProvider(widget.motifId)),
        ),
        data: (motifDetail) => NestedScrollView(
          headerSliverBuilder: (context, innerBoxIsScrolled) => [
            // Hero image header
            SliverAppBar(
              expandedHeight: 250,
              pinned: true,
              flexibleSpace: FlexibleSpaceBar(
                background: _buildHeroImage(motifDetail.motif),
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.share),
                  onPressed: () => _shareMotif(motifDetail.motif),
                ),
              ],
            ),
            
            // Tab bar
            SliverPersistentHeader(
              pinned: true,
              delegate: _TabBarDelegate(
                TabBar(
                  controller: _tabController,
                  tabs: const [
                    Tab(text: 'Bài Học'),
                    Tab(text: 'Thông Tin'),
                  ],
                ),
              ),
            ),
          ],
          body: TabBarView(
            controller: _tabController,
            children: [
              LessonTab(
                motif: motifDetail.motif,
                lesson: motifDetail.lesson,
                progress: motifDetail.progress,
              ),
              InfoTab(motif: motifDetail.motif),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildHeroImage(Motif motif) {
    return Stack(
      fit: StackFit.expand,
      children: [
        CachedNetworkImage(
          imageUrl: motif.thumbnailUrl ?? '',
          fit: BoxFit.cover,
          placeholder: (_, __) => Container(color: Colors.grey[300]),
          errorWidget: (_, __, ___) => Container(
            color: Colors.grey[300],
            child: const Icon(Icons.image, size: 64),
          ),
        ),
        // Gradient overlay
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Colors.transparent,
                Colors.black.withOpacity(0.7),
              ],
            ),
          ),
        ),
        // Motif info
        Positioned(
          left: 16,
          right: 16,
          bottom: 16,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                motif.name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  CategoryChip(category: motif.category),
                  const SizedBox(width: 8),
                  RarityChip(rarity: motif.rarity),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Hero image with motif thumbnail
- [ ] Tab navigation (Lesson / Info)
- [ ] Category and rarity displayed
- [ ] Share button functional

---

### Task 4.2: Implement Lesson Tab

**Estimated Time:** 6 hours

**File: `lib/features/lesson/presentation/widgets/lesson_tab.dart`**

```dart
class LessonTab extends ConsumerWidget {
  final Motif motif;
  final LessonContent? lesson;
  final Progress? progress;
  
  const LessonTab({
    super.key,
    required this.motif,
    this.lesson,
    this.progress,
  });
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    
    if (lesson == null) {
      return const EmptyState(
        icon: Icons.school_outlined,
        title: 'Chưa có bài học',
        message: 'Nội dung bài học đang được cập nhật.',
      );
    }
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Progress stepper
          ProgressStepper(status: progress?.status ?? 'discovered'),
          
          const SizedBox(height: 24),
          
          // Audio narration (if available)
          if (lesson!.audioNarrationUrl != null)
            AudioPlayerCard(url: lesson!.audioNarrationUrl!),
          
          // Video (if available)
          if (lesson!.videoUrl != null) ...[
            const SizedBox(height: 16),
            VideoPlayerCard(url: lesson!.videoUrl!),
          ],
          
          const SizedBox(height: 24),
          
          // Introduction
          if (lesson!.introText != null) ...[
            LessonSection(
              title: 'Giới thiệu',
              icon: Icons.info_outline,
              content: lesson!.introText!,
            ),
            const SizedBox(height: 16),
          ],
          
          // Description
          if (lesson!.description != null) ...[
            LessonSection(
              title: 'Mô tả chi tiết',
              icon: Icons.description_outlined,
              content: lesson!.description!,
            ),
            const SizedBox(height: 16),
          ],
          
          // Symbolism
          if (lesson!.symbolism != null) ...[
            LessonSection(
              title: 'Ý nghĩa biểu tượng',
              icon: Icons.auto_awesome_outlined,
              content: lesson!.symbolism!,
            ),
            const SizedBox(height: 16),
          ],
          
          // Historical context
          if (lesson!.historicalContext != null) ...[
            LessonSection(
              title: 'Bối cảnh lịch sử',
              icon: Icons.history_edu_outlined,
              content: lesson!.historicalContext!,
            ),
            const SizedBox(height: 16),
          ],
          
          // Fun fact
          if (lesson!.funFact != null) ...[
            FunFactCard(fact: lesson!.funFact!),
            const SizedBox(height: 16),
          ],
          
          // Image gallery
          if (lesson!.additionalImages?.isNotEmpty == true) ...[
            const SizedBox(height: 16),
            ImageGallery(images: lesson!.additionalImages!),
          ],
          
          const SizedBox(height: 32),
          
          // Action buttons
          _buildActionButtons(context, ref),
          
          const SizedBox(height: 24),
        ],
      ),
    );
  }
  
  Widget _buildActionButtons(BuildContext context, WidgetRef ref) {
    final status = progress?.status ?? 'discovered';
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (status == 'discovered')
          ElevatedButton.icon(
            onPressed: () => _completeLesson(context, ref),
            icon: const Icon(Icons.check),
            label: const Text('Hoàn thành bài học'),
          ),
        
        if (status == 'learned' || status == 'mastered') ...[
          ElevatedButton.icon(
            onPressed: () => context.goNamed(
              RouteNames.motifQuiz,
              pathParameters: {'motifId': motif.id},
            ),
            icon: const Icon(Icons.quiz),
            label: Text(status == 'mastered' 
                ? 'Làm lại trắc nghiệm' 
                : 'Làm trắc nghiệm'),
          ),
          if (status == 'mastered')
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                'Điểm cao nhất: ${progress?.quizBestScore ?? 0}%',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
        ],
      ],
    );
  }
  
  Future<void> _completeLesson(BuildContext context, WidgetRef ref) async {
    final result = await ref
        .read(lessonCompletionProvider.notifier)
        .completeLesson(motif.id);
    
    if (result != null && context.mounted) {
      // Show completion animation
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => LessonCompletionDialog(
          xpEarned: result.xpAwarded,
          onDismiss: () {
            Navigator.pop(context);
            // Optionally navigate to quiz
            context.goNamed(
              RouteNames.motifQuiz,
              pathParameters: {'motifId': motif.id},
            );
          },
        ),
      );
    }
  }
}
```

**Acceptance Criteria:**
- [ ] All lesson sections rendered
- [ ] Audio player (if available)
- [ ] Video player (if available)
- [ ] Image gallery (if available)
- [ ] Complete lesson button
- [ ] Navigate to quiz after completion

---

### Task 4.3: Implement Audio Player

**Estimated Time:** 3 hours

**File: `lib/features/lesson/presentation/widgets/audio_player_card.dart`**

```dart
import 'package:just_audio/just_audio.dart';

class AudioPlayerCard extends StatefulWidget {
  final String url;
  
  const AudioPlayerCard({super.key, required this.url});
  
  @override
  State<AudioPlayerCard> createState() => _AudioPlayerCardState();
}

class _AudioPlayerCardState extends State<AudioPlayerCard> {
  late AudioPlayer _player;
  bool _isLoading = true;
  bool _hasError = false;
  
  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _initPlayer();
  }
  
  Future<void> _initPlayer() async {
    try {
      await _player.setUrl(widget.url);
      setState(() => _isLoading = false);
    } catch (e) {
      setState(() {
        _isLoading = false;
        _hasError = true;
      });
    }
  }
  
  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    if (_hasError) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(Icons.error_outline, color: theme.colorScheme.error),
              const SizedBox(width: 12),
              const Text('Không thể tải audio'),
            ],
          ),
        ),
      );
    }
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.headphones, color: AppColors.primary),
                const SizedBox(width: 12),
                Text(
                  'Nghe thuyết minh',
                  style: theme.textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (_isLoading)
              const LinearProgressIndicator()
            else
              StreamBuilder<PlayerState>(
                stream: _player.playerStateStream,
                builder: (context, snapshot) {
                  final playerState = snapshot.data;
                  final playing = playerState?.playing ?? false;
                  
                  return Row(
                    children: [
                      // Play/Pause button
                      IconButton.filled(
                        onPressed: () {
                          if (playing) {
                            _player.pause();
                          } else {
                            _player.play();
                          }
                        },
                        icon: Icon(
                          playing ? Icons.pause : Icons.play_arrow,
                        ),
                      ),
                      const SizedBox(width: 16),
                      // Progress bar
                      Expanded(
                        child: StreamBuilder<Duration>(
                          stream: _player.positionStream,
                          builder: (context, snapshot) {
                            final position = snapshot.data ?? Duration.zero;
                            final duration = _player.duration ?? Duration.zero;
                            
                            return Column(
                              children: [
                                Slider(
                                  value: position.inMilliseconds.toDouble(),
                                  max: duration.inMilliseconds.toDouble(),
                                  onChanged: (value) {
                                    _player.seek(
                                      Duration(milliseconds: value.toInt()),
                                    );
                                  },
                                ),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      _formatDuration(position),
                                      style: theme.textTheme.bodySmall,
                                    ),
                                    Text(
                                      _formatDuration(duration),
                                      style: theme.textTheme.bodySmall,
                                    ),
                                  ],
                                ),
                              ],
                            );
                          },
                        ),
                      ),
                    ],
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
  
  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = duration.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}
```

**Acceptance Criteria:**
- [ ] Audio loads from URL
- [ ] Play/pause button works
- [ ] Progress bar shows position
- [ ] Seek functionality works
- [ ] Duration displayed
- [ ] Error state handled

---

### Task 4.4: Implement Video Player

**Estimated Time:** 3 hours

**File: `lib/features/lesson/presentation/widgets/video_player_card.dart`**

```dart
import 'package:video_player/video_player.dart';

class VideoPlayerCard extends StatefulWidget {
  final String url;
  
  const VideoPlayerCard({super.key, required this.url});
  
  @override
  State<VideoPlayerCard> createState() => _VideoPlayerCardState();
}

class _VideoPlayerCardState extends State<VideoPlayerCard> {
  late VideoPlayerController _controller;
  bool _isInitialized = false;
  bool _hasError = false;
  bool _showControls = true;
  
  @override
  void initState() {
    super.initState();
    _controller = VideoPlayerController.networkUrl(Uri.parse(widget.url))
      ..initialize().then((_) {
        setState(() => _isInitialized = true);
      }).catchError((e) {
        setState(() => _hasError = true);
      });
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    if (_hasError) {
      return Card(
        child: Container(
          height: 200,
          alignment: Alignment.center,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, 
                   color: Theme.of(context).colorScheme.error, 
                   size: 48),
              const SizedBox(height: 8),
              const Text('Không thể tải video'),
            ],
          ),
        ),
      );
    }
    
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Video header
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.play_circle, color: AppColors.primary),
                const SizedBox(width: 12),
                Text(
                  'Video bài giảng',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
          ),
          
          // Video player
          GestureDetector(
            onTap: () => setState(() => _showControls = !_showControls),
            child: AspectRatio(
              aspectRatio: _isInitialized 
                  ? _controller.value.aspectRatio 
                  : 16 / 9,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  if (_isInitialized)
                    VideoPlayer(_controller)
                  else
                    Container(
                      color: Colors.black,
                      child: const Center(child: CircularProgressIndicator()),
                    ),
                  
                  // Controls overlay
                  if (_showControls && _isInitialized)
                    Container(
                      color: Colors.black38,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          IconButton(
                            iconSize: 64,
                            color: Colors.white,
                            icon: Icon(
                              _controller.value.isPlaying 
                                  ? Icons.pause_circle 
                                  : Icons.play_circle,
                            ),
                            onPressed: () {
                              setState(() {
                                if (_controller.value.isPlaying) {
                                  _controller.pause();
                                } else {
                                  _controller.play();
                                }
                              });
                            },
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
          
          // Progress bar
          if (_isInitialized)
            VideoProgressIndicator(
              _controller,
              allowScrubbing: true,
              padding: const EdgeInsets.all(16),
            ),
        ],
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Video loads from URL
- [ ] Play/pause controls work
- [ ] Progress bar with scrubbing
- [ ] Fullscreen toggle (optional)
- [ ] Loading state shown
- [ ] Error state handled

---

### Task 4.5: Implement Image Gallery

**Estimated Time:** 3 hours

**File: `lib/features/lesson/presentation/widgets/image_gallery.dart`**

```dart
import 'package:photo_view/photo_view.dart';
import 'package:photo_view/photo_view_gallery.dart';

class ImageGallery extends StatelessWidget {
  final List<String> images;
  
  const ImageGallery({super.key, required this.images});
  
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.photo_library, color: AppColors.primary),
            const SizedBox(width: 12),
            Text(
              'Hình ảnh (${images.length})',
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ],
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 120,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: images.length,
            itemBuilder: (context, index) {
              return Padding(
                padding: EdgeInsets.only(
                  left: index == 0 ? 0 : 8,
                ),
                child: GestureDetector(
                  onTap: () => _openGallery(context, index),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: CachedNetworkImage(
                      imageUrl: images[index],
                      width: 160,
                      height: 120,
                      fit: BoxFit.cover,
                      placeholder: (_, __) => const ShimmerBox(
                        width: 160,
                        height: 120,
                      ),
                      errorWidget: (_, __, ___) => Container(
                        width: 160,
                        height: 120,
                        color: Colors.grey[300],
                        child: const Icon(Icons.broken_image),
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
  
  void _openGallery(BuildContext context, int initialIndex) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => GalleryViewer(
          images: images,
          initialIndex: initialIndex,
        ),
      ),
    );
  }
}

class GalleryViewer extends StatefulWidget {
  final List<String> images;
  final int initialIndex;
  
  const GalleryViewer({
    super.key,
    required this.images,
    required this.initialIndex,
  });
  
  @override
  State<GalleryViewer> createState() => _GalleryViewerState();
}

class _GalleryViewerState extends State<GalleryViewer> {
  late PageController _pageController;
  late int _currentIndex;
  
  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          '${_currentIndex + 1} / ${widget.images.length}',
          style: const TextStyle(color: Colors.white),
        ),
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: PhotoViewGallery.builder(
        pageController: _pageController,
        itemCount: widget.images.length,
        builder: (context, index) {
          return PhotoViewGalleryPageOptions(
            imageProvider: CachedNetworkImageProvider(widget.images[index]),
            minScale: PhotoViewComputedScale.contained,
            maxScale: PhotoViewComputedScale.covered * 3,
          );
        },
        onPageChanged: (index) {
          setState(() => _currentIndex = index);
        },
        loadingBuilder: (context, event) => const Center(
          child: CircularProgressIndicator(),
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Horizontal scrollable thumbnails
- [ ] Tap to open fullscreen viewer
- [ ] Pinch to zoom in fullscreen
- [ ] Swipe between images
- [ ] Image count indicator
- [ ] Loading states handled

---

## Week 2: Quiz System

### Task 4.6: Create Quiz Screen

**Estimated Time:** 6 hours

**File: `lib/features/quiz/presentation/screens/quiz_screen.dart`**

```dart
class QuizScreen extends ConsumerStatefulWidget {
  final String motifId;
  
  const QuizScreen({super.key, required this.motifId});
  
  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  int _currentQuestionIndex = 0;
  Map<String, String> _answers = {};
  DateTime? _startTime;
  bool _isSubmitting = false;
  
  @override
  void initState() {
    super.initState();
    _startTime = DateTime.now();
  }
  
  @override
  Widget build(BuildContext context) {
    final quizAsync = ref.watch(quizProvider(widget.motifId));
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Trắc nghiệm'),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 16),
              child: quizAsync.maybeWhen(
                data: (questions) => Text(
                  '${_currentQuestionIndex + 1}/${questions.length}',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                orElse: () => const SizedBox(),
              ),
            ),
          ),
        ],
      ),
      body: quizAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, s) => ErrorWidget(
          message: e.toString(),
          onRetry: () => ref.invalidate(quizProvider(widget.motifId)),
        ),
        data: (questions) {
          if (questions.isEmpty) {
            return const EmptyState(
              icon: Icons.quiz_outlined,
              title: 'Chưa có câu hỏi',
              message: 'Câu hỏi trắc nghiệm đang được cập nhật.',
            );
          }
          
          return Column(
            children: [
              // Progress bar
              LinearProgressIndicator(
                value: (_currentQuestionIndex + 1) / questions.length,
              ),
              
              // Question content
              Expanded(
                child: PageView.builder(
                  physics: const NeverScrollableScrollPhysics(),
                  controller: PageController(initialPage: _currentQuestionIndex),
                  itemCount: questions.length,
                  itemBuilder: (context, index) {
                    return QuestionCard(
                      question: questions[index],
                      selectedAnswer: _answers[questions[index].id],
                      onAnswerSelected: (answer) {
                        setState(() {
                          _answers[questions[index].id] = answer;
                        });
                      },
                    );
                  },
                ),
              ),
              
              // Navigation buttons
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    if (_currentQuestionIndex > 0)
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => setState(() {
                            _currentQuestionIndex--;
                          }),
                          child: const Text('Câu trước'),
                        ),
                      ),
                    if (_currentQuestionIndex > 0)
                      const SizedBox(width: 16),
                    Expanded(
                      child: _currentQuestionIndex < questions.length - 1
                          ? ElevatedButton(
                              onPressed: _answers.containsKey(
                                      questions[_currentQuestionIndex].id)
                                  ? () => setState(() {
                                        _currentQuestionIndex++;
                                      })
                                  : null,
                              child: const Text('Câu tiếp'),
                            )
                          : ElevatedButton(
                              onPressed: _answers.length == questions.length &&
                                      !_isSubmitting
                                  ? () => _submitQuiz(questions)
                                  : null,
                              child: _isSubmitting
                                  ? const SizedBox(
                                      width: 20,
                                      height: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Text('Nộp bài'),
                            ),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
  
  Future<void> _submitQuiz(List<QuizQuestion> questions) async {
    setState(() => _isSubmitting = true);
    
    final timeSpent = DateTime.now().difference(_startTime!).inSeconds;
    
    final result = await ref.read(quizSubmissionProvider.notifier).submit(
      motifId: widget.motifId,
      answers: _answers,
      timeSpentSeconds: timeSpent,
    );
    
    setState(() => _isSubmitting = false);
    
    if (result != null && mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => QuizResultScreen(
            result: result,
            questions: questions,
            answers: _answers,
          ),
        ),
      );
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Questions loaded from API
- [ ] Question navigation (next/previous)
- [ ] Progress bar shows completion
- [ ] Answer selection required before next
- [ ] Submit button after last question
- [ ] Timer tracking quiz duration

---

### Task 4.7: Implement Question Renderers

**Estimated Time:** 6 hours

**File: `lib/features/quiz/presentation/widgets/question_card.dart`**

```dart
class QuestionCard extends StatelessWidget {
  final QuizQuestion question;
  final String? selectedAnswer;
  final Function(String) onAnswerSelected;
  
  const QuestionCard({
    super.key,
    required this.question,
    this.selectedAnswer,
    required this.onAnswerSelected,
  });
  
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Question text
          Text(
            question.question,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          
          const SizedBox(height: 24),
          
          // Question-type specific renderer
          _buildAnswerOptions(context),
        ],