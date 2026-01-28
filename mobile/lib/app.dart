import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme/app_theme.dart';
import 'routing/app_router.dart';
import 'shared/widgets/network_status_indicator.dart';

/// Main app widget that configures MaterialApp with Riverpod.
class LuuniensukiApp extends ConsumerWidget {
  const LuuniensukiApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Cửu Đỉnh Ký',
      debugShowCheckedModeBanner: false,

      // Theme configuration
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light, // TODO: Make this configurable

      // Router configuration
      routerConfig: router,

      // Localization (Vietnamese primary)
      locale: const Locale('vi', 'VN'),
      supportedLocales: const [
        Locale('vi', 'VN'),
        Locale('en', 'US'),
      ],

      // Builder for global overlays and error handling
      builder: (context, child) {
        return NetworkStatusIndicator(
          child: MediaQuery(
            // Prevent text scaling from breaking layouts
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(
                MediaQuery.of(context).textScaler.scale(1.0).clamp(0.8, 1.2),
              ),
            ),
            child: child ?? const SizedBox.shrink(),
          ),
        );
      },
    );
  }
}

/// Root widget that wraps the app with ProviderScope.
/// This is the entry point for the Riverpod provider tree.
class AppRoot extends StatelessWidget {
  const AppRoot({super.key});

  @override
  Widget build(BuildContext context) {
    return const ProviderScope(
      child: LuuniensukiApp(),
    );
  }
}
