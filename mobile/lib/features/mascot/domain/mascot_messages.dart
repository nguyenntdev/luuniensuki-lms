/// Messages for the app mascot
/// Similar to Duolingo's Duo owl, providing encouragement and reminders
class MascotMessages {
  // Encouragement messages for progress
  static const encouragement = [
    "Bạn làm tốt lắm!",
    "Tiếp tục phát huy nhé!",
    "Còn một chút nữa thôi!",
    "Xuất sắc! Cố lên!",
    "Tuyệt vời! Bạn đang làm rất tốt!",
    "Không ai có thể cản bước bạn!",
  ];

  // Streak reminder messages
  static const streakReminder = [
    "Đừng quên học hôm nay!",
    "Streak của bạn đang chờ đấy!",
    "Học một chút thôi, đừng để streak bị mất!",
    "Hôm nay bạn học chưa?",
    "Chỉ cần vài phút là giữ được streak!",
  ];

  // Celebration messages for achievements
  static const celebration = [
    "Tuyệt vời! Bạn đã hoàn thành!",
    "Xuất sắc! Tiếp tục nào!",
    "Hoàn hảo! Bạn quá giỏi!",
    "Wow! Thật đáng kinh ngạc!",
    "Chúc mừng! Bạn đã làm được!",
    "Tài năng quá! Tiếp tục phát huy nhé!",
  ];

  // Welcome messages
  static const welcome = [
    "Xin chào! Vui lòng đồng hành cùng bạn!",
    "Hãy bắt đầu hành trình học tập nào!",
    "Chào mừng trở lại! Sẵn sàng học chưa?",
    "Mình sẽ giúp bạn học hiệu quả hơn!",
  ];

  // Sad/worried messages when streak is about to break
  static const streakWarning = [
    "Ồ không! Streak của bạn sắp mất rồi!",
    "Đừng để mình buồn nhé... Học ngay đi!",
    "Streak đã duy trì lâu rồi, đừng để mất!",
    "Mình sẽ buồn nếu bạn không học hôm nay...",
  ];

  // Perfect score messages
  static const perfectScore = [
    "Hoàn hảo 100%! Bạn quá tuyệt!",
    "Điểm tuyệt đối! Mình tự hào về bạn!",
    "Không sai một câu! Xuất sắc!",
    "Tuyệt vời! Bạn là thiên tài!",
  ];

  // Lesson completion messages
  static const lessonComplete = [
    "Bài học hoàn thành! Tuyệt lắm!",
    "Giỏi quá! Một bài học nữa hoàn thành!",
    "Kiến thức mới đã trong tay! Tốt lắm!",
    "Bạn đang tiến bộ từng ngày!",
  ];

  // First time messages
  static const firstQuiz = [
    "Bài quiz đầu tiên! Cố lên nhé!",
    "Chúc may mắn với quiz đầu tiên!",
    "Mình tin bạn sẽ làm tốt!",
  ];

  static const firstLesson = [
    "Bài học đầu tiên! Chúc bạn học vui!",
    "Hành trình học tập bắt đầu từ đây!",
    "Bước đầu tiên là quan trọng nhất!",
  ];

  // Motivational messages for low performance
  static const motivation = [
    "Đừng nản! Mọi người đều có lúc khó khăn!",
    "Học tập là quá trình, cứ cố gắng nhé!",
    "Thất bại là mẹ thành công! Thử lại nào!",
    "Mình tin bạn sẽ làm tốt hơn lần sau!",
    "Cố lên! Bạn có thể làm được!",
  ];

  // Empty state messages
  static const emptyState = [
    "Hãy bắt đầu học thôi!",
    "Chọn m��t bài học để bắt đầu nhé!",
    "Nhiều bài học thú vị đang chờ bạn!",
  ];

  // Helper method to get random message from a list
  static String random(List<String> messages) {
    return messages[DateTime.now().millisecondsSinceEpoch % messages.length];
  }

  // Context-aware message selection
  static String getMessageForContext(MascotContext context, {int? score}) {
    switch (context) {
      case MascotContext.welcome:
        return random(welcome);
      case MascotContext.encouragement:
        return random(encouragement);
      case MascotContext.celebration:
        return random(celebration);
      case MascotContext.streakReminder:
        return random(streakReminder);
      case MascotContext.streakWarning:
        return random(streakWarning);
      case MascotContext.perfectScore:
        return random(perfectScore);
      case MascotContext.lessonComplete:
        return random(lessonComplete);
      case MascotContext.firstQuiz:
        return random(firstQuiz);
      case MascotContext.firstLesson:
        return random(firstLesson);
      case MascotContext.motivation:
        return random(motivation);
      case MascotContext.emptyState:
        return random(emptyState);
    }
  }
}

/// Context for mascot messages
enum MascotContext {
  welcome,
  encouragement,
  celebration,
  streakReminder,
  streakWarning,
  perfectScore,
  lessonComplete,
  firstQuiz,
  firstLesson,
  motivation,
  emptyState,
}

