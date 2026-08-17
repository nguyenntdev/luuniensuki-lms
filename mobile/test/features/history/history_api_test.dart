import 'package:flutter_test/flutter_test.dart';

import '../../../lib/features/history/domain/history_api.dart';

void main() {
  group('HistoryEntity.fromJson', () {
    test('maps public entity fields', () {
      final entity = HistoryEntity.fromJson({
        'id': 'abc-123',
        'entity_type': 'urn',
        'slug': 'cao-dinh',
        'name_vi': 'Cao Đỉnh',
        'name_en': 'Cao Urn',
        'summary_vi': 'Chiếc đỉnh cao.',
        'publication_status': 'public_unverified',
      });

      expect(entity.id, 'abc-123');
      expect(entity.entityType, 'urn');
      expect(entity.slug, 'cao-dinh');
      expect(entity.nameVi, 'Cao Đỉnh');
      expect(entity.nameEn, 'Cao Urn');
      expect(entity.summaryVi, 'Chiếc đỉnh cao.');
      expect(entity.publicationStatus, 'public_unverified');
    });

    test('tolerates missing optional fields', () {
      final entity = HistoryEntity.fromJson({'id': '1', 'slug': 'x', 'name_vi': 'X'});
      expect(entity.nameEn, isNull);
      expect(entity.summaryVi, isNull);
      expect(entity.publicationStatus, isNull);
    });
  });

  group('HistoryStory.fromJson', () {
    test('parses story fields and featured flag', () {
      final story = HistoryStory.fromJson({
        'id': 's1',
        'slug': 'cau-chuyen',
        'title_vi': 'Câu chuyện',
        'summary_vi': 'Tóm tắt.',
        'featured': true,
      });

      expect(story.slug, 'cau-chuyen');
      expect(story.titleVi, 'Câu chuyện');
      expect(story.featured, isTrue);
    });

    test('featured defaults to false', () {
      final story = HistoryStory.fromJson({
        'id': 's2',
        'slug': 'khac',
        'title_vi': 'Khác',
      });
      expect(story.featured, isFalse);
    });
  });
}
