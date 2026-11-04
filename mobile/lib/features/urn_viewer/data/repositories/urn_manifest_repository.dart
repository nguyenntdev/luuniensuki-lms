import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../domain/entities/urn_manifest.dart';
import '../models/urn_manifest_parser.dart';

/// Repository for retrieving and caching published 3D/2D manifests.
class UrnManifestRepository {
  final ApiClient? _apiClient;
  final Map<String, UrnManifest> _cache = {};

  UrnManifestRepository([this._apiClient]);

  /// Get published manifest for an urn slug.
  /// 1. Tries local bundle asset (assets/data/manifests/{slug}.json).
  /// 2. Falls back to remote assets endpoint (assets/models/manifests/{slug}.json).
  Future<UrnManifest> getManifest(String slug) async {
    final normalizedSlug = slug.trim().toLowerCase();
    if (_cache.containsKey(normalizedSlug)) {
      return _cache[normalizedSlug]!;
    }

    // 1. Try local bundled manifest
    try {
      final assetPath = 'assets/data/manifests/$normalizedSlug.json';
      final raw = await rootBundle.loadString(assetPath);
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        final manifest = UrnManifestParser.fromJson(decoded);
        _cache[normalizedSlug] = manifest;
        debugPrint('[URN_MANIFEST_REPO] ✅ Loaded local manifest: $assetPath (mesh: ${manifest.meshStatus.value})');
        return manifest;
      }
    } catch (e) {
      debugPrint('[URN_MANIFEST_REPO] ⚠️ Local manifest load failed for $normalizedSlug: $e');
    }

    // 2. Try remote assets endpoint
    if (_apiClient != null) {
      try {
        final url = '${ApiConstants.modelsAssetsUrl}/manifests/$normalizedSlug.json';
        final response = await _apiClient.get<Map<String, dynamic>>(url);
        final manifest = UrnManifestParser.fromJson(response);
        _cache[normalizedSlug] = manifest;
        debugPrint('[URN_MANIFEST_REPO] ✅ Loaded remote manifest for $normalizedSlug');
        return manifest;
      } catch (e) {
        debugPrint('[URN_MANIFEST_REPO] ❌ Remote manifest load failed for $normalizedSlug: $e');
      }
    }

    // 3. Synthesize safe offline fallback if both failed (fails safe to 2D rubbing)
    final fallbackManifest = _createSafeFallbackManifest(normalizedSlug);
    _cache[normalizedSlug] = fallbackManifest;
    return fallbackManifest;
  }

  UrnManifest _createSafeFallbackManifest(String slug) {
    final isCaoDinh = (slug == 'cao-dinh');
    final meshStatus = isCaoDinh ? UrnMeshStatus.present : UrnMeshStatus.missing;
    final rubbingUrl = '${ApiConstants.assetsUrl}/ban-duc-noi/${slug.toUpperCase().replaceAll('-', ' ')}/${slug.toUpperCase().replaceAll('-', ' ')}.jpg';

    return UrnManifest(
      urnSlug: slug,
      modelVersion: 1,
      hotspotVersion: 1,
      meshStatus: meshStatus,
      has2dFallback: true,
      fallback2dUrl: rubbingUrl,
      viewerFallback: UrnViewerFallback(
        type: '2d_rubbing',
        component: 'UrnAccessibleFallback',
        assetUrl: rubbingUrl,
        diskPath: 'ban-duc-noi/${slug.toUpperCase().replaceAll('-', ' ')}/${slug.toUpperCase().replaceAll('-', ' ')}.jpg',
        format: 'image/jpeg',
        rightsAttribution: 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
        legalBasis: 'Public Domain / Educational Fair Use',
      ),
      lods: isCaoDinh
          ? {
              'low': const UrnLod(
                url: '${ApiConstants.modelsAssetsUrl}/CAO-DINH-v1-512.glb',
                bytes: 5207460,
                status: 'PRESENT',
              ),
              'medium': const UrnLod(
                url: '${ApiConstants.modelsAssetsUrl}/CAO-DINH-v1-1k.glb',
                bytes: 27417688,
                status: 'PRESENT',
              ),
              'high': const UrnLod(
                url: '${ApiConstants.modelsAssetsUrl}/CAO-DINH-v1-2k.glb',
                bytes: 30353888,
                status: 'PRESENT',
              ),
            }
          : {
              'low': const UrnLod(status: 'MISSING', bytes: 0),
              'medium': const UrnLod(status: 'MISSING', bytes: 0),
              'high': const UrnLod(status: 'MISSING', bytes: 0),
            },
      hotspots: const [],
      creator: 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab',
      rightsOwner: 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
      license: 'CC BY 4.0 / Educational Fair Use',
      rightsStatus: 'cleared',
    );
  }
}

final urnManifestRepositoryProvider = Provider<UrnManifestRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return UrnManifestRepository(apiClient);
});

final urnManifestProvider =
    FutureProvider.family<UrnManifest, String>((ref, slug) async {
  final repo = ref.watch(urnManifestRepositoryProvider);
  return repo.getManifest(slug);
});
