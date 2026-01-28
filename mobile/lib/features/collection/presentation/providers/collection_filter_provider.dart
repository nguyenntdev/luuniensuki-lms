import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../screens/collection_screen.dart';

/// Provider for persisting collection filter state across navigation
final collectionFilterProvider = StateProvider<CollectionFilter>((ref) {
  return CollectionFilter.all;
});

