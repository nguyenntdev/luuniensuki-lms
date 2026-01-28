import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_button.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../../shared/widgets/glass/glass_text_field.dart';
import '../../../auth/presentation/providers/auth_provider.dart';

/// Personal Info settings screen for editing user profile
class PersonalInfoScreen extends ConsumerStatefulWidget {
  const PersonalInfoScreen({super.key});

  @override
  ConsumerState<PersonalInfoScreen> createState() => _PersonalInfoScreenState();
}

class _PersonalInfoScreenState extends ConsumerState<PersonalInfoScreen>
    with SingleTickerProviderStateMixin {
  late TextEditingController _displayNameController;
  late TextEditingController _usernameController;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  bool _isLoading = false;
  bool _isProfilePublic = false;
  bool _hasChanges = false;

  @override
  void initState() {
    super.initState();

    // Initialize controllers
    final user = ref.read(authNotifierProvider).user;
    _displayNameController = TextEditingController(text: user?.displayName ?? '');
    _usernameController = TextEditingController(text: user?.username ?? '');
    _isProfilePublic = user?.isProfilePublic ?? false;

    // Add listeners to detect changes
    _displayNameController.addListener(_onFieldChanged);
    _usernameController.addListener(_onFieldChanged);

    // Setup animations
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeOut,
      ),
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.2),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeOutCubic,
      ),
    );

    _animationController.forward();
  }

  void _onFieldChanged() {
    final user = ref.read(authNotifierProvider).user;
    if (user == null) return;

    final hasChanges = _displayNameController.text.trim() != user.displayName ||
        _usernameController.text.trim() != (user.username ?? '') ||
        _isProfilePublic != user.isProfilePublic;

    if (hasChanges != _hasChanges) {
      setState(() {
        _hasChanges = hasChanges;
      });
    }
  }

  @override
  void dispose() {
    _displayNameController.dispose();
    _usernameController.dispose();
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _saveChanges() async {
    final user = ref.read(authNotifierProvider).user;
    if (user == null || !_hasChanges) return;

    setState(() {
      _isLoading = true;
    });

    final displayName = _displayNameController.text.trim();
    final username = _usernameController.text.trim();

    // Validate
    if (displayName.isEmpty) {
      _showErrorSnackbar('Tên hiển thị không được để trống');
      setState(() {
        _isLoading = false;
      });
      return;
    }

    // Update profile
    final authNotifier = ref.read(authNotifierProvider.notifier);
    final success = await authNotifier.updateProfile(
      displayName: displayName != user.displayName ? displayName : null,
      username: username.isNotEmpty && username != user.username ? username : null,
      isProfilePublic: _isProfilePublic != user.isProfilePublic ? _isProfilePublic : null,
    );

    setState(() {
      _isLoading = false;
    });

    if (success) {
      setState(() {
        _hasChanges = false;
      });
      _showSuccessSnackbar('Cập nhật thông tin thành công');
    } else {
      _showErrorSnackbar('Cập nhật thất bại. Vui lòng thử lại');
    }
  }

  void _showSuccessSnackbar(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showErrorSnackbar(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final user = authState.user;

    if (user == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: FadeTransition(
            opacity: _fadeAnimation,
            child: SlideTransition(
              position: _slideAnimation,
              child: CustomScrollView(
                physics: const BouncingScrollPhysics(),
                slivers: [
                  // App Bar
                  _buildAppBar(context),

                  // Content
                  SliverPadding(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    sliver: SliverList(
                      delegate: SliverChildListDelegate([
                        // Avatar Section
                        _buildAvatarSection(user),

                        AppSpacing.verticalSpaceLG,

                        // Display Name Field
                        _buildDisplayNameField(),

                        AppSpacing.verticalSpaceMD,

                        // Username Field
                        _buildUsernameField(),

                        AppSpacing.verticalSpaceMD,

                        // Email Field (read-only)
                        _buildEmailField(user),

                        AppSpacing.verticalSpaceLG,

                        // Profile Visibility Toggle
                        _buildProfileVisibilitySection(),

                        AppSpacing.verticalSpaceXL,

                        // Save Button
                        _buildSaveButton(),

                        const SizedBox(height: 40),
                      ]),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAppBar(BuildContext context) {
    return SliverAppBar(
      expandedHeight: 0,
      pinned: false,
      floating: true,
      backgroundColor: Colors.transparent,
      elevation: 0,
      leading: IconButton(
        icon: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: Colors.white.withOpacity(0.2),
              width: 1,
            ),
          ),
          child: const Icon(
            Icons.arrow_back_ios_new,
            color: Colors.white,
            size: 20,
          ),
        ),
        onPressed: () => context.pop(),
      ),
      title: Text(
        'Thông tin cá nhân',
        style: TextStyle(
          color: Colors.white.withOpacity(0.95),
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildAvatarSection(user) {
    return Center(
      child: Column(
        children: [
          // Avatar Circle
          Stack(
            children: [
              // Avatar
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: [
                      AppColors.primary.withOpacity(0.3),
                      AppColors.primaryDark.withOpacity(0.1),
                    ],
                  ),
                  border: Border.all(
                    color: AppColors.primary.withOpacity(0.5),
                    width: 3,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.3),
                      blurRadius: 20,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: user.avatarUrl != null && user.avatarUrl!.isNotEmpty
                    ? ClipOval(
                        child: CachedNetworkImage(
                          imageUrl: user.avatarUrl!,
                          fit: BoxFit.cover,
                          placeholder: (context, url) => const Center(
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          errorWidget: (context, url, error) {
                            return _buildDefaultAvatar(user);
                          },
                        ),
                      )
                    : _buildDefaultAvatar(user),
              ),

              // Camera Icon Button
              Positioned(
                bottom: 0,
                right: 0,
                child: GestureDetector(
                  onTap: () {
                    // TODO: Implement avatar upload
                    _showErrorSnackbar('Tính năng đang phát triển');
                  },
                  child: Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(
                        colors: [AppColors.primary, AppColors.primaryLight],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      border: Border.all(
                        color: Colors.white.withOpacity(0.3),
                        width: 2,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.primary.withOpacity(0.4),
                          blurRadius: 8,
                          spreadRadius: 1,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.camera_alt,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),
                ),
              ),
            ],
          ),

          AppSpacing.verticalSpaceSM,

          // Helper Text
          Text(
            'Nhấn vào biểu tượng để thay đổi ảnh đại diện',
            style: TextStyle(
              color: Colors.white.withOpacity(0.6),
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDefaultAvatar(user) {
    return Center(
      child: Text(
        user.displayName.isNotEmpty ? user.displayName[0].toUpperCase() : '?',
        style: TextStyle(
          fontSize: 48,
          fontWeight: FontWeight.bold,
          color: AppColors.primary.withOpacity(0.8),
        ),
      ),
    );
  }

  Widget _buildDisplayNameField() {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.person_outline,
                color: AppColors.primary.withOpacity(0.8),
                size: 20,
              ),
              AppSpacing.horizontalSpaceSM,
              Text(
                'Tên hiển thị',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          GlassTextField(
            controller: _displayNameController,
            hintText: 'Nhập tên hiển thị',
            textInputAction: TextInputAction.next,
            enabled: !_isLoading,
          ),
          AppSpacing.verticalSpaceXS,
          Text(
            'Tên này sẽ được hiển thị công khai',
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUsernameField() {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.alternate_email,
                color: AppColors.primary.withOpacity(0.8),
                size: 20,
              ),
              AppSpacing.horizontalSpaceSM,
              Text(
                'Tên người dùng',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          GlassTextField(
            controller: _usernameController,
            hintText: 'Nhập tên người dùng (tùy chọn)',
            textInputAction: TextInputAction.next,
            enabled: !_isLoading,
          ),
          AppSpacing.verticalSpaceXS,
          Text(
            'Tên người dùng duy nhất để chia sẻ hồ sơ',
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmailField(user) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      opacity: 0.05,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.email_outlined,
                color: AppColors.textSecondary.withOpacity(0.6),
                size: 20,
              ),
              AppSpacing.horizontalSpaceSM,
              Text(
                'Email',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          Text(
            user.email,
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontSize: 16,
            ),
          ),
          AppSpacing.verticalSpaceXS,
          Row(
            children: [
              Icon(
                Icons.lock_outline,
                color: Colors.white.withOpacity(0.4),
                size: 12,
              ),
              AppSpacing.horizontalSpaceXS,
              Text(
                'Email không thể thay đổi',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.4),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildProfileVisibilitySection() {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _isProfilePublic ? Icons.public : Icons.lock_outline,
                color: AppColors.primary.withOpacity(0.8),
                size: 20,
              ),
              AppSpacing.horizontalSpaceSM,
              Expanded(
                child: Text(
                  'Hiển thị hồ sơ công khai',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              // Toggle Switch
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: _isProfilePublic
                      ? [
                          BoxShadow(
                            color: AppColors.primary.withOpacity(0.3),
                            blurRadius: 8,
                            spreadRadius: 1,
                          ),
                        ]
                      : null,
                ),
                child: Switch(
                  value: _isProfilePublic,
                  onChanged: _isLoading
                      ? null
                      : (value) {
                          setState(() {
                            _isProfilePublic = value;
                            _onFieldChanged();
                          });
                        },
                  activeColor: AppColors.primary,
                  activeTrackColor: AppColors.primary.withOpacity(0.5),
                  inactiveThumbColor: Colors.white.withOpacity(0.6),
                  inactiveTrackColor: Colors.white.withOpacity(0.2),
                ),
              ),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: (_isProfilePublic ? AppColors.info : AppColors.textSecondary)
                  .withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: (_isProfilePublic ? AppColors.info : AppColors.textSecondary)
                    .withOpacity(0.2),
                width: 1,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  color: _isProfilePublic ? AppColors.info : AppColors.textSecondary,
                  size: 16,
                ),
                AppSpacing.horizontalSpaceSM,
                Expanded(
                  child: Text(
                    _isProfilePublic
                        ? 'Hồ sơ của bạn sẽ hiển thị công khai cho người khác'
                        : 'Chỉ bạn có thể xem hồ sơ của mình',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.7),
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSaveButton() {
    return AnimatedOpacity(
      opacity: _hasChanges ? 1.0 : 0.5,
      duration: const Duration(milliseconds: 300),
      child: GlassButton(
        text: 'Lưu thay đổi',
        onPressed: _hasChanges && !_isLoading ? _saveChanges : null,
        isLoading: _isLoading,
        isPrimary: true,
        icon: Icons.save_outlined,
      ),
    );
  }
}


