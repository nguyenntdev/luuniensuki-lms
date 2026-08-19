import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_typography.dart';
import '../../routing/route_names.dart';

class ReliefItem {
  final String id;
  final String slug;
  final String title;
  final String urnName;
  final String urnSlug;
  final String category;
  final String description;
  final String imageUrl;

  const ReliefItem({
    required this.id,
    required this.slug,
    required this.title,
    required this.urnName,
    required this.urnSlug,
    required this.category,
    required this.description,
    required this.imageUrl,
  });
}

// Sample canonical relief dataset for atlas exploration
const List<ReliefItem> kSampleReliefs = [
  ReliefItem(
    id: '1',
    slug: 'tuyen-trai',
    title: 'Tuyền Trãi (Sông Trãi)',
    urnName: 'Cao Đỉnh',
    urnSlug: 'cao-dinh',
    category: 'Sông núi',
    description: 'Dòng sông danh tiếng phương Nam được khắc trên Cao Đỉnh.',
    imageUrl: 'assets/images/ban-duc-noi/tuyen_trai.jpg',
  ),
  ReliefItem(
    id: '2',
    slug: 'long-thuyen',
    title: 'Thuyền Rồng (Long Thuyền)',
    urnName: 'Cao Đỉnh',
    urnSlug: 'cao-dinh',
    category: 'Binh khí & Thuyền',
    description: 'Thuyền chiến Hoàng gia Triều Nguyễn uy nghi mạnh mẽ.',
    imageUrl: 'assets/images/ban-duc-noi/long_thuyen.jpg',
  ),
  ReliefItem(
    id: '3',
    slug: 'ngu-binh',
    title: 'Núi Ngự Bình',
    urnName: 'Nhân Đỉnh',
    urnSlug: 'nhan-dinh',
    category: 'Sông núi',
    description: 'Núi án sơn che chắn cho Kinh thành Huế cổ kính.',
    imageUrl: 'assets/images/ban-duc-noi/ngu_binh.jpg',
  ),
  ReliefItem(
    id: '4',
    slug: 'huong-giang',
    title: 'Sông Hương (Hương Giang)',
    urnName: 'Nhân Đỉnh',
    urnSlug: 'nhan-dinh',
    category: 'Sông núi',
    description: 'Dòng sông thơ mộng của Xứ Huế truyền thống.',
    imageUrl: 'assets/images/ban-duc-noi/huong_giang.jpg',
  ),
  ReliefItem(
    id: '5',
    slug: 'hoa-sen',
    title: 'Hoa Sen (Lưu Hoa)',
    urnName: 'Chương Đỉnh',
    urnSlug: 'chuong-dinh',
    category: 'Thảo mộc',
    description: 'Quốc hoa cao quý tượng trưng cho sự thuần khiết.',
    imageUrl: 'assets/images/ban-duc-noi/hoa_sen.jpg',
  ),
  ReliefItem(
    id: '6',
    slug: 'con-voi',
    title: 'Tượng (Con Voi)',
    urnName: 'Anh Đỉnh',
    urnSlug: 'anh-dinh',
    category: 'Muông thú',
    description: 'Linh vật tượng trưng cho sức mạnh lực lượng quân sự.',
    imageUrl: 'assets/images/ban-duc-noi/con_voi.jpg',
  ),
];

const List<String> kUrnNames = [
  'Tất cả Đỉnh',
  'Cao Đỉnh',
  'Nhân Đỉnh',
  'Chương Đỉnh',
  'Anh Đỉnh',
  'Nghị Đỉnh',
  'Thuần Đỉnh',
  'Tuyên Đỉnh',
  'Dụ Đỉnh',
  'Huyền Đỉnh',
];

const List<String> kCategories = [
  'Tất cả thể loại',
  'Sông núi',
  'Thảo mộc',
  'Muông thú',
  'Binh khí & Thuyền',
];

class AtlasScreen extends ConsumerStatefulWidget {
  const AtlasScreen({super.key});

  @override
  ConsumerState<AtlasScreen> createState() => _AtlasScreenState();
}

class _AtlasScreenState extends ConsumerState<AtlasScreen> {
  String _selectedUrn = 'Tất cả Đỉnh';
  String _selectedCategory = 'Tất cả thể loại';
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<ReliefItem> get _filteredReliefs {
    return kSampleReliefs.where((relief) {
      final matchesUrn =
          _selectedUrn == 'Tất cả Đỉnh' || relief.urnName == _selectedUrn;
      final matchesCategory = _selectedCategory == 'Tất cả thể loại' ||
          relief.category == _selectedCategory;
      final matchesQuery = _searchQuery.isEmpty ||
          relief.title.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          relief.description.toLowerCase().contains(_searchQuery.toLowerCase());
      return matchesUrn && matchesCategory && matchesQuery;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _filteredReliefs;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bản Đồ Di Sản & Atlas'),
        actions: [
          IconButton(
            icon: const Icon(Icons.my_library_books_outlined),
            tooltip: 'Thư viện nguồn sử',
            onPressed: () => context.push(RoutePaths.sources),
          ),
          IconButton(
            icon: const Icon(Icons.view_in_ar),
            tooltip: 'Gói mô hình 3D',
            onPressed: () => context.push(RoutePaths.modelPackages),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search box
          Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: TextField(
              controller: _searchController,
              onChanged: (val) => setState(() => _searchQuery = val),
              decoration: InputDecoration(
                hintText: 'Tìm kiếm hình đúc, danh thắng, thảo mộc...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _searchQuery = '');
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16),
              ),
            ),
          ),

          // Filter bar: Urns selector
          SizedBox(
            height: 40,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
              itemCount: kUrnNames.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final urn = kUrnNames[index];
                final isSelected = urn == _selectedUrn;
                return ChoiceChip(
                  label: Text(urn),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedUrn = urn);
                  },
                );
              },
            ),
          ),
          const SizedBox(height: 8),

          // Filter bar: Categories selector
          SizedBox(
            height: 40,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
              itemCount: kCategories.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final category = kCategories[index];
                final isSelected = category == _selectedCategory;
                return FilterChip(
                  label: Text(category),
                  selected: isSelected,
                  onSelected: (selected) {
                    setState(() {
                      _selectedCategory =
                          selected ? category : 'Tất cả thể loại';
                    });
                  },
                );
              },
            ),
          ),
          const SizedBox(height: 12),

          // Relief Grid
          Expanded(
            child: filtered.isEmpty
                ? Center(
                    child: Text(
                      'Không tìm thấy hình đúc phù hợp.',
                      style: AppTypography.textTheme.bodyMedium,
                    ),
                  )
                : GridView.builder(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      childAspectRatio: 0.85,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                    ),
                    itemCount: filtered.length,
                    itemBuilder: (context, index) {
                      final item = filtered[index];
                      return Card(
                        clipBehavior: Clip.antiAlias,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: InkWell(
                          onTap: () {
                            context.push(
                              RoutePaths.atlasRelief(
                                item.urnSlug,
                                item.slug,
                              ),
                            );
                          },
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: Container(
                                  width: double.infinity,
                                  color: Colors.amber.shade900.withOpacity(0.2),
                                  child: Center(
                                    child: Icon(
                                      Icons.photo_size_select_actual_outlined,
                                      size: 48,
                                      color: Colors.amber.shade700,
                                    ),
                                  ),
                                ),
                              ),
                              Padding(
                                padding: const EdgeInsets.all(AppSpacing.sm),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item.title,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style:
                                          AppTypography.textTheme.titleSmall,
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 6,
                                            vertical: 2,
                                          ),
                                          decoration: BoxDecoration(
                                            color: Theme.of(context)
                                                .colorScheme
                                                .primaryContainer,
                                            borderRadius:
                                                BorderRadius.circular(4),
                                          ),
                                          child: Text(
                                            item.urnName,
                                            style: AppTypography
                                                .textTheme.labelSmall
                                                ?.copyWith(
                                              color: Theme.of(context)
                                                  .colorScheme
                                                  .onPrimaryContainer,
                                            ),
                                          ),
                                        ),
                                        const Spacer(),
                                        Text(
                                          item.category,
                                          style: AppTypography
                                              .textTheme.bodySmall,
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
