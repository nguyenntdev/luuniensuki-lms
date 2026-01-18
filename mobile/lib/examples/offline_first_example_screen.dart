import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/services/sync_service.dart';
import '../../../features/lesson/data/repositories/lesson_repository.dart';
import '../../../features/urn_viewer/data/repositories/urn_repository.dart';

class OfflineFirstExampleScreen extends ConsumerWidget {
  const OfflineFirstExampleScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendingCount = ref.watch(pendingSyncCountProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Offline-First Example'),
        actions: [
          if (pendingCount.hasValue && pendingCount.value! > 0)
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Center(
                child: Badge(
                  label: Text('${pendingCount.value}'),
                  child: IconButton(
                    icon: const Icon(Icons.sync),
                    onPressed: () async {
                      final notifier = ref.read(syncNotifierProvider.notifier);
                      await notifier.triggerSync();
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Sync completed')),
                        );
                      }
                    },
                  ),
                ),
              ),
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSection(
            context,
            title: 'Read Operations (Offline-First)',
            children: [
              _ExampleReadUrns(),
              const SizedBox(height: 16),
              _ExampleReadUrnDetail(),
            ],
          ),
          const SizedBox(height: 24),
          _buildSection(
            context,
            title: 'Write Operations (Auto Sync)',
            children: [
              _ExampleCompleteLesson(),
              const SizedBox(height: 16),
              _ExampleSubmitQuiz(),
            ],
          ),
          const SizedBox(height: 24),
          _buildSection(
            context,
            title: 'Sync Status',
            children: [
              _ExampleSyncStatus(),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required String title,
    required List<Widget> children,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _ExampleReadUrns extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urnsAsync = ref.watch(urnsOfflineFirstProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Fetch Urns List',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        urnsAsync.when(
          data: (urns) => Text('Loaded ${urns.length} urns'),
          loading: () => const CircularProgressIndicator(),
          error: (error, _) => Text(
            'Error: $error',
            style: const TextStyle(color: Colors.red),
          ),
        ),
        const SizedBox(height: 8),
        ElevatedButton(
          onPressed: () => ref.invalidate(urnsOfflineFirstProvider),
          child: const Text('Refresh'),
        ),
      ],
    );
  }
}

class _ExampleReadUrnDetail extends ConsumerStatefulWidget {
  @override
  ConsumerState<_ExampleReadUrnDetail> createState() => _ExampleReadUrnDetailState();
}

class _ExampleReadUrnDetailState extends ConsumerState<_ExampleReadUrnDetail> {
  String? selectedSlug;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Fetch Urn Detail',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        TextField(
          decoration: const InputDecoration(
            labelText: 'Urn Slug',
            hintText: 'Enter urn slug',
          ),
          onChanged: (value) => selectedSlug = value,
        ),
        const SizedBox(height: 8),
        ElevatedButton(
          onPressed: selectedSlug == null || selectedSlug!.isEmpty
              ? null
              : () {
                  setState(() {});
                },
          child: const Text('Load Detail'),
        ),
        if (selectedSlug != null && selectedSlug!.isNotEmpty) ...[
          const SizedBox(height: 8),
          Consumer(
            builder: (context, ref, _) {
              final urnDetailAsync = ref.watch(urnDetailOfflineFirstProvider(selectedSlug!));
              return urnDetailAsync.when(
                data: (detail) => Text('Loaded: ${detail.name}'),
                loading: () => const CircularProgressIndicator(),
                error: (error, _) => Text(
                  'Error: $error',
                  style: const TextStyle(color: Colors.red),
                ),
              );
            },
          ),
        ],
      ],
    );
  }
}

class _ExampleCompleteLesson extends ConsumerStatefulWidget {
  @override
  ConsumerState<_ExampleCompleteLesson> createState() => _ExampleCompleteLessonState();
}

class _ExampleCompleteLessonState extends ConsumerState<_ExampleCompleteLesson> {
  String? motifId;

  @override
  Widget build(BuildContext context) {
    final completionState = ref.watch(lessonCompletionOfflineFirstProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Complete Lesson',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        TextField(
          decoration: const InputDecoration(
            labelText: 'Motif ID',
            hintText: 'Enter motif ID',
          ),
          onChanged: (value) => motifId = value,
        ),
        const SizedBox(height: 8),
        ElevatedButton(
          onPressed: motifId == null || motifId!.isEmpty || completionState.isLoading
              ? null
              : () async {
                  final notifier = ref.read(lessonCompletionOfflineFirstProvider.notifier);
                  final result = await notifier.completeLesson(motifId!);
                  
                  if (context.mounted) {
                    if (result != null) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Lesson completed! XP: ${result.xpEarned}'),
                        ),
                      );
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Queued for sync when online'),
                          backgroundColor: Colors.orange,
                        ),
                      );
                    }
                  }
                },
          child: completionState.isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Complete Lesson'),
        ),
      ],
    );
  }
}

class _ExampleSubmitQuiz extends ConsumerStatefulWidget {
  @override
  ConsumerState<_ExampleSubmitQuiz> createState() => _ExampleSubmitQuizState();
}

class _ExampleSubmitQuizState extends ConsumerState<_ExampleSubmitQuiz> {
  String? motifId;

  @override
  Widget build(BuildContext context) {
    final quizState = ref.watch(quizSubmissionOfflineFirstProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Submit Quiz',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        const Text(
          'Note: This is a demo. In real usage, pass actual quiz answers.',
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
        const SizedBox(height: 8),
        TextField(
          decoration: const InputDecoration(
            labelText: 'Motif ID',
            hintText: 'Enter motif ID',
          ),
          onChanged: (value) => motifId = value,
        ),
        const SizedBox(height: 8),
        ElevatedButton(
          onPressed: motifId == null || motifId!.isEmpty || quizState.isLoading
              ? null
              : () async {
                  final notifier = ref.read(quizSubmissionOfflineFirstProvider.notifier);
                  
                  // In real usage, get actual quiz answers
                  final result = await notifier.submitQuiz(
                    motifId: motifId!,
                    answers: [], // Demo: empty answers
                  );
                  
                  if (context.mounted) {
                    if (result != null) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(
                            result.passed ? 'Quiz passed!' : 'Quiz failed. Try again.',
                          ),
                          backgroundColor: result.passed ? Colors.green : Colors.red,
                        ),
                      );
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Queued for sync when online'),
                          backgroundColor: Colors.orange,
                        ),
                      );
                    }
                  }
                },
          child: quizState.isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Submit Quiz'),
        ),
      ],
    );
  }
}

class _ExampleSyncStatus extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendingCount = ref.watch(pendingSyncCountProvider);
    final syncState = ref.watch(syncNotifierProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Sync Status',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        pendingCount.when(
          data: (count) => Text(
            'Pending operations: $count',
            style: TextStyle(
              color: count > 0 ? Colors.orange : Colors.green,
              fontWeight: FontWeight.bold,
            ),
          ),
          loading: () => const Text('Loading...'),
          error: (error, _) => Text('Error: $error'),
        ),
        const SizedBox(height: 8),
        syncState.when(
          data: (_) => const Text('Sync idle'),
          loading: () => const Row(
            children: [
              SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              SizedBox(width: 8),
              Text('Syncing...'),
            ],
          ),
          error: (error, _) => Text(
            'Sync error: $error',
            style: const TextStyle(color: Colors.red),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            ElevatedButton(
              onPressed: () async {
                final notifier = ref.read(syncNotifierProvider.notifier);
                await notifier.triggerSync();
              },
              child: const Text('Trigger Sync'),
            ),
            const SizedBox(width: 8),
            OutlinedButton(
              onPressed: () async {
                final notifier = ref.read(syncNotifierProvider.notifier);
                await notifier.clearQueue();
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Queue cleared')),
                  );
                }
              },
              child: const Text('Clear Queue'),
            ),
          ],
        ),
      ],
    );
  }
}

