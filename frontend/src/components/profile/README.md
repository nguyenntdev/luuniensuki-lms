# Profile Gamification Components

Các component gamification cho trang profile, tương tự như mobile app.

## Components

### StreakCalendar
Hiển thị chuỗi học tập 7 ngày với trạng thái hoàn thành.

**Props:**
- `streak`: Object chứa `current_streak`, `last_activity_date`

### XpProgressBar
Thanh tiến trình XP đến cấp độ tiếp theo.

**Props:**
- `stats`: Object chứa `total_xp`, `rank`, `xp_to_next_rank`, `next_rank`

### GamificationHub
Các liên kết nhanh đến bảng xếp hạng, huy hiệu, mục tiêu, phần thưởng.

**Props:**
- `badges`: Số lượng huy hiệu (number)
- `rank`: Vị trí xếp hạng (number | null)

### StatsGrid
Lưới thống kê chi tiết (Khám phá, Học, Thành thạo, XP).

**Props:**
- `stats`: Object stats từ auth store
- `collection`: Object collection stats

### DailyGoalProgress
Tiến trình mục tiêu hàng ngày.

**Props:**
- `goal`: Object (optional) chứa `target`, `current`, `description`
- `progress`: Number - XP hiện tại (fallback)

## API Endpoints

- `GET /api/v1/users/me/streak` - Lấy thông tin streak
- `GET /api/v1/users/me/badges` - Lấy danh sách badges
- `GET /api/v1/users/me/collection` - Lấy thông tin collection

## Usage

```jsx
import {
  StreakCalendar,
  XpProgressBar,
  GamificationHub,
  StatsGrid,
  DailyGoalProgress,
} from '@/components/profile'

// Trong component
<StreakCalendar streak={streakData} />
<XpProgressBar stats={statsData} />
<GamificationHub badges={5} rank={12} />
<StatsGrid stats={statsData} collection={collectionData} />
<DailyGoalProgress progress={currentXp} />
```

