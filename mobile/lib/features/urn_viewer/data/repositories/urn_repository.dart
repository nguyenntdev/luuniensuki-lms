import 'package:dartz/dartz.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/errors/failures.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/network_info.dart';
import '../../../../core/repositories/offline_first_repository.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../../../urn_viewer/data/models/urn_mappers.dart';
import '../../../urn_viewer/domain/entities/urn.dart';

part 'urn_repository.g.dart';

class UrnRepository extends OfflineFirstRepository<List<Urn>> {
  final ApiClient apiClient;

  UrnRepository({
    required this.apiClient,
    required super.networkInfo,
    required super.hiveStorage,
  });

  Future<Either<Failure, List<Urn>>> getUrns() async {
    return executeOfflineFirst<List<Urn>>(
      networkCall: () async {
        final response = await apiClient.get<List<dynamic>>('/api/v1/urns');
        return (response as List)
            .map((json) => UrnListItemDto.fromJson(json as Map<String, dynamic>))
            .map((dto) => dto.toEntity())
            .toList();
      },
      getCached: () async {
        final cached = hiveStorage.getCachedUrns();
        if (cached == null) return null;
        return cached.map((json) => UrnToJson.fromJson(json)).toList();
      },
      saveCache: (urns) async {
        await hiveStorage.cacheUrns(urns.map((u) => u.toJson()).toList());
      },
      operationName: 'GetUrns',
    );
  }

  Future<Either<Failure, UrnDetail>> getUrnDetail(String slug) async {
    Map<String, UserProgressDto>? progressByMotifId;
    try {
      final progressResponse = await apiClient.get<List<dynamic>>('/api/v1/progress');
      progressByMotifId = {
        for (final p in (progressResponse as List))
          (p as Map<String, dynamic>)['motif_id'] as String: UserProgressDto.fromJson(p)
      };
    } catch (e) {
      // Progress fetch is optional
    }

    return executeOfflineFirst<UrnDetail>(
      networkCall: () async {
        final response = await apiClient.get<Map<String, dynamic>>('/api/v1/urns/$slug');
        final dto = UrnDetailResponseDto.fromJson(response);
        return dto.toEntity(progressByMotifId: progressByMotifId);
      },
      getCached: () async {
        final cached = hiveStorage.getCachedUrn(slug);
        if (cached == null) return null;
        final dto = UrnDetailResponseDto.fromJson(cached);
        return dto.toEntity(progressByMotifId: progressByMotifId);
      },
      saveCache: (urnDetail) async {
        final cached = hiveStorage.getCachedUrn(slug);
        if (cached != null) {
          await hiveStorage.cacheUrn(slug, cached);
        }
      },
      operationName: 'GetUrnDetail($slug)',
    );
  }

  Future<Either<Failure, Motif>> getMotif(String motifId) async {
    return executeOfflineFirst<Motif>(
      networkCall: () async {
        final response = await apiClient.get<Map<String, dynamic>>('/api/v1/motifs/$motifId');
        final dto = MotifDetailDto.fromJson(response);
        return dto.toEntity();
      },
      getCached: () async {
        final cached = hiveStorage.getCachedMotif(motifId);
        if (cached == null) return null;
        final dto = MotifDetailDto.fromJson(cached);
        return dto.toEntity();
      },
      saveCache: (motif) async {
        await hiveStorage.cacheMotif(motifId, motif.toJson());
      },
      operationName: 'GetMotif($motifId)',
    );
  }
}

@Riverpod(keepAlive: true)
UrnRepository urnRepository(UrnRepositoryRef ref) {
  return UrnRepository(
    apiClient: ref.watch(apiClientProvider),
    networkInfo: ref.watch(networkInfoProvider),
    hiveStorage: ref.watch(hiveStorageProvider),
  );
}

@riverpod
Future<List<Urn>> urnsOfflineFirst(UrnsOfflineFirstRef ref) async {
  final repository = ref.watch(urnRepositoryProvider);
  final result = await repository.getUrns();
  
  return result.fold(
    (failure) => throw Exception(failure.message),
    (urns) => urns,
  );
}

@riverpod
Future<UrnDetail> urnDetailOfflineFirst(
  UrnDetailOfflineFirstRef ref,
  String slug,
) async {
  final repository = ref.watch(urnRepositoryProvider);
  final result = await repository.getUrnDetail(slug);
  
  return result.fold(
    (failure) => throw Exception(failure.message),
    (urnDetail) => urnDetail,
  );
}

@riverpod
Future<Motif> motifOfflineFirst(
  MotifOfflineFirstRef ref,
  String motifId,
) async {
  final repository = ref.watch(urnRepositoryProvider);
  final result = await repository.getMotif(motifId);
  
  return result.fold(
    (failure) => throw Exception(failure.message),
    (motif) => motif,
  );
}

