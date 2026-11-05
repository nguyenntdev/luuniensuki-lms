import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/features/offline_kit/data/models/offline_kit_model.dart';

void main() {
  group('LowBandwidthKitModel (Ticket V5-T096)', () {
    test('defaultStandard4 returns curated 4 stations with authentic content', () {
      final kit = LowBandwidthKitModel.defaultStandard4();

      expect(kit.kitId, equals('kit-low-bandwidth-standard_4'));
      expect(kit.zeroDeviceGuarantee, isTrue);
      expect(kit.paperAchievablePercent, equals(100));
      expect(kit.arOrSmartphoneMandatory, isFalse);
      expect(kit.stations.length, equals(4));

      final slugs = kit.stations.map((s) => s.monumentSlug).toList();
      expect(slugs, containsAll(['ngo-mon', 'dien-thai-hoa', 'hien-lam-cac', 'cung-dien-tho']));
    });

    test('verifies zero AR/smartphone requirement invariant on all stations', () {
      final kit = LowBandwidthKitModel.defaultStandard4();

      for (final station in kit.stations) {
        // Negative abuse invariant: No AR or smartphone required
        expect(station.offlineTask.arOrSmartphoneRequired, isFalse);
        expect(station.offlineTask.paperAchievable, isTrue);

        // Verification of 2D rubbing asset
        expect(station.rubbingAsset.assetUrl, isNotEmpty);
        expect(station.rubbingAsset.captionVi, contains('Bản dập 2D'));
        expect(station.rubbingAsset.highContrastCss, contains('contrast'));

        // Verification of primary source with rights
        expect(station.primarySource.sourceTitle, isNotEmpty);
        expect(station.primarySource.citation, isNotEmpty);
        expect(station.primarySource.rightsOwner, contains('HMCC'));

        // Verification of audio transcript (eliminating network streaming)
        expect(station.audioTranscript.scriptText, isNotEmpty);
        expect(station.audioTranscript.narrator, isNotEmpty);

        // Offline checkpoints
        expect(station.offlineTask.checkpoints.length, greaterThanOrEqualTo(2));
      }
    });

    test('serializes and deserializes correctly via toJson / fromJson', () {
      final kit = LowBandwidthKitModel.defaultStandard4();
      final jsonMap = kit.stations.first.toJson();

      final reconstructed = OfflineKitStationModel.fromJson(jsonMap);
      expect(reconstructed.monumentSlug, equals(kit.stations.first.monumentSlug));
      expect(reconstructed.primarySource.sourceTitle, equals(kit.stations.first.primarySource.sourceTitle));
      expect(reconstructed.offlineTask.paperAchievable, isTrue);
      expect(reconstructed.offlineTask.arOrSmartphoneRequired, isFalse);
    });
  });
}
