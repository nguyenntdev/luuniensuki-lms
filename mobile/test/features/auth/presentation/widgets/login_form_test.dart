import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/features/auth/presentation/widgets/login_form.dart';
import 'package:luuniensuki_lms/shared/widgets/glass/glass_text_field.dart';

void main() {
  group('LoginForm Widget Tests', () {
    group('Email Validation', () {
      testWidgets('shows error when email is empty', (tester) async {
        bool loginCalled = false;

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () => loginCalled = true,
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), '');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        
        await tester.tap(find.byType(GlassTextField).first);
        await tester.pumpAndSettle();

        expect(loginCalled, false);
      });

      testWidgets('shows error when email has invalid format', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'invalid-email');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        
        await tester.tap(find.byKey(const Key('email_field')));
        await tester.pumpAndSettle();
        
        await tester.tap(find.byKey(const Key('password_field')));
        await tester.pumpAndSettle();

        final emailField = tester.widget<GlassTextField>(find.byKey(const Key('email_field')));
        expect(emailField.errorText, isNotNull);
      });

      testWidgets('accepts valid email format', (tester) async {
        bool loginCalled = false;

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () => loginCalled = true,
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        await tester.pumpAndSettle();

        final emailField = tester.widget<GlassTextField>(find.byKey(const Key('email_field')));
        expect(emailField.errorText, null);
      });

      testWidgets('validates email must contain @ symbol', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'testexample.com');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        
        await tester.tap(find.byKey(const Key('email_field')));
        await tester.pumpAndSettle();
        await tester.tap(find.byKey(const Key('password_field')));
        await tester.pumpAndSettle();

        final emailField = tester.widget<GlassTextField>(find.byKey(const Key('email_field')));
        expect(emailField.errorText, isNotNull);
      });
    });

    group('Password Validation', () {
      testWidgets('shows error when password is empty', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), '');
        
        await tester.tap(find.byKey(const Key('password_field')));
        await tester.pumpAndSettle();
        
        await tester.tap(find.byKey(const Key('email_field')));
        await tester.pumpAndSettle();

        final passwordField = tester.widget<GlassTextField>(find.byKey(const Key('password_field')));
        expect(passwordField.errorText, isNotNull);
      });

      testWidgets('shows error when password is too short', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), '12345');
        
        await tester.tap(find.byKey(const Key('password_field')));
        await tester.pumpAndSettle();
        
        await tester.tap(find.byKey(const Key('email_field')));
        await tester.pumpAndSettle();

        final passwordField = tester.widget<GlassTextField>(find.byKey(const Key('password_field')));
        expect(passwordField.errorText, isNotNull);
      });

      testWidgets('accepts valid password (6+ characters)', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        await tester.pumpAndSettle();

        final passwordField = tester.widget<GlassTextField>(find.byKey(const Key('password_field')));
        expect(passwordField.errorText, null);
      });

      testWidgets('password visibility toggle works', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        final passwordFieldBefore = tester.widget<GlassTextField>(
          find.byKey(const Key('password_field')),
        );
        expect(passwordFieldBefore.obscureText, true);

        await tester.tap(find.byKey(const Key('password_visibility_toggle')));
        await tester.pumpAndSettle();

        final passwordFieldAfter = tester.widget<GlassTextField>(
          find.byKey(const Key('password_field')),
        );
        expect(passwordFieldAfter.obscureText, false);
      });
    });

    group('Form Submission', () {
      testWidgets('calls onLogin when form is valid', (tester) async {
        bool loginCalled = false;

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () => loginCalled = true,
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        await tester.pumpAndSettle();

        await tester.testTextInput.receiveAction(TextInputAction.done);
        await tester.pumpAndSettle();

        expect(loginCalled, true);
      });

      testWidgets('does not call onLogin when email is invalid', (tester) async {
        bool loginCalled = false;

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () => loginCalled = true,
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'invalid-email');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        await tester.pumpAndSettle();

        await tester.testTextInput.receiveAction(TextInputAction.done);
        await tester.pumpAndSettle();

        expect(loginCalled, false);
      });

      testWidgets('does not call onLogin when password is invalid', (tester) async {
        bool loginCalled = false;

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () => loginCalled = true,
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), '123');
        await tester.pumpAndSettle();

        await tester.testTextInput.receiveAction(TextInputAction.done);
        await tester.pumpAndSettle();

        expect(loginCalled, false);
      });

      testWidgets('does not call onLogin when both fields are invalid', (tester) async {
        bool loginCalled = false;

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () => loginCalled = true,
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'invalid');
        await tester.enterText(find.byKey(const Key('password_field')), '123');
        await tester.pumpAndSettle();

        await tester.testTextInput.receiveAction(TextInputAction.done);
        await tester.pumpAndSettle();

        expect(loginCalled, false);
      });
    });

    group('Error Display', () {
      testWidgets('displays error message when provided', (tester) async {
        const errorMessage = 'Invalid credentials';

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                errorMessage: errorMessage,
                onLogin: () {},
              ),
            ),
          ),
        );

        expect(find.text(errorMessage), findsOneWidget);
        expect(find.byKey(const Key('error_message')), findsOneWidget);
      });

      testWidgets('does not display error message when null', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        expect(find.byKey(const Key('error_message')), findsNothing);
      });

      testWidgets('updates error message dynamically', (tester) async {
        String? errorMessage;

        await tester.pumpWidget(
          MaterialApp(
            home: StatefulBuilder(
              builder: (context, setState) {
                return Scaffold(
                  body: Column(
                    children: [
                      LoginForm(
                        errorMessage: errorMessage,
                        onLogin: () {},
                      ),
                      ElevatedButton(
                        onPressed: () {
                          setState(() {
                            errorMessage = 'New error message';
                          });
                        },
                        child: const Text('Set Error'),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        );

        expect(find.byKey(const Key('error_message')), findsNothing);

        await tester.tap(find.text('Set Error'));
        await tester.pumpAndSettle();

        expect(find.text('New error message'), findsOneWidget);
        expect(find.byKey(const Key('error_message')), findsOneWidget);
      });
    });

    group('Focus and Navigation', () {
      testWidgets('email field requests password focus on submit', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                onLogin: () {},
              ),
            ),
          ),
        );

        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.testTextInput.receiveAction(TextInputAction.next);
        await tester.pumpAndSettle();

        expect(
          tester.widget<GlassTextField>(find.byKey(const Key('password_field'))).focusNode?.hasFocus,
          isNotNull,
        );
      });
    });

    group('Loading State', () {
      testWidgets('respects isLoading property', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: LoginForm(
                isLoading: true,
                onLogin: () {},
              ),
            ),
          ),
        );

        expect(find.byType(LoginForm), findsOneWidget);
      });
    });
  });
}

