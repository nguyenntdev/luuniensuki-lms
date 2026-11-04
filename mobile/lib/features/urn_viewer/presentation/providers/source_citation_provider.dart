import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/errors/exceptions.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/network_info.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../domain/entities/source_citation.dart';

/// Provider for resolving full source citation and evidence bundles for urns and motifs.
final entityCitationsProvider =
    FutureProvider.family<EntityCitationBundle, String>((ref, slugOrId) async {
  final apiClient = ref.watch(apiClientProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  final isConnected = await networkInfo.isConnected;

  // 1. Offline branch: load strictly from authenticated Hive cache
  if (!isConnected) {
    final cached = hiveStorage.getCachedEntityCitations(slugOrId);
    if (cached != null) {
      final bundle = EntityCitationBundle.fromJson(cached);
      // Enforce negative abuse check: cannot strip citation provenance offline
      bundle.verifyProvenanceIntegrity();
      return bundle;
    }
    throw const NetworkException('Không có kết nối mạng và chưa lưu bản ghi thư tịch ngoại tuyến.');
  }

  // 2. Online branch: query backend citation endpoint
  try {
    final response = await apiClient.get<Map<String, dynamic>>(
      '/api/v1/history/citations/$slugOrId',
    );

    final bundle = EntityCitationBundle.fromJson(response);
    // Enforce provenance integrity on receive
    bundle.verifyProvenanceIntegrity();

    // Persist verified bundle into Hive cache for offline provenance preservation
    await hiveStorage.cacheEntityCitations(slugOrId, bundle.toJson());

    return bundle;
  } on ServerException catch (e) {
    // Try offline cache fallback on server error
    final cached = hiveStorage.getCachedEntityCitations(slugOrId);
    if (cached != null) {
      final bundle = EntityCitationBundle.fromJson(cached);
      bundle.verifyProvenanceIntegrity();
      return bundle;
    }
    debugPrint('[CITATIONS] Server error fetching citations: ${e.message}');
    rethrow;
  } catch (e) {
    final cached = hiveStorage.getCachedEntityCitations(slugOrId);
    if (cached != null) {
      final bundle = EntityCitationBundle.fromJson(cached);
      bundle.verifyProvenanceIntegrity();
      return bundle;
    }
    rethrow;
  }
});
