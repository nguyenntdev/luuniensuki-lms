import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_button.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../../shared/widgets/glass/glass_text_field.dart';
import '../../../mascot/presentation/widgets/mascot_widget.dart';
import '../providers/auth_provider.dart';
import '../providers/auth_state.dart';

/// Register screen with proper state handling using ref.listen
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen>
    with TickerProviderStateMixin {
  final _displayNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  final _displayNameFocusNode = FocusNode();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();
  final _confirmPasswordFocusNode = FocusNode();

  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _isLoading = false;
  String? _errorMessage;

  late AnimationController _fadeController;
  late AnimationController _slideController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _slideController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeOut),
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(
        CurvedAnimation(parent: _slideController, curve: Curves.easeOutCubic));

    _fadeController.forward();
    _slideController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _slideController.dispose();
    _displayNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _displayNameFocusNode.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    _confirmPasswordFocusNode.dispose();
    super.dispose();
  }

  void _handleRegister() {
    // Unfocus to dismiss keyboard
    FocusScope.of(context).unfocus();

    final displayName = _displayNameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    final confirmPassword = _confirmPasswordController.text;

    // Validation
    if (displayName.isEmpty) {
      setState(() => _errorMessage = 'Vui lòng nhập tên hiển thị');
      return;
    }
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _errorMessage = 'Vui lòng nhập email hợp lệ');
      return;
    }
    if (password.length < 8) {
      setState(() => _errorMessage = 'Mật khẩu phải có ít nhất 8 ký tự');
      return;
    }
    if (password != confirmPassword) {
      setState(() => _errorMessage = 'Mật khẩu không khớp');
      return;
    }

    setState(() {
      _errorMessage = null;
      _isLoading = true;
    });

    debugPrint('[REGISTER] Starting register for: $email');

    // Call register - the state changes will be handled by ref.listen in build()
    ref.read(authNotifierProvider.notifier).register(
          email: email,
          password: password,
          displayName: displayName,
        );
  }

  void _navigateToLogin() {
    final returnUrl =
        GoRouterState.of(context).uri.queryParameters['returnUrl'];
    if (returnUrl != null && returnUrl.isNotEmpty) {
      context.go('${RoutePaths.login}?returnUrl=$returnUrl');
    } else {
      context.go(RoutePaths.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Listen to auth state changes
    ref.listen<AuthState>(authNotifierProvider, (previous, next) {
      debugPrint(
          '[REGISTER] Auth state changed: ${previous?.runtimeType} -> ${next.runtimeType}');

      if (!mounted) return;

      if (next.isAuthenticated) {
        debugPrint('[REGISTER] Register successful, navigating to explore');
        setState(() => _isLoading = false);
        final returnUrl =
            GoRouterState.of(context).uri.queryParameters['returnUrl'];
        if (returnUrl != null && returnUrl.isNotEmpty) {
          context.go(Uri.decodeComponent(returnUrl));
        } else {
          context.go(RoutePaths.explore);
        }
      } else if (next.isError) {
        debugPrint('[REGISTER] Auth error: ${next.errorMessage}');
        setState(() {
          _errorMessage = next.errorMessage ?? 'Đăng ký thất bại';
          _isLoading = false;
        });
      } else if (next.isUnauthenticated &&
          previous != null &&
          previous.isLoading) {
        debugPrint(
            '[REGISTER] Auth state went from loading to unauthenticated');
        setState(() {
          _errorMessage = 'Đăng ký thất bại. Vui lòng thử lại.';
          _isLoading = false;
        });
      }
    });

    final headlineStyle = Theme.of(context).textTheme.headlineSmall?.copyWith(
          color: Colors.white,
          fontWeight: FontWeight.w700,
        );
    final subtitleStyle = Theme.of(context).textTheme.bodyLarge?.copyWith(
          color: Colors.white.withOpacity(0.75),
        );

    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: FadeTransition(
            opacity: _fadeAnimation,
            child: SlideTransition(
              position: _slideAnimation,
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    AppSpacing.verticalSpaceXXL,
                    Center(
                      child: Hero(
                        tag: 'app_logo',
                        child: SizedBox(
                          width: 100,
                          height: 100,
                          child: Center(
                            child: MascotWidget(
                              expression: MascotExpression.excited,
                              size: 80,
                              animate: true,
                            ),
                          ),
                        ),
                      ),
                    ),
                    AppSpacing.verticalSpaceXL,
                    Text(
                      'Tạo tài khoản',
                      textAlign: TextAlign.center,
                      style: headlineStyle,
                    ),
                    AppSpacing.verticalSpaceSM,
                    Text(
                      'Bắt đầu hành trình khám phá văn hóa Việt Nam',
                      textAlign: TextAlign.center,
                      style: subtitleStyle,
                    ),
                    AppSpacing.verticalSpaceXL,
                    GlassContainer(
                      padding: const EdgeInsets.all(AppSpacing.lg),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          AnimatedSwitcher(
                            duration: const Duration(milliseconds: 300),
                            transitionBuilder:
                                (Widget child, Animation<double> animation) {
                              return FadeTransition(
                                opacity: animation,
                                child: SlideTransition(
                                  position: Tween<Offset>(
                                    begin: const Offset(0, -0.2),
                                    end: Offset.zero,
                                  ).animate(animation),
                                  child: child,
                                ),
                              );
                            },
                            child: _errorMessage != null
                                ? Container(
                                    key: ValueKey<String>(_errorMessage!),
                                    padding:
                                        const EdgeInsets.all(AppSpacing.md),
                                    margin: const EdgeInsets.only(
                                        bottom: AppSpacing.md),
                                    decoration: BoxDecoration(
                                      color: AppColors.error.withOpacity(0.15),
                                      borderRadius: BorderRadius.circular(
                                          AppSpacing.radiusMD),
                                      border: Border.all(
                                        color: AppColors.error.withOpacity(0.4),
                                        width: 1.5,
                                      ),
                                      boxShadow: [
                                        BoxShadow(
                                          color:
                                              AppColors.error.withOpacity(0.2),
                                          blurRadius: 8,
                                          offset: const Offset(0, 2),
                                        ),
                                      ],
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.error_outline,
                                            color: AppColors.error, size: 22),
                                        AppSpacing.horizontalSpaceSM,
                                        Expanded(
                                          child: Text(
                                            _errorMessage!,
                                            style: const TextStyle(
                                              color: AppColors.error,
                                              fontSize: 14,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  )
                                : const SizedBox.shrink(
                                    key: ValueKey<String>('no_error')),
                          ),
                          GlassTextField(
                            controller: _displayNameController,
                            focusNode: _displayNameFocusNode,
                            labelText: 'Tên hiển thị',
                            hintText: 'Nhập tên của bạn',
                            textInputAction: TextInputAction.next,
                            prefixIcon: Icon(
                              Icons.badge_outlined,
                              color: Colors.white.withOpacity(0.6),
                            ),
                            onSubmitted: (_) => _emailFocusNode.requestFocus(),
                          ),
                          AppSpacing.verticalSpaceLG,
                          GlassTextField(
                            controller: _emailController,
                            focusNode: _emailFocusNode,
                            labelText: 'Email',
                            hintText: 'you@example.com',
                            keyboardType: TextInputType.emailAddress,
                            textInputAction: TextInputAction.next,
                            prefixIcon: Icon(
                              Icons.email_outlined,
                              color: Colors.white.withOpacity(0.6),
                            ),
                            onSubmitted: (_) =>
                                _passwordFocusNode.requestFocus(),
                          ),
                          AppSpacing.verticalSpaceLG,
                          GlassTextField(
                            controller: _passwordController,
                            focusNode: _passwordFocusNode,
                            labelText: 'Mật khẩu',
                            hintText: '••••••••',
                            obscureText: _obscurePassword,
                            textInputAction: TextInputAction.next,
                            prefixIcon: Icon(
                              Icons.lock_outline,
                              color: Colors.white.withOpacity(0.6),
                            ),
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePassword
                                    ? Icons.visibility_off
                                    : Icons.visibility,
                                color: Colors.white.withOpacity(0.6),
                              ),
                              onPressed: () {
                                setState(
                                    () => _obscurePassword = !_obscurePassword);
                              },
                            ),
                            onSubmitted: (_) =>
                                _confirmPasswordFocusNode.requestFocus(),
                          ),
                          AppSpacing.verticalSpaceLG,
                          GlassTextField(
                            controller: _confirmPasswordController,
                            focusNode: _confirmPasswordFocusNode,
                            labelText: 'Xác nhận mật khẩu',
                            hintText: '••••••••',
                            obscureText: _obscureConfirmPassword,
                            textInputAction: TextInputAction.done,
                            prefixIcon: Icon(
                              Icons.lock_outline,
                              color: Colors.white.withOpacity(0.6),
                            ),
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscureConfirmPassword
                                    ? Icons.visibility_off
                                    : Icons.visibility,
                                color: Colors.white.withOpacity(0.6),
                              ),
                              onPressed: () {
                                setState(() => _obscureConfirmPassword =
                                    !_obscureConfirmPassword);
                              },
                            ),
                            onSubmitted: (_) => _handleRegister(),
                          ),
                          AppSpacing.verticalSpaceLG,
                          GlassButton(
                            text: 'Đăng ký',
                            onPressed: _isLoading ? null : _handleRegister,
                            isLoading: _isLoading,
                            isPrimary: true,
                            height: 56,
                          ),
                        ],
                      ),
                    ),
                    AppSpacing.verticalSpaceXL,
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          'Đã có tài khoản? ',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.7),
                            fontSize: 15,
                          ),
                        ),
                        GestureDetector(
                          onTap: _isLoading ? null : _navigateToLogin,
                          child: const Text(
                            'Đăng nhập',
                            style: TextStyle(
                              color: AppColors.primary,
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ),
                      ],
                    ),
                    AppSpacing.verticalSpaceXL,
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
