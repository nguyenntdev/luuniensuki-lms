// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'urn_dtos.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$UrnListItemDtoImpl _$$UrnListItemDtoImplFromJson(Map<String, dynamic> json) =>
    _$UrnListItemDtoImpl(
      id: json['id'] as String,
      slug: json['slug'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      displayOrder: (json['display_order'] as num?)?.toInt() ?? 0,
      thumbnailUrl: json['thumbnail_url'] as String?,
      modelUrl: json['model_url'] as String?,
      motifCount: (json['motif_count'] as num?)?.toInt() ?? 0,
      discoveredCount: (json['discovered_count'] as num?)?.toInt() ?? 0,
      learnedCount: (json['learned_count'] as num?)?.toInt() ?? 0,
      masteredCount: (json['mastered_count'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$UrnListItemDtoImplToJson(
        _$UrnListItemDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'slug': instance.slug,
      'name': instance.name,
      'name_en': instance.nameEn,
      'display_order': instance.displayOrder,
      'thumbnail_url': instance.thumbnailUrl,
      'model_url': instance.modelUrl,
      'motif_count': instance.motifCount,
      'discovered_count': instance.discoveredCount,
      'learned_count': instance.learnedCount,
      'mastered_count': instance.masteredCount,
    };

_$UrnDetailResponseDtoImpl _$$UrnDetailResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$UrnDetailResponseDtoImpl(
      urn: UrnDetailDto.fromJson(json['urn'] as Map<String, dynamic>),
      motifs: (json['motifs'] as List<dynamic>?)
              ?.map((e) => MotifDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$UrnDetailResponseDtoImplToJson(
        _$UrnDetailResponseDtoImpl instance) =>
    <String, dynamic>{
      'urn': instance.urn,
      'motifs': instance.motifs,
    };

_$UrnDetailDtoImpl _$$UrnDetailDtoImplFromJson(Map<String, dynamic> json) =>
    _$UrnDetailDtoImpl(
      id: json['id'] as String,
      slug: json['slug'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      nameHan: json['name_han'] as String?,
      represents: json['represents'] as String?,
      description: json['description'] as String?,
      descriptionEn: json['description_en'] as String?,
      displayOrder: (json['display_order'] as num?)?.toInt() ?? 0,
      thumbnailUrl: json['thumbnail_url'] as String?,
      modelUrl: json['model_url'] as String?,
      isDemo: json['is_demo'] as bool? ?? false,
    );

Map<String, dynamic> _$$UrnDetailDtoImplToJson(_$UrnDetailDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'slug': instance.slug,
      'name': instance.name,
      'name_en': instance.nameEn,
      'name_han': instance.nameHan,
      'represents': instance.represents,
      'description': instance.description,
      'description_en': instance.descriptionEn,
      'display_order': instance.displayOrder,
      'thumbnail_url': instance.thumbnailUrl,
      'model_url': instance.modelUrl,
      'is_demo': instance.isDemo,
    };

_$MotifDtoImpl _$$MotifDtoImplFromJson(Map<String, dynamic> json) =>
    _$MotifDtoImpl(
      id: json['id'] as String,
      urnId: json['urn_id'] as String,
      meshName: json['mesh_name'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      category: json['category'] as String,
      rarity: json['rarity'] as String,
      posX: (json['pos_x'] as num?)?.toDouble() ?? 0.0,
      posY: (json['pos_y'] as num?)?.toDouble() ?? 0.0,
      posZ: (json['pos_z'] as num?)?.toDouble() ?? 0.0,
      boundingRadius: (json['bounding_radius'] as num?)?.toDouble() ?? 0.08,
      thumbnailUrl: json['thumbnail_url'] as String?,
      imageUrl: json['image_url'] as String?,
      isDemo: json['is_demo'] as bool? ?? false,
    );

Map<String, dynamic> _$$MotifDtoImplToJson(_$MotifDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'urn_id': instance.urnId,
      'mesh_name': instance.meshName,
      'name': instance.name,
      'name_en': instance.nameEn,
      'category': instance.category,
      'rarity': instance.rarity,
      'pos_x': instance.posX,
      'pos_y': instance.posY,
      'pos_z': instance.posZ,
      'bounding_radius': instance.boundingRadius,
      'thumbnail_url': instance.thumbnailUrl,
      'image_url': instance.imageUrl,
      'is_demo': instance.isDemo,
    };

_$MotifDetailDtoImpl _$$MotifDetailDtoImplFromJson(Map<String, dynamic> json) =>
    _$MotifDetailDtoImpl(
      id: json['id'] as String,
      urnId: json['urn_id'] as String,
      meshName: json['mesh_name'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      category: json['category'] as String,
      rarity: json['rarity'] as String,
      posX: (json['pos_x'] as num?)?.toDouble() ?? 0.0,
      posY: (json['pos_y'] as num?)?.toDouble() ?? 0.0,
      posZ: (json['pos_z'] as num?)?.toDouble() ?? 0.0,
      boundingRadius: (json['bounding_radius'] as num?)?.toDouble() ?? 0.08,
      thumbnailUrl: json['thumbnail_url'] as String?,
      imageUrl: json['image_url'] as String?,
      isDemo: json['is_demo'] as bool? ?? false,
      lesson: json['lesson'] == null
          ? null
          : LessonContentDto.fromJson(json['lesson'] as Map<String, dynamic>),
      progress: json['progress'] == null
          ? null
          : UserProgressDto.fromJson(json['progress'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$MotifDetailDtoImplToJson(
        _$MotifDetailDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'urn_id': instance.urnId,
      'mesh_name': instance.meshName,
      'name': instance.name,
      'name_en': instance.nameEn,
      'category': instance.category,
      'rarity': instance.rarity,
      'pos_x': instance.posX,
      'pos_y': instance.posY,
      'pos_z': instance.posZ,
      'bounding_radius': instance.boundingRadius,
      'thumbnail_url': instance.thumbnailUrl,
      'image_url': instance.imageUrl,
      'is_demo': instance.isDemo,
      'lesson': instance.lesson,
      'progress': instance.progress,
    };

_$LessonContentDtoImpl _$$LessonContentDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$LessonContentDtoImpl(
      id: json['id'] as String,
      motifId: json['motif_id'] as String,
      introText: json['intro_text'] as String?,
      description: json['description'] as String?,
      historicalContext: json['historical_context'] as String?,
      symbolism: json['symbolism'] as String?,
      funFact: json['fun_fact'] as String?,
      audioUrl: json['audio_url'] as String?,
      videoUrl: json['video_url'] as String?,
      images: (json['images'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$LessonContentDtoImplToJson(
        _$LessonContentDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'motif_id': instance.motifId,
      'intro_text': instance.introText,
      'description': instance.description,
      'historical_context': instance.historicalContext,
      'symbolism': instance.symbolism,
      'fun_fact': instance.funFact,
      'audio_url': instance.audioUrl,
      'video_url': instance.videoUrl,
      'images': instance.images,
    };

_$UserProgressDtoImpl _$$UserProgressDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$UserProgressDtoImpl(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      motifId: json['motif_id'] as String,
      status: json['status'] as String,
      discoveredAt: json['discovered_at'] as String?,
      learnedAt: json['learned_at'] as String?,
      masteredAt: json['mastered_at'] as String?,
      xpEarned: (json['xp_earned'] as num?)?.toInt() ?? 0,
      quizBestScore: (json['quiz_best_score'] as num?)?.toInt(),
    );

Map<String, dynamic> _$$UserProgressDtoImplToJson(
        _$UserProgressDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'user_id': instance.userId,
      'motif_id': instance.motifId,
      'status': instance.status,
      'discovered_at': instance.discoveredAt,
      'learned_at': instance.learnedAt,
      'mastered_at': instance.masteredAt,
      'xp_earned': instance.xpEarned,
      'quiz_best_score': instance.quizBestScore,
    };

_$UnlockResponseDtoImpl _$$UnlockResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$UnlockResponseDtoImpl(
      progress:
          UserProgressDto.fromJson(json['progress'] as Map<String, dynamic>),
      xpEarned: (json['xp_earned'] as num?)?.toInt() ?? 0,
      totalXp: (json['total_xp'] as num?)?.toInt() ?? 0,
      newBadges: (json['new_badges'] as List<dynamic>?)
              ?.map((e) => BadgeDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      streakUpdated: json['streak_updated'] as bool? ?? false,
      currentStreak: (json['current_streak'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$UnlockResponseDtoImplToJson(
        _$UnlockResponseDtoImpl instance) =>
    <String, dynamic>{
      'progress': instance.progress,
      'xp_earned': instance.xpEarned,
      'total_xp': instance.totalXp,
      'new_badges': instance.newBadges,
      'streak_updated': instance.streakUpdated,
      'current_streak': instance.currentStreak,
    };

_$BadgeDtoImpl _$$BadgeDtoImplFromJson(Map<String, dynamic> json) =>
    _$BadgeDtoImpl(
      id: json['id'] as String,
      slug: json['slug'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      description: json['description'] as String?,
      iconUrl: json['icon_url'] as String?,
      category: json['category'] as String,
      xpBonus: (json['xp_bonus'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$BadgeDtoImplToJson(_$BadgeDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'slug': instance.slug,
      'name': instance.name,
      'name_en': instance.nameEn,
      'description': instance.description,
      'icon_url': instance.iconUrl,
      'category': instance.category,
      'xp_bonus': instance.xpBonus,
    };

_$CompleteLessonResponseDtoImpl _$$CompleteLessonResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$CompleteLessonResponseDtoImpl(
      progress:
          UserProgressDto.fromJson(json['progress'] as Map<String, dynamic>),
      xpEarned: (json['xp_earned'] as num?)?.toInt() ?? 0,
      totalXp: (json['total_xp'] as num?)?.toInt() ?? 0,
      newBadges: (json['new_badges'] as List<dynamic>?)
              ?.map((e) => BadgeDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$CompleteLessonResponseDtoImplToJson(
        _$CompleteLessonResponseDtoImpl instance) =>
    <String, dynamic>{
      'progress': instance.progress,
      'xp_earned': instance.xpEarned,
      'total_xp': instance.totalXp,
      'new_badges': instance.newBadges,
    };

_$QuizQuestionDtoImpl _$$QuizQuestionDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$QuizQuestionDtoImpl(
      id: json['id'] as String,
      motifId: json['motif_id'] as String,
      questionType: json['question_type'] as String,
      questionText: json['question_text'] as String,
      correctAnswer: json['correct_answer'] as String,
      options: (json['options'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      imageUrl: json['image_url'] as String?,
      explanation: json['explanation'] as String?,
      displayOrder: (json['display_order'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$QuizQuestionDtoImplToJson(
        _$QuizQuestionDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'motif_id': instance.motifId,
      'question_type': instance.questionType,
      'question_text': instance.questionText,
      'correct_answer': instance.correctAnswer,
      'options': instance.options,
      'image_url': instance.imageUrl,
      'explanation': instance.explanation,
      'display_order': instance.displayOrder,
    };

_$QuizResponseDtoImpl _$$QuizResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$QuizResponseDtoImpl(
      motifId: json['motif_id'] as String,
      motifName: json['motif_name'] as String,
      questions: (json['questions'] as List<dynamic>)
          .map((e) => QuizQuestionDto.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$QuizResponseDtoImplToJson(
        _$QuizResponseDtoImpl instance) =>
    <String, dynamic>{
      'motif_id': instance.motifId,
      'motif_name': instance.motifName,
      'questions': instance.questions,
    };

_$QuizSubmitRequestDtoImpl _$$QuizSubmitRequestDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$QuizSubmitRequestDtoImpl(
      answers: (json['answers'] as List<dynamic>)
          .map((e) => QuizAnswerDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      timeTakenSeconds: (json['time_taken_seconds'] as num?)?.toInt(),
    );

Map<String, dynamic> _$$QuizSubmitRequestDtoImplToJson(
        _$QuizSubmitRequestDtoImpl instance) =>
    <String, dynamic>{
      'answers': instance.answers,
      'time_taken_seconds': instance.timeTakenSeconds,
    };

_$QuizAnswerDtoImpl _$$QuizAnswerDtoImplFromJson(Map<String, dynamic> json) =>
    _$QuizAnswerDtoImpl(
      questionId: json['question_id'] as String,
      answer: json['answer'] as String,
    );

Map<String, dynamic> _$$QuizAnswerDtoImplToJson(_$QuizAnswerDtoImpl instance) =>
    <String, dynamic>{
      'question_id': instance.questionId,
      'answer': instance.answer,
    };

_$QuizResultDtoImpl _$$QuizResultDtoImplFromJson(Map<String, dynamic> json) =>
    _$QuizResultDtoImpl(
      passed: json['passed'] as bool,
      score: (json['score'] as num).toInt(),
      totalQuestions: (json['total_questions'] as num).toInt(),
      correctAnswers: (json['correct_answers'] as num).toInt(),
      percentage: (json['percentage'] as num).toInt(),
      xpEarned: (json['xp_earned'] as num?)?.toInt() ?? 0,
      totalXp: (json['total_xp'] as num?)?.toInt() ?? 0,
      newBadges: (json['new_badges'] as List<dynamic>?)
              ?.map((e) => BadgeDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      isNewBest: json['is_new_best'] as bool? ?? false,
      progress: json['progress'] == null
          ? null
          : UserProgressDto.fromJson(json['progress'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$QuizResultDtoImplToJson(_$QuizResultDtoImpl instance) =>
    <String, dynamic>{
      'passed': instance.passed,
      'score': instance.score,
      'total_questions': instance.totalQuestions,
      'correct_answers': instance.correctAnswers,
      'percentage': instance.percentage,
      'xp_earned': instance.xpEarned,
      'total_xp': instance.totalXp,
      'new_badges': instance.newBadges,
      'is_new_best': instance.isNewBest,
      'progress': instance.progress,
    };
