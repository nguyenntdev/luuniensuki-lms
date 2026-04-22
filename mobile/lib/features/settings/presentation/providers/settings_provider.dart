import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../../core/storage/hive_storage.dart';

part 'settings_provider.freezed.dart';

/// Settings state model
@freezed
class SettingsState with _$SettingsState {
  const factory SettingsState({
    @Default(true) bool notificationsEnabled,
    @Default(true) bool soundEffectsEnabled,
    @Default('vi') String language,
  }) = _SettingsState;
}

/// Settings state notifier
class SettingsNotifier extends StateNotifier<SettingsState> {
  final HiveStorage _storage;

  SettingsNotifier(this._storage) : super(const SettingsState()) {
    _loadSettings();
  }

  static const _keyNotifications = 'settings_notifications';
  static const _keySoundEffects = 'settings_sound_effects';
  static const _keyLanguage = 'settings_language';

  Future<void> _loadSettings() async {
    final notifications = _storage.getSetting<bool>(_keyNotifications, defaultValue: true) ?? true;
    final soundEffects = _storage.getSetting<bool>(_keySoundEffects, defaultValue: true) ?? true;
    final language = _storage.getSetting<String>(_keyLanguage, defaultValue: 'vi') ?? 'vi';

    state = state.copyWith(
      notificationsEnabled: notifications,
      soundEffectsEnabled: soundEffects,
      language: language,
    );
  }

  Future<void> setNotifications(bool enabled) async {
    await _storage.setSetting(_keyNotifications, enabled);
    state = state.copyWith(notificationsEnabled: enabled);
  }

  Future<void> setSoundEffects(bool enabled) async {
    await _storage.setSetting(_keySoundEffects, enabled);
    state = state.copyWith(soundEffectsEnabled: enabled);
  }

  Future<void> setLanguage(String language) async {
    await _storage.setSetting(_keyLanguage, language);
    state = state.copyWith(language: language);
  }

  Future<void> clearCache() async {
    // Clear image cache
    await CachedNetworkImage.evictFromCache('');
    // Clear Hive content cache
    await _storage.clearContentCache();
    // Compact to free up space
    await _storage.compact();
  }
}

/// Settings provider
final settingsNotifierProvider =
    StateNotifierProvider<SettingsNotifier, SettingsState>((ref) {
  final storage = ref.watch(hiveStorageProvider);
  return SettingsNotifier(storage);
});

