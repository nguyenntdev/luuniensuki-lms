import 'package:freezed_annotation/freezed_annotation.dart';

part 'quiz_question.freezed.dart';
part 'quiz_question.g.dart';

enum QuizType {
  multipleChoice,
  imageMatching,
  trueFalse,
  fillInBlank,
  dragAndDrop,
}

@freezed
class QuizQuestion with _$QuizQuestion {
  const factory QuizQuestion({
    required String id,
    required QuizType type,
    required String motifId,
    required String question,
    required List<String> options,
    required String correctAnswer,
    String? imageUrl,
    String? hint,
    @Default(10) int points,
    String? explanation,
  }) = _QuizQuestion;

  factory QuizQuestion.fromJson(Map<String, dynamic> json) =>
      _$QuizQuestionFromJson(json);
}

// Mock data for testing
class MockQuizData {
  static final List<QuizQuestion> mockQuestions = [
    // Multiple Choice Questions
    QuizQuestion(
      id: 'mc1',
      type: QuizType.multipleChoice,
      motifId: 'motif_1',
      question: 'Họa tiết nào tượng trưng cho sự may mắn và thịnh vượng?',
      options: [
        'Rồng',
        'Phượng',
        'Rùa',
        'Hổ',
      ],
      correctAnswer: 'Rồng',
      points: 10,
      explanation: 'Rồng là biểu tượng của quyền lực, sức mạnh và may mắn trong văn hóa Việt Nam.',
    ),
    QuizQuestion(
      id: 'mc2',
      type: QuizType.multipleChoice,
      motifId: 'motif_2',
      question: 'Họa tiết Sen thường xuất hiện ở đâu?',
      options: [
        'Áo dài',
        'Tranh dân gian',
        'Đền chùa',
        'Tất cả các đáp án',
      ],
      correctAnswer: 'Tất cả các đáp án',
      points: 10,
      explanation: 'Họa tiết Sen rất phổ biến trong văn hóa Việt Nam, xuất hiện ở nhiều nơi.',
    ),
    
    // Image Matching Questions
    QuizQuestion(
      id: 'im1',
      type: QuizType.imageMatching,
      motifId: 'motif_3',
      question: 'Đây là họa tiết gì?',
      options: [
        'Rồng',
        'Phượng Hoàng',
        'Hổ',
        'Rùa',
      ],
      correctAnswer: 'Phượng Hoàng',
      imageUrl: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800',
      points: 15,
      explanation: 'Phượng Hoàng là biểu tượng của sự cao quý và thanh nhã.',
    ),
    QuizQuestion(
      id: 'im2',
      type: QuizType.imageMatching,
      motifId: 'motif_4',
      question: 'Hình ảnh này là họa tiết nào?',
      options: [
        'Hoa Sen',
        'Hoa Mai',
        'Hoa Đào',
        'Hoa Cúc',
      ],
      correctAnswer: 'Hoa Sen',
      imageUrl: 'https://images.unsplash.com/photo-1566207462966-9a481f604da3?w=800',
      points: 15,
      explanation: 'Sen là biểu tượng của sự thanh khiết và cao quý.',
    ),
    
    // True/False Questions
    QuizQuestion(
      id: 'tf1',
      type: QuizType.trueFalse,
      motifId: 'motif_5',
      question: 'Họa tiết Rồng chỉ được sử dụng cho hoàng gia trong quá khứ.',
      options: ['Đúng', 'Sai'],
      correctAnswer: 'Đúng',
      points: 5,
      explanation: 'Trong thời phong kiến, họa tiết Rồng là biểu tượng quyền lực chỉ dành cho vua chúa.',
    ),
    QuizQuestion(
      id: 'tf2',
      type: QuizType.trueFalse,
      motifId: 'motif_6',
      question: 'Họa tiết Tứ Linh bao gồm: Rồng, Lân, Quy, Phượng.',
      options: ['Đúng', 'Sai'],
      correctAnswer: 'Đúng',
      points: 5,
      explanation: 'Tứ Linh là bốn con vật linh thiêng trong văn hóa Á Đông.',
    ),
    QuizQuestion(
      id: 'tf3',
      type: QuizType.trueFalse,
      motifId: 'motif_7',
      question: 'Họa tiết Sen chỉ xuất hiện trong Phật giáo.',
      options: ['Đúng', 'Sai'],
      correctAnswer: 'Sai',
      points: 5,
      explanation: 'Họa tiết Sen xuất hiện rộng rãi trong nhiều lĩnh vực văn hóa, không chỉ Phật giáo.',
    ),
  ];

  static List<QuizQuestion> getQuestionsByType(QuizType type) {
    return mockQuestions.where((q) => q.type == type).toList();
  }

  static QuizQuestion? getQuestionById(String id) {
    try {
      return mockQuestions.firstWhere((q) => q.id == id);
    } catch (e) {
      return null;
    }
  }
}

