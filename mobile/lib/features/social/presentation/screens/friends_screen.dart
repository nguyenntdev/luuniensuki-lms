import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../../shared/widgets/shimmer/shimmer_skeleton.dart';
import '../providers/friends_provider.dart';
import '../widgets/friend_card.dart';
import '../widgets/friend_request_card.dart';

/// Friends screen showing friends list and friend requests
class FriendsScreen extends ConsumerStatefulWidget {
  const FriendsScreen({super.key});

  @override
  ConsumerState<FriendsScreen> createState() => _FriendsScreenState();
}

class _FriendsScreenState extends ConsumerState<FriendsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final friendsState = ref.watch(friendsNotifierProvider);

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => context.pop(),
          ),
          title: const Text(
            'Bạn Bè',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          actions: [
            // Add friend button
            IconButton(
              icon: const Icon(Icons.person_add, color: Colors.white),
              onPressed: () => _showAddFriendDialog(context),
            ),
            // Mock data button (for demo)
            IconButton(
              icon: const Icon(Icons.refresh, color: Colors.white70),
              onPressed: () {
                ref.read(friendsNotifierProvider.notifier).addMockFriends();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Đã thêm dữ liệu mẫu'),
                    duration: Duration(seconds: 2),
                  ),
                );
              },
            ),
          ],
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(48),
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: TabBar(
                controller: _tabController,
                indicator: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  gradient: const LinearGradient(
                    colors: [
                      AppColors.primary,
                      AppColors.primaryDark,
                    ],
                  ),
                ),
                indicatorSize: TabBarIndicatorSize.tab,
                labelColor: Colors.white,
                unselectedLabelColor: Colors.white60,
                tabs: [
                  Tab(
                    text: 'Bạn Bè (${friendsState.acceptedFriends.length})',
                  ),
                  Tab(
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text('Lời Mời'),
                        if (friendsState.pendingRequestsCount > 0) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.error,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${friendsState.pendingRequestsCount}',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildFriendsList(friendsState),
            _buildRequestsList(friendsState),
          ],
        ),
      ),
    );
  }

  Widget _buildFriendsList(FriendsState state) {
    if (state.isLoading) {
      return _buildFriendsShimmerList();
    }

    if (state.acceptedFriends.isEmpty) {
      return _buildEmptyState(
        icon: Icons.people_outline,
        title: 'Chưa có bạn bè',
        subtitle: 'Thêm bạn bè để cùng học tập và thi đua!',
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: state.acceptedFriends.length,
      separatorBuilder: (context, index) => AppSpacing.verticalSpaceMD,
      itemBuilder: (context, index) {
        final friend = state.acceptedFriends[index];
        return FriendCard(
          friend: friend,
          onRemove: () => _confirmRemoveFriend(friend),
        );
      },
    );
  }

  Widget _buildRequestsList(FriendsState state) {
    if (state.isLoading) {
      return _buildRequestsShimmerList();
    }

    if (state.incomingRequests.isEmpty) {
      return _buildEmptyState(
        icon: Icons.inbox_outlined,
        title: 'Không có lời mời',
        subtitle: 'Lời mời kết bạn sẽ hiển thị ở đây',
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: state.incomingRequests.length,
      separatorBuilder: (context, index) => AppSpacing.verticalSpaceMD,
      itemBuilder: (context, index) {
        final request = state.incomingRequests[index];
        return FriendRequestCard(
          request: request,
          onAccept: () => _acceptRequest(request),
          onReject: () => _rejectRequest(request),
        );
      },
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    AppColors.primary.withOpacity(0.3),
                    AppColors.primaryDark.withOpacity(0.1),
                  ],
                ),
              ),
              child: Icon(
                icon,
                size: 64,
                color: Colors.white54,
              ),
            ),
            AppSpacing.verticalSpaceLG,
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            AppSpacing.verticalSpaceSM,
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14,
                color: Colors.white60,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showAddFriendDialog(BuildContext context) {
    final controller = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
        ),
        title: const Text(
          'Thêm bạn bè',
          style: TextStyle(color: Colors.white),
        ),
        content: TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'Nhập tên người dùng...',
            hintStyle: const TextStyle(color: Colors.white54),
            filled: true,
            fillColor: Colors.white.withOpacity(0.1),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          ElevatedButton(
            onPressed: () {
              // TODO: Implement search and send request
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Tính năng đang phát triển'),
                ),
              );
            },
            child: const Text('Gửi lời mời'),
          ),
        ],
      ),
    );
  }

  void _confirmRemoveFriend(friend) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
        ),
        title: const Text(
          'Xác nhận',
          style: TextStyle(color: Colors.white),
        ),
        content: Text(
          'Bạn có chắc muốn hủy kết bạn với ${friend.displayName}?',
          style: const TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          ElevatedButton(
            onPressed: () {
              ref.read(friendsNotifierProvider.notifier).removeFriend(friend);
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
            ),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
  }

  Future<void> _acceptRequest(request) async {
    await ref
        .read(friendsNotifierProvider.notifier)
        .acceptFriendRequest(request);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Đã chấp nhận lời mời từ ${request.fromUserName}'),
          backgroundColor: AppColors.success,
        ),
      );
    }
  }

  Future<void> _rejectRequest(request) async {
    await ref
        .read(friendsNotifierProvider.notifier)
        .rejectFriendRequest(request);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã từ chối lời mời kết bạn'),
        ),
      );
    }
  }

  Widget _buildFriendsShimmerList() {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 5,
      separatorBuilder: (context, index) => AppSpacing.verticalSpaceMD,
      itemBuilder: (context, index) => GlassContainer(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Avatar shimmer
              ShimmerSkeleton(
                width: 56,
                height: 56,
                borderRadius: BorderRadius.circular(28),
              ),

              AppSpacing.horizontalSpaceMD,

              // Friend info shimmer
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Name shimmer
                    ShimmerSkeleton(
                      width: 120,
                      height: 16,
                      borderRadius: BorderRadius.circular(4),
                    ),

                    AppSpacing.verticalSpaceXS,

                    // Stats row shimmer
                    Row(
                      children: [
                        ShimmerSkeleton(
                          width: 60,
                          height: 20,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        AppSpacing.horizontalSpaceSM,
                        ShimmerSkeleton(
                          width: 50,
                          height: 20,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        AppSpacing.horizontalSpaceSM,
                        ShimmerSkeleton(
                          width: 55,
                          height: 20,
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              // More icon shimmer
              ShimmerSkeleton(
                width: 24,
                height: 24,
                borderRadius: BorderRadius.circular(12),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRequestsShimmerList() {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 3,
      separatorBuilder: (context, index) => AppSpacing.verticalSpaceMD,
      itemBuilder: (context, index) => GlassContainer(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Avatar shimmer
              ShimmerSkeleton(
                width: 48,
                height: 48,
                borderRadius: BorderRadius.circular(24),
              ),

              AppSpacing.horizontalSpaceMD,

              // User info shimmer
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Name shimmer
                    ShimmerSkeleton(
                      width: 100,
                      height: 16,
                      borderRadius: BorderRadius.circular(4),
                    ),

                    AppSpacing.verticalSpaceXS,

                    // Time ago shimmer
                    ShimmerSkeleton(
                      width: 70,
                      height: 12,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ],
                ),
              ),

              // Action buttons shimmer
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ShimmerSkeleton(
                    width: 40,
                    height: 40,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  const SizedBox(width: 8),
                  ShimmerSkeleton(
                    width: 40,
                    height: 40,
                    borderRadius: BorderRadius.circular(20),
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
