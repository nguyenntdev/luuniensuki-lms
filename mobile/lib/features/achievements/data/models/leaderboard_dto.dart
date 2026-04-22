/// Data transfer object for leaderboard entry from API
class LeaderboardEntryDto {
  final int rank;
  final String userId;
  final String displayName;
  final String? avatarUrl;
  final int totalXp;
  final String title;

  const LeaderboardEntryDto({
    required this.rank,
    required this.userId,
    required this.displayName,
    this.avatarUrl,
    required this.totalXp,
    required this.title,
  });

  factory LeaderboardEntryDto.fromJson(Map<String, dynamic> json) {
    return LeaderboardEntryDto(
      rank: json['rank'] as int,
      userId: json['user_id'] as String,
      displayName: json['display_name'] as String,
      avatarUrl: json['avatar_url'] as String?,
      totalXp: json['total_xp'] as int,
      title: json['title'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'rank': rank,
      'user_id': userId,
      'display_name': displayName,
      'avatar_url': avatarUrl,
      'total_xp': totalXp,
      'title': title,
    };
  }
}

