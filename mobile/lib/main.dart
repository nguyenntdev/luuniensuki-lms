import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'core/storage/hive_storage.dart';
import 'core/theme/app_theme.dart';
import 'routing/app_router.dart';
import 'features/auth/presentation/providers/auth_provider.dart';
import 'features/daily_goals/presentation/providers/daily_goal_provider.dart';
import 'features/notifications/data/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

  String? startupError;

  // Initialize Hive storage with one recovery attempt to avoid startup black screen.
  try {
    await HiveStorage.init();
  } catch (error, stackTrace) {
    debugPrint('[BOOT] Hive init failed: $error');
    debugPrint('[BOOT] StackTrace: $stackTrace');

    try {
      await HiveStorage.recoverAndInit();
      debugPrint('[BOOT] Hive recovery succeeded.');
    } catch (recoveryError, recoveryStackTrace) {
      debugPrint('[BOOT] Hive recovery failed: $recoveryError');
      debugPrint('[BOOT] Recovery stackTrace: $recoveryStackTrace');
      startupError = recoveryError.toString();
    }
  }

  runApp(
    ProviderScope(
      child: LuuniensukiApp(startupError: startupError),
    ),
  );
}

class LuuniensukiApp extends ConsumerStatefulWidget {
  final String? startupError;

  const LuuniensukiApp({
    super.key,
    this.startupError,
  });

  @override
  ConsumerState<LuuniensukiApp> createState() => _LuuniensukiAppState();
}

class _LuuniensukiAppState extends ConsumerState<LuuniensukiApp> {
  @override
  void initState() {
    super.initState();
    // Initialize auth in initState, not in build
    // Use Future.microtask to avoid calling ref during initState
    Future.microtask(() async {
      // Await initialize() to complete before accessing dailyGoalXpSyncProvider
      await ref.read(authNotifierProvider.notifier).initialize();
      // Initialize daily goal XP sync to track XP changes
      ref.read(dailyGoalXpSyncProvider);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (widget.startupError != null) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.dark,
        home: _StartupErrorScreen(errorMessage: widget.startupError!),
      );
    }

    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Lưu Niên Sử Kí',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark,
      routerConfig: router,
    );
  }
}

class _StartupErrorScreen extends StatelessWidget {
  final String errorMessage;

  const _StartupErrorScreen({required this.errorMessage});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.redAccent,
              ),
              const SizedBox(height: 16),
              const Text(
                'Không thể khởi động ứng dụng',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Vui lòng mở lại ứng dụng.\nChi tiết: $errorMessage',
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
