import 'package:flutter/material.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/glass_button.dart';
import '../../../../shared/widgets/glass/glass_text_field.dart';

class LoginForm extends StatefulWidget {
  final VoidCallback? onLogin;
  final bool isLoading;
  final String? errorMessage;
  final TextEditingController? emailController;
  final TextEditingController? passwordController;

  const LoginForm({
    super.key,
    this.onLogin,
    this.isLoading = false,
    this.errorMessage,
    this.emailController,
    this.passwordController,
  });

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  late TextEditingController _emailController;
  late TextEditingController _passwordController;
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();
  bool _obscurePassword = true;
  String? _emailError;
  String? _passwordError;

  @override
  void initState() {
    super.initState();
    _emailController = widget.emailController ?? TextEditingController();
    _passwordController = widget.passwordController ?? TextEditingController();
  }

  @override
  void dispose() {
    if (widget.emailController == null) _emailController.dispose();
    if (widget.passwordController == null) _passwordController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

  bool _validateEmail() {
    final email = _emailController.text.trim();
    if (email.isEmpty) {
      setState(() => _emailError = 'Email không được để trống');
      return false;
    }
    if (!email.contains('@') || !email.contains('.')) {
      setState(() => _emailError = 'Email không hợp lệ');
      return false;
    }
    setState(() => _emailError = null);
    return true;
  }

  bool _validatePassword() {
    final password = _passwordController.text;
    if (password.isEmpty) {
      setState(() => _passwordError = 'Mật khẩu không được để trống');
      return false;
    }
    if (password.length < 6) {
      setState(() => _passwordError = 'Mật khẩu phải có ít nhất 6 ký tự');
      return false;
    }
    setState(() => _passwordError = null);
    return true;
  }

  void _handleSubmit() {
    final emailValid = _validateEmail();
    final passwordValid = _validatePassword();

    if (emailValid && passwordValid && widget.onLogin != null) {
      widget.onLogin!();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (widget.errorMessage != null) ...[
          Container(
            key: const Key('error_message'),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.red.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.withOpacity(0.3)),
            ),
            child: Text(
              widget.errorMessage!,
              style: const TextStyle(color: Colors.red, fontSize: 14),
              textAlign: TextAlign.center,
            ),
          ),
          AppSpacing.verticalSpaceMD,
        ],
        GlassTextField(
          key: const Key('email_field'),
          controller: _emailController,
          focusNode: _emailFocusNode,
          labelText: 'Email',
          hintText: 'you@example.com',
          keyboardType: TextInputType.emailAddress,
          textInputAction: TextInputAction.next,
          errorText: _emailError,
          prefixIcon: Icon(
            Icons.email_outlined,
            color: Colors.white.withOpacity(0.6),
          ),
          onSubmitted: (_) => _passwordFocusNode.requestFocus(),
          onChanged: (_) {
            if (_emailError != null) _validateEmail();
          },
        ),
        AppSpacing.verticalSpaceLG,
        GlassTextField(
          key: const Key('password_field'),
          controller: _passwordController,
          focusNode: _passwordFocusNode,
          labelText: 'Mật khẩu',
          hintText: '••••••••',
          obscureText: _obscurePassword,
          textInputAction: TextInputAction.done,
          errorText: _passwordError,
          prefixIcon: Icon(
            Icons.lock_outline,
            color: Colors.white.withOpacity(0.6),
          ),
          suffixIcon: IconButton(
            key: const Key('password_visibility_toggle'),
            icon: Icon(
              _obscurePassword ? Icons.visibility_off : Icons.visibility,
              color: Colors.white.withOpacity(0.6),
            ),
            onPressed: () {
              setState(() => _obscurePassword = !_obscurePassword);
            },
          ),
          onSubmitted: (_) => _handleSubmit(),
          onChanged: (_) {
            if (_passwordError != null) _validatePassword();
          },
        ),
      ],
    );
  }
}

