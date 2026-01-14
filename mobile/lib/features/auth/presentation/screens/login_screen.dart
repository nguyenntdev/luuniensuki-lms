import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/glass/glass_button.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../../shared/widgets/glass/glass_text_field.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../mascot/presentation/widgets/mascot_widget.dart';
import '../providers/auth_provider.dart';
import '../providers/auth_state.dart';

/// Login screen with proper state handling using ref.listen
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> with TickerProviderStateMixin {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();

  bool _hasAttemptedLogin = false;
  bool _isLoading = false;
  bool _obscurePassword = true;
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
    ).animate(CurvedAnimation(parent: _slideController, curve: Curves.easeOutCubic));

    _fadeController.forward();
    _slideController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _slideController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

  void _handleLogin() {
    // Unfocus to dismiss keyboard
    FocusScope.of(context).unfocus();

    final email = _emailController.text.trim();
    final password = _passwordController.text;

    // Validation
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _errorMessage = 'Vui lòng nhập email hợp lệ');
      return;
    }
    if (password.isEmpty) {
      setState(() => _errorMessage = 'Vui lòng nhập mật khẩu');
      return;
    }

    setState(() {
      _errorMessage = null;
      _isLoading = true;
      _hasAttemptedLogin = true;
    });

    debugPrint('[LOGIN] Starting login for: $email');

    // Call login - the state changes will be handled by ref.listen in build()
    ref.read(authNotifierProvider.notifier).login(
          email: email,
          password: password,
        );
  }

  void _navigateToRegister() {
    final returnUrl =
        GoRouterState.of(context).uri.queryParameters['returnUrl'];
    if (returnUrl != null && returnUrl.isNotEmpty) {
      context.go('${RoutePaths.register}?returnUrl=$returnUrl');
    } else {
      context.go(RoutePaths.register);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Listen to auth state changes
    ref.listen<AuthState>(authNotifierProvider, (previous, next) {
      debugPrint('[LOGIN] Auth state changed: ${previous?.runtimeType} -> ${next.runtimeType}');

      if (!mounted) return;

      if (next.isAuthenticated) {
        debugPrint('[LOGIN] Login successful, navigating to explore');
        setState(() => _isLoading = false);
        final returnUrl =
            GoRouterState.of(context).uri.queryParameters['returnUrl'];
        if (returnUrl != null && returnUrl.isNotEmpty) {
          context.go(Uri.decodeComponent(returnUrl));
        } else {
          context.go(RoutePaths.explore);
        }
      } else if (next.isError) {
        debugPrint('[LOGIN] Auth error: ${next.errorMessage}');
        setState(() {
          _errorMessage = next.errorMessage ?? 'Đăng nhập thất bại';
          _isLoading = false;
        });
      } else if (next.isUnauthenticated && previous != null && previous.isLoading && _hasAttemptedLogin) {
        // Went from loading to unauthenticated = login failed silently
        debugPrint('[LOGIN] Auth state went from loading to unauthenticated');
        setState(() {
          _errorMessage = 'Đăng nhập thất bại. Vui lòng thử lại.';
          _isLoading = false;
          _hasAttemptedLogin = false;
        });
      }
    });

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
                    AppSpacing.verticalSpaceMD,

                    // Logo with enhanced styling
                    Center(
                      child: Hero(
                        tag: 'app_logo',
                        child: Container(
                          width: 100,
                          height: 100,
                          child: const Center(
                            child: MascotWidget(
                              expression: MascotExpression.happy,
                              size: 80,
                              animate: true,
                            ),
                          ),
                        ),
                      ),
                    ),

                    AppSpacing.verticalSpaceXL,

                    // Title
                    const Text(
                      'Lưu Niên Sử Kí',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.2,
                      ),
                    ),

                    AppSpacing.verticalSpaceSM,

                    Text(
                      'Đăng nhập để tiếp tục',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 16,
                        letterSpacing: 0.5,
                      ),
                    ),

                    AppSpacing.verticalSpaceXXL,

                    // Error message with animation
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 300),
                      transitionBuilder: (Widget child, Animation<double> animation) {
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
                              padding: const EdgeInsets.all(AppSpacing.md),
                              margin: const EdgeInsets.only(bottom: AppSpacing.md),
                              decoration: BoxDecoration(
                                color: Colors.red.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
                                border: Border.all(
                                  color: Colors.red.withOpacity(0.4),
                                  width: 1.5,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.red.withOpacity(0.2),
                                    blurRadius: 8,
                                    offset: const Offset(0, 2),
                                  ),
                                ],
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.error_outline, color: Colors.red, size: 22),
                                  AppSpacing.horizontalSpaceSM,
                                  Expanded(
                                    child: Text(
                                      _errorMessage!,
                                      style: const TextStyle(
                                        color: Colors.red,
                                        fontSize: 14,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            )
                          : const SizedBox.shrink(key: ValueKey<String>('no_error')),
                    ),

                    // Email field with glassmorphism
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
                      onSubmitted: (_) => _passwordFocusNode.requestFocus(),
                    ),

                    AppSpacing.verticalSpaceLG,

                    // Password field with glassmorphism
                    GlassTextField(
                      controller: _passwordController,
                      focusNode: _passwordFocusNode,
                      labelText: 'Mật khẩu',
                      hintText: '••••••••',
                      obscureText: _obscurePassword,
                      textInputAction: TextInputAction.done,
                      prefixIcon: Icon(
                        Icons.lock_outline,
                        color: Colors.white.withOpacity(0.6),
                      ),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePassword ? Icons.visibility_off : Icons.visibility,
                          color: Colors.white.withOpacity(0.6),
                        ),
                        onPressed: () {
                          setState(() => _obscurePassword = !_obscurePassword);
                        },
                      ),
                      onSubmitted: (_) => _handleLogin(),
                    ),

                    AppSpacing.verticalSpaceSM,

                    // Forgot password link
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () {
                          // TODO: Implement forgot password
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Chức năng đang được phát triển'),
                              behavior: SnackBarBehavior.floating,
                            ),
                          );
                        },
                        style: TextButton.styleFrom(
                          foregroundColor: const Color(0xFFD4A84B),
                          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm),
                        ),
                        child: Text(
                          'Quên mật khẩu?',
                          style: TextStyle(
                            color: const Color(0xFFD4A84B).withOpacity(0.9),
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),

                    AppSpacing.verticalSpaceLG,

                    // Login button with enhanced styling
                    GlassButton(
                      text: 'Đăng nhập',
                      onPressed: _handleLogin,
                      isLoading: _isLoading,
                      isPrimary: true,
                      height: 56,
                    ),

                    AppSpacing.verticalSpaceXL,

                    // Register link
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          'Chưa có tài khoản? ',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.7),
                            fontSize: 15,
                          ),
                        ),
                        GestureDetector(
                          onTap: _navigateToRegister,
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.sm,
                              vertical: AppSpacing.xs,
                            ),
                            child: const Text(
                              'Đăng ký',
                              style: TextStyle(
                                color: Color(0xFFD4A84B),
                                fontSize: 15,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.3,
                              ),
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
