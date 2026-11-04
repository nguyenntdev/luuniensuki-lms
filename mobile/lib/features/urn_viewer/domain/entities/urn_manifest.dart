import 'package:equatable/equatable.dart';

/// Mesh presence status matching published 3D manifest
enum UrnMeshStatus {
  present('PRESENT'),
  missing('MISSING');

  final String value;
  const UrnMeshStatus(this.value);

  static UrnMeshStatus fromString(String? value) {
    if (value != null && value.toUpperCase() == 'PRESENT') {
      return UrnMeshStatus.present;
    }
    return UrnMeshStatus.missing;
  }
}

/// LOD model configuration
class UrnLod extends Equatable {
  final String? url;
  final String? fallbackUrl;
  final String? sha256;
  final int bytes;
  final String status;

  const UrnLod({
    this.url,
    this.fallbackUrl,
    this.sha256,
    this.bytes = 0,
    required this.status,
  });

  bool get isPresent =>
      status.toUpperCase() == 'PRESENT' && url != null && url!.isNotEmpty;

  @override
  List<Object?> get props => [url, fallbackUrl, sha256, bytes, status];
}

/// 2D rubbing fallback asset metadata
class UrnViewerFallback extends Equatable {
  final String type;
  final String component;
  final String assetUrl;
  final String diskPath;
  final String format;
  final int bytes;
  final String sha256;
  final String rightsAttribution;
  final String legalBasis;

  const UrnViewerFallback({
    required this.type,
    required this.component,
    required this.assetUrl,
    required this.diskPath,
    this.format = 'image/jpeg',
    this.bytes = 0,
    this.sha256 = '',
    this.rightsAttribution = 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
    this.legalBasis = 'Public Domain / Educational Fair Use',
  });

  @override
  List<Object?> get props => [
        type,
        component,
        assetUrl,
        diskPath,
        format,
        bytes,
        sha256,
        rightsAttribution,
        legalBasis,
      ];
}

/// Hotspot coordinate definition from published manifest
class UrnManifestHotspot extends Equatable {
  final String hotspotId;
  final String urnSlug;
  final String reliefSlug;
  final String reliefName;
  final String meshName;
  final double posX;
  final double posY;
  final double posZ;
  final List<double> cameraPosition;
  final List<double> cameraTarget;
  final double boundingRadius;
  final int coordinateVersion;
  final int modelVersion;
  final String? modelUrl;
  final String threeDMeshId;
  final String motifId;
  final String? fallbackThumbnailUrl;
  final String? fallbackDiskPath;
  final String? rightsAttribution;

  const UrnManifestHotspot({
    required this.hotspotId,
    required this.urnSlug,
    required this.reliefSlug,
    required this.reliefName,
    required this.meshName,
    required this.posX,
    required this.posY,
    required this.posZ,
    this.cameraPosition = const [0.0, 0.0, 0.0],
    this.cameraTarget = const [0.0, 0.0, 0.0],
    this.boundingRadius = 0.08,
    this.coordinateVersion = 1,
    this.modelVersion = 1,
    this.modelUrl,
    required this.threeDMeshId,
    required this.motifId,
    this.fallbackThumbnailUrl,
    this.fallbackDiskPath,
    this.rightsAttribution,
  });

  List<double> get position => [posX, posY, posZ];

  @override
  List<Object?> get props => [
        hotspotId,
        urnSlug,
        reliefSlug,
        reliefName,
        meshName,
        posX,
        posY,
        posZ,
        cameraPosition,
        cameraTarget,
        boundingRadius,
        coordinateVersion,
        modelVersion,
        modelUrl,
        threeDMeshId,
        motifId,
        fallbackThumbnailUrl,
        fallbackDiskPath,
        rightsAttribution,
      ];
}

/// Published 3D/2D manifest for an Urn
class UrnManifest extends Equatable {
  final String urnSlug;
  final int modelVersion;
  final int hotspotVersion;
  final UrnMeshStatus meshStatus;
  final bool has2dFallback;
  final String fallback2dUrl;
  final UrnViewerFallback viewerFallback;
  final Map<String, UrnLod> lods;
  final List<UrnManifestHotspot> hotspots;
  final String creator;
  final String rightsOwner;
  final String rightsAttribution;
  final String license;
  final String rightsStatus;
  final bool publicDistributionAllowed;
  final bool publicDisplayAllowed;
  final String? checksum;

  const UrnManifest({
    required this.urnSlug,
    this.modelVersion = 1,
    this.hotspotVersion = 1,
    required this.meshStatus,
    this.has2dFallback = true,
    required this.fallback2dUrl,
    required this.viewerFallback,
    this.lods = const {},
    this.hotspots = const [],
    this.creator = 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab',
    this.rightsOwner = 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
    this.rightsAttribution = 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
    this.license = 'CC BY 4.0 / Educational Fair Use',
    this.rightsStatus = 'cleared',
    this.publicDistributionAllowed = true,
    this.publicDisplayAllowed = true,
    this.checksum,
  });

  bool get hasPresentMesh => meshStatus == UrnMeshStatus.present;

  UrnManifestHotspot? findHotspot({
    String? motifId,
    String? name,
    String? meshName,
  }) {
    if (motifId != null && motifId.isNotEmpty) {
      for (final hs in hotspots) {
        if (hs.motifId == motifId || hs.hotspotId == motifId) return hs;
      }
    }
    if (name != null && name.isNotEmpty) {
      final norm = name.trim().toLowerCase();
      for (final hs in hotspots) {
        if (hs.reliefName.trim().toLowerCase() == norm ||
            hs.meshName.trim().toLowerCase() == norm) {
          return hs;
        }
      }
    }
    if (meshName != null && meshName.isNotEmpty) {
      final norm = meshName.trim().toLowerCase();
      for (final hs in hotspots) {
        if (hs.meshName.trim().toLowerCase() == norm) return hs;
      }
    }
    return null;
  }

  @override
  List<Object?> get props => [
        urnSlug,
        modelVersion,
        hotspotVersion,
        meshStatus,
        has2dFallback,
        fallback2dUrl,
        viewerFallback,
        lods,
        hotspots,
        creator,
        rightsOwner,
        license,
        rightsStatus,
      ];
}
