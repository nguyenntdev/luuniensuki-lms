# Leaderboard Enhancement - Testing Guide

## Manual Testing Checklist

### 1. User Authentication Tests

#### Test Case 1.1: Unauthenticated User
**Steps:**
1. Log out if currently logged in
2. Navigate to `/leaderboard`
3. Observe the leaderboard display

**Expected Results:**
- ✅ Leaderboard displays all entries
- ✅ No UserRankCard shown at top
- ✅ No rows highlighted
- ✅ No "(Bạn)" labels
- ✅ Rank badges display correctly for all ranks

#### Test Case 1.2: Authenticated User in Leaderboard
**Steps:**
1. Log in with a user that has earned XP
2. Navigate to `/leaderboard`
3. Locate your entry in the list

**Expected Results:**
- ✅ UserRankCard displays at top with your rank info
- ✅ Your row in table has `bg-primary/10` background
- ✅ "(Bạn)" label appears next to your name
- ✅ RankBadge shows your rank correctly
- ✅ XP totals match in both card and table row

#### Test Case 1.3: Authenticated User Not in Leaderboard
**Steps:**
1. Log in with a new user (0 XP)
2. Navigate to `/leaderboard`

**Expected Results:**
- ✅ No UserRankCard shown (user not in top 50)
- ✅ No rows highlighted
- ✅ Leaderboard displays normally

### 2. Rank Badge Tests

#### Test Case 2.1: Top 3 Ranks
**Steps:**
1. Navigate to `/leaderboard`
2. Check first three entries

**Expected Results:**
- ✅ Rank 1: Gold medal 🥇 with yellow background
- ✅ Rank 2: Silver medal 🥈 with gray background
- ✅ Rank 3: Bronze medal 🥉 with amber background
- ✅ All badges are circular (8x8) with shadow

#### Test Case 2.2: Ranks 4+
**Steps:**
1. Scroll to ranks beyond top 3
2. Check badge appearance

**Expected Results:**
- ✅ Number displayed in circular badge
- ✅ Muted background color
- ✅ Consistent size with top 3 badges

### 3. UserRankCard Tests

#### Test Case 3.1: Card Display
**Steps:**
1. Log in and navigate to `/leaderboard`
2. Check UserRankCard at top

**Expected Results:**
- ✅ Card has gradient background (primary/10 to primary/5)
- ✅ Card has 2px primary border
- ✅ Card has shadow effect
- ✅ RankBadge displays on left
- ✅ "Hạng của bạn" label visible
- ✅ User name and title displayed
- ✅ XP label and value on right

#### Test Case 3.2: Card Responsive Design
**Steps:**
1. Resize browser to mobile width (< 640px)
2. Check card layout

**Expected Results:**
- ✅ Card maintains readability
- ✅ Content doesn't overflow
- ✅ Proper spacing maintained

### 4. Table Interaction Tests

#### Test Case 4.1: Hover Effects
**Steps:**
1. Log in and navigate to `/leaderboard`
2. Hover over different table rows

**Expected Results:**
- ✅ Non-current user rows show hover state (`bg-muted/50`)
- ✅ Current user row doesn't change on hover
- ✅ Smooth transition animation

#### Test Case 4.2: Current User Highlighting
**Steps:**
1. Log in and find your row
2. Compare with other rows

**Expected Results:**
- ✅ Your row has distinct `bg-primary/10` background
- ✅ Background color consistent across entire row
- ✅ "(Bạn)" label in primary color

### 5. Data Loading Tests

#### Test Case 5.1: Loading State
**Steps:**
1. Clear cache and reload `/leaderboard`
2. Observe loading state

**Expected Results:**
- ✅ Skeleton loaders display for 10 rows
- ✅ Skeleton in rank column (w-6)
- ✅ Skeleton in name column (w-32)
- ✅ Skeleton in title column (w-24)
- ✅ Skeleton in XP column (w-12)

#### Test Case 5.2: Empty State
**Steps:**
1. Mock API to return empty array
2. Navigate to `/leaderboard`

**Expected Results:**
- ✅ "Chưa có dữ liệu." message displays
- ✅ Message spans all 4 columns
- ✅ Centered text

#### Test Case 5.3: Error State
**Steps:**
1. Mock API to throw error
2. Navigate to `/leaderboard`

**Expected Results:**
- ✅ Error message displays in red box
- ✅ Error box has destructive styling
- ✅ Table still renders (empty or cached)

### 6. Visual Consistency Tests

#### Test Case 6.1: Theme Compatibility
**Steps:**
1. Test with light theme
2. Test with dark theme (if applicable)

**Expected Results:**
- ✅ All colors use theme tokens (primary, muted, etc.)
- ✅ Text remains readable
- ✅ Borders and shadows appropriate for theme

#### Test Case 6.2: Font Consistency
**Steps:**
1. Check all text elements
2. Compare with rest of application

**Expected Results:**
- ✅ `font-display` used for rank numbers and XP
- ✅ `tabular-nums` for numeric values
- ✅ Consistent font weights

### 7. Edge Cases

#### Test Case 7.1: Long User Names
**Steps:**
1. Test with very long display name
2. Check table layout

**Expected Results:**
- ✅ Name doesn't overflow cell
- ✅ Table layout remains intact
- ✅ Consider truncation if needed

#### Test Case 7.2: Zero XP Users
**Steps:**
1. Check users with 0 XP
2. Verify display

**Expected Results:**
- ✅ "0" displays correctly
- ✅ No formatting issues

#### Test Case 7.3: Large XP Values
**Steps:**
1. Check users with high XP (100,000+)
2. Verify display

**Expected Results:**
- ✅ Numbers formatted correctly
- ✅ No overflow issues
- ✅ Alignment maintained

## Automated Testing (Future)

### Unit Tests
```javascript
describe('RankBadge', () => {
  it('renders gold medal for rank 1', () => {});
  it('renders silver medal for rank 2', () => {});
  it('renders bronze medal for rank 3', () => {});
  it('renders number for other ranks', () => {});
});

describe('UserRankCard', () => {
  it('renders when userEntry provided', () => {});
  it('returns null when no userEntry', () => {});
  it('displays correct user information', () => {});
});

describe('LeaderboardPage', () => {
  it('highlights current user row', () => {});
  it('shows UserRankCard for authenticated user', () => {});
  it('hides UserRankCard for unauthenticated user', () => {});
});
```

### Integration Tests
- API integration with `/api/v1/leaderboard`
- Auth store integration
- Route navigation

## Performance Checklist
- ✅ No unnecessary re-renders
- ✅ Efficient user lookup (`find` once)
- ✅ Conditional rendering optimized
- ✅ No layout shifts during load

## Accessibility Checklist
- ✅ Semantic HTML (table structure)
- ✅ Proper heading hierarchy
- ✅ Sufficient color contrast
- ✅ Keyboard navigation support
- ✅ Screen reader friendly

## Browser Compatibility
Test in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Sign-off
- [ ] All manual tests passed
- [ ] Visual review complete
- [ ] Responsive design verified
- [ ] Performance acceptable
- [ ] Ready for production

