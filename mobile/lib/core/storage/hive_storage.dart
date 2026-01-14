import 'package:hive_flutter/hive_flutter.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'hive_storage.g.dart';

/// Hive storage wrapper for local caching
/// Provides type-safe access to cached data with expiration support
class HiveStorage {
  static const String _urnsBox = 'urns';
  static const String _motifsBox = 'motifs';
  static const String _progressBox = 'progress';
  static const String _badgesBox = 'badges';
  static const String _questsBox = 'quests';
  static const String _leaderboardBox = 'leaderboard';
  static const String _userBox = 'user';
  static const String _settingsBox = 'settings';
  static const String _cacheMetaBox = 'cache_meta';
  static const String _quizProgressBox = 'quiz_progress';

  /// Initialize Hive and open all boxes
  static Future<void> init() async {
    await Hive.initFlutter();

    // Open all boxes
    await Future.wait([
      Hive.openBox(_urnsBox),
      Hive.openBox(_motifsBox),
      Hive.openBox(_progressBox),
      Hive.openBox(_badgesBox),
      Hive.openBox(_questsBox),
      Hive.openBox(_leaderboardBox),
      Hive.openBox(_userBox),
      Hive.openBox(_settingsBox),
      Hive.openBox(_cacheMetaBox),
      Hive.openBox(_quizProgressBox),
    ]);
  }

  /// Get a box by name
  static Box _getBox(String name) => Hive.box(name);

  // === Urns ===

  Box get urnsBox => _getBox(_urnsBox);

  Future<void> cacheUrns(List<Map<String, dynamic>> urns) async {
    await urnsBox.put('all', urns);
    await _setCacheTime(_urnsBox);
  }

  List<Map<String, dynamic>>? getCachedUrns() {
    final data = urnsBox.get('all');
    if (data == null) return null;
    return List<Map<String, dynamic>>.from(data);
  }

  Future<void> cacheUrn(String slug, Map<String, dynamic> urn) async {
    await urnsBox.put(slug, urn);
  }

  Map<String, dynamic>? getCachedUrn(String slug) {
    final data = urnsBox.get(slug);
    if (data == null) return null;
    return Map<String, dynamic>.from(data);
  }

  // === Motifs ===

  Box get motifsBox => _getBox(_motifsBox);

  Future<void> cacheMotif(String id, Map<String, dynamic> motif) async {
    await motifsBox.put(id, motif);
  }

  Map<String, dynamic>? getCachedMotif(String id) {
    final data = motifsBox.get(id);
    if (data == null) return null;
    return Map<String, dynamic>.from(data);
  }

  Future<void> cacheMotifLesson(String motifId, Map<String, dynamic> lesson) async {
    await motifsBox.put('lesson_$motifId', lesson);
  }

  Map<String, dynamic>? getCachedMotifLesson(String motifId) {
    final data = motifsBox.get('lesson_$motifId');
    if (data == null) return null;
    return Map<String, dynamic>.from(data);
  }

  // === Progress ===

  Box get progressBox => _getBox(_progressBox);

  Future<void> cacheProgress(Map<String, Map<String, dynamic>> progress) async {
    await progressBox.put('all', progress);
    await _setCacheTime(_progressBox);
  }

  Map<String, Map<String, dynamic>>? getCachedProgress() {
    final data = progressBox.get('all');
    if (data == null) return null;
    return Map<String, Map<String, dynamic>>.from(
      (data as Map).map((key, value) => MapEntry(key.toString(), Map<String, dynamic>.from(value))),
    );
  }

  Future<void> updateProgressForMotif(String motifId, Map<String, dynamic> progress) async {
    final allProgress = getCachedProgress() ?? {};
    allProgress[motifId] = progress;
    await cacheProgress(allProgress);
  }

  // === Badges ===

  Box get badgesBox => _getBox(_badgesBox);

  Future<void> cacheBadges(List<Map<String, dynamic>> badges) async {
    await badgesBox.put('all', badges);
    await _setCacheTime(_badgesBox);
  }

  List<Map<String, dynamic>>? getCachedBadges() {
    final data = badgesBox.get('all');
    if (data == null) return null;
    return List<Map<String, dynamic>>.from(data);
  }

  Future<void> cacheUserBadges(List<Map<String, dynamic>> badges) async {
    await badgesBox.put('user', badges);
  }

  List<Map<String, dynamic>>? getCachedUserBadges() {
    final data = badgesBox.get('user');
    if (data == null) return null;
    return List<Map<String, dynamic>>.from(data);
  }

  // === Quests ===

  Box get questsBox => _getBox(_questsBox);

  Future<void> cacheQuests(List<Map<String, dynamic>> quests) async {
    await questsBox.put('all', quests);
    await _setCacheTime(_questsBox);
  }

  List<Map<String, dynamic>>? getCachedQuests() {
    final data = questsBox.get('all');
    if (data == null) return null;
    return List<Map<String, dynamic>>.from(data);
  }

  // === Leaderboard ===

  Box get leaderboardBox => _getBox(_leaderboardBox);

  Future<void> cacheLeaderboard(List<Map<String, dynamic>> leaderboard) async {
    await leaderboardBox.put('global', leaderboard);
    await _setCacheTime(_leaderboardBox);
  }

  List<Map<String, dynamic>>? getCachedLeaderboard() {
    final data = leaderboardBox.get('global');
    if (data == null) return null;
    return List<Map<String, dynamic>>.from(data);
  }

  // === User ===

  Box get userBox => _getBox(_userBox);

  Future<void> cacheUser(Map<String, dynamic> user) async {
    await userBox.put('current', user);
  }

  Map<String, dynamic>? getCachedUser() {
    final data = userBox.get('current');
    if (data == null) return null;
    return Map<String, dynamic>.from(data);
  }

  Future<void> cacheUserStats(Map<String, dynamic> stats) async {
    await userBox.put('stats', stats);
  }

  Map<String, dynamic>? getCachedUserStats() {
    final data = userBox.get('stats');
    if (data == null) return null;
    return Map<String, dynamic>.from(data);
  }

  Future<void> clearUser() async {
    await userBox.delete('current');
    await userBox.delete('stats');
  }

  // === Settings ===

  Box get settingsBox => _getBox(_settingsBox);

  Future<void> setSetting(String key, dynamic value) async {
    await settingsBox.put(key, value);
  }

  T? getSetting<T>(String key, {T? defaultValue}) {
    return settingsBox.get(key, defaultValue: defaultValue) as T?;
  }

  bool hasSeenOnboarding() {
    return settingsBox.get('hasSeenOnboarding', defaultValue: false) as bool;
  }

  Future<void> setHasSeenOnboarding(bool value) async {
    await settingsBox.put('hasSeenOnboarding', value);
  }

  bool hasSeenViewerTips() {
    return settingsBox.get('hasSeenViewerTips', defaultValue: false) as bool;
  }

  Future<void> setHasSeenViewerTips(bool value) async {
    await settingsBox.put('hasSeenViewerTips', value);
  }

  String getSelectedLanguage() {
    return settingsBox.get('selectedLanguage', defaultValue: 'vi') as String;
  }

  Future<void> setSelectedLanguage(String locale) async {
    await settingsBox.put('selectedLanguage', locale);
  }

  // === Quiz Progress ===

  Box get quizProgressBox => _getBox(_quizProgressBox);

  /// Save quiz progress for a motif
  Future<void> saveQuizProgress(
    String motifId,
    Map<String, dynamic> progress,
  ) async {
    await quizProgressBox.put('quiz_progress_$motifId', progress);
  }

  /// Get saved quiz progress for a motif
  Map<String, dynamic>? getQuizProgress(String motifId) {
    final data = quizProgressBox.get('quiz_progress_$motifId');
    if (data == null) return null;
    return Map<String, dynamic>.from(data);
  }

  /// Clear quiz progress for a motif
  Future<void> clearQuizProgress(String motifId) async {
    await quizProgressBox.delete('quiz_progress_$motifId');
  }

  /// Clear all quiz progress
  Future<void> clearAllQuizProgress() async {
    await quizProgressBox.clear();
  }

  // === Cache Metadata ===

  Box get _cacheMetaBoxInstance => _getBox(_cacheMetaBox);

  Future<void> _setCacheTime(String boxName) async {
    await _cacheMetaBoxInstance.put('${boxName}_time', DateTime.now().millisecondsSinceEpoch);
  }

  DateTime? getCacheTime(String boxName) {
    final timestamp = _cacheMetaBoxInstance.get('${boxName}_time') as int?;
    if (timestamp == null) return null;
    return DateTime.fromMillisecondsSinceEpoch(timestamp);
  }

  bool isCacheValid(String boxName, Duration maxAge) {
    final cacheTime = getCacheTime(boxName);
    if (cacheTime == null) return false;
    return DateTime.now().difference(cacheTime) < maxAge;
  }

  bool isUrnsCacheValid(Duration maxAge) => isCacheValid(_urnsBox, maxAge);
  bool isProgressCacheValid(Duration maxAge) => isCacheValid(_progressBox, maxAge);
  bool isBadgesCacheValid(Duration maxAge) => isCacheValid(_badgesBox, maxAge);
  bool isLeaderboardCacheValid(Duration maxAge) => isCacheValid(_leaderboardBox, maxAge);
  bool isQuestsCacheValid(Duration maxAge) => isCacheValid(_questsBox, maxAge);

  // === Clear Cache ===

  Future<void> clearAllCache() async {
    await urnsBox.clear();
    await motifsBox.clear();
    await progressBox.clear();
    await badgesBox.clear();
    await questsBox.clear();
    await leaderboardBox.clear();
    await _cacheMetaBoxInstance.clear();
    // Note: userBox and settingsBox are NOT cleared
  }

  Future<void> clearUserData() async {
    await progressBox.clear();
    await userBox.clear();
    await badgesBox.delete('user');
    await questsBox.clear();
  }

  Future<void> clearContentCache() async {
    await urnsBox.clear();
    await motifsBox.clear();
    await leaderboardBox.clear();
  }

  /// Compact all boxes to reclaim storage space
  Future<void> compact() async {
    await urnsBox.compact();
    await motifsBox.compact();
    await progressBox.compact();
    await badgesBox.compact();
    await questsBox.compact();
    await leaderboardBox.compact();
    await userBox.compact();
    await settingsBox.compact();
    await _cacheMetaBoxInstance.compact();
  }
}

/// Riverpod provider for HiveStorage
@Riverpod(keepAlive: true)
HiveStorage hiveStorage(HiveStorageRef ref) {
  return HiveStorage();
}
