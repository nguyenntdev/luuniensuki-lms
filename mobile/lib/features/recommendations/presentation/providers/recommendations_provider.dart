import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/network/api_client.dart';
import '../../data/models/recommendation_dto.dart';

part 'recommendations_provider.g.dart';

@riverpod
Future<RecommendationsResponseDto> recommendations(
  RecommendationsRef ref, {
  String? type,
  int limit = 10,
}) async {
  final apiClient = ref.watch(apiClientProvider);

  final queryParams = <String, dynamic>{
    'limit': limit,
  };
  if (type != null) {
    queryParams['recommendation_type'] = type;
  }

  return apiClient.get<RecommendationsResponseDto>(
    '/api/v1/recommendations',
    queryParameters: queryParams,
    parser: (json) =>
        RecommendationsResponseDto.fromJson(json as Map<String, dynamic>),
  );
}

