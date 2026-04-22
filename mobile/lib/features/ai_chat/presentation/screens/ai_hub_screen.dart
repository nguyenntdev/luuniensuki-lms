import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/ai_chat_service.dart';

class AiHubScreen extends ConsumerStatefulWidget {
  const AiHubScreen({super.key});

  @override
  ConsumerState<AiHubScreen> createState() => _AiHubScreenState();
}

enum _AiMode { tutor, qa }

class _AiMessage {
  final String id;
  final String role;
  final String content;
  final List<Map<String, String>> sources;

  const _AiMessage({
    required this.id,
    required this.role,
    required this.content,
    this.sources = const [],
  });
}

class _AiHubScreenState extends ConsumerState<AiHubScreen> {
  final TextEditingController _inputController = TextEditingController();
  final TextEditingController _motifController = TextEditingController();
  final TextEditingController _urnController = TextEditingController();
  final TextEditingController _explainController = TextEditingController();
  final TextEditingController _feedbackQuestionController =
      TextEditingController();
  final TextEditingController _feedbackCorrectController =
      TextEditingController();
  final TextEditingController _feedbackAnswerController =
      TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<_AiMessage> _messages = [
    const _AiMessage(
      id: 'welcome',
      role: 'assistant',
      content:
          'Chào bạn! Mình là AI Tutor. Hãy hỏi về bài học, quiz hoặc nhờ tóm tắt nội dung nhé.',
    ),
  ];

  _AiMode _mode = _AiMode.tutor;
  String _level = 'beginner';
  String _explainLevel = 'teen';
  bool _isSending = false;
  String? _error;

  @override
  void dispose() {
    _inputController.dispose();
    _motifController.dispose();
    _urnController.dispose();
    _explainController.dispose();
    _feedbackQuestionController.dispose();
    _feedbackCorrectController.dispose();
    _feedbackAnswerController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Map<String, dynamic>? get _contextPayload {
    final motifId = _motifController.text.trim();
    final urnSlug = _urnController.text.trim();
    final payload = <String, dynamic>{};
    if (motifId.isNotEmpty) payload['motif_id'] = motifId;
    if (urnSlug.isNotEmpty) payload['urn_slug'] = urnSlug;
    return payload.isEmpty ? null : payload;
  }

  List<Map<String, String>> _buildHistory() {
    return _messages
        .where((m) => m.role == 'user' || m.role == 'assistant')
        .take(10)
        .map((m) => {'role': m.role, 'content': m.content})
        .toList();
  }

  String _normalizeAiContent(dynamic payload) {
    if (payload == null) return '';
    if (payload is String) {
      final trimmed = payload.trim();
      return trimmed.isEmpty ? payload : trimmed;
    }

    if (payload is List) {
      return payload.map((item) => '• ${item.toString()}').join('\n');
    }

    if (payload is Map<String, dynamic>) {
      if (payload['summary'] != null || payload['key_points'] != null) {
        final points = (payload['key_points'] as List?)
                ?.map((item) => '• $item')
                .join('\n') ??
            '';
        return [
          if (payload['summary'] != null) 'Tóm tắt: ${payload['summary']}',
          if (points.isNotEmpty) 'Điểm chính:\n$points',
        ].join('\n\n');
      }

      if (payload['cards'] is List) {
        final cards = (payload['cards'] as List).map((card) {
          if (card is Map<String, dynamic>) {
            final front = card['front'] ?? card['question'] ?? 'Thẻ';
            final back = card['back'] ?? card['answer'] ?? '';
            return '• $front → $back';
          }
          return '• $card';
        }).join('\n');
        return 'Flashcards:\n$cards';
      }

      if (payload['questions'] is List) {
        final questions = (payload['questions'] as List)
            .map((q) => q is Map<String, dynamic>
                ? '• ${q['question_text'] ?? q['question'] ?? q}'
                : '• $q')
            .join('\n');
        return 'Câu hỏi chẩn đoán:\n$questions';
      }

      if (payload['message'] != null || payload['weekly_plan'] is List) {
        final weeklyPlan = (payload['weekly_plan'] as List?)
                ?.map((item) => '• $item')
                .join('\n') ??
            '';
        return [
          if (payload['message'] != null) payload['message'].toString(),
          if (weeklyPlan.isNotEmpty) 'Kế hoạch tuần:\n$weeklyPlan',
        ].join('\n\n');
      }
    }

    return payload.toString();
  }

  List<Map<String, String>> _formatSources(dynamic citations) {
    if (citations is! List) return const [];
    return citations
        .whereType<Map>()
        .map(
          (source) => {
            'title': (source['title'] ?? 'Nguồn tham khảo').toString(),
            'snippet': (source['snippet'] ?? '').toString(),
            'type': (source['source_type'] ?? 'source').toString(),
          },
        )
        .toList();
  }

  void _appendMessage({
    required String role,
    required String content,
    List<Map<String, String>> sources = const [],
  }) {
    setState(() {
      _messages.add(
        _AiMessage(
          id: '$role-${DateTime.now().microsecondsSinceEpoch}',
          role: role,
          content: _normalizeAiContent(content),
          sources: sources,
        ),
      );
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent + 120,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  String _normalizeError(Object error) {
    final text = error.toString();
    final lower = text.toLowerCase();
    if (text.contains('502') ||
        lower.contains('deepseek') ||
        lower.contains('ai')) {
      return 'AI đang bận, thử lại sau nhé.';
    }
    return text;
  }

  Future<void> _sendChat() async {
    final text = _inputController.text.trim();
    if (text.isEmpty || _isSending) return;

    final authState = ref.read(authNotifierProvider);
    if (!authState.isAuthenticated) {
      setState(() => _error = 'Hãy đăng nhập để sử dụng AI Tutor.');
      return;
    }

    _appendMessage(role: 'user', content: text);
    _inputController.clear();

    setState(() {
      _isSending = true;
      _error = null;
    });

    final ai = ref.read(aiChatServiceProvider);

    try {
      final response = _mode == _AiMode.tutor
          ? await ai.tutor(
              message: text,
              history: _buildHistory(),
              context: _contextPayload,
              level: _level,
            )
          : await ai.qa(
              question: text,
              context: _contextPayload,
              limit: 6,
            );

      final content = response['response'] ??
          response['answer'] ??
          response['message'] ??
          response;
      final sources = _formatSources(response['citations']);
      _appendMessage(
        role: 'assistant',
        content: _normalizeAiContent(content),
        sources: sources,
      );
    } catch (error) {
      setState(() => _error = _normalizeError(error));
      _appendMessage(
          role: 'assistant', content: 'AI đang bận, thử lại sau nhé.');
    } finally {
      if (mounted) {
        setState(() => _isSending = false);
      }
    }
  }

  Future<void> _runAction(
      Future<String> Function() action, String fallback) async {
    if (_isSending) return;

    final authState = ref.read(authNotifierProvider);
    if (!authState.isAuthenticated) {
      setState(() => _error = 'Hãy đăng nhập để sử dụng AI.');
      return;
    }

    setState(() {
      _isSending = true;
      _error = null;
    });

    try {
      final result = await action();
      _appendMessage(
          role: 'assistant', content: result.isEmpty ? fallback : result);
    } catch (error) {
      setState(() => _error = _normalizeError(error));
      _appendMessage(role: 'assistant', content: fallback);
    } finally {
      if (mounted) {
        setState(() => _isSending = false);
      }
    }
  }

  Future<void> _handleSummary() async {
    await _runAction(() async {
      final ai = ref.read(aiChatServiceProvider);
      final response = await ai.summary(
        motifId: _motifController.text.trim().isEmpty
            ? null
            : _motifController.text.trim(),
        urnSlug: _urnController.text.trim().isEmpty
            ? null
            : _urnController.text.trim(),
      );
      return _normalizeAiContent(response);
    }, 'Chưa thể tóm tắt, thử lại nhé.');
  }

  Future<void> _handleFlashcards() async {
    await _runAction(() async {
      final ai = ref.read(aiChatServiceProvider);
      final response = await ai.flashcards(
        motifId: _motifController.text.trim().isEmpty
            ? null
            : _motifController.text.trim(),
        topic: (_motifController.text.trim().isEmpty &&
                _urnController.text.trim().isEmpty)
            ? 'Cửu Đỉnh'
            : null,
        count: 6,
        level: _level,
      );
      return _normalizeAiContent(response);
    }, 'Không tạo được flashcards lúc này.');
  }

  Future<void> _handleCoach() async {
    await _runAction(() async {
      final ai = ref.read(aiChatServiceProvider);
      final response = await ai.coach();
      return _normalizeAiContent(response);
    }, 'Không thể tạo coach plan lúc này.');
  }

  Future<void> _handleReviewPlan() async {
    await _runAction(() async {
      final ai = ref.read(aiChatServiceProvider);
      final response = await ai.reviewPlan();
      return _normalizeAiContent(response);
    }, 'Không thể tạo kế hoạch ôn tập.');
  }

  Future<void> _handleDiagnostic() async {
    await _runAction(() async {
      final ai = ref.read(aiChatServiceProvider);
      final response = await ai.diagnostic(
        urnSlug: _urnController.text.trim().isEmpty
            ? null
            : _urnController.text.trim(),
        count: 6,
        level: _level,
      );
      return _normalizeAiContent(response);
    }, 'Không thể tạo bài chẩn đoán.');
  }

  Future<void> _handleExplain() async {
    final explainText = _explainController.text.trim();
    if (explainText.isEmpty) {
      setState(() => _error = 'Nhập nội dung cần giải thích trước nhé.');
      return;
    }

    await _runAction(() async {
      final ai = ref.read(aiChatServiceProvider);
      final response =
          await ai.explain(text: explainText, level: _explainLevel);
      _explainController.clear();
      return _normalizeAiContent(response['explanation'] ?? response);
    }, 'Không thể giải thích lúc này.');
  }

  Future<void> _handleFeedback() async {
    final question = _feedbackQuestionController.text.trim();
    final correct = _feedbackCorrectController.text.trim();
    final answer = _feedbackAnswerController.text.trim();

    if (question.isEmpty || correct.isEmpty || answer.isEmpty) {
      setState(() {
        _error = 'Nhập đủ câu hỏi, đáp án đúng và câu trả lời của bạn.';
      });
      return;
    }

    await _runAction(() async {
      final ai = ref.read(aiChatServiceProvider);
      final response = await ai.feedback(
        question: question,
        correctAnswer: correct,
        userAnswer: answer,
        context: _contextPayload,
      );
      _feedbackQuestionController.clear();
      _feedbackCorrectController.clear();
      _feedbackAnswerController.clear();
      return _normalizeAiContent(response);
    }, 'Chưa tạo được phản hồi.');
  }

  @override
  Widget build(BuildContext context) {
    final isAuthed = ref.watch(authNotifierProvider).isAuthenticated;

    return AnimatedGradientBackground(
      child: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.md,
                AppSpacing.sm,
                AppSpacing.md,
                AppSpacing.xs,
              ),
              child: _buildCompactHeader(context),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md,
                  0,
                  AppSpacing.md,
                  AppSpacing.xs,
                ),
                child: _buildErrorBanner(),
              ),
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md,
                  0,
                  AppSpacing.md,
                  AppSpacing.md,
                ),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final message = _messages[index];
                  return _buildMessageBubble(message);
                },
              ),
            ),
            _buildComposer(isAuthed),
          ],
        ),
      ),
    );
  }

  Widget _buildCompactHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface.withOpacity(0.36),
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        border: Border.all(color: AppColors.glassBorder.withOpacity(0.8)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              'AI Tutor',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          _buildModeChip(_AiMode.tutor, 'Tutor'),
          const SizedBox(width: 6),
          _buildModeChip(_AiMode.qa, 'Q&A'),
          const SizedBox(width: 6),
          IconButton(
            onPressed: _isSending ? null : () => _openToolsSheet(context),
            splashRadius: 18,
            icon: const Icon(Icons.tune_rounded, size: 20),
            color: AppColors.textSecondary,
            tooltip: 'AI Tools',
          ),
        ],
      ),
    );
  }

  Widget _buildErrorBanner() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.error.withOpacity(0.14),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.error.withOpacity(0.35)),
      ),
      child: Text(
        _error!,
        style: TextStyle(
          color: AppColors.error,
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Future<void> _openToolsSheet(BuildContext context) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        final bottomPadding = MediaQuery.of(sheetContext).viewInsets.bottom;
        return SafeArea(
          top: false,
          child: Container(
            margin: const EdgeInsets.fromLTRB(10, 0, 10, 10),
            padding: EdgeInsets.fromLTRB(
              AppSpacing.md,
              AppSpacing.md,
              AppSpacing.md,
              AppSpacing.md + bottomPadding,
            ),
            decoration: BoxDecoration(
              color: AppColors.surface.withOpacity(0.95),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.glassBorder.withOpacity(0.9)),
            ),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'AI Tools',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Thiết lập ngữ cảnh và chạy tác vụ nhanh.',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      SizedBox(
                        width: 120,
                        child: TextField(
                          controller: _motifController,
                          decoration: _inputDecoration('Motif ID'),
                        ),
                      ),
                      SizedBox(
                        width: 120,
                        child: TextField(
                          controller: _urnController,
                          decoration: _inputDecoration('Urn slug'),
                        ),
                      ),
                      _buildLevelSelector(),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _actionChip('Tóm tắt', _handleSummary),
                      _actionChip('Flashcards', _handleFlashcards),
                      _actionChip('Coach', _handleCoach),
                      _actionChip('Ôn tập', _handleReviewPlan),
                      _actionChip('Chẩn đoán', _handleDiagnostic),
                    ],
                  ),
                  const SizedBox(height: 10),
                  ExpansionTile(
                    tilePadding: EdgeInsets.zero,
                    iconColor: AppColors.textSecondary,
                    collapsedIconColor: AppColors.textSecondary,
                    title: Text(
                      'Giải thích & phản hồi',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    children: [
                      TextField(
                        controller: _explainController,
                        maxLines: 2,
                        decoration: _inputDecoration('Nội dung cần giải thích'),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          DropdownButton<String>(
                            value: _explainLevel,
                            dropdownColor: AppColors.surface,
                            style:
                                const TextStyle(color: AppColors.textPrimary),
                            items: const [
                              DropdownMenuItem(
                                  value: 'child', child: Text('12 tuổi')),
                              DropdownMenuItem(
                                  value: 'teen', child: Text('18 tuổi')),
                              DropdownMenuItem(
                                  value: 'expert', child: Text('Chuyên gia')),
                            ],
                            onChanged: (value) {
                              if (value == null) return;
                              setState(() => _explainLevel = value);
                            },
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: _isSending ? null : _handleExplain,
                            child: const Text('Giải thích'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _feedbackQuestionController,
                        decoration: _inputDecoration('Câu hỏi'),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _feedbackCorrectController,
                        decoration: _inputDecoration('Đáp án đúng'),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _feedbackAnswerController,
                        decoration: _inputDecoration('Câu trả lời của bạn'),
                      ),
                      const SizedBox(height: 10),
                      ElevatedButton(
                        onPressed: _isSending ? null : _handleFeedback,
                        child: const Text('Nhận phản hồi'),
                      ),
                      const SizedBox(height: 10),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildModeChip(_AiMode mode, String label) {
    final isSelected = _mode == mode;
    return GestureDetector(
      onTap: () => setState(() => _mode = mode),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.primary.withOpacity(0.25)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(
            color: isSelected
                ? AppColors.primary.withOpacity(0.75)
                : AppColors.glassBorder.withOpacity(0.8),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? AppColors.primary : AppColors.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _buildLevelSelector() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.surface.withOpacity(0.35),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.glassBorder.withOpacity(0.8)),
      ),
      child: DropdownButton<String>(
        value: _level,
        underline: const SizedBox.shrink(),
        dropdownColor: AppColors.surface,
        style: const TextStyle(color: AppColors.textPrimary),
        items: const [
          DropdownMenuItem(value: 'beginner', child: Text('Cơ bản')),
          DropdownMenuItem(value: 'intermediate', child: Text('Trung bình')),
          DropdownMenuItem(value: 'advanced', child: Text('Nâng cao')),
        ],
        onChanged: (value) {
          if (value == null) return;
          setState(() => _level = value);
        },
      ),
    );
  }

  Widget _actionChip(String label, Future<void> Function() onTap) {
    return InkWell(
      onTap: _isSending ? null : onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.surface.withOpacity(0.35),
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: AppColors.glassBorder.withOpacity(0.8)),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: _isSending ? AppColors.textHint : AppColors.textPrimary,
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }

  Widget _buildMessageBubble(_AiMessage message) {
    final isUser = message.role == 'user';

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        constraints: const BoxConstraints(maxWidth: 360),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isUser
              ? AppColors.primary.withOpacity(0.2)
              : AppColors.surface.withOpacity(0.45),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isUser
                ? AppColors.primary.withOpacity(0.6)
                : AppColors.glassBorder.withOpacity(0.8),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isUser ? 'Bạn' : 'AI Tutor',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 11,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              message.content,
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 14,
                height: 1.4,
              ),
            ),
            if (message.sources.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(10),
                  color: AppColors.background.withOpacity(0.45),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: message.sources
                      .map(
                        (source) => Padding(
                          padding: const EdgeInsets.only(bottom: 6),
                          child: Text(
                            '• ${source['title']}${(source['snippet'] ?? '').isEmpty ? '' : ': ${source['snippet']}'}',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 11,
                              height: 1.35,
                            ),
                          ),
                        ),
                      )
                      .toList(),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildComposer(bool isAuthed) {
    return Container(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.md,
      ),
      decoration: BoxDecoration(
        color: AppColors.surface.withOpacity(0.5),
        border: Border(
            top: BorderSide(color: AppColors.glassBorder.withOpacity(0.8))),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _inputController,
              minLines: 1,
              maxLines: 4,
              enabled: isAuthed && !_isSending,
              decoration: _inputDecoration('Nhập câu hỏi cho AI Tutor...'),
            ),
          ),
          const SizedBox(width: 10),
          ElevatedButton(
            onPressed: (!isAuthed || _isSending) ? null : _sendChat,
            style: ElevatedButton.styleFrom(
              minimumSize: const Size(54, 48),
              padding: const EdgeInsets.symmetric(horizontal: 14),
            ),
            child: _isSending
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send_rounded),
          ),
        ],
      ),
    );
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: AppColors.textHint, fontSize: 12),
      filled: true,
      fillColor: AppColors.background.withOpacity(0.45),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: AppColors.glassBorder.withOpacity(0.8)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:
            BorderSide(color: AppColors.primary.withOpacity(0.75), width: 1.3),
      ),
    );
  }
}
