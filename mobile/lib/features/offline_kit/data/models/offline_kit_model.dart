/// Low-Bandwidth Printable / Offline Kit Model (Ticket V5-T096).
///
/// Ensures 100% learning outcomes are achievable offline without requiring
/// any AR, WebXR, camera permission, or high-end smartphone hardware.

class OfflineSourceExcerpt {
  final String sourceTitle;
  final String volume;
  final String citation;
  final String rightsOwner;
  final String license;

  const OfflineSourceExcerpt({
    required this.sourceTitle,
    required this.volume,
    required this.citation,
    this.rightsOwner = 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
    this.license = 'CC BY 4.0 / Educational Fair Use',
  });

  factory OfflineSourceExcerpt.fromJson(Map<String, dynamic> json) {
    return OfflineSourceExcerpt(
      sourceTitle: json['source_title'] ?? '',
      volume: json['volume_or_chapter'] ?? json['volume'] ?? '',
      citation: json['citation'] ?? '',
      rightsOwner: json['rights_owner'] ?? 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
      license: json['license'] ?? 'CC BY 4.0 / Educational Fair Use',
    );
  }

  Map<String, dynamic> toJson() => {
        'source_title': sourceTitle,
        'volume_or_chapter': volume,
        'citation': citation,
        'rights_owner': rightsOwner,
        'license': license,
      };
}

class OfflineRubbingAsset {
  final String assetUrl;
  final String localPath;
  final String captionVi;
  final String highContrastCss;
  final String rightsAttribution;

  const OfflineRubbingAsset({
    required this.assetUrl,
    required this.localPath,
    required this.captionVi,
    this.highContrastCss = 'filter: contrast(160%) grayscale(100%) brightness(95%);',
    this.rightsAttribution = 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
  });

  factory OfflineRubbingAsset.fromJson(Map<String, dynamic> json) {
    return OfflineRubbingAsset(
      assetUrl: json['asset_url'] ?? '',
      localPath: json['local_path'] ?? '',
      captionVi: json['caption_vi'] ?? 'Bản dập 2D độ tương phản cao',
      highContrastCss: json['high_contrast_css'] ?? 'filter: contrast(160%) grayscale(100%) brightness(95%);',
      rightsAttribution: json['rights_attribution'] ?? 'Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)',
    );
  }

  Map<String, dynamic> toJson() => {
        'asset_url': assetUrl,
        'local_path': localPath,
        'caption_vi': captionVi,
        'high_contrast_css': highContrastCss,
        'rights_attribution': rightsAttribution,
      };
}

class OfflineInspectionTask {
  final String taskTitleVi;
  final String instructionsVi;
  final List<String> checkpoints;
  final String sketchPromptVi;
  final bool paperAchievable;
  final bool arOrSmartphoneRequired;

  const OfflineInspectionTask({
    required this.taskTitleVi,
    required this.instructionsVi,
    required this.checkpoints,
    required this.sketchPromptVi,
    this.paperAchievable = true,
    this.arOrSmartphoneRequired = false,
  });

  factory OfflineInspectionTask.fromJson(Map<String, dynamic> json) {
    return OfflineInspectionTask(
      taskTitleVi: json['task_title_vi'] ?? '',
      instructionsVi: json['instructions_vi'] ?? '',
      checkpoints: List<String>.from(json['checkpoints'] ?? []),
      sketchPromptVi: json['sketch_prompt_vi'] ?? 'Khung phác họa thực địa:',
      paperAchievable: json['paper_achievable'] ?? true,
      arOrSmartphoneRequired: json['ar_or_smartphone_required'] ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'task_title_vi': taskTitleVi,
        'instructions_vi': instructionsVi,
        'checkpoints': checkpoints,
        'sketch_prompt_vi': sketchPromptVi,
        'paper_achievable': paperAchievable,
        'ar_or_smartphone_required': arOrSmartphoneRequired,
      };
}

class OfflineAudioTranscript {
  final String trackTitleVi;
  final String narrator;
  final String durationText;
  final String scriptText;
  final List<String> keyQuotes;

  const OfflineAudioTranscript({
    required this.trackTitleVi,
    required this.narrator,
    required this.durationText,
    required this.scriptText,
    required this.keyQuotes,
  });

  factory OfflineAudioTranscript.fromJson(Map<String, dynamic> json) {
    return OfflineAudioTranscript(
      trackTitleVi: json['track_title_vi'] ?? '',
      narrator: json['narrator'] ?? 'Lưu Niên Voice Guide',
      durationText: json['duration_text'] ?? '2 phút',
      scriptText: json['script_text'] ?? '',
      keyQuotes: List<String>.from(json['key_quotes'] ?? []),
    );
  }

  Map<String, dynamic> toJson() => {
        'track_title_vi': trackTitleVi,
        'narrator': narrator,
        'duration_text': durationText,
        'script_text': scriptText,
        'key_quotes': keyQuotes,
      };
}

class OfflineKitStationModel {
  final int stationIndex;
  final String monumentSlug;
  final String monumentNameVi;
  final String zoneNameVi;
  final String reign;
  final int constructionYear;
  final OfflineSourceExcerpt primarySource;
  final OfflineRubbingAsset rubbingAsset;
  final OfflineInspectionTask offlineTask;
  final OfflineAudioTranscript audioTranscript;
  final String qrCodeUrl;

  const OfflineKitStationModel({
    required this.stationIndex,
    required this.monumentSlug,
    required this.monumentNameVi,
    required this.zoneNameVi,
    required this.reign,
    required this.constructionYear,
    required this.primarySource,
    required this.rubbingAsset,
    required this.offlineTask,
    required this.audioTranscript,
    required this.qrCodeUrl,
  });

  factory OfflineKitStationModel.fromJson(Map<String, dynamic> json) {
    return OfflineKitStationModel(
      stationIndex: json['station_index'] ?? 1,
      monumentSlug: json['monument_slug'] ?? '',
      monumentNameVi: json['monument_name_vi'] ?? '',
      zoneNameVi: json['zone_name_vi'] ?? '',
      reign: json['reign'] ?? 'Nguyễn',
      constructionYear: json['construction_year'] ?? 1804,
      primarySource: OfflineSourceExcerpt.fromJson(json['primary_source'] ?? {}),
      rubbingAsset: OfflineRubbingAsset.fromJson(json['rubbing_asset'] ?? {}),
      offlineTask: OfflineInspectionTask.fromJson(json['offline_task'] ?? {}),
      audioTranscript: OfflineAudioTranscript.fromJson(json['audio_transcript'] ?? {}),
      qrCodeUrl: json['qr_code_url'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'station_index': stationIndex,
        'monument_slug': monumentSlug,
        'monument_name_vi': monumentNameVi,
        'zone_name_vi': zoneNameVi,
        'reign': reign,
        'construction_year': constructionYear,
        'primary_source': primarySource.toJson(),
        'rubbing_asset': rubbingAsset.toJson(),
        'offline_task': offlineTask.toJson(),
        'audio_transcript': audioTranscript.toJson(),
        'qr_code_url': qrCodeUrl,
      };
}

class LowBandwidthKitModel {
  final String kitId;
  final String titleVi;
  final String subtitleVi;
  final bool zeroDeviceGuarantee;
  final int paperAchievablePercent;
  final bool arOrSmartphoneMandatory;
  final List<OfflineKitStationModel> stations;

  const LowBandwidthKitModel({
    required this.kitId,
    required this.titleVi,
    required this.subtitleVi,
    this.zeroDeviceGuarantee = true,
    this.paperAchievablePercent = 100,
    this.arOrSmartphoneMandatory = false,
    required this.stations,
  });

  factory LowBandwidthKitModel.fromJson(Map<String, dynamic> json) {
    return LowBandwidthKitModel(
      kitId: json['kit_id'] ?? 'kit-low-bandwidth-standard_4',
      titleVi: json['title_vi'] ?? 'Gói học tập ngoại tuyến di sản Huế',
      subtitleVi: json['subtitle_vi'] ?? 'Bộ công cụ điền dã không bắt buộc AR',
      zeroDeviceGuarantee: json['zero_device_guarantee'] ?? true,
      paperAchievablePercent: json['paper_achievable_percent'] ?? 100,
      arOrSmartphoneMandatory: json['ar_or_smartphone_mandatory'] ?? false,
      stations: (json['stations'] as List<dynamic>?)
              ?.map((e) => OfflineKitStationModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  /// Default curated bundle covering the 4 standard pedagogical stations
  static LowBandwidthKitModel defaultStandard4() {
    return LowBandwidthKitModel(
      kitId: 'kit-low-bandwidth-standard_4',
      titleVi: 'Gói học tập ngoại tuyến & Phiếu in thực địa di sản Huế',
      subtitleVi: 'Bộ công cụ điền dã dành cho trường học vùng xa & không bắt buộc AR',
      zeroDeviceGuarantee: true,
      paperAchievablePercent: 100,
      arOrSmartphoneMandatory: false,
      stations: [
        OfflineKitStationModel(
          stationIndex: 1,
          monumentSlug: 'ngo-mon',
          monumentNameVi: 'Ngọ Môn (Lầu Ngũ Phụng)',
          zoneNameVi: 'Trục nghi lễ trung tâm',
          reign: 'Minh Mạng',
          constructionYear: 1833,
          primarySource: const OfflineSourceExcerpt(
            sourceTitle: 'Đại Nam Thực Lục Chính Biên',
            volume: 'Đệ nhị kỷ, Quyển 98',
            citation: 'Dựng cổng Ngọ Môn ở đài Nam Sách cũ; dưới trổ 5 cửa: cửa giữa dành cho thiên tử, hai bên dành cho bá quan, hai cửa dực dành cho binh mã cấm vệ.',
          ),
          rubbingAsset: const OfflineRubbingAsset(
            assetUrl: '/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg',
            localPath: 'ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg',
            captionVi: 'Bản dập 2D độ tương phản cao — Hoa văn rồng mây Ngọ Môn (Cao Đỉnh)',
          ),
          offlineTask: const OfflineInspectionTask(
            taskTitleVi: 'Nhiệm vụ 100% trên giấy: Khảo sát Ngọ Môn',
            instructionsVi: 'Quan sát hệ thống cổng đá chữ U hoặc bản dập 2D. Đếm 5 lối cửa và đối chiếu trật tự thiên tử - bá quan.',
            checkpoints: [
              'Đếm đủ 5 lối cửa vòm đá trên thân đài Ngọ Môn.',
              'Đối chiếu vị trí cửa giữa (dành riêng cho vua) với hai cửa Giáp Môn.',
              'Phác họa sơ đồ mặt bằng chữ U vào khung vẽ.',
            ],
            sketchPromptVi: 'Khung phác họa mặt bằng chữ U Ngọ Môn:',
            paperAchievable: true,
            arOrSmartphoneRequired: false,
          ),
          audioTranscript: const OfflineAudioTranscript(
            trackTitleVi: 'Thuyết minh âm thanh: Ngọ Môn',
            narrator: 'Lưu Niên Voice Guide — Giọng Cố Đô',
            durationText: '2 phút (128s)',
            scriptText: 'Chào mừng các bạn đến với Ngọ Môn — chiếc cổng chính sừng sững tại mặt nam Hoàng Thành Huế. Khởi dựng vào năm Minh Mạng thứ 14 (1833), Ngọ Môn gồm đài đá chữ U trổ đúng 5 cửa ngõ và Lầu Ngũ Phụng với 100 cột gỗ lim vững chãi.',
            keyQuotes: [
              'Cấu trúc chữ U phân luồng tuyệt đối thể hiện trật tự đẳng cấp triều Nguyễn.',
              'Ngọ Môn là kiệt tác nghệ thuật kiến trúc gỗ và đá đỉnh cao.',
            ],
          ),
          qrCodeUrl: 'https://luuniensuki.vn/dai-noi/cong-trinh/ngo-mon',
        ),
        OfflineKitStationModel(
          stationIndex: 2,
          monumentSlug: 'dien-thai-hoa',
          monumentNameVi: 'Điện Thái Hòa & Sân Đại Triều Nghi',
          zoneNameVi: 'Trục nghi lễ trung tâm',
          reign: 'Gia Long',
          constructionYear: 1805,
          primarySource: const OfflineSourceExcerpt(
            sourceTitle: 'Khâm Định Đại Nam Hội Điển Sự Lệ',
            volume: 'Quyển 65 (Lại bộ - Lễ Triều nghi)',
            citation: 'Văn võ bá quan vào chầu: quan tứ phẩm trở lên đứng tầng sân trên, ngũ phẩm đến cửu phẩm đứng tầng sân dưới, quan văn bên tả, quan võ bên hữu.',
          ),
          rubbingAsset: const OfflineRubbingAsset(
            assetUrl: '/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg',
            localPath: 'ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg',
            captionVi: 'Bản dập 2D độ tương phản cao — Điện Thái Hòa & Sân Đại Triều (Nhân Đỉnh)',
          ),
          offlineTask: const OfflineInspectionTask(
            taskTitleVi: 'Nhiệm vụ 100% trên giấy: Khảo sát Điện Thái Hòa',
            instructionsVi: 'Quan sát mặt bằng hai tầng sân Đại Triều Nghi và hàng bia phẩm sơn đá thanh.',
            checkpoints: [
              'Xác định ranh giới giữa tầng sân trên và tầng sân dưới.',
              'Quan sát các hàng bia đá khắc phẩm trật quan chế.',
              'Ghi chép kết cấu trùng thiềm điệp ốc đặc trưng.',
            ],
            sketchPromptVi: 'Khung phác họa mặt cắt hai tầng sân Đại Triều:',
            paperAchievable: true,
            arOrSmartphoneRequired: false,
          ),
          audioTranscript: const OfflineAudioTranscript(
            trackTitleVi: 'Thuyết minh âm thanh: Điện Thái Hòa',
            narrator: 'Lưu Niên Voice Guide — Giọng Cố Đô',
            durationText: '2 phút (135s)',
            scriptText: 'Điện Thái Hòa là trái tim của Hoàng Thành Huế, nơi diễn ra các đại lễ đăng quang, thiết triều và tiếp đón sứ thần. Kiến trúc nhà kép trùng thiềm điệp ốc lợp ngói hoàng lưu ly rực rỡ.',
            keyQuotes: [
              'Hai tầng sân phản ánh trực tiếp hệ thống cửu phẩm quan chế triều Nguyễn.',
            ],
          ),
          qrCodeUrl: 'https://luuniensuki.vn/dai-noi/cong-trinh/dien-thai-hoa',
        ),
        OfflineKitStationModel(
          stationIndex: 3,
          monumentSlug: 'hien-lam-cac',
          monumentNameVi: 'Hiển Lâm Các & Thế Miếu',
          zoneNameVi: 'Không gian thờ tự tổ tiên',
          reign: 'Minh Mạng',
          constructionYear: 1822,
          primarySource: const OfflineSourceExcerpt(
            sourceTitle: 'Đại Nam Nhất Thống Chí',
            volume: 'Quyển 1 (Kinh sư - Hiển Lâm Các)',
            citation: 'Hiển Lâm Các dựng năm Minh Mạng thứ 3 (1822), ba tầng cao vút, dùng để ghi nhớ công đức các vua và công thần mở cõi.',
          ),
          rubbingAsset: const OfflineRubbingAsset(
            assetUrl: '/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg',
            localPath: 'ban-duc-noi/CHUONG DINH/CHƯƠNG ĐỈNH.jpg',
            captionVi: 'Bản dập 2D độ tương phản cao — Hiển Lâm Các (Chương Đỉnh)',
          ),
          offlineTask: const OfflineInspectionTask(
            taskTitleVi: 'Nhiệm vụ 100% trên giấy: Khảo sát Hiển Lâm Các',
            instructionsVi: 'Quan sát kiến trúc 3 tầng lầu bằng gỗ và mối quan hệ vị trí phong thủy chắn trước Thế Miếu.',
            checkpoints: [
              'Đếm đủ 3 tầng lầu gỗ với hệ mái vươn cao.',
              'Ghi nhận vị trí phong thủy đối diện Cửu Đỉnh và sân Thế Miếu.',
              'Xác nhận không công trình nào trong Thành được phép xây cao hơn.',
            ],
            sketchPromptVi: 'Khung phác họa tỷ lệ 3 tầng gỗ Hiển Lâm Các:',
            paperAchievable: true,
            arOrSmartphoneRequired: false,
          ),
          audioTranscript: const OfflineAudioTranscript(
            trackTitleVi: 'Thuyết minh âm thanh: Hiển Lâm Các',
            narrator: 'Lưu Niên Voice Guide — Giọng Cố Đô',
            durationText: '2 phút (120s)',
            scriptText: 'Hiển Lâm Các là đài tưởng niệm tôn vinh các bậc tiên đế và khai quốc công thần. Với chiều cao 17m, đây là công trình kiến trúc gỗ cao nhất trong Hoàng Thành Huế.',
            keyQuotes: [
              'Hiển Lâm Các giữ trật tự tôn ti thiêng liêng trước sân Thế Miếu.',
            ],
          ),
          qrCodeUrl: 'https://luuniensuki.vn/dai-noi/cong-trinh/hien-lam-cac',
        ),
        OfflineKitStationModel(
          stationIndex: 4,
          monumentSlug: 'cung-dien-tho',
          monumentNameVi: 'Cung Diên Thọ',
          zoneNameVi: 'Khu sinh hoạt hoàng gia',
          reign: 'Gia Long',
          constructionYear: 1804,
          primarySource: const OfflineSourceExcerpt(
            sourceTitle: 'Đại Nam Thực Lục Chính Biên',
            volume: 'Đệ nhất kỷ, Quyển 23',
            citation: 'Tháng 4 năm Giáp Tý (1804), dựng cung Trường Thọ phía tây bắc Tử Cấm Thành để phụng dưỡng Vương Thái Hậu.',
          ),
          rubbingAsset: const OfflineRubbingAsset(
            assetUrl: '/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg',
            localPath: 'ban-duc-noi/ANH DINH/ANH ĐỈNH.jpg',
            captionVi: 'Bản dập 2D độ tương phản cao — Cung Diên Thọ (Anh Đỉnh)',
          ),
          offlineTask: const OfflineInspectionTask(
            taskTitleVi: 'Nhiệm vụ 100% trên giấy: Khảo sát Cung Diên Thọ',
            instructionsVi: 'Quan sát chính điện Diên Thọ, hành lang có mái che dương lang và lầu Tịnh Minh mang phong cách Pháp - Việt.',
            checkpoints: [
              'Quan sát hành lang có mái che nối giữa các công trình.',
              'So sánh nét kiến trúc truyền thống chính điện với Tịnh Minh Lâu.',
              'Ghi nhận văn hóa hiếu đạo cung đình triều Nguyễn.',
            ],
            sketchPromptVi: 'Khung phác họa hành lang dương lang Cung Diên Thọ:',
            paperAchievable: true,
            arOrSmartphoneRequired: false,
          ),
          audioTranscript: const OfflineAudioTranscript(
            trackTitleVi: 'Thuyết minh âm thanh: Cung Diên Thọ',
            narrator: 'Lưu Niên Voice Guide — Giọng Cố Đô',
            durationText: '2 phút (118s)',
            scriptText: 'Cung Diên Thọ là tổ hợp kiến trúc hoàng cung nguyên vẹn nhất, nơi sinh sống của các Hoàng Thái Hậu triều Nguyễn. Nơi đây thể hiện nét sinh hoạt hoàng gia thanh tao và đạo hiếu truyền thống.',
            keyQuotes: [
              'Cung Diên Thọ lưu giữ nguyên vẹn trật tự sinh hoạt hoàng tộc triều Nguyễn.',
            ],
          ),
          qrCodeUrl: 'https://luuniensuki.vn/dai-noi/cong-trinh/cung-dien-tho',
        ),
      ],
    );
  }
}
