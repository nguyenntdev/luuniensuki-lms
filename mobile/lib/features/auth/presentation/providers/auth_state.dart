import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/user.dart';

part 'auth_state.freezed.dart';

/// Authentication state using Freezed union types.
/// Represents all possible authentication states in the app.
@freezed
class AuthState with _$AuthState {
  // Private constructor to allow adding getters/methods
  const AuthState._();

  /// Initial state - app is starting up
  const factory AuthState.initial() = AuthStateInitial;

  /// Loading state - checking auth status or logging in/out
  const factory AuthState.loading({
    /// Optional message to show during loading
    String? message,
  }) = AuthStateLoading;

  /// Authenticated state - user is logged in
  const factory AuthState.authenticated({
    required User user,
  }) = AuthStateAuthenticated;

  /// Unauthenticated state - user is not logged in
  const factory AuthState.unauthenticated() = AuthStateUnauthenticated;

  /// Error state - authentication failed
  const factory AuthState.error({
    required String message,
    String? code,
  }) = AuthStateError;

  // Getters directly in the class (not extension)
  /// Check if user is authenticated
  bool get isAuthenticated => this is AuthStateAuthenticated;

  /// Check if state is loading
  bool get isLoading => this is AuthStateLoading;

  /// Check if state is initial
  bool get isInitial => this is AuthStateInitial;

  /// Check if state is unauthenticated
  bool get isUnauthenticated => this is AuthStateUnauthenticated;

  /// Check if state is error
  bool get isError => this is AuthStateError;

  /// Get the authenticated user if available
  User? get user => mapOrNull(
        authenticated: (state) => state.user,
      );

  /// Get the error message if in error state
  String? get errorMessage => mapOrNull(
        error: (state) => state.message,
      );

  /// Get the error code if in error state
  String? get errorCode => mapOrNull(
        error: (state) => state.code,
      );

  /// Get loading message if in loading state
  String? get loadingMessage => mapOrNull(
        loading: (state) => state.message,
      );

  /// Check if user is a guest
  bool get isGuest => user?.isGuest ?? false;

  /// Check if user has admin privileges
  bool get isAdmin => user?.isAdmin ?? false;

  /// Check if we should show the login screen
  bool get shouldShowLogin => isUnauthenticated || isError;

  /// Check if auth check is in progress
  bool get isCheckingAuth => isInitial || isLoading;
}

/// Login form state
@freezed
class LoginFormState with _$LoginFormState {
  const factory LoginFormState({
    @Default('') String email,
    @Default('') String password,
    @Default(false) bool isSubmitting,
    @Default(false) bool obscurePassword,
    String? emailError,
    String? passwordError,
    String? generalError,
  }) = _LoginFormState;
}

/// Extension methods for LoginFormState
extension LoginFormStateX on LoginFormState {
  /// Check if form has any errors
  bool get hasErrors =>
      emailError != null || passwordError != null || generalError != null;

  /// Check if form is valid (has values and no errors)
  bool get isValid =>
      email.isNotEmpty && password.isNotEmpty && !hasErrors;

  /// Check if form can be submitted
  bool get canSubmit => isValid && !isSubmitting;
}

/// Register form state
@freezed
class RegisterFormState with _$RegisterFormState {
  const factory RegisterFormState({
    @Default('') String email,
    @Default('') String password,
    @Default('') String confirmPassword,
    @Default('') String displayName,
    @Default(false) bool isSubmitting,
    @Default(true) bool obscurePassword,
    @Default(true) bool obscureConfirmPassword,
    String? emailError,
    String? passwordError,
    String? confirmPasswordError,
    String? displayNameError,
    String? generalError,
  }) = _RegisterFormState;
}

/// Extension methods for RegisterFormState
extension RegisterFormStateX on RegisterFormState {
  /// Check if form has any errors
  bool get hasErrors =>
      emailError != null ||
      passwordError != null ||
      confirmPasswordError != null ||
      displayNameError != null ||
      generalError != null;

  /// Check if form is valid
  bool get isValid =>
      email.isNotEmpty &&
      password.isNotEmpty &&
      confirmPassword.isNotEmpty &&
      displayName.isNotEmpty &&
      password == confirmPassword &&
      !hasErrors;

  /// Check if form can be submitted
  bool get canSubmit => isValid && !isSubmitting;

  /// Check if passwords match
  bool get passwordsMatch => password == confirmPassword;
}
