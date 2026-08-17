import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../domain/history_api.dart';

/// History-first Atlas screen: lists the 9 canonical urns (public, no auth).
class HistoryAtlasScreen extends ConsumerWidget {
  const HistoryAtlasScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urns = ref.watch(historyUrnsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Cửu Đỉnh — Atlas')),
      body: urns.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Text(
              'Không tải được dữ liệu lịch sử.\n$err',
              textAlign: TextAlign.center,
              style: AppTypography.textTheme.bodyMedium,
            ),
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const Center(
              child: Text('Chưa có đỉnh nào được đồng bộ.'),
            );
          }
          return GridView.builder(
            padding: const EdgeInsets.all(AppSpacing.md),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 1.4,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
            ),
            itemCount: items.length,
            itemBuilder: (context, index) {
              final urn = items[index];
              return Card(
                clipBehavior: Clip.antiAlias,
                child: InkWell(
                  onTap: () {},
                  child: Padding(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          urn.nameVi,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTypography.textTheme.titleMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          urn.slug,
                          style: AppTypography.textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
