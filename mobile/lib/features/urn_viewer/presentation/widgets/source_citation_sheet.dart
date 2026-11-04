import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/entities/source_citation.dart';
import '../providers/source_citation_provider.dart';
import 'epistemic_badge.dart';

/// Modal bottom sheet displaying verified historical source citations, public locators,
/// Hán-Nôm script/translations, and epistemic uncertainty indicators.
class SourceCitationSheet extends ConsumerWidget {
  final String slugOrId;
  final String? initialTitle;

  const SourceCitationSheet({
    super.key,
    required this.slugOrId,
    this.initialTitle,
  });

  /// Static helper to display the sheet from any screen or widget.
  static Future<void> show(
    BuildContext context, {
    required String slugOrId,
    String? title,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => SourceCitationSheet(
        slugOrId: slugOrId,
        initialTitle: title,
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final citationsAsync = ref.watch(entityCitationsProvider(slugOrId));

    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.45,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.3),
                blurRadius: 20,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Column(
            children: [
              // Drag handle
              Center(
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 12),
                  width: 48,
                  height: 5,
                  decoration: BoxDecoration(
                    color: Colors.grey[400],
                    borderRadius: BorderRadius.circular(2.5),
                  ),
                ),
              ),

              // Title Header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Row(
                  children: [
                    const Icon(Icons.menu_book_rounded, color: AppColors.primary, size: 24),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            initialTitle ?? 'Nguồn Thư Tịch & Sử Liệu Gốc',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              fontSize: 18,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          Text(
                            'Khảo đính tư liệu Cửu Đỉnh triều Nguyễn',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.of(context).pop(),
                      tooltip: 'Đóng',
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),

              // Content based on AsyncValue
              Expanded(
                child: citationsAsync.when(
                  loading: () => _buildLoadingState(context),
                  error: (err, stack) => _buildErrorState(context, ref, err),
                  data: (bundle) => _buildLoadedState(context, scrollController, bundle),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildLoadingState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(strokeWidth: 3),
          const SizedBox(height: 16),
          Text(
            'Đang đối chiếu sử liệu và thư tịch...',
            style: TextStyle(color: Colors.grey[600], fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(BuildContext context, WidgetRef ref, Object error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off_rounded, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            const Text(
              'Không thể tải nguồn sử liệu',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 6),
            Text(
              'Vui lòng kiểm tra kết nối mạng hoặc thử lại sau.\n($error)',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () => ref.refresh(entityCitationsProvider(slugOrId)),
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text('Thử lại'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoadedState(
    BuildContext context,
    ScrollController scrollController,
    EntityCitationBundle bundle,
  ) {
    final theme = Theme.of(context);

    if (bundle.claims.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.info_outline, size: 48, color: Colors.grey),
              const SizedBox(height: 12),
              Text(
                'Chưa có thư tịch liên kết cho "${bundle.nameVi}"',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
              ),
              const SizedBox(height: 6),
              const Text(
                'Hồ sơ sử liệu đang được Hội đồng Khoa học thẩm định và cập nhật.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
        ),
      );
    }

    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(20),
      children: [
        // Entity Header Card (Hán-Nôm & Reading)
        _buildEntityCard(context, bundle),
        const SizedBox(height: 16),

        // Section Title: Historical Claims & Backing Sources
        Row(
          children: [
            const Icon(Icons.verified_user_outlined, size: 18, color: AppColors.primary),
            const SizedBox(width: 8),
            Text(
              'Khẳng Định Lịch Sử & Nguồn Chứng Thực',
              style: theme.textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
                letterSpacing: 0.3,
              ),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${bundle.claims.length} khẳng định',
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Claims list
        ...bundle.claims.map((claim) => _buildClaimCard(context, claim)),

        const SizedBox(height: 20),

        // Provenance & Authenticity Footer
        _buildProvenanceFooter(context, bundle),
      ],
    );
  }

  Widget _buildEntityCard(BuildContext context, EntityCitationBundle bundle) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primary.withOpacity(0.08),
            AppColors.primary.withOpacity(0.02),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.primary.withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      bundle.nameVi,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    if (bundle.nameEn != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        bundle.nameEn!,
                        style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                      ),
                    ],
                  ],
                ),
              ),
              // Hán-Nôm Glyphs
              if (bundle.nameHanNom != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.primary.withOpacity(0.3)),
                  ),
                  child: Column(
                    children: [
                      Text(
                        bundle.nameHanNom!,
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'serif',
                          color: AppColors.primary,
                        ),
                      ),
                      if (bundle.readingHanNom != null)
                        Text(
                          bundle.readingHanNom!,
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                            color: AppColors.textSecondary,
                          ),
                        ),
                    ],
                  ),
                ),
            ],
          ),
          if (bundle.summaryVi != null) ...[
            const SizedBox(height: 10),
            Text(
              bundle.summaryVi!,
              style: const TextStyle(fontSize: 13, height: 1.4),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildClaimCard(BuildContext context, HistoricalClaimCitation claim) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: claim.isDisputed
              ? Colors.red[300]!
              : Colors.grey[250] ?? const Color(0xFFE0E0E0),
          width: claim.isDisputed ? 1.5 : 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Epistemic Uncertainty Badge
            Row(
              children: [
                EpistemicBadge(
                  certainty: claim.epistemicCertainty,
                  isCompact: true,
                ),
                const Spacer(),
                Text(
                  claim.claimType.toUpperCase(),
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[500],
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Claim statement (Vietnamese)
            Text(
              claim.statementVi,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                height: 1.4,
              ),
            ),

            // English statement if available
            if (claim.statementEn != null) ...[
              const SizedBox(height: 4),
              Text(
                claim.statementEn!,
                style: TextStyle(
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  color: Colors.grey[600],
                ),
              ),
            ],

            // Disputed Warning Banner
            if (claim.isDisputed) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.red[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red[200]!),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_rounded, color: Colors.red[700], size: 18),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        'Nội dung có ý kiến tranh luận học thuật. Chưa được công nhận là sử liệu đồng thuận tuyệt đối.',
                        style: TextStyle(
                          fontSize: 11,
                          color: Color(0xFFB71C1C),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 14),
            const Divider(height: 1),
            const SizedBox(height: 12),

            // Backing Sources List
            Text(
              'Thư tịch chứng minh (${claim.sources.length}):',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
            ),
            const SizedBox(height: 8),

            if (claim.sources.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Text(
                  'Chưa gắn nguồn thư tịch sơ cấp (đang khảo cứu).',
                  style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.orange[800]),
                ),
              )
            else
              ...claim.sources.map((src) => _buildSourceItem(context, src)),
          ],
        ),
      ),
    );
  }

  Widget _buildSourceItem(BuildContext context, SourceCitation source) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Source Title & Year
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.bookmark_outline, size: 16, color: AppColors.primary),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  source.sourceTitle,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
              if (source.publicationYear != null)
                Text(
                  '(${source.publicationYear})',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
            ],
          ),

          // Author & Publisher
          if (source.author != null || source.publisher != null) ...[
            const SizedBox(height: 4),
            Padding(
              padding: const EdgeInsets.only(left: 22),
              child: Text(
                [
                  if (source.author != null) source.author,
                  if (source.publisher != null) source.publisher,
                ].join(' • '),
                style: TextStyle(fontSize: 11, color: Colors.grey[700]),
              ),
            ),
          ],

          const SizedBox(height: 8),

          // Public Locator & Rights Chips
          Padding(
            padding: const EdgeInsets.only(left: 22),
            child: Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                // Public locator pill
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.primary.withOpacity(0.2)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.find_in_page_outlined, size: 12, color: AppColors.primary),
                      const SizedBox(width: 4),
                      Text(
                        source.locator,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: AppColors.primary,
                        ),
                      ),
                    ],
                  ),
                ),

                // Rights status chip
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: source.isRestrictedSnippet ? Colors.red[50] : Colors.green[50],
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: source.isRestrictedSnippet ? Colors.red[200]! : Colors.green[200]!,
                    ),
                  ),
                  child: Text(
                    source.rightsStatus.labelVi,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w500,
                      color: source.isRestrictedSnippet ? Colors.red[800] : Colors.green[800],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Excerpt Section (Redacted if restricted, visible if public domain)
          if (source.quotationExcerpt != null) ...[
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.only(left: 22),
              child: source.isRestrictedSnippet
                  ? Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.amber[50],
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: Colors.amber[300]!),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.lock_outline, size: 14, color: Colors.amber[900]),
                          const SizedBox(width: 6),
                          const Expanded(
                            child: Text(
                              '[REDACTED: RIGHTS_RESTRICTED] Trích đoạn văn bản được bảo lưu bản quyền. Tham khảo trực tiếp theo định danh lưu trữ.',
                              style: TextStyle(
                                fontSize: 10.5,
                                color: Color(0xFF795548),
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                  : Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: Text(
                        '“${source.quotationExcerpt}”',
                        style: const TextStyle(
                          fontSize: 11.5,
                          fontStyle: FontStyle.italic,
                          color: Colors.black87,
                        ),
                      ),
                    ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildProvenanceFooter(BuildContext context, EntityCitationBundle bundle) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.shield_outlined, size: 16, color: Colors.green),
              const SizedBox(width: 6),
              const Text(
                'Bảo Chứng Sử Liệu & Provenance Hash',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            'Mã băm chữ ký sử liệu: ${bundle.bundleProvenanceHash.substring(0, 16)}...',
            style: TextStyle(
              fontSize: 11,
              fontFamily: 'monospace',
              color: Colors.grey[700],
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Tư liệu được bảo chứng nguyên vẹn; bản ghi ngoại tuyến giữ nguyên xuất xứ nguồn thư tịch.',
            style: TextStyle(fontSize: 11, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }
}
