import 'dart:async';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../domain/entities/heart_state.dart';

part 'hearts_provider.g.dart';

/// Provider for managing hearts/energy system
@riverpod
class HeartsNotifier extends _$HeartsNotifier {
  static const String _heartsKey = 'hearts_state';
  Timer? _autoRefillTimer;

  @override
  HeartState build() {
    // Load hearts from storage or create initial state
    final heartState = _loadFromStorage() ?? HeartState.initial();
    
    // Auto-refill hearts based on time passed
    final autoRefilled = heartState.autoRefill();
    
    // Save if hearts were refilled
    if (autoRefilled != heartState) {
      _saveToStorage(autoRefilled);
    }
    
    // Start auto-refill timer
    _startAutoRefillTimer();
    
    // Clean up timer when provider is disposed
    ref.onDispose(() {
      _autoRefillTimer?.cancel();
    });
    
    return autoRefilled;
  }

  /// Load heart state from Hive storage
  HeartState? _loadFromStorage() {
    try {
      final hiveStorage = ref.read(hiveStorageProvider);
      final data = hiveStorage.userBox.get(_heartsKey);
      
      if (data != null) {
        return HeartState.fromJson(Map<String, dynamic>.from(data));
      }
    } catch (e) {
      // If there's an error, return null to use initial state
      print('Error loading hearts from storage: $e');
    }
    return null;
  }

  /// Save heart state to Hive storage
  Future<void> _saveToStorage(HeartState heartState) async {
    try {
      final hiveStorage = ref.read(hiveStorageProvider);
      await hiveStorage.userBox.put(_heartsKey, heartState.toJson());
    } catch (e) {
      print('Error saving hearts to storage: $e');
    }
  }

  /// Start a timer to auto-refill hearts every minute
  void _startAutoRefillTimer() {
    _autoRefillTimer?.cancel();
    _autoRefillTimer = Timer.periodic(const Duration(minutes: 1), (_) {
      _checkAndRefillHearts();
    });
  }

  /// Check if hearts need to be refilled and update state
  void _checkAndRefillHearts() {
    final currentState = state;
    final refilled = currentState.autoRefill();
    
    if (refilled != currentState) {
      state = refilled;
      _saveToStorage(refilled);
    }
  }

  /// Lose a heart (called when user answers incorrectly in quiz)
  Future<void> loseHeart() async {
    final newState = state.loseHeart();
    state = newState;
    await _saveToStorage(newState);
  }

  /// Check if user can continue (has hearts)
  bool canContinue() {
    return state.hasHearts;
  }

  /// Refill all hearts using gems
  /// Returns true if successful, false if not enough gems
  Future<bool> refillWithGems({
    required int gemCost,
    required int currentGems,
  }) async {
    if (currentGems < gemCost) {
      return false;
    }
    
    final newState = state.refillAll();
    state = newState;
    await _saveToStorage(newState);
    
    return true;
  }

  /// Refill all hearts for free (e.g., after watching ad)
  Future<void> refillForFree() async {
    final newState = state.refillAll();
    state = newState;
    await _saveToStorage(newState);
  }

  /// Add a single heart (e.g., from practice mode or rewards)
  Future<void> addHeart() async {
    final newState = state.addHeart();
    state = newState;
    await _saveToStorage(newState);
  }

  /// Set unlimited hearts (e.g., for premium users)
  Future<void> setUnlimited(bool unlimited) async {
    final newState = state.setUnlimited(unlimited);
    state = newState;
    await _saveToStorage(newState);
  }

  /// Force refresh hearts state (check for auto-refill)
  Future<void> refresh() async {
    final newState = state.autoRefill();
    if (newState != state) {
      state = newState;
      await _saveToStorage(newState);
    }
  }

  /// Reset hearts to initial state (for testing or admin)
  Future<void> reset() async {
    final newState = HeartState.initial();
    state = newState;
    await _saveToStorage(newState);
  }
}

/// Helper provider to check if user has hearts
@riverpod
bool hasHearts(HasHeartsRef ref) {
  final heartState = ref.watch(heartsNotifierProvider);
  return heartState.hasHearts;
}

/// Helper provider to get current hearts count
@riverpod
int currentHearts(CurrentHeartsRef ref) {
  final heartState = ref.watch(heartsNotifierProvider);
  return heartState.currentHearts;
}

