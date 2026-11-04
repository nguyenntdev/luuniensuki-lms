import 'package:equatable/equatable.dart';

/// Exceptions for citation provenance integrity violations.
class CitationProvenanceError implements Exception {
  final String message;
  const CitationProvenanceError(this.message);

  @override
  String toString() => 'CitationProvenanceError: $message';
}

class MissingSourceAttributionError implements Exception {
  final String message;
  const MissingSourceAttributionError(this.message);

  @override
  String toString() => 'MissingSourceAttributionError: $message';
}

/// Epistemic uncertainty status classifying historical evidence certainty.
enum EpistemicCertainty {
  documented('su_lieu_xac_thuc', 'Sử liệu xác thực', 'Documented Historical Fact'),
  traditional('truyen_thuyet_dan_gian', 'Truyền thuyết dân gian', 'Traditional Folklore'),
  uncertain('dang_khao_cuu', 'Đang khảo cứu', 'Under Investigation'),
  disputed('co_tranh_luan', 'Có tranh luận', 'Scholarly Dispute'),
  unreviewed('chua_kiem_chung', 'Chưa kiểm chứng', 'Unreviewed');

  final String code;
  final String labelVi;
  final String labelEn;

  const EpistemicCertainty(this.code, this.labelVi, this.labelEn);

  static EpistemicCertainty fromString(String? value) {
    if (value == null) return EpistemicCertainty.uncertain;
    final norm = value.trim().toLowerCase().replaceAll('-', '_').replaceAll(' ', '_');

    if (norm == 'su_lieu_xac_thuc' ||
        norm == 'documented' ||
        norm == 'verified' ||
        norm == 'expert_verified' ||
        norm == 'editor_reviewed') {
      return EpistemicCertainty.documented;
    }
    if (norm == 'truyen_thuyet_dan_gian' ||
        norm == 'traditional' ||
        norm == 'traditional_account' ||
        norm == 'legend' ||
        norm == 'folk_legend') {
      return EpistemicCertainty.traditional;
    }
    if (norm == 'co_tranh_luan' || norm == 'disputed' || norm == 'rejected') {
      return EpistemicCertainty.disputed;
    }
    if (norm == 'chua_kiem_chung' || norm == 'unreviewed' || norm == 'needs_source') {
      return EpistemicCertainty.unreviewed;
    }
    return EpistemicCertainty.uncertain;
  }
}

/// Rights status of the backing bibliographic source.
enum SourceRightsStatus {
  publicDomain('public_domain', 'Phạm vi công cộng'),
  openAccess('open_access', 'Truy cập mở'),
  restricted('restricted', 'Hạn chế truy cập'),
  copyright('copyright', 'Có bản quyền');

  final String code;
  final String labelVi;

  const SourceRightsStatus(this.code, this.labelVi);

  static SourceRightsStatus fromString(String? value) {
    if (value == null) return SourceRightsStatus.publicDomain;
    final norm = value.trim().toLowerCase().replaceAll('-', '_');
    if (norm.contains('restricted') || norm.contains('unlicensed')) {
      return SourceRightsStatus.restricted;
    }
    if (norm.contains('copyright') || norm.contains('all_rights_reserved')) {
      return SourceRightsStatus.copyright;
    }
    if (norm.contains('open') || norm.contains('cc_by') || norm.contains('cc0')) {
      return SourceRightsStatus.openAccess;
    }
    return SourceRightsStatus.publicDomain;
  }
}

/// Bibliographic Source Citation attached to a historical claim.
class SourceCitation extends Equatable {
  final String sourceId;
  final String sourceTitle;
  final String? author;
  final String? publisher;
  final int? publicationYear;
  final String locator;
  final String? quotationExcerpt;
  final bool isExcerptRedacted;
  final String? citationText;
  final SourceRightsStatus rightsStatus;
  final String? license;
  final bool publicDisplayAllowed;
  final String? url;
  final String? archiveUrl;
  final String supportType;
  final EpistemicCertainty epistemicCertainty;
  final String provenanceHash;

  const SourceCitation({
    required this.sourceId,
    required this.sourceTitle,
    this.author,
    this.publisher,
    this.publicationYear,
    required this.locator,
    this.quotationExcerpt,
    this.isExcerptRedacted = false,
    this.citationText,
    required this.rightsStatus,
    this.license,
    this.publicDisplayAllowed = true,
    this.url,
    this.archiveUrl,
    this.supportType = 'supports',
    this.epistemicCertainty = EpistemicCertainty.documented,
    required this.provenanceHash,
  });

  /// Check whether excerpt is restricted and protected from unauthorized leak.
  bool get isRestrictedSnippet =>
      isExcerptRedacted ||
      quotationExcerpt == '[REDACTED: RIGHTS_RESTRICTED]' ||
      (!publicDisplayAllowed && rightsStatus == SourceRightsStatus.restricted);

  factory SourceCitation.fromJson(Map<String, dynamic> json) {
    final rawExcerpt = json['quotation_excerpt']?.toString();
    final isRedacted = json['is_excerpt_redacted'] == true ||
        rawExcerpt == '[REDACTED: RIGHTS_RESTRICTED]';

    return SourceCitation(
      sourceId: json['source_id']?.toString() ?? '',
      sourceTitle: json['source_title']?.toString() ?? 'Nguồn sử liệu',
      author: json['author']?.toString(),
      publisher: json['publisher']?.toString(),
      publicationYear: json['publication_year'] is int
          ? json['publication_year'] as int
          : int.tryParse(json['publication_year']?.toString() ?? ''),
      locator: json['locator']?.toString() ?? 'Tài liệu lưu trữ',
      quotationExcerpt: rawExcerpt,
      isExcerptRedacted: isRedacted,
      citationText: json['citation_text']?.toString(),
      rightsStatus: SourceRightsStatus.fromString(json['rights_status']?.toString()),
      license: json['license']?.toString(),
      publicDisplayAllowed: json['public_display_allowed'] != false,
      url: json['url']?.toString(),
      archiveUrl: json['archive_url']?.toString(),
      supportType: json['support_type']?.toString() ?? 'supports',
      epistemicCertainty: EpistemicCertainty.fromString(json['epistemic_certainty']?.toString()),
      provenanceHash: json['provenance_hash']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'source_id': sourceId,
      'source_title': sourceTitle,
      'author': author,
      'publisher': publisher,
      'publication_year': publicationYear,
      'locator': locator,
      'quotation_excerpt': quotationExcerpt,
      'is_excerpt_redacted': isExcerptRedacted,
      'citation_text': citationText,
      'rights_status': rightsStatus.code,
      'license': license,
      'public_display_allowed': publicDisplayAllowed,
      'url': url,
      'archive_url': archiveUrl,
      'support_type': supportType,
      'epistemic_certainty': epistemicCertainty.code,
      'provenance_hash': provenanceHash,
    };
  }

  @override
  List<Object?> get props => [
        sourceId,
        sourceTitle,
        author,
        publisher,
        publicationYear,
        locator,
        quotationExcerpt,
        isExcerptRedacted,
        citationText,
        rightsStatus,
        license,
        publicDisplayAllowed,
        url,
        archiveUrl,
        supportType,
        epistemicCertainty,
        provenanceHash,
      ];
}

/// Historical Claim Citation linking assertion with source evidence.
class HistoricalClaimCitation extends Equatable {
  final String claimId;
  final String claimType;
  final String statementVi;
  final String? statementEn;
  final String? nameHanNom;
  final String? readingHanNom;
  final EpistemicCertainty epistemicCertainty;
  final String epistemicLabelVi;
  final String epistemicLabelEn;
  final String verificationStatus;
  final bool isDisputed;
  final bool hasSource;
  final List<SourceCitation> sources;
  final String provenanceSignature;

  const HistoricalClaimCitation({
    required this.claimId,
    required this.claimType,
    required this.statementVi,
    this.statementEn,
    this.nameHanNom,
    this.readingHanNom,
    required this.epistemicCertainty,
    required this.epistemicLabelVi,
    required this.epistemicLabelEn,
    required this.verificationStatus,
    this.isDisputed = false,
    this.hasSource = true,
    required this.sources,
    required this.provenanceSignature,
  });

  factory HistoricalClaimCitation.fromJson(Map<String, dynamic> json) {
    final sourcesList = (json['sources'] as List<dynamic>?)
            ?.map((s) => SourceCitation.fromJson(s as Map<String, dynamic>))
            .toList() ??
        const [];

    final epistemic = EpistemicCertainty.fromString(json['epistemic_certainty']?.toString());

    return HistoricalClaimCitation(
      claimId: json['claim_id']?.toString() ?? '',
      claimType: json['claim_type']?.toString() ?? 'factual',
      statementVi: json['statement_vi']?.toString() ?? '',
      statementEn: json['statement_en']?.toString(),
      nameHanNom: json['name_han_nom']?.toString(),
      readingHanNom: json['reading_han_nom']?.toString(),
      epistemicCertainty: epistemic,
      epistemicLabelVi: json['epistemic_label_vi']?.toString() ?? epistemic.labelVi,
      epistemicLabelEn: json['epistemic_label_en']?.toString() ?? epistemic.labelEn,
      verificationStatus: json['verification_status']?.toString() ?? 'unreviewed',
      isDisputed: json['is_disputed'] == true,
      hasSource: json['has_source'] != false && sourcesList.isNotEmpty,
      sources: sourcesList,
      provenanceSignature: json['provenance_signature']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'claim_id': claimId,
      'claim_type': claimType,
      'statement_vi': statementVi,
      'statement_en': statementEn,
      'name_han_nom': nameHanNom,
      'reading_han_nom': readingHanNom,
      'epistemic_certainty': epistemicCertainty.code,
      'epistemic_label_vi': epistemicLabelVi,
      'epistemic_label_en': epistemicLabelEn,
      'verification_status': verificationStatus,
      'is_disputed': isDisputed,
      'has_source': hasSource,
      'sources': sources.map((s) => s.toJson()).toList(),
      'provenance_signature': provenanceSignature,
    };
  }

  @override
  List<Object?> get props => [
        claimId,
        claimType,
        statementVi,
        statementEn,
        nameHanNom,
        readingHanNom,
        epistemicCertainty,
        epistemicLabelVi,
        epistemicLabelEn,
        verificationStatus,
        isDisputed,
        hasSource,
        sources,
        provenanceSignature,
      ];
}

/// Full Citation Bundle for an Urn or Motif/Relief Entity.
class EntityCitationBundle extends Equatable {
  final String entityId;
  final String slug;
  final String nameVi;
  final String? nameEn;
  final String? nameHanNom;
  final String? readingHanNom;
  final String entityType;
  final String? summaryVi;
  final String? summaryEn;
  final List<HistoricalClaimCitation> claims;
  final String bundleProvenanceHash;
  final int totalSourcesCount;
  final bool hasRestrictedSources;

  const EntityCitationBundle({
    required this.entityId,
    required this.slug,
    required this.nameVi,
    this.nameEn,
    this.nameHanNom,
    this.readingHanNom,
    required this.entityType,
    this.summaryVi,
    this.summaryEn,
    required this.claims,
    required this.bundleProvenanceHash,
    this.totalSourcesCount = 0,
    this.hasRestrictedSources = false,
  });

  /// Negative abuse validation: enforces that citation provenance cannot be stripped or falsified.
  void verifyProvenanceIntegrity() {
    if (bundleProvenanceHash.isEmpty || bundleProvenanceHash.length < 16) {
      throw const MissingSourceAttributionError(
        'Source attribution stripped: bundleProvenanceHash is missing or truncated.',
      );
    }

    for (final claim in claims) {
      // 1. Cannot claim 'documented' ('su_lieu_xac_thuc') without backing sources
      if (claim.epistemicCertainty == EpistemicCertainty.documented && claim.sources.isEmpty) {
        throw MissingSourceAttributionError(
          'Negative abuse detected: claim "${claim.claimId}" asserts "su_lieu_xac_thuc" '
          'without backing bibliographic source attribution.',
        );
      }

      // 2. Disputed claims cannot be marked documented
      if (claim.isDisputed && claim.epistemicCertainty == EpistemicCertainty.documented) {
        throw CitationProvenanceError(
          'Negative abuse detected: disputed claim "${claim.claimId}" cannot masquerade as verified fact.',
        );
      }

      // 3. Sources must contain valid attribution metadata
      for (final s in claim.sources) {
        if (s.sourceTitle.trim().isEmpty) {
          throw const MissingSourceAttributionError('Source title stripped from citation.');
        }
        if (s.locator.trim().isEmpty) {
          throw const MissingSourceAttributionError('Public locator stripped from citation.');
        }
      }
    }
  }

  factory EntityCitationBundle.fromJson(Map<String, dynamic> json) {
    final claimsList = (json['claims'] as List<dynamic>?)
            ?.map((c) => HistoricalClaimCitation.fromJson(c as Map<String, dynamic>))
            .toList() ??
        const [];

    final bundle = EntityCitationBundle(
      entityId: json['entity_id']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      nameVi: json['name_vi']?.toString() ?? '',
      nameEn: json['name_en']?.toString(),
      nameHanNom: json['name_han_nom']?.toString(),
      readingHanNom: json['reading_han_nom']?.toString(),
      entityType: json['entity_type']?.toString() ?? 'relief',
      summaryVi: json['summary_vi']?.toString(),
      summaryEn: json['summary_en']?.toString(),
      claims: claimsList,
      bundleProvenanceHash: json['bundle_provenance_hash']?.toString() ?? '',
      totalSourcesCount: json['total_sources_count'] is int
          ? json['total_sources_count'] as int
          : int.tryParse(json['total_sources_count']?.toString() ?? '') ??
              claimsList.fold<int>(0, (acc, c) => acc + c.sources.length),
      hasRestrictedSources: json['has_restricted_sources'] == true,
    );

    return bundle;
  }

  Map<String, dynamic> toJson() {
    return {
      'entity_id': entityId,
      'slug': slug,
      'name_vi': nameVi,
      'name_en': nameEn,
      'name_han_nom': nameHanNom,
      'reading_han_nom': readingHanNom,
      'entity_type': entityType,
      'summary_vi': summaryVi,
      'summary_en': summaryEn,
      'claims': claims.map((c) => c.toJson()).toList(),
      'bundle_provenance_hash': bundleProvenanceHash,
      'total_sources_count': totalSourcesCount,
      'has_restricted_sources': hasRestrictedSources,
    };
  }

  @override
  List<Object?> get props => [
        entityId,
        slug,
        nameVi,
        nameEn,
        nameHanNom,
        readingHanNom,
        entityType,
        summaryVi,
        summaryEn,
        claims,
        bundleProvenanceHash,
        totalSourcesCount,
        hasRestrictedSources,
      ];
}
