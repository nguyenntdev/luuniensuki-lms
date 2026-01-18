import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'cache_service.g.dart';

/// Cache service for storing and retrieving lesson payloads and other data.
///
/// Features:
/// - TTL (Time To Live) support for cached items
/// - Automatic cache expiration
/// - Size management with automatic cleanup
/// - Separate boxes for different data types
class CacheService {
  static const String _lessonBoxName = 'lesson_cache';
  static const String _metadataBoxName = 'cache_metadata';
  static const String _imageBoxName = 'image_cache';
  
  // Default TTL: 24 hours
  static const Duration defaultTTL = Duration(hours: 24);
  
  // Max cache size in bytes (50MB)
  static const int maxCacheSize = 50 * 1024 * 1024;
  
  Box<String>? _lessonBox;
  Box<Map<dynamic, dynamic>>? _metadataBox;
  Box<String>? _imageBox;
  
  /// Initialize cache service
  Future<void> initialize() async {
    try {
      _lessonBox = await Hive.openBox<String>(_lessonBoxName);
      _metadataBox = await Hive.openBox<Map<dynamic, dynamic>>(_metadataBoxName);
      _imageBox = await Hive.openBox<String>(_imageBoxName);
      
      // Clean up expired entries on initialization
      await _cleanupExpiredEntries();
      
      debugPrint('CacheService initialized successfully');
    } catch (e) {
      debugPrint('Error initializing CacheService: $e');
    }
  }
  
  /// Cache a lesson payload
  Future<void> cacheLesson(
    String lessonId,
    Map<String, dynamic> lessonData, {
    Duration? ttl,
  }) async {
    try {
      final box = _lessonBox;
      if (box == null) {
        debugPrint('Lesson cache box not initialized');
        return;
      }
      
      final jsonString = jsonEncode(lessonData);
      await box.put(lessonId, jsonString);
      
      // Store metadata
      await _storeCacheMetadata(
        _lessonBoxName,
        lessonId,
        jsonString.length,
        ttl ?? defaultTTL,
      );
      
      // Check cache size and cleanup if needed
      await _checkCacheSizeAndCleanup();
      
      debugPrint('Cached lesson: $lessonId');
    } catch (e) {
      debugPrint('Error caching lesson: $e');
    }
  }
  
  /// Get cached lesson payload
  Future<Map<String, dynamic>?> getCachedLesson(String lessonId) async {
    try {
      final box = _lessonBox;
      if (box == null) return null;
      
      // Check if entry exists and is not expired
      if (!await _isCacheValid(_lessonBoxName, lessonId)) {
        await invalidateLessonCache(lessonId);
        return null;
      }
      
      final jsonString = box.get(lessonId);
      if (jsonString == null) return null;
      
      return jsonDecode(jsonString) as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Error getting cached lesson: $e');
      return null;
    }
  }
  
  /// Invalidate a specific lesson cache
  Future<void> invalidateLessonCache(String lessonId) async {
    try {
      await _lessonBox?.delete(lessonId);
      await _deleteCacheMetadata(_lessonBoxName, lessonId);
      debugPrint('Invalidated lesson cache: $lessonId');
    } catch (e) {
      debugPrint('Error invalidating lesson cache: $e');
    }
  }
  
  /// Store cache metadata for TTL tracking
  Future<void> _storeCacheMetadata(
    String boxName,
    String key,
    int size,
    Duration ttl,
  ) async {
    final metadataBox = _metadataBox;
    if (metadataBox == null) return;
    
    final expiryTime = DateTime.now().add(ttl).millisecondsSinceEpoch;
    final metadataKey = '$boxName:$key';
    
    await metadataBox.put(metadataKey, {
      'expiryTime': expiryTime,
      'size': size,
      'createdAt': DateTime.now().millisecondsSinceEpoch,
    });
  }
  
  /// Check if cache entry is valid (not expired)
  Future<bool> _isCacheValid(String boxName, String key) async {
    final metadataBox = _metadataBox;
    if (metadataBox == null) return false;
    
    final metadataKey = '$boxName:$key';
    final metadata = metadataBox.get(metadataKey);
    
    if (metadata == null) return false;
    
    final expiryTime = metadata['expiryTime'] as int?;
    if (expiryTime == null) return false;
    
    return DateTime.now().millisecondsSinceEpoch < expiryTime;
  }
  
  /// Delete cache metadata
  Future<void> _deleteCacheMetadata(String boxName, String key) async {
    final metadataKey = '$boxName:$key';
    await _metadataBox?.delete(metadataKey);
  }

  /// Clean up expired cache entries
  Future<void> _cleanupExpiredEntries() async {
    try {
      final metadataBox = _metadataBox;
      if (metadataBox == null) return;

      final now = DateTime.now().millisecondsSinceEpoch;
      final expiredKeys = <String>[];

      for (final metadataKey in metadataBox.keys) {
        final metadata = metadataBox.get(metadataKey);
        if (metadata == null) continue;

        final expiryTime = metadata['expiryTime'] as int?;
        if (expiryTime != null && now >= expiryTime) {
          expiredKeys.add(metadataKey as String);
        }
      }

      // Delete expired entries
      for (final metadataKey in expiredKeys) {
        final parts = metadataKey.split(':');
        if (parts.length != 2) continue;

        final boxName = parts[0];
        final key = parts[1];

        // Delete from actual cache box
        if (boxName == _lessonBoxName) {
          await _lessonBox?.delete(key);
        } else if (boxName == _imageBoxName) {
          await _imageBox?.delete(key);
        }

        // Delete metadata
        await metadataBox.delete(metadataKey);
      }

      if (expiredKeys.isNotEmpty) {
        debugPrint('Cleaned up ${expiredKeys.length} expired cache entries');
      }
    } catch (e) {
      debugPrint('Error cleaning up expired entries: $e');
    }
  }

  /// Check cache size and cleanup if needed
  Future<void> _checkCacheSizeAndCleanup() async {
    try {
      final totalSize = await _calculateTotalCacheSize();

      if (totalSize > maxCacheSize) {
        debugPrint('Cache size exceeded limit: $totalSize bytes. Cleaning up...');
        await _cleanupOldestEntries(totalSize - maxCacheSize);
      }
    } catch (e) {
      debugPrint('Error checking cache size: $e');
    }
  }

  /// Calculate total cache size
  Future<int> _calculateTotalCacheSize() async {
    final metadataBox = _metadataBox;
    if (metadataBox == null) return 0;

    int totalSize = 0;
    for (final metadata in metadataBox.values) {
      final size = metadata['size'] as int?;
      if (size != null) {
        totalSize += size;
      }
    }

    return totalSize;
  }

  /// Clean up oldest cache entries to free up space
  Future<void> _cleanupOldestEntries(int targetSize) async {
    try {
      final metadataBox = _metadataBox;
      if (metadataBox == null) return;

      // Get all metadata sorted by creation time
      final entries = <MapEntry<String, Map<dynamic, dynamic>>>[];
      for (final key in metadataBox.keys) {
        final metadata = metadataBox.get(key);
        if (metadata != null) {
          entries.add(MapEntry(key as String, metadata));
        }
      }

      entries.sort((a, b) {
        final aCreated = a.value['createdAt'] as int? ?? 0;
        final bCreated = b.value['createdAt'] as int? ?? 0;
        return aCreated.compareTo(bCreated);
      });

      int freedSize = 0;
      int deletedCount = 0;

      for (final entry in entries) {
        if (freedSize >= targetSize) break;

        final metadataKey = entry.key;
        final metadata = entry.value;
        final size = metadata['size'] as int? ?? 0;

        final parts = metadataKey.split(':');
        if (parts.length != 2) continue;

        final boxName = parts[0];
        final key = parts[1];

        // Delete from actual cache box
        if (boxName == _lessonBoxName) {
          await _lessonBox?.delete(key);
        } else if (boxName == _imageBoxName) {
          await _imageBox?.delete(key);
        }

        // Delete metadata
        await metadataBox.delete(metadataKey);

        freedSize += size;
        deletedCount++;
      }

      debugPrint('Freed $freedSize bytes by deleting $deletedCount entries');
    } catch (e) {
      debugPrint('Error cleaning up oldest entries: $e');
    }
  }

  /// Clear all lesson cache
  Future<void> clearLessonCache() async {
    try {
      await _lessonBox?.clear();

      // Clear metadata for lesson cache
      final metadataBox = _metadataBox;
      if (metadataBox != null) {
        final keysToDelete = <String>[];
        for (final key in metadataBox.keys) {
          if ((key as String).startsWith('$_lessonBoxName:')) {
            keysToDelete.add(key);
          }
        }
        for (final key in keysToDelete) {
          await metadataBox.delete(key);
        }
      }

      debugPrint('Cleared all lesson cache');
    } catch (e) {
      debugPrint('Error clearing lesson cache: $e');
    }
  }

  /// Clear all cache
  Future<void> clearAllCache() async {
    try {
      await _lessonBox?.clear();
      await _imageBox?.clear();
      await _metadataBox?.clear();
      debugPrint('Cleared all cache');
    } catch (e) {
      debugPrint('Error clearing all cache: $e');
    }
  }

  /// Get cache statistics
  Future<Map<String, dynamic>> getCacheStats() async {
    try {
      final totalSize = await _calculateTotalCacheSize();
      final lessonCount = _lessonBox?.length ?? 0;
      final imageCount = _imageBox?.length ?? 0;

      return {
        'totalSize': totalSize,
        'maxSize': maxCacheSize,
        'lessonCount': lessonCount,
        'imageCount': imageCount,
        'percentUsed': (totalSize / maxCacheSize * 100).toStringAsFixed(1),
      };
    } catch (e) {
      debugPrint('Error getting cache stats: $e');
      return {};
    }
  }

  /// Dispose cache service
  Future<void> dispose() async {
    await _lessonBox?.close();
    await _metadataBox?.close();
    await _imageBox?.close();
  }
}

/// Provides the CacheService instance
@Riverpod(keepAlive: true)
CacheService cacheService(CacheServiceRef ref) {
  final service = CacheService();
  // Initialize asynchronously
  service.initialize();
  return service;
}

