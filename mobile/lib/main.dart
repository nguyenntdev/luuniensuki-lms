import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/storage/hive_storage.dart';
import 'core/theme/app_theme.dart';
import 'routing/app_router.dart';
import 'features/auth/presentation/providers/auth_provider.dart';
import 'features/daily_goals/presentation/providers/daily_goal_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Hive storage
  await HiveStorage.init();

  runApp(
    const ProviderScope(
      child: LuuniensukiApp(),
    ),
  );
}

class LuuniensukiApp extends ConsumerStatefulWidget {
  const LuuniensukiApp({super.key});

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
