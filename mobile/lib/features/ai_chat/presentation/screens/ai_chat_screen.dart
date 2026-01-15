import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/errors/exceptions.dart';

class AiChatScreen extends ConsumerStatefulWidget {
  final String? motifId;
  final String? urnSlug;

  const AiChatScreen({super.key, this.motifId, this.urnSlug});

  @override
  ConsumerState<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends ConsumerState<AiChatScreen> {
  final List<_ChatMessage> _messages = [];
  final TextEditingController _controller = TextEditingController();
  final TextEditingController _motifController = TextEditingController();
  final TextEditingController _urnController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isSending = false;
  AiChatMode _mode = AiChatMode.tutor;
  String _level = "beginner";
  String? _motifId;
  String? _urnSlug;

  @override
  void initState() {
    super.initState();
    _motifId = widget.motifId;
    _urnSlug = widget.urnSlug;
    _motifController.text = _motifId ?? "";
    _urnController.text = _urnSlug ?? "";
  }

  @override
  void dispose() {
    _controller.dispose();
    _motifController.dispose();
    _urnController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _isSending) return;

    setState(() {
      _isSending = true;
      _messages.add(_ChatMessage.user(text));
    });
    _controller.clear();
    _scrollToBottom();

    final apiClient = ref.read(apiClientProvider);
    try {
      final response = _mode == AiChatMode.tutor
          ? await apiClient.post<Map<String, dynamic>>(
              '/api/v1/ai/tutor',
              data: {
                'message': text,
                'history': _buildHistoryPayload(_messages),
                'context': _buildContextPayload(),
                'level': _level,
              },
              parser: (json) => json as Map<String, dynamic>,
            )
          : await apiClient.post<Map<String, dynamic>>(
              '/api/v1/ai/qa',
              data: {
                'question': text,
                'context': _buildContextPayload(),
                'limit': 6,
              },
              parser: (json) => json as Map<String, dynamic>,
            );

      final answer = (response['answer'] as String?)?.trim();
      final sources = _parseCitations(response['citations']);
      _appendAssistant(
        answer?.isNotEmpty == true
            ? answer!
            : 'AI chưa có phản hồi, thử lại nhé.',
        sources: sources,
      );
    } catch (err) {
      _appendAssistant(_formatErrorMessage(err));
    } finally {
      setState(() {
        _isSending = false;
      });
      _scrollToBottom();
    }
  }

  List<Map<String, String>> _buildHistoryPayload(List<_ChatMessage> history) {
    if (history.isEmpty) return [];
    final slice =
        history.length > 6 ? history.sublist(history.length - 6) : history;
    return slice
        .map(
          (message) => {
            'role': message.role.apiValue,
            'content': message.content,
          },
        )
        .toList();
  }

  Map<String, dynamic> _buildContextPayload() {
    return {
      if (_motifId != null && _motifId!.trim().isNotEmpty)
        'motif_id': _motifId!.trim(),
      if (_urnSlug != null && _urnSlug!.trim().isNotEmpty)
        'urn_slug': _urnSlug!.trim(),
    };
  }

  void _appendAssistant(String content, {List<_ChatCitation> sources = const []}) {
    setState(() {
      _messages.add(
        _ChatMessage.assistant(_normalizeAiContent(content), sources: sources),
      );
    });
  }

  List<_ChatCitation> _parseCitations(dynamic raw) {
    if (raw is! List) return const [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(_ChatCitation.fromJson)
        .toList();
  }

  String _normalizeAiContent(String content) {
    final trimmed = content.trim();
    if (trimmed.isEmpty) return content;
    final parsed = _tryParseJsonPayload(trimmed);
    if (parsed == null) return content;
    return _formatAiPayload(parsed);
  }

  dynamic _tryParseJsonPayload(String content) {
    try {
      return jsonDecode(content);
    } catch (_) {
      final payload = _extractJsonPayload(content);
      if (payload == null) return null;
      try {
        return jsonDecode(payload);
      } catch (_) {
        return null;
      }
    }
  }

  String? _extractJsonPayload(String content) {
    final fence = RegExp(r"```(?:json)?\\s*([\\s\\S]*?)```",
            caseSensitive: false)
        .firstMatch(content);
    if (fence != null) {
      final fenced = fence.group(1)?.trim();
      final candidate = _sliceJsonCandidate(fenced);
      return candidate ?? fenced;
    }
    return _sliceJsonCandidate(content);
  }

  String? _sliceJsonCandidate(String? content) {
    if (content == null || content.isEmpty) return null;
    final startObj = content.indexOf('{');
    final startArr = content.indexOf('[');
    final starts = [startObj, startArr].where((value) => value >= 0).toList();
    if (starts.isEmpty) return null;
    final start = starts.reduce((a, b) => a < b ? a : b);
    final endObj = content.lastIndexOf('}');
    final endArr = content.lastIndexOf(']');
    final end = endObj > endArr ? endObj : endArr;
    if (end <= start) return null;
    return content.substring(start, end + 1);
  }

  String _formatAiPayload(dynamic payload) {
    if (payload == null) return '';
    if (payload is List) {
      return payload.map((item) => '• ${item.toString()}').join('\n');
    }
    if (payload is Map<String, dynamic>) {
      if (payload.containsKey('summary') || payload.containsKey('key_points')) {
        final summary = payload['summary']?.toString() ?? '';
        final points = payload['key_points'];
        final formattedPoints = points is List
            ? points.map((item) => '• ${item.toString()}').join('\n')
            : '';
        return [
          if (summary.isNotEmpty) 'Tóm tắt: $summary',
          if (formattedPoints.isNotEmpty) 'Điểm chính:\n$formattedPoints',
        ].join('\n\n');
      }
      if (payload['cards'] is List) {
        final cards = (payload['cards'] as List)
            .map((item) {
              if (item is Map) {
                final front = item['front']?.toString() ?? '';
                final back = item['back']?.toString() ?? '';
                if (front.isNotEmpty || back.isNotEmpty) {
                  return '• $front → $back';
                }
              }
              return '• ${item.toString()}';
            })
            .join('\n');
        return cards.isEmpty ? '' : 'Flashcards:\n$cards';
      }
      if (payload['questions'] is List) {
        final questions = (payload['questions'] as List)
            .map((item) {
              if (item is Map) {
                return '• ${item['question_text'] ?? item['question'] ?? ''}';
              }
              return '• ${item.toString()}';
            })
            .join('\n');
        return questions.isEmpty ? '' : 'Câu hỏi chẩn đoán:\n$questions';
      }
      if (payload.containsKey('message') || payload.containsKey('weekly_plan')) {
        final message = payload['message']?.toString() ?? '';
        final plan = payload['weekly_plan'];
        final formattedPlan = plan is List
            ? plan.map((item) => '• ${item.toString()}').join('\n')
            : '';
        return [
          if (message.isNotEmpty) message,
          if (formattedPlan.isNotEmpty) 'Kế hoạch tuần:\n$formattedPlan',
        ].join('\n\n');
      }
      return const JsonEncoder.withIndent('  ').convert(payload);
    }
    return payload.toString();
  }

  Future<void> _runSummary() async {
    if (_isSending) return;
    final payload = _buildContextPayload();
    if (payload.isEmpty) {
      _appendAssistant('Chọn họa tiết hoặc đỉnh để tóm tắt nhé.');
      return;
    }
    await _runAction(
      () async {
        final apiClient = ref.read(apiClientProvider);
        final response = await apiClient.post<Map<String, dynamic>>(
          '/api/v1/ai/summary',
          data: payload,
          parser: (json) => json as Map<String, dynamic>,
        );
        final summary = (response['summary'] as String?)?.trim() ?? '';
        final keyPoints = response['key_points'] as List<dynamic>? ?? [];
        final points = keyPoints.map((item) => '• ${item.toString()}').join('\n');
        return [
          'Tóm tắt nhanh:\n$summary',
          if (points.isNotEmpty) 'Điểm chính:\n$points',
        ].join('\n\n');
      },
    );
  }

  Future<void> _runFlashcards() async {
    if (_isSending) return;
    await _runAction(
      () async {
        final apiClient = ref.read(apiClientProvider);
        final response = await apiClient.post<Map<String, dynamic>>(
          '/api/v1/ai/flashcards',
          data: {
            'motif_id': _motifId,
            'topic': _motifId == null && _urnSlug == null ? 'Cửu Đỉnh' : null,
            'count': 6,
          },
          parser: (json) => json as Map<String, dynamic>,
        );
        final cards = response['cards'] as List<dynamic>? ?? [];
        if (cards.isEmpty) {
          return 'Chưa tạo được flashcards, thử lại nhé.';
        }
        final formatted = cards.map((card) {
          if (card is Map<String, dynamic>) {
            final front = card['front']?.toString() ?? '';
            final back = card['back']?.toString() ?? '';
            return '• $front → $back';
          }
          return '• ${card.toString()}';
        }).join('\n');
        return 'Flashcards:\n$formatted';
      },
    );
  }

  Future<void> _runExplain() async {
    if (_isSending) return;
    final controller = TextEditingController();
    String level = 'teen';
    final result = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        final viewInsets = MediaQuery.of(context).viewInsets;
        return Padding(
          padding: EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.lg,
            AppSpacing.lg,
            viewInsets.bottom + AppSpacing.navBarInset,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Giải thích theo cấp độ',
                  style: AppTypography.textTheme.titleLarge?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                TextField(
                  controller: controller,
                  minLines: 2,
                  maxLines: 4,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: Colors.white,
                  ),
                  decoration: InputDecoration(
                    hintText: 'Nhập nội dung cần giải thích...',
                    hintStyle: TextStyle(color: Colors.white.withOpacity(0.5)),
                    filled: true,
                    fillColor: AppColors.surfaceElevated.withOpacity(0.7),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide:
                          BorderSide(color: Colors.white.withOpacity(0.1)),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                DropdownButtonFormField<String>(
                  value: level,
                  dropdownColor: AppColors.surface,
                  decoration: InputDecoration(
                    labelText: 'Mức độ',
                    labelStyle: TextStyle(color: Colors.white.withOpacity(0.7)),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide:
                          BorderSide(color: Colors.white.withOpacity(0.1)),
                    ),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'child', child: Text('12 tuổi')),
                    DropdownMenuItem(value: 'teen', child: Text('18 tuổi')),
                    DropdownMenuItem(value: 'expert', child: Text('Chuyên gia')),
                  ],
                  onChanged: (value) {
                    level = value ?? 'teen';
                  },
                ),
                const SizedBox(height: AppSpacing.md),
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Huỷ'),
                      ),
                    ),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.pop(
                            context,
                            controller.text.trim().isEmpty
                                ? null
                                : '$level||${controller.text.trim()}',
                          );
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: AppColors.onPrimary,
                        ),
                        child: const Text('Giải thích'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );

    if (result == null) return;
    final parts = result.split('||');
    if (parts.length != 2) return;
    final levelValue = parts[0];
    final text = parts[1];
    await _runAction(
      () async {
        final apiClient = ref.read(apiClientProvider);
        final response = await apiClient.post<Map<String, dynamic>>(
          '/api/v1/ai/explain',
          data: {'text': text, 'level': levelValue},
          parser: (json) => json as Map<String, dynamic>,
        );
        final explanation = (response['explanation'] as String?)?.trim() ?? '';
        return explanation.isNotEmpty
            ? explanation
            : 'AI chưa có phản hồi, thử lại nhé.';
      },
    );
  }

  Future<void> _runCoach() async {
    if (_isSending) return;
    await _runAction(
      () async {
        final apiClient = ref.read(apiClientProvider);
        final response = await apiClient.post<Map<String, dynamic>>(
          '/api/v1/ai/coach',
          data: {},
          parser: (json) => json as Map<String, dynamic>,
        );
        final message = (response['message'] as String?)?.trim() ?? '';
        final plan = response['weekly_plan'] as List<dynamic>? ?? [];
        final planText = plan.map((item) => '• ${item.toString()}').join('\n');
        return [
          message.isEmpty ? 'Coach: hãy học đều đặn mỗi ngày.' : message,
          if (planText.isNotEmpty) 'Kế hoạch tuần:\n$planText',
        ].join('\n\n');
      },
    );
  }

  Future<void> _runReviewPlan() async {
    if (_isSending) return;
    await _runAction(
      () async {
        final apiClient = ref.read(apiClientProvider);
        final response = await apiClient.get<Map<String, dynamic>>(
          '/api/v1/ai/review-plan',
          parser: (json) => json as Map<String, dynamic>,
        );
        final items = response['items'] as List<dynamic>? ?? [];
        if (items.isEmpty) {
          return 'Chưa có kế hoạch ôn tập.';
        }
        final formatted = items.map((item) {
          if (item is Map<String, dynamic>) {
            final name = item['motif_name']?.toString() ?? 'Họa tiết';
            final due = item['due_in_days']?.toString() ?? '0';
            return '• $name (còn $due ngày)';
          }
          return '• ${item.toString()}';
        }).join('\n');
        return 'Kế hoạch ôn tập:\n$formatted';
      },
    );
  }

  Future<void> _runDiagnostic() async {
    if (_isSending) return;
    await _runAction(
      () async {
        final apiClient = ref.read(apiClientProvider);
        final response = await apiClient.post<Map<String, dynamic>>(
          '/api/v1/ai/diagnostic',
          data: {
            if (_urnSlug != null && _urnSlug!.isNotEmpty)
              'urn_slug': _urnSlug,
            'count': 6,
          },
          parser: (json) => json as Map<String, dynamic>,
        );
        final questions = response['questions'] as List<dynamic>? ?? [];
        if (questions.isEmpty) {
          return 'Chưa tạo được bài chẩn đoán.';
        }
        final formatted = questions.map((item) {
          if (item is Map<String, dynamic>) {
            final question = item['question_text']?.toString() ?? '';
            return '• $question';
          }
          return '• ${item.toString()}';
        }).join('\n');
        return 'Câu hỏi chẩn đoán:\n$formatted';
      },
    );
  }

  Future<void> _runFeedbackDialog() async {
    if (_isSending) return;
    final questionController = TextEditingController();
    final correctController = TextEditingController();
    final answerController = TextEditingController();

    final shouldSend = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: AppColors.surface,
          title: Text(
            'Phản hồi bài làm',
            style: AppTypography.textTheme.titleMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
          content: SingleChildScrollView(
            child: Column(
              children: [
                TextField(
                  controller: questionController,
                  minLines: 2,
                  maxLines: 4,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: Colors.white,
                  ),
                  decoration: InputDecoration(
                    hintText: 'Câu hỏi',
                    hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                    filled: true,
                    fillColor: AppColors.surfaceElevated.withOpacity(0.6),
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                TextField(
                  controller: correctController,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: Colors.white,
                  ),
                  decoration: InputDecoration(
                    hintText: 'Đáp án đúng',
                    hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                    filled: true,
                    fillColor: AppColors.surfaceElevated.withOpacity(0.6),
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                TextField(
                  controller: answerController,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: Colors.white,
                  ),
                  decoration: InputDecoration(
                    hintText: 'Câu trả lời của bạn',
                    hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                    filled: true,
                    fillColor: AppColors.surfaceElevated.withOpacity(0.6),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Huỷ'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
              ),
              child: const Text('Gửi'),
            ),
          ],
        );
      },
    );

    if (shouldSend != true) {
      questionController.dispose();
      correctController.dispose();
      answerController.dispose();
      return;
    }

    final question = questionController.text.trim();
    final correct = correctController.text.trim();
    final answer = answerController.text.trim();
    questionController.dispose();
    correctController.dispose();
    answerController.dispose();

    if (question.isEmpty || correct.isEmpty || answer.isEmpty) {
      _appendAssistant('Nhập đủ câu hỏi và đáp án trước nhé.');
      return;
    }

    await _runAction(
      () async {
        final apiClient = ref.read(apiClientProvider);
        final response = await apiClient.post<Map<String, dynamic>>(
          '/api/v1/ai/feedback',
          data: {
            'question': question,
            'correct_answer': correct,
            'user_answer': answer,
            'context': _buildContextPayload(),
          },
          parser: (json) => json as Map<String, dynamic>,
        );
        final explanation = response['explanation']?.toString() ?? '';
        final nextStep = response['next_step']?.toString() ?? '';
        final isCorrect = response['is_correct'] == true;
        final parts = <String>[
          isCorrect ? 'Kết quả: Đúng ✅' : 'Kết quả: Chưa đúng ❌',
          if (explanation.isNotEmpty) 'Giải thích: $explanation',
          if (nextStep.isNotEmpty) 'Gợi ý tiếp theo: $nextStep',
        ];
        return parts.join('\n\n');
      },
    );
  }

  Future<void> _runAction(Future<String> Function() handler) async {
    setState(() {
      _isSending = true;
    });
    try {
      final response = await handler();
      _appendAssistant(response);
    } catch (err) {
      _appendAssistant(_formatErrorMessage(err));
    } finally {
      setState(() {
        _isSending = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent + 80,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  String _formatErrorMessage(Object err) {
    if (err is AuthException) {
      return 'Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.';
    }
    if (err is NetworkException) {
      return err.message;
    }
    if (err is TimeoutException) {
      return 'Kết nối quá chậm, thử lại sau nhé.';
    }
    if (err is ServerException) {
      if (err.statusCode == 503) {
        return 'AI chưa được cấu hình trên máy chủ.';
      }
      if (err.statusCode == 502) {
        return 'AI đang bận, thử lại sau nhé.';
      }
      return err.message;
    }
    return 'AI đang bận, thử lại sau nhé.';
  }

  Future<void> _openSettingsSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        AiChatMode tempMode = _mode;
        String tempLevel = _level;
        final viewInsets = MediaQuery.of(context).viewInsets;
        return Padding(
          padding: EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.lg,
            AppSpacing.lg,
            viewInsets.bottom + AppSpacing.navBarInset,
          ),
          child: SingleChildScrollView(
            child: StatefulBuilder(
              builder: (context, setSheetState) {
                return Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Tuỳ chỉnh AI',
                      style: AppTypography.textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    DropdownButtonFormField<AiChatMode>(
                      value: tempMode,
                      dropdownColor: AppColors.surface,
                      decoration: InputDecoration(
                        labelText: 'Chế độ',
                        labelStyle:
                            TextStyle(color: Colors.white.withOpacity(0.7)),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide:
                              BorderSide(color: Colors.white.withOpacity(0.1)),
                        ),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: AiChatMode.tutor,
                          child: Text('Tutor'),
                        ),
                        DropdownMenuItem(
                          value: AiChatMode.qa,
                          child: Text('Q&A'),
                        ),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setSheetState(() => tempMode = value);
                      },
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    DropdownButtonFormField<String>(
                      value: tempLevel,
                      dropdownColor: AppColors.surface,
                      decoration: InputDecoration(
                        labelText: 'Mức độ',
                        labelStyle:
                            TextStyle(color: Colors.white.withOpacity(0.7)),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide:
                              BorderSide(color: Colors.white.withOpacity(0.1)),
                        ),
                      ),
                      items: const [
                        DropdownMenuItem(
                            value: 'beginner', child: Text('Cơ bản')),
                        DropdownMenuItem(
                          value: 'intermediate',
                          child: Text('Trung bình'),
                        ),
                        DropdownMenuItem(
                            value: 'advanced', child: Text('Nâng cao')),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setSheetState(() => tempLevel = value);
                      },
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    TextField(
                      controller: _motifController,
                      style: AppTypography.textTheme.bodyMedium?.copyWith(
                        color: Colors.white,
                      ),
                      decoration: InputDecoration(
                        hintText: 'Motif ID (tuỳ chọn)',
                        hintStyle:
                            TextStyle(color: Colors.white.withOpacity(0.4)),
                        filled: true,
                        fillColor: AppColors.surfaceElevated.withOpacity(0.6),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide:
                              BorderSide(color: Colors.white.withOpacity(0.1)),
                        ),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    TextField(
                      controller: _urnController,
                      style: AppTypography.textTheme.bodyMedium?.copyWith(
                        color: Colors.white,
                      ),
                      decoration: InputDecoration(
                        hintText: 'Urn slug (tuỳ chọn)',
                        hintStyle:
                            TextStyle(color: Colors.white.withOpacity(0.4)),
                        filled: true,
                        fillColor: AppColors.surfaceElevated.withOpacity(0.6),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide:
                              BorderSide(color: Colors.white.withOpacity(0.1)),
                        ),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    Row(
                      children: [
                        Expanded(
                          child: TextButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('Huỷ'),
                          ),
                        ),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () {
                              setState(() {
                                _mode = tempMode;
                                _level = tempLevel;
                                _motifId = _motifController.text.trim();
                                _urnSlug = _urnController.text.trim();
                              });
                              Navigator.pop(context);
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: AppColors.onPrimary,
                            ),
                            child: const Text('Lưu'),
                          ),
                        ),
                      ],
                    ),
                  ],
                );
              },
            ),
          ),
        );
      },
    );
  }

  Future<void> _openActionsSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        final viewInsets = MediaQuery.of(context).viewInsets;
        return Padding(
          padding: EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.lg,
            AppSpacing.lg,
            viewInsets.bottom + AppSpacing.navBarInset,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Hành động nhanh',
                  style: AppTypography.textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                _ActionRow(label: 'Tóm tắt', onTap: () {
                  Navigator.pop(context);
                  _runSummary();
                }),
                _ActionRow(label: 'Flashcards', onTap: () {
                  Navigator.pop(context);
                  _runFlashcards();
                }),
                _ActionRow(label: 'Giải thích', onTap: () {
                  Navigator.pop(context);
                  _runExplain();
                }),
                _ActionRow(label: 'Coach', onTap: () {
                  Navigator.pop(context);
                  _runCoach();
                }),
                _ActionRow(label: 'Ôn tập', onTap: () {
                  Navigator.pop(context);
                  _runReviewPlan();
                }),
                _ActionRow(label: 'Chẩn đoán', onTap: () {
                  Navigator.pop(context);
                  _runDiagnostic();
                }),
                _ActionRow(label: 'Phản hồi bài làm', onTap: () {
                  Navigator.pop(context);
                  _runFeedbackDialog();
                }),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final viewInsets = MediaQuery.of(context).viewInsets;
    return Scaffold(
      backgroundColor: AppColors.background,
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: const Text('AI Chat'),
        actions: [
          IconButton(
            onPressed: _openActionsSheet,
            icon: const Icon(Icons.auto_awesome_outlined),
            tooltip: 'Hành động',
          ),
          IconButton(
            onPressed: _openSettingsSheet,
            icon: const Icon(Icons.tune),
            tooltip: 'Tuỳ chỉnh',
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg,
                AppSpacing.sm,
                AppSpacing.lg,
                AppSpacing.xs,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      _mode == AiChatMode.tutor
                          ? 'Tutor · ${_level == "beginner" ? "Cơ bản" : _level == "intermediate" ? "Trung bình" : "Nâng cao"}'
                          : 'Q&A · Nguồn nội bộ',
                      style: AppTypography.textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                  if ((_motifId ?? "").isNotEmpty || (_urnSlug ?? "").isNotEmpty)
                    Text(
                      [
                        if ((_motifId ?? "").isNotEmpty) 'Motif',
                        if ((_urnSlug ?? "").isNotEmpty) 'Urn',
                      ].join(' · '),
                      style: AppTypography.textTheme.bodySmall?.copyWith(
                        color: AppColors.primaryLight,
                      ),
                    ),
                ],
              ),
            ),
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.lg,
                  AppSpacing.sm,
                  AppSpacing.lg,
                  AppSpacing.sm,
                ),
                itemCount: _messages.length + (_isSending ? 1 : 0),
                itemBuilder: (context, index) {
                  if (_isSending && index == _messages.length) {
                    return _buildTypingBubble();
                  }
                  final message = _messages[index];
                  return _buildChatBubble(message);
                },
              ),
            ),
            AnimatedPadding(
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
              padding: EdgeInsets.fromLTRB(
                AppSpacing.lg,
                AppSpacing.sm,
                AppSpacing.lg,
                AppSpacing.sm + viewInsets.bottom,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      minLines: 1,
                      maxLines: 4,
                      style: AppTypography.textTheme.bodyMedium?.copyWith(
                        color: Colors.white,
                      ),
                      decoration: InputDecoration(
                        hintText: 'Nhập câu hỏi...',
                        hintStyle: TextStyle(
                          color: Colors.white.withOpacity(0.5),
                        ),
                        filled: true,
                        fillColor: AppColors.surface,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.md,
                          vertical: AppSpacing.sm,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(
                            color: Colors.white.withOpacity(0.08),
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(
                            color: Colors.white.withOpacity(0.08),
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(
                            color: AppColors.primary.withOpacity(0.5),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  SizedBox(
                    height: 48,
                    width: 48,
                    child: ElevatedButton(
                      onPressed: _isSending ? null : _sendMessage,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: AppColors.onPrimary,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                        padding: EdgeInsets.zero,
                      ),
                      child: const Icon(Icons.send),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChatBubble(_ChatMessage message) {
    final isUser = message.role == ChatRole.user;
    final alignment = isUser ? Alignment.centerRight : Alignment.centerLeft;
    final bubbleColor = isUser
        ? AppColors.primary.withOpacity(0.9)
        : AppColors.surface.withOpacity(0.7);
    final borderColor = isUser
        ? AppColors.primaryLight.withOpacity(0.5)
        : Colors.white.withOpacity(0.1);
    final textColor = isUser ? AppColors.onPrimary : Colors.white;
    final textStyle = AppTypography.textTheme.bodyMedium?.copyWith(
      color: textColor,
      height: 1.4,
    );
    final markdownStyle = MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
      p: textStyle,
      strong: textStyle?.copyWith(fontWeight: FontWeight.w700),
      em: textStyle,
      listBullet: textStyle,
      a: textStyle?.copyWith(color: AppColors.primaryLight),
      code: textStyle?.copyWith(
        fontFamily: 'monospace',
        backgroundColor: Colors.white.withOpacity(0.12),
      ),
      blockquoteDecoration: BoxDecoration(
        color: Colors.white.withOpacity(0.06),
        borderRadius: BorderRadius.circular(8),
        border: Border(
          left: BorderSide(
            color: AppColors.primaryLight.withOpacity(0.6),
            width: 2,
          ),
        ),
      ),
    );

    return Align(
      alignment: alignment,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        constraints: const BoxConstraints(maxWidth: 320),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: borderColor, width: 1),
        ),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            MarkdownBody(
              data: message.content,
              selectable: true,
              styleSheet: markdownStyle,
            ),
            if (!isUser && message.sources.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.sm),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(AppSpacing.sm),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.white.withOpacity(0.08)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Nguồn tham khảo',
                      style: AppTypography.textTheme.bodySmall?.copyWith(
                        color: Colors.white.withOpacity(0.8),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 6),
                    for (final source in message.sources)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'S${source.index} · ${source.title}',
                              style:
                                  AppTypography.textTheme.bodySmall?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            if (source.snippet.isNotEmpty)
                              Text(
                                source.snippet,
                                style:
                                    AppTypography.textTheme.bodySmall?.copyWith(
                                  color: Colors.white.withOpacity(0.7),
                                ),
                              ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTypingBubble() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: BoxDecoration(
          color: AppColors.surface.withOpacity(0.7),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: Colors.white.withOpacity(0.1),
          ),
        ),
        child: Text(
          'AI đang trả lời...',
          style: AppTypography.textTheme.bodySmall?.copyWith(
            color: Colors.white.withOpacity(0.7),
          ),
        ),
      ),
    );
  }
}

enum AiChatMode { tutor, qa }

class _ActionRow extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _ActionRow({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(
        label,
        style: AppTypography.textTheme.bodyMedium?.copyWith(
          color: Colors.white,
          fontWeight: FontWeight.w600,
        ),
      ),
      trailing: const Icon(Icons.chevron_right, color: Colors.white70),
      onTap: onTap,
    );
  }
}

enum ChatRole {
  user,
  assistant;

  String get apiValue {
    switch (this) {
      case ChatRole.user:
        return 'user';
      case ChatRole.assistant:
        return 'assistant';
    }
  }
}

class _ChatMessage {
  final ChatRole role;
  final String content;
  final List<_ChatCitation> sources;

  const _ChatMessage({
    required this.role,
    required this.content,
    this.sources = const [],
  });

  factory _ChatMessage.user(String content) {
    return _ChatMessage(role: ChatRole.user, content: content);
  }

  factory _ChatMessage.assistant(
    String content, {
    List<_ChatCitation> sources = const [],
  }) {
    return _ChatMessage(
      role: ChatRole.assistant,
      content: content,
      sources: sources,
    );
  }
}

class _ChatCitation {
  final int index;
  final String title;
  final String snippet;

  const _ChatCitation({
    required this.index,
    required this.title,
    required this.snippet,
  });

  factory _ChatCitation.fromJson(Map<String, dynamic> json) {
    return _ChatCitation(
      index: json['index'] is int ? json['index'] as int : 0,
      title: (json['title'] as String?)?.trim().isNotEmpty == true
          ? json['title'] as String
          : 'Nguồn tham khảo',
      snippet: (json['snippet'] as String?)?.trim() ?? '',
    );
  }
}
