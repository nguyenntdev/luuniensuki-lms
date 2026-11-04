import '../../domain/entities/urn_manifest.dart';

/// Parses raw JSON into [UrnManifest] domain entity.
class UrnManifestParser {
  static UrnManifest fromJson(Map<String, dynamic> json) {
    final slug = (json['urn_slug'] ?? '').toString();
    final modelVersion = (json['model_version'] as num?)?.toInt() ?? 1;
    final hotspotVersion = (json['hotspot_version'] as num?)?.toInt() ?? 1;
    final meshStatusStr = (json['mesh_status'] ?? 'MISSING').toString();
    final has2dFallback = (json['has_2d_fallback'] as bool?) ?? true;
    final fallback2dUrl = (json['fallback_2d_url'] ?? '').toString();

    // Viewer fallback
    final vfRaw = json['viewer_fallback'] as Map<String, dynamic>? ?? {};
    final viewerFallback = UrnViewerFallback(
      type: (vfRaw['type'] ?? '2d_rubbing').toString(),
      component: (vfRaw['component'] ?? 'UrnAccessibleFallback').toString(),
      assetUrl: (vfRaw['asset_url'] ?? fallback2dUrl).toString(),
      diskPath: (vfRaw['disk_path'] ?? '').toString(),
      format: (vfRaw['format'] ?? 'image/jpeg').toString(),
      bytes: (vfRaw['bytes'] as num?)?.toInt() ?? 0,
      sha256: (vfRaw['sha256'] ?? '').toString(),
      rightsAttribution: (vfRaw['rights_attribution'] ??
              'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)')
          .toString(),
      legalBasis: (vfRaw['legal_basis'] ??
              'Public Domain / Educational Fair Use')
          .toString(),
    );

    // LODs
    final lodsRaw = json['lods'] as Map<String, dynamic>? ?? {};
    final lods = <String, UrnLod>{};
    lodsRaw.forEach((key, val) {
      if (val is Map<String, dynamic>) {
        lods[key] = UrnLod(
          url: val['url']?.toString(),
          fallbackUrl: val['fallback_url']?.toString(),
          sha256: val['sha256']?.toString(),
          bytes: (val['bytes'] as num?)?.toInt() ?? 0,
          status: (val['status'] ?? (meshStatusStr == 'PRESENT' ? 'PRESENT' : 'MISSING')).toString(),
        );
      }
    });

    // Hotspots
    final hotspotsRaw = json['hotspots'] as List<dynamic>? ?? [];
    final hotspots = <UrnManifestHotspot>[];
    for (final hs in hotspotsRaw) {
      if (hs is Map<String, dynamic>) {
        final posList = (hs['pos'] as List<dynamic>?)
                ?.map((e) => (e as num).toDouble())
                .toList() ??
            [0.0, 0.0, 0.0];
        final camPos = (hs['camera_position'] as List<dynamic>?)
                ?.map((e) => (e as num).toDouble())
                .toList() ??
            [0.0, 0.0, 0.0];
        final camTarget = (hs['camera_target'] as List<dynamic>?)
                ?.map((e) => (e as num).toDouble())
                .toList() ??
            [0.0, 0.0, 0.0];

        final fb2d = hs['fallback_2d'] as Map<String, dynamic>?;

        hotspots.add(UrnManifestHotspot(
          hotspotId: (hs['hotspot_id'] ?? '').toString(),
          urnSlug: (hs['urn_slug'] ?? slug).toString(),
          reliefSlug: (hs['relief_slug'] ?? '').toString(),
          reliefName: (hs['relief_name'] ?? '').toString(),
          meshName: (hs['mesh_name'] ?? '').toString(),
          posX: posList.isNotEmpty ? posList[0] : 0.0,
          posY: posList.length > 1 ? posList[1] : 0.0,
          posZ: posList.length > 2 ? posList[2] : 0.0,
          cameraPosition: camPos,
          cameraTarget: camTarget,
          boundingRadius: (hs['bounding_radius'] as num?)?.toDouble() ?? 0.08,
          coordinateVersion: (hs['coordinate_version'] as num?)?.toInt() ?? 1,
          modelVersion: (hs['model_version'] as num?)?.toInt() ?? 1,
          modelUrl: hs['model_url']?.toString(),
          threeDMeshId: (hs['3d_mesh_id'] ?? '').toString(),
          motifId: (hs['motif_id'] ?? '').toString(),
          fallbackThumbnailUrl: fb2d?['thumbnail_url']?.toString(),
          fallbackDiskPath: fb2d?['disk_path']?.toString(),
          rightsAttribution: fb2d?['rights_attribution']?.toString(),
        ));
      }
    }

    return UrnManifest(
      urnSlug: slug,
      modelVersion: modelVersion,
      hotspotVersion: hotspotVersion,
      meshStatus: UrnMeshStatus.fromString(meshStatusStr),
      has2dFallback: has2dFallback,
      fallback2dUrl: fallback2dUrl,
      viewerFallback: viewerFallback,
      lods: lods,
      hotspots: hotspots,
      creator: (json['creator'] ??
              'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab')
          .toString(),
      rightsOwner: (json['rights_owner'] ??
              'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)')
          .toString(),
      rightsAttribution: (json['rights_attribution'] ??
              'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)')
          .toString(),
      license:
          (json['license'] ?? 'CC BY 4.0 / Educational Fair Use').toString(),
      rightsStatus: (json['rights_status'] ?? 'cleared').toString(),
      publicDistributionAllowed:
          (json['public_distribution_allowed'] as bool?) ?? true,
      publicDisplayAllowed: (json['public_display_allowed'] as bool?) ?? true,
      checksum: json['checksum']?.toString(),
    );
  }
}
