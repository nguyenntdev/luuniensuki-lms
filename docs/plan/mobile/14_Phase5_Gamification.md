# 14_Phase5_Gamification.md — Gamification System

## Overview

Phase 5 implements the complete gamification system: XP display, badges collection, streak tracking, leaderboard, and quest progression.

**Duration:** 2 weeks  
**Priority:** P1 (High)  
**Prerequisites:** Phase 4 (Learning Flow) completed

---

## Week 1: XP, Ranks, and Badges

### Task 5.1: Implement XP Display Components

**Estimated Time:** 3 hours

**File: `lib/shared/widgets/xp_badge.dart`**

```dart
enum XpBadgeSize { small, medium, large }

class XpBadge extends StatelessWidget {
  final int amount;
  final XpBadgeSize size;
  final bool showPlus;
  
  const XpBadge({
    super.key,
    required this.amount,
    this.size = XpBadgeSize.medium,
    this.showPlus = true,
  });
  
  @override
  Widget build(BuildContext context) {
    final (iconSize, fontSize, padding) = switch (size) {
      XpBadgeSize.small => (12.0, 12.0, 4.0),
      XpBadgeSize.medium => (16.0, 14.0, 8.0),
      XpBadgeSize.large => (24.0, 18.0, 12.0),
    };
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: padding, vertical: padding / 2),
      decoration: BoxDecoration(
        color: AppColors.xpGold.withOpacity(0.2),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.xpGold, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.star, color: AppColors.xpGold, size: iconSize),
          const SizedBox(width: 4),
          Text(
            '${showPlus ? '+' : ''}$amount XP',
            style: TextStyle(
              color: AppColors.xpGold,
              fontSize: fontSize,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
```

**File: `lib/shared/widgets/xp_progress_bar.dart`**

```dart
class XpProgressBar extends StatelessWidget {
  final int currentXp;
  final int currentRankXp;
  final int nextRankXp;
  final String currentRankName;
  final String? nextRankName;
  
  const XpProgressBar({
    super.key,
    required this.currentXp,
    required this.currentRankXp,
    required this.nextRankXp,
    required this.currentRankName,
    this.nextRankName,
  });
  
  double get progress {
    if (nextRankXp <= currentRankXp) return 1.0;
    return (currentXp - currentRankXp) / (nextRankXp - currentRankXp);
  }
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              currentRankName,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: AppColors.primary,
              ),
            ),
            Text(
              '$currentXp XP',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: AppColors.xpGold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 12,
            backgroundColor: theme.colorScheme.surfaceVariant,
            valueColor: const AlwaysStoppedAnimation(AppColors.xpGold),
          ),
        ),
        if (nextRankName != null) ...[
          const SizedBox(height: 4),
          Text(
            '${nextRankXp - currentXp} XP còn thiếu để lên $nextRankName',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ],
    );
  }
}
```

**Acceptance Criteria:**
- [ ] XP badge shows amount with icon
- [ ] Progress bar shows rank progress
- [ ] Vietnamese rank names displayed
- [ ] Next rank requirements shown

---

### Task 5.2: Implement Rank Display

**Estimated Time:** 2 hours

**File: `lib/shared/widgets/rank_badge.dart`**

```dart
class RankBadge extends StatelessWidget {
  final Rank rank;
  final bool showXp;
  
  const RankBadge({
    super.key,
    required this.rank,
    this.showXp = false,
  });
  
  Color get _rankColor {
    return switch (rank.level) {
      1 => Colors.grey,
      2 => Colors.green,
      3 => Colors.blue,
      4 => Colors.purple,
      5 => Colors.orange,
      6 => AppColors.xpGold,
      _ => AppColors.legendary,
    };
  }
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_rankColor.withOpacity(0.8), _rankColor],
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: _rankColor.withOpacity(0.4),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.military_tech, color: Colors.white, size: 16),
          const SizedBox(width: 4),
          Text(
            rank.name,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          if (showXp) ...[
            const SizedBox(width: 8),
            Text(
              '${rank.xp} XP',
              style: TextStyle(
                color: Colors.white.withOpacity(0.8),
                fontSize: 10,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
```

**Vietnamese Rank Names (from backend):**
1. Lính Mới (0 XP)
2. Thư Sinh (500 XP)
3. Nho Sinh (1500 XP)
4. Cử Nhân (3500 XP)
5. Tiến Sĩ (7000 XP)
6. Trạng Nguyên (12000 XP)
7. Đại Học Sĩ (20000 XP)
8. Thái Sư (35000 XP)
9. Sử Quan (50000 XP)

**Acceptance Criteria:**
- [ ] Rank badge with color gradient
- [ ] Vietnamese rank name displayed
- [ ] Level-appropriate colors

---

### Task 5.3: Implement Badges Grid

**Estimated Time:** 4 hours

**File: `lib/features/gamification/presentation/widgets/badges_grid.dart`**

```dart
class BadgesGrid extends ConsumerWidget {
  final bool showOnlyEarned;
  
  const BadgesGrid({super.key, this.showOnlyEarned = false});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final badgesAsync = ref.watch(allBadgesProvider);
    final earnedAsync = ref.watch(userBadgesProvider);
    
    return badgesAsync.when(
      loading: () => const BadgesGridSkeleton(),
      error: (e, s) => ErrorWidget(message: e.toString()),
      data: (allBadges) => earnedAsync.when(
        loading: () => const BadgesGridSkeleton(),
        error: (e, s) => ErrorWidget(message: e.toString()),
        data: (earnedBadges) {
          final earnedSlugs = earnedBadges.map((b) => b.slug).toSet();
          
          var badges = allBadges;
          if (showOnlyEarned) {
            badges = badges.where((b) => earnedSlugs.contains(b.slug)).toList();
          }
          
          if (badges.isEmpty) {
            return const EmptyState(
              icon: Icons.emoji_events_outlined,
              title: 'Chưa có huy hiệu',
              message: 'Hoàn thành các nhiệm vụ để nhận huy hiệu!',
            );
          }
          
          return GridView.builder(
            padding: const EdgeInsets.all(16),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              childAspectRatio: 0.8,
            ),
            itemCount: badges.length,
            itemBuilder: (context, index) {
              final badge = badges[index];
              final isEarned = earnedSlugs.contains(badge.slug);
              
              return BadgeCard(
                badge: badge,
                isEarned: isEarned,
                onTap: () => _showBadgeDetail(context, badge, isEarned),
              );
            },
          );
        },
      ),
    );
  }
  
  void _showBadgeDetail(BuildContext context, Badge badge, bool isEarned) {
    showModalBottomSheet(
      context: context,
      builder: (context) => BadgeDetailSheet(badge: badge, isEarned: isEarned),
    );
  }
}
```

**File: `lib/features/gamification/presentation/widgets/badge_card.dart`**

```dart
class BadgeCard extends StatelessWidget {
  final Badge badge;
  final bool isEarned;
  final VoidCallback onTap;
  
  const BadgeCard({
    super.key,
    required this.badge,
    required this.isEarned,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isEarned 
                  ? AppColors.primary.withOpacity(0.2) 
                  : theme.colorScheme.surfaceVariant,
              border: Border.all(
                color: isEarned ? AppColors.primary : Colors.transparent,
                width: 2,
              ),
            ),
            child: Center(
              child: Text(
                badge.iconUrl, // Emoji icon
                style: TextStyle(
                  fontSize: 32,
                  color: isEarned ? null : Colors.grey,
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            badge.name,
            style: theme.textTheme.labelSmall?.copyWith(
              color: isEarned 
                  ? theme.colorScheme.onSurface 
                  : theme.colorScheme.onSurfaceVariant,
              fontWeight: isEarned ? FontWeight.bold : null,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (isEarned)
            XpBadge(amount: badge.xpBonus, size: XpBadgeSize.small),
        ],
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Grid of all badges
- [ ] Earned badges highlighted
- [ ] Unearned badges grayed out
- [ ] Tap to show detail sheet
- [ ] XP bonus displayed for earned

---

### Task 5.4: Implement Streak Display

**Estimated Time:** 3 hours

**File: `lib/features/gamification/presentation/widgets/streak_card.dart`**

```dart
class StreakCard extends ConsumerWidget {
  const StreakCard({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(userStatsProvider);
    
    return statsAsync.when(
      loading: () => const ShimmerBox(height: 100),
      error: (e, s) => const SizedBox(),
      data: (stats) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Streak icon with animation
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.8, end: 1.0),
                duration: const Duration(milliseconds: 500),
                builder: (context, value, child) => Transform.scale(
                  scale: value,
                  child: child,
                ),
                child: Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: [
                        AppColors.streakOrange,
                        AppColors.streakOrange.withOpacity(0.7),
                      ],
                    ),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.local_fire_department, 
                                 color: Colors.white, size: 24),
                      Text(
                        '${stats.currentStreak}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Chuỗi ${stats.currentStreak} ngày',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Kỷ lục: ${stats.longestStreak} ngày',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    if (stats.streakFreezes > 0) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.ac_unit, 
                                     color: Colors.blue, size: 16),
                          const SizedBox(width: 4),
                          Text(
                            '${stats.streakFreezes} lần đóng băng',
                            style: const TextStyle(
                              color: Colors.blue,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Current streak count displayed
- [ ] Fire icon with animation
- [ ] Longest streak shown
- [ ] Streak freezes count (if any)

---

## Week 2: Leaderboard and Quests

### Task 5.5: Implement Leaderboard

**Estimated Time:** 4 hours

**File: `lib/features/gamification/presentation/widgets/leaderboard_list.dart`**

```dart
class LeaderboardList extends ConsumerWidget {
  const LeaderboardList({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final leaderboardAsync = ref.watch(leaderboardProvider);
    final currentUser = ref.watch(authNotifierProvider).user;
    
    return leaderboardAsync.when(
      loading: () => const LeaderboardSkeleton(),
      error: (e, s) => ErrorWidget(message: e.toString()),
      data: (entries) {
        if (entries.isEmpty) {
          return const EmptyState(
            icon: Icons.leaderboard_outlined,
            title: 'Chưa có dữ liệu',
            message: 'Hãy là người đầu tiên lên bảng xếp hạng!',
          );
        }
        
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: entries.length,
          itemBuilder: (context, index) {
            final entry = entries[index];
            final isCurrentUser = currentUser?.id == entry.userId;
            
            return LeaderboardTile(
              entry: entry,
              isCurrentUser: isCurrentUser,
              onTap: () => context.goNamed(
                RouteNames.userPublicProfile,
                pathParameters: {'userId': entry.userId},
              ),
            );
          },
        );
      },
    );
  }
}

class LeaderboardTile extends StatelessWidget {
  final LeaderboardEntry entry;
  final bool isCurrentUser;
  final VoidCallback onTap;
  
  const LeaderboardTile({
    super.key,
    required this.entry,
    required this.isCurrentUser,
    required this.onTap,
  });
  
  Widget _buildRankBadge() {
    final (icon, color) = switch (entry.rank) {
      1 => (Icons.emoji_events, Colors.amber),
      2 => (Icons.emoji_events, Colors.grey[400]!),
      3 => (Icons.emoji_events, Colors.brown),
      _ => (null, Colors.transparent),
    };
    
    if (icon != null) {
      return Icon(icon, color: color, size: 28);
    }
    
    return Container(
      width: 28,
      height: 28,
      alignment: Alignment.center,
      child: Text(
        '${entry.rank}',
        style: const TextStyle(
          fontWeight: FontWeight.bold,
          fontSize: 16,
        ),
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Card(
      color: isCurrentUser ? AppColors.primary.withOpacity(0.1) : null,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              _buildRankBadge(),
              const SizedBox(width: 12),
              CircleAvatar(
                radius: 20,
                backgroundImage: entry.avatarUrl != null
                    ? CachedNetworkImageProvider(entry.avatarUrl!)
                    : null,
                child: entry.avatarUrl == null
                    ? Text(entry.displayName[0].toUpperCase())
                    : null,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      entry.displayName,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: isCurrentUser ? FontWeight.bold : null,
                      ),
                    ),
                    Text(
                      '${entry.badgeCount} huy hiệu',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${entry.totalXp}',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppColors.xpGold,
                    ),
                  ),
                  Text(
                    'XP',
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Top users displayed with ranks
- [ ] Medal icons for top 3
- [ ] Current user highlighted
- [ ] XP and badge count shown
- [ ] Tap to view profile

---

### Task 5.6: Implement Quests List

**Estimated Time:** 6 hours

**File: `lib/features/quests/presentation/widgets/quests_list.dart`**

```dart
class QuestsList extends ConsumerWidget {
  const QuestsList({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final questsAsync = ref.watch(questsProvider);
    
    return questsAsync.when(
      loading: () => const QuestsListSkeleton(),
      error: (e, s) => ErrorWidget(
        message: e.toString(),
        onRetry: () => ref.invalidate(questsProvider),
      ),
      data: (quests) {
        if (quests.isEmpty) {
          return const EmptyState(
            icon: Icons.flag_outlined,
            title: 'Chưa có nhiệm vụ',
            message: 'Các nhiệm vụ sẽ sớm được cập nhật!',
          );
        }
        
        // Group by category
        final grouped = <String, List<Quest>>{};
        for (final quest in quests) {
          grouped.putIfAbsent(quest.category ?? 'other', () => []).add(quest);
        }
        
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: quests.length,
          itemBuilder: (context, index) {
            final quest = quests[index];
            return QuestCard(
              quest: quest,
              onTap: () => context.goNamed(
                RouteNames.questDetail,
                pathParameters: {'questSlug': quest.slug},
              ),
            );
          },
        );
      },
    );
  }
}

class QuestCard extends StatelessWidget {
  final Quest quest;
  final VoidCallback onTap;
  
  const QuestCard({
    super.key,
    required this.quest,
    required this.onTap,
  });
  
  Color get _statusColor {
    if (quest.isLocked) return Colors.grey;
    return switch (quest.status) {
      'completed' => AppColors.discovered,
      'in_progress' => AppColors.primary,
      _ => AppColors.textSecondary,
    };
  }
  
  IconData get _statusIcon {
    if (quest.isLocked) return Icons.lock;
    return switch (quest.status) {
      'completed' => Icons.check_circle,
      'in_progress' => Icons.pending,
      _ => Icons.flag,
    };
  }
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: quest.isLocked ? null : onTap,
        borderRadius: BorderRadius.circular(12),
        child: Opacity(
          opacity: quest.isLocked ? 0.5 : 1.0,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(_statusIcon, color: _statusColor, size: 24),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        quest.name,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    if (quest.rewards.isNotEmpty)
                      XpBadge(
                        amount: quest.rewards
                            .where((r) => r.rewardType == 'xp')
                            .fold(0, (sum, r) => sum + (r.amount ?? 0)),
                        size: XpBadgeSize.small,
                      ),
                  ],
                ),
                if (quest.description != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    quest.description!,
                    style: theme.textTheme.bodySmall,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                if (quest.isLocked && quest.lockReason != null) ...[
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.info_outline, size: 14, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text(
                        quest.lockReason!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: Colors.grey,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                ],
                if (!quest.isLocked && quest.status != 'not_started') ...[
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: quest.progressPercent / 100,
                      minHeight: 6,
                      backgroundColor: theme.colorScheme.surfaceVariant,
                      valueColor: AlwaysStoppedAnimation(_statusColor),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${quest.progressPercent.toInt()}% hoàn thành',
                    style: theme.textTheme.labelSmall,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] All quests displayed
- [ ] Locked quests grayed out with reason
- [ ] Progress bar for in-progress quests
- [ ] XP reward shown
- [ ] Navigate to quest detail on tap

---

### Task 5.7: Implement Quest Detail Screen

**Estimated Time:** 4 hours

**File: `lib/features/quests/presentation/screens/quest_detail_screen.dart`**

```dart
class QuestDetailScreen extends ConsumerWidget {
  final String questSlug;
  
  const QuestDetailScreen({super.key, required this.questSlug});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final questAsync = ref.watch(questDetailProvider(questSlug));
    
    return Scaffold(
      appBar: AppBar(title: const Text('Chi tiết nhiệm vụ')),
      body: questAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, s) => ErrorWidget(message: e.toString()),
        data: (quest) => SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Text(
                quest.name,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (quest.description != null) ...[
                const SizedBox(height: 8),
                Text(quest.description!),
              ],
              
              const SizedBox(height: 24),
              
              // Progress
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Tiến độ',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  Text(
                    '${quest.progressPercent.toInt()}%',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  value: quest.progressPercent / 100,
                  minHeight: 12,
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Steps
              Text(
                'Các bước',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              ...quest.steps.map((step) => QuestStepCard(step: step)),
              
              const SizedBox(height: 24),
              
              // Rewards
              Text(
                'Phần thưởng',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: quest.rewards.map((reward) {
                  if (reward.rewardType == 'xp') {
                    return XpBadge(amount: reward.amount ?? 0);
                  }
                  if (reward.rewardType == 'badge' && reward.badgeSlug != null) {
                    return Chip(label: Text(reward.badgeSlug!));
                  }
                  return const SizedBox();
                }).toList(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Quest name and description
- [ ] Overall progress bar
- [ ] Steps with objectives
- [ ] Rewards displayed
- [ ] Objective completion status

---

## Phase 5 Checklist

### XP & Ranks
- [ ] P5-X1: XP badge component
- [ ] P5-X2: XP progress bar
- [ ] P5-X3: Rank badge with colors
- [ ] P5-X4: XP animation on earn

### Badges
- [ ] P5-B1: Badges grid view
- [ ] P5-B2: Badge card (earned/unearned)
- [ ] P5-B3: Badge detail sheet
- [ ] P5-B4: Badge earn animation

### Streaks
- [ ] P5-S1: Streak card with fire icon
- [ ] P5-S2: Streak freeze display
- [ ] P5-S3: