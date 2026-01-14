import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_constants.dart';
import '../../../shared/services/xp_celebration_service.dart';
import '../../../shared/widgets/xp_gain_handler.dart';

/// Example screen demonstrating XP celebration system
class XpCelebrationDemo extends ConsumerStatefulWidget {
  const XpCelebrationDemo({super.key});

  @override
  ConsumerState<XpCelebrationDemo> createState() => _XpCelebrationDemoState();
}

class _XpCelebrationDemoState extends ConsumerState<XpCelebrationDemo> {
  int _currentXp = 0;

  void _testSmallCelebration() {
    context.showXpCelebration(
      xpGained: AppConstants.discoveryXp,
      oldTotalXp: _currentXp,
      newTotalXp: _currentXp + AppConstants.discoveryXp,
    );
    setState(() {
      _currentXp += AppConstants.discoveryXp;
    });
  }

  void _testMediumCelebration() {
    context.showXpCelebration(
      xpGained: AppConstants.lessonXp,
      oldTotalXp: _currentXp,
      newTotalXp: _currentXp + AppConstants.lessonXp,
    );
    setState(() {
      _currentXp += AppConstants.lessonXp;
    });
  }

  void _testLargeCelebration() {
    context.showXpCelebration(
      xpGained: AppConstants.urnExamXp,
      oldTotalXp: _currentXp,
      newTotalXp: _currentXp + AppConstants.urnExamXp,
    );
    setState(() {
      _currentXp += AppConstants.urnExamXp;
    });
  }

  void _testLevelUp() {
    // Simulate level up from rank 1 to rank 2
    const oldXp = 90;
    const newXp = 110; // Crosses threshold of 100
    
    context.showXpCelebration(
      xpGained: newXp - oldXp,
      oldTotalXp: oldXp,
      newTotalXp: newXp,
      badges: ['level_up_bonus'],
    );
    
    setState(() {
      _currentXp = newXp;
    });
  }

  void _reset() {
    setState(() {
      _currentXp = 0;
    });
  }

  @override
  Widget build(BuildContext context) {
    final currentRank = AppConstants.getRankForXp(_currentXp);
    final nextRank = AppConstants.getNextRank(_currentXp);

    return Scaffold(
      appBar: AppBar(
        title: const Text('XP Celebration Demo'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _reset,
            tooltip: 'Reset XP',
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Current XP Display
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Text(
                      'Current XP: $_currentXp',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Rank: ${currentRank['name']} (Level ${currentRank['level']})',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    if (nextRank != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Next: ${nextRank['name']} at ${nextRank['xp']} XP',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Test Buttons
            const Text(
              'Test Celebrations:',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),

            ElevatedButton.icon(
              onPressed: _testSmallCelebration,
              icon: const Icon(Icons.star),
              label: Text('Small (+${AppConstants.discoveryXp} XP)'),
            ),
            const SizedBox(height: 12),

            ElevatedButton.icon(
              onPressed: _testMediumCelebration,
              icon: const Icon(Icons.star),
              label: Text('Medium (+${AppConstants.lessonXp} XP)'),
            ),
            const SizedBox(height: 12),

            ElevatedButton.icon(
              onPressed: _testLargeCelebration,
              icon: const Icon(Icons.star),
              label: Text('Large (+${AppConstants.urnExamXp} XP)'),
            ),
            const SizedBox(height: 12),

            ElevatedButton.icon(
              onPressed: _testLevelUp,
              icon: const Icon(Icons.military_tech),
              label: const Text('Level Up (90 → 110 XP)'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

