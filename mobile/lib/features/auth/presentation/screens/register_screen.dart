import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../routing/route_names.dart';
import '../providers/auth_provider.dart';
import '../providers/auth_state.dart';

/// Register screen with proper state handling using ref.listen
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
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

  @override
  void dispose() {
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

  InputDecoration _buildInputDecoration({
    required String hintText,
    Widget? suffixIcon,
  }) {
    return InputDecoration(
      hintText: hintText,
      hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
      filled: true,
      fillColor: Colors.white.withOpacity(0.1),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.white.withOpacity(0.2)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFD4A84B), width: 2),
      ),
      suffixIcon: suffixIcon,
    );
  }

  @override
  Widget build(BuildContext context) {
    // Listen to auth state changes
    ref.listen<AuthState>(authNotifierProvider, (previous, next) {
      debugPrint('[REGISTER] Auth state changed: ${previous?.runtimeType} -> ${next.runtimeType}');

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
      } else if (next.isUnauthenticated && previous != null && previous.isLoading) {
        debugPrint('[REGISTER] Auth state went from loading to unauthenticated');
        setState(() {
          _errorMessage = 'Đăng ký thất bại. Vui lòng thử lại.';
          _isLoading = false;
        });
      }
    });

    return Scaffold(
          backgroundColor: const Color(0xFF1A1A2E),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 40),

                  // Logo
                  Center(
                    child: Container(
                      width: 70,
                      height: 70,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFFD4A84B), Color(0xFFE8C87E)],
                        ),
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: const Center(
                        child: Text(
                          'M',
                          style: TextStyle(
                            fontSize: 38,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1A1A2E),
                          ),
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Title
                  const Text(
                    'Lưu Niên Sử Kí',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),

                  const SizedBox(height: 6),

                  // Subtitle
                  Text(
                    'Tạo tài khoản mới',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 15,
                      color: Colors.white.withOpacity(0.7),
                    ),
                  ),

                  const SizedBox(height: 32),

                  // Form Card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.2)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Error message
                        if (_errorMessage != null) ...[
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.red.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _errorMessage!,
                              style: const TextStyle(
                                color: Colors.redAccent,
                                fontSize: 14,
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ],

                        // Display Name label
                        Text(
                          'Tên hiển thị',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.8),
                          ),
                        ),
                        const SizedBox(height: 8),

                        // Display Name TextField
                        TextField(
                          controller: _displayNameController,
                          focusNode: _displayNameFocusNode,
                          textInputAction: TextInputAction.next,
                          enabled: !_isLoading,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                          ),
                          decoration: _buildInputDecoration(
                            hintText: 'Nhập tên của bạn',
                          ),
                          onSubmitted: (_) {
                            _emailFocusNode.requestFocus();
                          },
                        ),

                        const SizedBox(height: 16),

                        // Email label
                        Text(
                          'Email',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.8),
                          ),
                        ),
                        const SizedBox(height: 8),

                        // Email TextField
                        TextField(
                          controller: _emailController,
                          focusNode: _emailFocusNode,
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.next,
                          enabled: !_isLoading,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                          ),
                          decoration: _buildInputDecoration(
                            hintText: 'you@example.com',
                          ),
                          onSubmitted: (_) {
                            _passwordFocusNode.requestFocus();
                          },
                        ),

                        const SizedBox(height: 16),

                        // Password label
                        Text(
                          'Mật khẩu',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.8),
                          ),
                        ),
                        const SizedBox(height: 8),

                        // Password TextField
                        TextField(
                          controller: _passwordController,
                          focusNode: _passwordFocusNode,
                          obscureText: _obscurePassword,
                          textInputAction: TextInputAction.next,
                          enabled: !_isLoading,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                          ),
                          decoration: _buildInputDecoration(
                            hintText: '••••••••',
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePassword
                                    ? Icons.visibility_outlined
                                    : Icons.visibility_off_outlined,
                                color: Colors.white.withOpacity(0.5),
                              ),
                              onPressed: () {
                                setState(() {
                                  _obscurePassword = !_obscurePassword;
                                });
                              },
                            ),
                          ),
                          onSubmitted: (_) {
                            _confirmPasswordFocusNode.requestFocus();
                          },
                        ),

                        const SizedBox(height: 16),

                        // Confirm Password label
                        Text(
                          'Xác nhận mật khẩu',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.8),
                          ),
                        ),
                        const SizedBox(height: 8),

                        // Confirm Password TextField
                        TextField(
                          controller: _confirmPasswordController,
                          focusNode: _confirmPasswordFocusNode,
                          obscureText: _obscureConfirmPassword,
                          textInputAction: TextInputAction.done,
                          enabled: !_isLoading,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                          ),
                          decoration: _buildInputDecoration(
                            hintText: '••••••••',
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscureConfirmPassword
                                    ? Icons.visibility_outlined
                                    : Icons.visibility_off_outlined,
                                color: Colors.white.withOpacity(0.5),
                              ),
                              onPressed: () {
                                setState(() {
                                  _obscureConfirmPassword =
                                      !_obscureConfirmPassword;
                                });
                              },
                            ),
                          ),
                          onSubmitted: (_) => _handleRegister(),
                        ),

                        const SizedBox(height: 24),

                        // Register button
                        SizedBox(
                          height: 52,
                          child: ElevatedButton(
                            onPressed:
                                _isLoading ? null : () => _handleRegister(),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFFD4A84B),
                              foregroundColor: const Color(0xFF1A1A2E),
                              disabledBackgroundColor:
                                  const Color(0xFFD4A84B).withOpacity(0.5),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 0,
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    height: 24,
                                    width: 24,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.5,
                                      color: Color(0xFF1A1A2E),
                                    ),
                                  )
                                : const Text(
                                    'Đăng ký',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Login link
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'Đã có tài khoản? ',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 14,
                        ),
                      ),
                      GestureDetector(
                        onTap: _isLoading ? null : _navigateToLogin,
                        child: const Text(
                          'Đăng nhập',
                          style: TextStyle(
                            color: Color(0xFFD4A84B),
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
    );
  }
}
