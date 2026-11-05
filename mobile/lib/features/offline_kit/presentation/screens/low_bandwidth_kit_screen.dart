import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../data/models/offline_kit_model.dart';

/// Low-Bandwidth Printable / Offline Kit Screen (Ticket V5-T096).
///
/// Ensures 100% learning outcomes are achievable offline without requiring
/// any AR, WebXR, camera permission, or high-end smartphone hardware.
class LowBandwidthKitScreen extends StatefulWidget {
  const LowBandwidthKitScreen({super.key});

  @override
  State<LowBandwidthKitScreen> createState() => _LowBandwidthKitScreenState();
}

class _LowBandwidthKitScreenState extends State<LowBandwidthKitScreen> {
  late LowBandwidthKitModel _kit;
  final Set<String> _completedStations = {};
  bool _highContrast = true;

  @override
  void initState() {
    super.initState();
    _kit = LowBandwidthKitModel.defaultStandard4();
  }

  void _markInspectionComplete(String slug) {
    setState(() {
      _completedStations.add(slug);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Đã ghi nhận khảo sát thực địa 2D / Giấy (+25 XP). Bình đẳng 100% với AR.',
          style: TextStyle(color: Colors.white, fontSize: 13),
        ),
        backgroundColor: Color(0xFF10B981),
        duration: Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        title: const Text(
          'Gói Học Tập Ngoại Tuyến (2D & Giấy)',
          style: TextStyle(color: AppColors.primary, fontSize: 16, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: Icon(
              _highContrast ? Icons.contrast : Icons.contrast_outlined,
              color: AppColors.primary,
            ),
            tooltip: 'Đổi chế độ tương phản cao',
            onPressed: () {
              setState(() {
                _highContrast = !_highContrast;
              });
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          // 1. Strict Equity & Offline Guarantee Banner
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: const Color(0xFF064E3B).withOpacity(0.4),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF10B981).withOpacity(0.6)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.verified_user_rounded,
                      color: Color(0xFF10B981),
                      size: 20,
                    ),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '100% HOÀN THÀNH TRÊN GIẤY • KHÔNG YÊU CẦU AR',
                        style: TextStyle(
                          color: Color(0xFF10B981),
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 6),
                Text(
                  'Học sinh hoàn thành trọn vẹn 100% mục tiêu bài học bằng phiếu in và bản dập 2D độ tương phản cao. Tuyệt đối không bắt buộc máy ảnh, smartphone hay kính AR.',
                  style: TextStyle(
                    color: Colors.white70,
                    height: 1.4,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.md),

          // 2. Stations List
          ..._kit.stations.map((station) {
            final isCompleted = _completedStations.contains(station.monumentSlug);

            return Card(
              margin: const EdgeInsets.only(bottom: AppSpacing.md),
              color: AppColors.surface,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(
                  color: isCompleted
                      ? const Color(0xFF10B981).withOpacity(0.6)
                      : AppColors.primary.withOpacity(0.2),
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Station Header
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            'TRẠM ${station.stationIndex}',
                            style: const TextStyle(
                              color: Colors.black,
                              fontWeight: FontWeight.bold,
                              fontSize: 11,
                            ),
                          ),
                        ),
                        Text(
                          'Khởi dựng: ${station.constructionYear}',
                          style: const TextStyle(
                            color: AppColors.primaryLight,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      station.monumentNameVi,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      station.zoneNameVi,
                      style: const TextStyle(
                        color: Colors.white60,
                        fontSize: 12,
                      ),
                    ),
                    const Divider(height: 20, color: Colors.white12),

                    // Primary Source Excerpt
                    Container(
                      padding: const EdgeInsets.all(AppSpacing.sm),
                      decoration: BoxDecoration(
                        color: Colors.black26,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.menu_book_rounded, size: 14, color: AppColors.primary),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  '${station.primarySource.sourceTitle} (${station.primarySource.volume})',
                                  style: const TextStyle(
                                    color: AppColors.primary,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 11,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '“${station.primarySource.citation}”',
                            style: const TextStyle(
                              color: Colors.white70,
                              fontStyle: FontStyle.italic,
                              height: 1.3,
                              fontSize: 12,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Nguồn: ${station.primarySource.rightsOwner} • ${station.primarySource.license}',
                            style: const TextStyle(
                              color: Colors.white38,
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // 2D Rubbing Note
                    Container(
                      padding: const EdgeInsets.all(AppSpacing.sm),
                      decoration: BoxDecoration(
                        color: _highContrast ? Colors.black : const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: _highContrast ? Colors.white70 : Colors.white24,
                          width: _highContrast ? 1.5 : 1.0,
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.photo_size_select_actual_outlined,
                            size: 20,
                            color: _highContrast ? Colors.white : AppColors.primary,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  station.rubbingAsset.captionVi,
                                  style: TextStyle(
                                    color: _highContrast ? Colors.white : AppColors.primaryLight,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 11,
                                  ),
                                ),
                                const Text(
                                  'Bản dập 2D độ tương phản cao phục vụ quan sát chi tiết hoa văn khi không dùng 3D/AR.',
                                  style: TextStyle(
                                    color: Colors.white60,
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Offline Inspection Task (100% paper achievable)
                    Text(
                      '📋 ${station.offlineTask.taskTitleVi}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      station.offlineTask.instructionsVi,
                      style: const TextStyle(
                        color: Colors.white70,
                        height: 1.3,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 6),
                    ...station.offlineTask.checkpoints.map(
                      (cp) => Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('• ', style: TextStyle(color: AppColors.primary)),
                            Expanded(
                              child: Text(
                                cp,
                                style: const TextStyle(
                                  color: Colors.white70,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Audio Guide Transcript (Zero streaming data)
                    Container(
                      padding: const EdgeInsets.all(AppSpacing.sm),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.04),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '🎙️ Toàn văn Thuyết minh Âm thanh',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11,
                                ),
                              ),
                              Text(
                                '0 MB Data',
                                style: TextStyle(
                                  color: Color(0xFF10B981),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            station.audioTranscript.scriptText,
                            style: const TextStyle(
                              color: Colors.white70,
                              fontStyle: FontStyle.italic,
                              height: 1.3,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Completion Action
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: isCompleted
                              ? const Color(0xFF064E3B)
                              : AppColors.primary,
                          foregroundColor: isCompleted ? Colors.white : Colors.black,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        onPressed: isCompleted
                            ? null
                            : () => _markInspectionComplete(station.monumentSlug),
                        icon: Icon(
                          isCompleted ? Icons.check_circle : Icons.edit_note_rounded,
                          size: 18,
                        ),
                        label: Text(
                          isCompleted
                              ? 'Đã hoàn thành khảo sát 2D / Giấy'
                              : 'Hoàn thành khảo sát trên giấy (+25 XP)',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
