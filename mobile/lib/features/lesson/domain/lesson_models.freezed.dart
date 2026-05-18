// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'lesson_models.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$MotifDetail {
  String get id => throw _privateConstructorUsedError;
  String get urnId => throw _privateConstructorUsedError;
  String get meshName => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String? get nameEn => throw _privateConstructorUsedError;
  String get category => throw _privateConstructorUsedError;
  String get rarity => throw _privateConstructorUsedError;
  double get posX => throw _privateConstructorUsedError;
  double get posY => throw _privateConstructorUsedError;
  double get posZ => throw _privateConstructorUsedError;
  double get boundingRadius => throw _privateConstructorUsedError;
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  String? get imageUrl => throw _privateConstructorUsedError;
  bool get isDemo => throw _privateConstructorUsedError;
  LessonContent? get lesson => throw _privateConstructorUsedError;
  UserProgress? get progress => throw _privateConstructorUsedError;

  /// Create a copy of MotifDetail
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MotifDetailCopyWith<MotifDetail> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MotifDetailCopyWith<$Res> {
  factory $MotifDetailCopyWith(
          MotifDetail value, $Res Function(MotifDetail) then) =
      _$MotifDetailCopyWithImpl<$Res, MotifDetail>;
  @useResult
  $Res call(
      {String id,
      String urnId,
      String meshName,
      String name,
      String? nameEn,
      String category,
      String rarity,
      double posX,
      double posY,
      double posZ,
      double boundingRadius,
      String? thumbnailUrl,
      String? imageUrl,
      bool isDemo,
      LessonContent? lesson,
      UserProgress? progress});

  $LessonContentCopyWith<$Res>? get lesson;
  $UserProgressCopyWith<$Res>? get progress;
}

/// @nodoc
class _$MotifDetailCopyWithImpl<$Res, $Val extends MotifDetail>
    implements $MotifDetailCopyWith<$Res> {
  _$MotifDetailCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MotifDetail
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? urnId = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? posX = null,
    Object? posY = null,
    Object? posZ = null,
    Object? boundingRadius = null,
    Object? thumbnailUrl = freezed,
    Object? imageUrl = freezed,
    Object? isDemo = null,
    Object? lesson = freezed,
    Object? progress = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      urnId: null == urnId
          ? _value.urnId
          : urnId // ignore: cast_nullable_to_non_nullable
              as String,
      meshName: null == meshName
          ? _value.meshName
          : meshName // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      rarity: null == rarity
          ? _value.rarity
          : rarity // ignore: cast_nullable_to_non_nullable
              as String,
      posX: null == posX
          ? _value.posX
          : posX // ignore: cast_nullable_to_non_nullable
              as double,
      posY: null == posY
          ? _value.posY
          : posY // ignore: cast_nullable_to_non_nullable
              as double,
      posZ: null == posZ
          ? _value.posZ
          : posZ // ignore: cast_nullable_to_non_nullable
              as double,
      boundingRadius: null == boundingRadius
          ? _value.boundingRadius
          : boundingRadius // ignore: cast_nullable_to_non_nullable
              as double,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
      lesson: freezed == lesson
          ? _value.lesson
          : lesson // ignore: cast_nullable_to_non_nullable
              as LessonContent?,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgress?,
    ) as $Val);
  }

  /// Create a copy of MotifDetail
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $LessonContentCopyWith<$Res>? get lesson {
    if (_value.lesson == null) {
      return null;
    }

    return $LessonContentCopyWith<$Res>(_value.lesson!, (value) {
      return _then(_value.copyWith(lesson: value) as $Val);
    });
  }

  /// Create a copy of MotifDetail
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserProgressCopyWith<$Res>? get progress {
    if (_value.progress == null) {
      return null;
    }

    return $UserProgressCopyWith<$Res>(_value.progress!, (value) {
      return _then(_value.copyWith(progress: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$MotifDetailImplCopyWith<$Res>
    implements $MotifDetailCopyWith<$Res> {
  factory _$$MotifDetailImplCopyWith(
          _$MotifDetailImpl value, $Res Function(_$MotifDetailImpl) then) =
      __$$MotifDetailImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String urnId,
      String meshName,
      String name,
      String? nameEn,
      String category,
      String rarity,
      double posX,
      double posY,
      double posZ,
      double boundingRadius,
      String? thumbnailUrl,
      String? imageUrl,
      bool isDemo,
      LessonContent? lesson,
      UserProgress? progress});

  @override
  $LessonContentCopyWith<$Res>? get lesson;
  @override
  $UserProgressCopyWith<$Res>? get progress;
}

/// @nodoc
class __$$MotifDetailImplCopyWithImpl<$Res>
    extends _$MotifDetailCopyWithImpl<$Res, _$MotifDetailImpl>
    implements _$$MotifDetailImplCopyWith<$Res> {
  __$$MotifDetailImplCopyWithImpl(
      _$MotifDetailImpl _value, $Res Function(_$MotifDetailImpl) _then)
      : super(_value, _then);

  /// Create a copy of MotifDetail
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? urnId = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? posX = null,
    Object? posY = null,
    Object? posZ = null,
    Object? boundingRadius = null,
    Object? thumbnailUrl = freezed,
    Object? imageUrl = freezed,
    Object? isDemo = null,
    Object? lesson = freezed,
    Object? progress = freezed,
  }) {
    return _then(_$MotifDetailImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      urnId: null == urnId
          ? _value.urnId
          : urnId // ignore: cast_nullable_to_non_nullable
              as String,
      meshName: null == meshName
          ? _value.meshName
          : meshName // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      rarity: null == rarity
          ? _value.rarity
          : rarity // ignore: cast_nullable_to_non_nullable
              as String,
      posX: null == posX
          ? _value.posX
          : posX // ignore: cast_nullable_to_non_nullable
              as double,
      posY: null == posY
          ? _value.posY
          : posY // ignore: cast_nullable_to_non_nullable
              as double,
      posZ: null == posZ
          ? _value.posZ
          : posZ // ignore: cast_nullable_to_non_nullable
              as double,
      boundingRadius: null == boundingRadius
          ? _value.boundingRadius
          : boundingRadius // ignore: cast_nullable_to_non_nullable
              as double,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
      lesson: freezed == lesson
          ? _value.lesson
          : lesson // ignore: cast_nullable_to_non_nullable
              as LessonContent?,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgress?,
    ));
  }
}

/// @nodoc

class _$MotifDetailImpl extends _MotifDetail {
  const _$MotifDetailImpl(
      {required this.id,
      required this.urnId,
      required this.meshName,
      required this.name,
      this.nameEn,
      required this.category,
      required this.rarity,
      required this.posX,
      required this.posY,
      required this.posZ,
      required this.boundingRadius,
      this.thumbnailUrl,
      this.imageUrl,
      required this.isDemo,
      this.lesson,
      this.progress})
      : super._();

  @override
  final String id;
  @override
  final String urnId;
  @override
  final String meshName;
  @override
  final String name;
  @override
  final String? nameEn;
  @override
  final String category;
  @override
  final String rarity;
  @override
  final double posX;
  @override
  final double posY;
  @override
  final double posZ;
  @override
  final double boundingRadius;
  @override
  final String? thumbnailUrl;
  @override
  final String? imageUrl;
  @override
  final bool isDemo;
  @override
  final LessonContent? lesson;
  @override
  final UserProgress? progress;

  @override
  String toString() {
    return 'MotifDetail(id: $id, urnId: $urnId, meshName: $meshName, name: $name, nameEn: $nameEn, category: $category, rarity: $rarity, posX: $posX, posY: $posY, posZ: $posZ, boundingRadius: $boundingRadius, thumbnailUrl: $thumbnailUrl, imageUrl: $imageUrl, isDemo: $isDemo, lesson: $lesson, progress: $progress)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MotifDetailImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.urnId, urnId) || other.urnId == urnId) &&
            (identical(other.meshName, meshName) ||
                other.meshName == meshName) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.rarity, rarity) || other.rarity == rarity) &&
            (identical(other.posX, posX) || other.posX == posX) &&
            (identical(other.posY, posY) || other.posY == posY) &&
            (identical(other.posZ, posZ) || other.posZ == posZ) &&
            (identical(other.boundingRadius, boundingRadius) ||
                other.boundingRadius == boundingRadius) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl) &&
            (identical(other.isDemo, isDemo) || other.isDemo == isDemo) &&
            (identical(other.lesson, lesson) || other.lesson == lesson) &&
            (identical(other.progress, progress) ||
                other.progress == progress));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      urnId,
      meshName,
      name,
      nameEn,
      category,
      rarity,
      posX,
      posY,
      posZ,
      boundingRadius,
      thumbnailUrl,
      imageUrl,
      isDemo,
      lesson,
      progress);

  /// Create a copy of MotifDetail
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MotifDetailImplCopyWith<_$MotifDetailImpl> get copyWith =>
      __$$MotifDetailImplCopyWithImpl<_$MotifDetailImpl>(this, _$identity);
}

abstract class _MotifDetail extends MotifDetail {
  const factory _MotifDetail(
      {required final String id,
      required final String urnId,
      required final String meshName,
      required final String name,
      final String? nameEn,
      required final String category,
      required final String rarity,
      required final double posX,
      required final double posY,
      required final double posZ,
      required final double boundingRadius,
      final String? thumbnailUrl,
      final String? imageUrl,
      required final bool isDemo,
      final LessonContent? lesson,
      final UserProgress? progress}) = _$MotifDetailImpl;
  const _MotifDetail._() : super._();

  @override
  String get id;
  @override
  String get urnId;
  @override
  String get meshName;
  @override
  String get name;
  @override
  String? get nameEn;
  @override
  String get category;
  @override
  String get rarity;
  @override
  double get posX;
  @override
  double get posY;
  @override
  double get posZ;
  @override
  double get boundingRadius;
  @override
  String? get thumbnailUrl;
  @override
  String? get imageUrl;
  @override
  bool get isDemo;
  @override
  LessonContent? get lesson;
  @override
  UserProgress? get progress;

  /// Create a copy of MotifDetail
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MotifDetailImplCopyWith<_$MotifDetailImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$LessonContent {
  String get id => throw _privateConstructorUsedError;
  String get motifId => throw _privateConstructorUsedError;
  String? get introText => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  String? get historicalContext => throw _privateConstructorUsedError;
  String? get symbolism => throw _privateConstructorUsedError;
  String? get funFact => throw _privateConstructorUsedError;
  String? get audioUrl => throw _privateConstructorUsedError;
  String? get videoUrl => throw _privateConstructorUsedError;
  List<String> get images => throw _privateConstructorUsedError;

  /// Create a copy of LessonContent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LessonContentCopyWith<LessonContent> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LessonContentCopyWith<$Res> {
  factory $LessonContentCopyWith(
          LessonContent value, $Res Function(LessonContent) then) =
      _$LessonContentCopyWithImpl<$Res, LessonContent>;
  @useResult
  $Res call(
      {String id,
      String motifId,
      String? introText,
      String? description,
      String? historicalContext,
      String? symbolism,
      String? funFact,
      String? audioUrl,
      String? videoUrl,
      List<String> images});
}

/// @nodoc
class _$LessonContentCopyWithImpl<$Res, $Val extends LessonContent>
    implements $LessonContentCopyWith<$Res> {
  _$LessonContentCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LessonContent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = null,
    Object? introText = freezed,
    Object? description = freezed,
    Object? historicalContext = freezed,
    Object? symbolism = freezed,
    Object? funFact = freezed,
    Object? audioUrl = freezed,
    Object? videoUrl = freezed,
    Object? images = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      introText: freezed == introText
          ? _value.introText
          : introText // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      historicalContext: freezed == historicalContext
          ? _value.historicalContext
          : historicalContext // ignore: cast_nullable_to_non_nullable
              as String?,
      symbolism: freezed == symbolism
          ? _value.symbolism
          : symbolism // ignore: cast_nullable_to_non_nullable
              as String?,
      funFact: freezed == funFact
          ? _value.funFact
          : funFact // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _value.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      videoUrl: freezed == videoUrl
          ? _value.videoUrl
          : videoUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      images: null == images
          ? _value.images
          : images // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$LessonContentImplCopyWith<$Res>
    implements $LessonContentCopyWith<$Res> {
  factory _$$LessonContentImplCopyWith(
          _$LessonContentImpl value, $Res Function(_$LessonContentImpl) then) =
      __$$LessonContentImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String motifId,
      String? introText,
      String? description,
      String? historicalContext,
      String? symbolism,
      String? funFact,
      String? audioUrl,
      String? videoUrl,
      List<String> images});
}

/// @nodoc
class __$$LessonContentImplCopyWithImpl<$Res>
    extends _$LessonContentCopyWithImpl<$Res, _$LessonContentImpl>
    implements _$$LessonContentImplCopyWith<$Res> {
  __$$LessonContentImplCopyWithImpl(
      _$LessonContentImpl _value, $Res Function(_$LessonContentImpl) _then)
      : super(_value, _then);

  /// Create a copy of LessonContent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = null,
    Object? introText = freezed,
    Object? description = freezed,
    Object? historicalContext = freezed,
    Object? symbolism = freezed,
    Object? funFact = freezed,
    Object? audioUrl = freezed,
    Object? videoUrl = freezed,
    Object? images = null,
  }) {
    return _then(_$LessonContentImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      introText: freezed == introText
          ? _value.introText
          : introText // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      historicalContext: freezed == historicalContext
          ? _value.historicalContext
          : historicalContext // ignore: cast_nullable_to_non_nullable
              as String?,
      symbolism: freezed == symbolism
          ? _value.symbolism
          : symbolism // ignore: cast_nullable_to_non_nullable
              as String?,
      funFact: freezed == funFact
          ? _value.funFact
          : funFact // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _value.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      videoUrl: freezed == videoUrl
          ? _value.videoUrl
          : videoUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      images: null == images
          ? _value._images
          : images // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc

class _$LessonContentImpl extends _LessonContent {
  const _$LessonContentImpl(
      {required this.id,
      required this.motifId,
      this.introText,
      this.description,
      this.historicalContext,
      this.symbolism,
      this.funFact,
      this.audioUrl,
      this.videoUrl,
      final List<String> images = const []})
      : _images = images,
        super._();

  @override
  final String id;
  @override
  final String motifId;
  @override
  final String? introText;
  @override
  final String? description;
  @override
  final String? historicalContext;
  @override
  final String? symbolism;
  @override
  final String? funFact;
  @override
  final String? audioUrl;
  @override
  final String? videoUrl;
  final List<String> _images;
  @override
  @JsonKey()
  List<String> get images {
    if (_images is EqualUnmodifiableListView) return _images;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_images);
  }

  @override
  String toString() {
    return 'LessonContent(id: $id, motifId: $motifId, introText: $introText, description: $description, historicalContext: $historicalContext, symbolism: $symbolism, funFact: $funFact, audioUrl: $audioUrl, videoUrl: $videoUrl, images: $images)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LessonContentImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.introText, introText) ||
                other.introText == introText) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.historicalContext, historicalContext) ||
                other.historicalContext == historicalContext) &&
            (identical(other.symbolism, symbolism) ||
                other.symbolism == symbolism) &&
            (identical(other.funFact, funFact) || other.funFact == funFact) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            (identical(other.videoUrl, videoUrl) ||
                other.videoUrl == videoUrl) &&
            const DeepCollectionEquality().equals(other._images, _images));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      motifId,
      introText,
      description,
      historicalContext,
      symbolism,
      funFact,
      audioUrl,
      videoUrl,
      const DeepCollectionEquality().hash(_images));

  /// Create a copy of LessonContent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LessonContentImplCopyWith<_$LessonContentImpl> get copyWith =>
      __$$LessonContentImplCopyWithImpl<_$LessonContentImpl>(this, _$identity);
}

abstract class _LessonContent extends LessonContent {
  const factory _LessonContent(
      {required final String id,
      required final String motifId,
      final String? introText,
      final String? description,
      final String? historicalContext,
      final String? symbolism,
      final String? funFact,
      final String? audioUrl,
      final String? videoUrl,
      final List<String> images}) = _$LessonContentImpl;
  const _LessonContent._() : super._();

  @override
  String get id;
  @override
  String get motifId;
  @override
  String? get introText;
  @override
  String? get description;
  @override
  String? get historicalContext;
  @override
  String? get symbolism;
  @override
  String? get funFact;
  @override
  String? get audioUrl;
  @override
  String? get videoUrl;
  @override
  List<String> get images;

  /// Create a copy of LessonContent
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LessonContentImplCopyWith<_$LessonContentImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$UserProgress {
  String get id => throw _privateConstructorUsedError;
  String get oderId => throw _privateConstructorUsedError;
  String get motifId => throw _privateConstructorUsedError;
  ProgressStatus get status => throw _privateConstructorUsedError;
  DateTime? get discoveredAt => throw _privateConstructorUsedError;
  DateTime? get learnedAt => throw _privateConstructorUsedError;
  DateTime? get masteredAt => throw _privateConstructorUsedError;
  int get xpEarned => throw _privateConstructorUsedError;
  int? get quizBestScore => throw _privateConstructorUsedError;

  /// Create a copy of UserProgress
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UserProgressCopyWith<UserProgress> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UserProgressCopyWith<$Res> {
  factory $UserProgressCopyWith(
          UserProgress value, $Res Function(UserProgress) then) =
      _$UserProgressCopyWithImpl<$Res, UserProgress>;
  @useResult
  $Res call(
      {String id,
      String oderId,
      String motifId,
      ProgressStatus status,
      DateTime? discoveredAt,
      DateTime? learnedAt,
      DateTime? masteredAt,
      int xpEarned,
      int? quizBestScore});
}

/// @nodoc
class _$UserProgressCopyWithImpl<$Res, $Val extends UserProgress>
    implements $UserProgressCopyWith<$Res> {
  _$UserProgressCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UserProgress
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? oderId = null,
    Object? motifId = null,
    Object? status = null,
    Object? discoveredAt = freezed,
    Object? learnedAt = freezed,
    Object? masteredAt = freezed,
    Object? xpEarned = null,
    Object? quizBestScore = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      oderId: null == oderId
          ? _value.oderId
          : oderId // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as ProgressStatus,
      discoveredAt: freezed == discoveredAt
          ? _value.discoveredAt
          : discoveredAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      learnedAt: freezed == learnedAt
          ? _value.learnedAt
          : learnedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      masteredAt: freezed == masteredAt
          ? _value.masteredAt
          : masteredAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      quizBestScore: freezed == quizBestScore
          ? _value.quizBestScore
          : quizBestScore // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UserProgressImplCopyWith<$Res>
    implements $UserProgressCopyWith<$Res> {
  factory _$$UserProgressImplCopyWith(
          _$UserProgressImpl value, $Res Function(_$UserProgressImpl) then) =
      __$$UserProgressImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String oderId,
      String motifId,
      ProgressStatus status,
      DateTime? discoveredAt,
      DateTime? learnedAt,
      DateTime? masteredAt,
      int xpEarned,
      int? quizBestScore});
}

/// @nodoc
class __$$UserProgressImplCopyWithImpl<$Res>
    extends _$UserProgressCopyWithImpl<$Res, _$UserProgressImpl>
    implements _$$UserProgressImplCopyWith<$Res> {
  __$$UserProgressImplCopyWithImpl(
      _$UserProgressImpl _value, $Res Function(_$UserProgressImpl) _then)
      : super(_value, _then);

  /// Create a copy of UserProgress
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? oderId = null,
    Object? motifId = null,
    Object? status = null,
    Object? discoveredAt = freezed,
    Object? learnedAt = freezed,
    Object? masteredAt = freezed,
    Object? xpEarned = null,
    Object? quizBestScore = freezed,
  }) {
    return _then(_$UserProgressImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      oderId: null == oderId
          ? _value.oderId
          : oderId // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as ProgressStatus,
      discoveredAt: freezed == discoveredAt
          ? _value.discoveredAt
          : discoveredAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      learnedAt: freezed == learnedAt
          ? _value.learnedAt
          : learnedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      masteredAt: freezed == masteredAt
          ? _value.masteredAt
          : masteredAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      quizBestScore: freezed == quizBestScore
          ? _value.quizBestScore
          : quizBestScore // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc

class _$UserProgressImpl extends _UserProgress {
  const _$UserProgressImpl(
      {required this.id,
      required this.oderId,
      required this.motifId,
      required this.status,
      this.discoveredAt,
      this.learnedAt,
      this.masteredAt,
      this.xpEarned = 0,
      this.quizBestScore})
      : super._();

  @override
  final String id;
  @override
  final String oderId;
  @override
  final String motifId;
  @override
  final ProgressStatus status;
  @override
  final DateTime? discoveredAt;
  @override
  final DateTime? learnedAt;
  @override
  final DateTime? masteredAt;
  @override
  @JsonKey()
  final int xpEarned;
  @override
  final int? quizBestScore;

  @override
  String toString() {
    return 'UserProgress(id: $id, oderId: $oderId, motifId: $motifId, status: $status, discoveredAt: $discoveredAt, learnedAt: $learnedAt, masteredAt: $masteredAt, xpEarned: $xpEarned, quizBestScore: $quizBestScore)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UserProgressImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.oderId, oderId) || other.oderId == oderId) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.discoveredAt, discoveredAt) ||
                other.discoveredAt == discoveredAt) &&
            (identical(other.learnedAt, learnedAt) ||
                other.learnedAt == learnedAt) &&
            (identical(other.masteredAt, masteredAt) ||
                other.masteredAt == masteredAt) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.quizBestScore, quizBestScore) ||
                other.quizBestScore == quizBestScore));
  }

  @override
  int get hashCode => Object.hash(runtimeType, id, oderId, motifId, status,
      discoveredAt, learnedAt, masteredAt, xpEarned, quizBestScore);

  /// Create a copy of UserProgress
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UserProgressImplCopyWith<_$UserProgressImpl> get copyWith =>
      __$$UserProgressImplCopyWithImpl<_$UserProgressImpl>(this, _$identity);
}

abstract class _UserProgress extends UserProgress {
  const factory _UserProgress(
      {required final String id,
      required final String oderId,
      required final String motifId,
      required final ProgressStatus status,
      final DateTime? discoveredAt,
      final DateTime? learnedAt,
      final DateTime? masteredAt,
      final int xpEarned,
      final int? quizBestScore}) = _$UserProgressImpl;
  const _UserProgress._() : super._();

  @override
  String get id;
  @override
  String get oderId;
  @override
  String get motifId;
  @override
  ProgressStatus get status;
  @override
  DateTime? get discoveredAt;
  @override
  DateTime? get learnedAt;
  @override
  DateTime? get masteredAt;
  @override
  int get xpEarned;
  @override
  int? get quizBestScore;

  /// Create a copy of UserProgress
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UserProgressImplCopyWith<_$UserProgressImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$Badge {
  String get id => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String? get nameEn => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  String? get iconUrl => throw _privateConstructorUsedError;
  String get category => throw _privateConstructorUsedError;
  int get xpBonus => throw _privateConstructorUsedError;

  /// Create a copy of Badge
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $BadgeCopyWith<Badge> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BadgeCopyWith<$Res> {
  factory $BadgeCopyWith(Badge value, $Res Function(Badge) then) =
      _$BadgeCopyWithImpl<$Res, Badge>;
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      String? nameEn,
      String? description,
      String? iconUrl,
      String category,
      int xpBonus});
}

/// @nodoc
class _$BadgeCopyWithImpl<$Res, $Val extends Badge>
    implements $BadgeCopyWith<$Res> {
  _$BadgeCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of Badge
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? description = freezed,
    Object? iconUrl = freezed,
    Object? category = null,
    Object? xpBonus = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      iconUrl: freezed == iconUrl
          ? _value.iconUrl
          : iconUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      xpBonus: null == xpBonus
          ? _value.xpBonus
          : xpBonus // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BadgeImplCopyWith<$Res> implements $BadgeCopyWith<$Res> {
  factory _$$BadgeImplCopyWith(
          _$BadgeImpl value, $Res Function(_$BadgeImpl) then) =
      __$$BadgeImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      String? nameEn,
      String? description,
      String? iconUrl,
      String category,
      int xpBonus});
}

/// @nodoc
class __$$BadgeImplCopyWithImpl<$Res>
    extends _$BadgeCopyWithImpl<$Res, _$BadgeImpl>
    implements _$$BadgeImplCopyWith<$Res> {
  __$$BadgeImplCopyWithImpl(
      _$BadgeImpl _value, $Res Function(_$BadgeImpl) _then)
      : super(_value, _then);

  /// Create a copy of Badge
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? description = freezed,
    Object? iconUrl = freezed,
    Object? category = null,
    Object? xpBonus = null,
  }) {
    return _then(_$BadgeImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      iconUrl: freezed == iconUrl
          ? _value.iconUrl
          : iconUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      xpBonus: null == xpBonus
          ? _value.xpBonus
          : xpBonus // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$BadgeImpl implements _Badge {
  const _$BadgeImpl(
      {required this.id,
      required this.slug,
      required this.name,
      this.nameEn,
      this.description,
      this.iconUrl,
      required this.category,
      this.xpBonus = 0});

  @override
  final String id;
  @override
  final String slug;
  @override
  final String name;
  @override
  final String? nameEn;
  @override
  final String? description;
  @override
  final String? iconUrl;
  @override
  final String category;
  @override
  @JsonKey()
  final int xpBonus;

  @override
  String toString() {
    return 'Badge(id: $id, slug: $slug, name: $name, nameEn: $nameEn, description: $description, iconUrl: $iconUrl, category: $category, xpBonus: $xpBonus)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BadgeImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.slug, slug) || other.slug == slug) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.iconUrl, iconUrl) || other.iconUrl == iconUrl) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.xpBonus, xpBonus) || other.xpBonus == xpBonus));
  }

  @override
  int get hashCode => Object.hash(runtimeType, id, slug, name, nameEn,
      description, iconUrl, category, xpBonus);

  /// Create a copy of Badge
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$BadgeImplCopyWith<_$BadgeImpl> get copyWith =>
      __$$BadgeImplCopyWithImpl<_$BadgeImpl>(this, _$identity);
}

abstract class _Badge implements Badge {
  const factory _Badge(
      {required final String id,
      required final String slug,
      required final String name,
      final String? nameEn,
      final String? description,
      final String? iconUrl,
      required final String category,
      final int xpBonus}) = _$BadgeImpl;

  @override
  String get id;
  @override
  String get slug;
  @override
  String get name;
  @override
  String? get nameEn;
  @override
  String? get description;
  @override
  String? get iconUrl;
  @override
  String get category;
  @override
  int get xpBonus;

  /// Create a copy of Badge
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$BadgeImplCopyWith<_$BadgeImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$LessonCompletionResult {
  UserProgress get progress => throw _privateConstructorUsedError;
  int get xpEarned => throw _privateConstructorUsedError;
  int get totalXp => throw _privateConstructorUsedError;
  List<Badge> get newBadges => throw _privateConstructorUsedError;

  /// Create a copy of LessonCompletionResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LessonCompletionResultCopyWith<LessonCompletionResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LessonCompletionResultCopyWith<$Res> {
  factory $LessonCompletionResultCopyWith(LessonCompletionResult value,
          $Res Function(LessonCompletionResult) then) =
      _$LessonCompletionResultCopyWithImpl<$Res, LessonCompletionResult>;
  @useResult
  $Res call(
      {UserProgress progress,
      int xpEarned,
      int totalXp,
      List<Badge> newBadges});

  $UserProgressCopyWith<$Res> get progress;
}

/// @nodoc
class _$LessonCompletionResultCopyWithImpl<$Res,
        $Val extends LessonCompletionResult>
    implements $LessonCompletionResultCopyWith<$Res> {
  _$LessonCompletionResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LessonCompletionResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? progress = null,
    Object? xpEarned = null,
    Object? totalXp = null,
    Object? newBadges = null,
  }) {
    return _then(_value.copyWith(
      progress: null == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgress,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      newBadges: null == newBadges
          ? _value.newBadges
          : newBadges // ignore: cast_nullable_to_non_nullable
              as List<Badge>,
    ) as $Val);
  }

  /// Create a copy of LessonCompletionResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserProgressCopyWith<$Res> get progress {
    return $UserProgressCopyWith<$Res>(_value.progress, (value) {
      return _then(_value.copyWith(progress: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$LessonCompletionResultImplCopyWith<$Res>
    implements $LessonCompletionResultCopyWith<$Res> {
  factory _$$LessonCompletionResultImplCopyWith(
          _$LessonCompletionResultImpl value,
          $Res Function(_$LessonCompletionResultImpl) then) =
      __$$LessonCompletionResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {UserProgress progress,
      int xpEarned,
      int totalXp,
      List<Badge> newBadges});

  @override
  $UserProgressCopyWith<$Res> get progress;
}

/// @nodoc
class __$$LessonCompletionResultImplCopyWithImpl<$Res>
    extends _$LessonCompletionResultCopyWithImpl<$Res,
        _$LessonCompletionResultImpl>
    implements _$$LessonCompletionResultImplCopyWith<$Res> {
  __$$LessonCompletionResultImplCopyWithImpl(
      _$LessonCompletionResultImpl _value,
      $Res Function(_$LessonCompletionResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of LessonCompletionResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? progress = null,
    Object? xpEarned = null,
    Object? totalXp = null,
    Object? newBadges = null,
  }) {
    return _then(_$LessonCompletionResultImpl(
      progress: null == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgress,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      newBadges: null == newBadges
          ? _value._newBadges
          : newBadges // ignore: cast_nullable_to_non_nullable
              as List<Badge>,
    ));
  }
}

/// @nodoc

class _$LessonCompletionResultImpl implements _LessonCompletionResult {
  const _$LessonCompletionResultImpl(
      {required this.progress,
      required this.xpEarned,
      required this.totalXp,
      final List<Badge> newBadges = const []})
      : _newBadges = newBadges;

  @override
  final UserProgress progress;
  @override
  final int xpEarned;
  @override
  final int totalXp;
  final List<Badge> _newBadges;
  @override
  @JsonKey()
  List<Badge> get newBadges {
    if (_newBadges is EqualUnmodifiableListView) return _newBadges;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_newBadges);
  }

  @override
  String toString() {
    return 'LessonCompletionResult(progress: $progress, xpEarned: $xpEarned, totalXp: $totalXp, newBadges: $newBadges)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LessonCompletionResultImpl &&
            (identical(other.progress, progress) ||
                other.progress == progress) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            const DeepCollectionEquality()
                .equals(other._newBadges, _newBadges));
  }

  @override
  int get hashCode => Object.hash(runtimeType, progress, xpEarned, totalXp,
      const DeepCollectionEquality().hash(_newBadges));

  /// Create a copy of LessonCompletionResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LessonCompletionResultImplCopyWith<_$LessonCompletionResultImpl>
      get copyWith => __$$LessonCompletionResultImplCopyWithImpl<
          _$LessonCompletionResultImpl>(this, _$identity);
}

abstract class _LessonCompletionResult implements LessonCompletionResult {
  const factory _LessonCompletionResult(
      {required final UserProgress progress,
      required final int xpEarned,
      required final int totalXp,
      final List<Badge> newBadges}) = _$LessonCompletionResultImpl;

  @override
  UserProgress get progress;
  @override
  int get xpEarned;
  @override
  int get totalXp;
  @override
  List<Badge> get newBadges;

  /// Create a copy of LessonCompletionResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LessonCompletionResultImplCopyWith<_$LessonCompletionResultImpl>
      get copyWith => throw _privateConstructorUsedError;
}
