# PHASE 2: TECHNICAL SPECIFICATIONS

> **Project:** Lưu Niên Sử Kí LMS  
> **Version:** 1.0  
> **Date:** 2024-12-14  
> **Status:** APPROVED

> **Repo layout note:** backend code lives in `backend/` (e.g. `backend/main.py`, `backend/models.py`). Adjust file paths/imports in examples accordingly.

---

## 1. BACKEND API SPECIFICATIONS

### 1.1 New Pydantic Schemas (to add in main.py or schemas.py)

```python
# ============================================
# QUIZ SCHEMAS
# ============================================

class QuizQuestionOut(BaseModel):
    id: UUID
    question_type: str  # multiple_choice, true_false, image_select, mesh_location
    question_text: str
    options: Optional[list[str]] = None  # shuffled for multiple_choice
    difficulty: int
    target_mesh_name: Optional[str] = None  # for mesh_location type

class QuizQuestionsResponse(BaseModel):
    motif_id: UUID
    motif_name: str
    questions: list[QuizQuestionOut]
    total_questions: int

class QuizAnswerItem(BaseModel):
    question_id: UUID
    answer: str

class QuizSubmitRequest(BaseModel):
    motif_id: UUID
    answers: list[QuizAnswerItem]
    time_taken_seconds: int = Field(ge=0)

class QuizResultItem(BaseModel):
    question_id: UUID
    correct: bool
    user_answer: str
    correct_answer: str
    explanation: Optional[str] = None

class QuizSubmitResponse(BaseModel):
    attempt_id: UUID
    score: float  # 0.0 - 1.0
    passed: bool
    xp_earned: int
    new_status: str  # discovered, learned, mastered
    total_xp: int
    results: list[QuizResultItem]
    badges_earned: list[str] = []

# ============================================
# BADGE SCHEMAS
# ============================================

class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon_url: str
    category: str
    xp_bonus: int

class EarnedBadgeOut(BaseModel):
    badge: BadgeOut
    earned_at: datetime

class BadgeProgressOut(BaseModel):
    badge: BadgeOut
    current: int
    target: int
    progress_percent: float

class UserBadgesResponse(BaseModel):
    earned: list[EarnedBadgeOut]
    in_progress: list[BadgeProgressOut]
    total_badge_xp: int

# ============================================
# LEADERBOARD SCHEMAS
# ============================================

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    display_name: str
    avatar_url: Optional[str] = None
    total_xp: int
    level: int
    level_name: str

class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    current_user: Optional[LeaderboardEntry] = None
    total_users: int
    period: str  # all_time, weekly, monthly

# ============================================
# STREAK SCHEMAS
# ============================================

class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_active_date: Optional[date] = None
    streak_freezes_available: int
    streak_at_risk: bool
    days_until_next_badge: Optional[int] = None

# ============================================
# URN SCHEMAS (Enhanced)
# ============================================

class UrnProgressOut(BaseModel):
    discovered: int
    learned: int
    mastered: int
    total: int
    completion_percent: float

class UrnDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    name: str
    name_han: Optional[str] = None
    represents: Optional[str] = None
    description: Optional[str] = None
    model_url: str
    thumbnail_url: Optional[str] = None
    display_order: int
    motif_count: int
    user_progress: Optional[UrnProgressOut] = None

class UrnsListResponse(BaseModel):
    urns: list[UrnDetailOut]

# ============================================
# MOTIF SCHEMAS (Enhanced)
# ============================================

class LessonContentOut(BaseModel):
    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    video_url: Optional[str] = None

class MotifProgressOut(BaseModel):
    status: str
    discovered_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    xp_earned: int

class MotifDetailOut(BaseModel):
    id: UUID
    urn_id: UUID
    urn_slug: str
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    # 3D positioning
    pos_x: float
    pos_y: float
    pos_z: float
    bounding_radius: float
    cam_pos_x: Optional[float] = None
    cam_pos_y: Optional[float] = None
    cam_pos_z: Optional[float] = None
    cam_look_at_x: Optional[float] = None
    cam_look_at_y: Optional[float] = None
    cam_look_at_z: Optional[float] = None
    # Media
    thumbnail_url: Optional[str] = None
    silhouette_url: Optional[str] = None
    # Content
    lesson: Optional[LessonContentOut] = None
    quiz_question_count: int
    # Progress
    user_progress: Optional[MotifProgressOut] = None

# ============================================
# COLLECTION SCHEMAS (Enhanced)
# ============================================

class CollectionFilterParams(BaseModel):
    urn_slug: Optional[str] = None
    category: Optional[str] = None
    rarity: Optional[str] = None
    status: Optional[str] = None  # hidden, discovered, learned, mastered
    sort_by: str = "name"  # name, discovered_at, rarity
    sort_order: str = "asc"
    limit: int = Field(default=50, le=100)
    offset: int = 0

class CollectionStatsDetailOut(BaseModel):
    total: int
    discovered: int
    learned: int
    mastered: int

class CollectionByUrnOut(BaseModel):
    urn_slug: str
    urn_name: str
    stats: CollectionStatsDetailOut

class CollectionByCategoryOut(BaseModel):
    category: str
    stats: CollectionStatsDetailOut

class CollectionFullStatsResponse(BaseModel):
    overall: CollectionStatsDetailOut
    by_urn: list[CollectionByUrnOut]
    by_category: list[CollectionByCategoryOut]
    completion_percentage: float

# ============================================
# PROFILE SCHEMAS
# ============================================

class UserProfileResponse(BaseModel):
    user: UserOut
    stats: UserStatsOut
    streak: StreakResponse
    collection: CollectionStatsDetailOut
    badges: dict  # { earned_count, recent }
    quiz: dict  # { attempts, avg_score, perfect_count }

# ============================================
# ADMIN SCHEMAS
# ============================================

class AdminMotifCreateRequest(BaseModel):
    urn_id: UUID
    mesh_name: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    name_en: Optional[str] = None
    category: str
    rarity: str = "common"
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    bounding_radius: float = 0.1
    thumbnail_url: Optional[str] = None
    is_demo: bool = False

class AdminMotifUpdateRequest(BaseModel):
    mesh_name: Optional[str] = None
    name: Optional[str] = None
    name_en: Optional[str] = None
    category: Optional[str] = None
    rarity: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None
    bounding_radius: Optional[float] = None
    is_active: Optional[bool] = None

class AdminQuizQuestionCreateRequest(BaseModel):
    motif_id: UUID
    question_type: str  # multiple_choice, true_false, image_select, mesh_location
    question_text: str
    options: Optional[list[str]] = None  # Required for multiple_choice
    correct_answer: str
    target_mesh_name: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=5)
    explanation: Optional[str] = None

class AdminUserListParams(BaseModel):
    role: Optional[str] = None
    search: Optional[str] = None
    limit: int = Field(default=50, le=100)
    offset: int = 0

class AdminAnalyticsResponse(BaseModel):
    user_stats: dict
    learning_stats: dict
    content_stats: dict
    engagement: dict
```

---

### 1.2 API Endpoints Implementation Spec

#### 1.2.1 Quiz Endpoints

```python
# ============================================
# QUIZ ROUTES - Add to main.py
# ============================================

@app.get("/api/v1/motifs/{motif_id}/quiz", response_model=QuizQuestionsResponse)
def get_motif_quiz(
    motif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizQuestionsResponse:
    """
    Get quiz questions for a motif.
    User must have discovered the motif first.
    """
    # 1. Verify motif exists
    motif = db.get(Motif, motif_id)
    if not motif:
        raise HTTPException(404, "Motif not found")

    # 2. Check user has discovered motif
    progress = db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .where(UserProgress.motif_id == motif_id)
    ).scalar_one_or_none()

    if not progress or progress.status == UnlockStatus.hidden:
        raise HTTPException(403, "You must discover this motif first")

    # 3. Fetch questions
    questions = db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.motif_id == motif_id)
        .where(QuizQuestion.is_active.is_(True))
        .order_by(QuizQuestion.difficulty)
    ).scalars().all()

    # 4. Shuffle options for each question
    result = []
    for q in questions:
        options = q.options
        if options and q.question_type == QuestionType.multiple_choice:
            import random
            options = options.copy()
            random.shuffle(options)

        result.append(QuizQuestionOut(
            id=q.id,
            question_type=q.question_type.value,
            question_text=q.question_text,
            options=options,
            difficulty=q.difficulty,
            target_mesh_name=q.target_mesh_name,
        ))

    return QuizQuestionsResponse(
        motif_id=motif.id,
        motif_name=motif.name,
        questions=result,
        total_questions=len(result),
    )


@app.post("/api/v1/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    payload: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizSubmitResponse:
    """
    Submit quiz answers and receive results.
    Awards XP and updates progress status.
    """
    motif = db.get(Motif, payload.motif_id)
    if not motif:
        raise HTTPException(404, "Motif not found")

    # Fetch questions for validation
    question_ids = [a.question_id for a in payload.answers]
    questions = db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.id.in_(question_ids))
    ).scalars().all()
    question_map = {q.id: q for q in questions}

    # Grade answers
    results = []
    correct_count = 0
    for answer in payload.answers:
        q = question_map.get(answer.question_id)
        if not q:
            continue
        is_correct = answer.answer.strip().lower() == q.correct_answer.strip().lower()
        if is_correct:
            correct_count += 1
        results.append(QuizResultItem(
            question_id=q.id,
            correct=is_correct,
            user_answer=answer.answer,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
        ))

    total_questions = len(results)
    score = correct_count / total_questions if total_questions > 0 else 0.0
    passed = score >= 0.7

    # Calculate XP
    xp_earned = 10  # participation
    new_status = UnlockStatus.discovered

    progress = db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .where(UserProgress.motif_id == motif.id)
    ).scalar_one_or_none()

    if passed:
        xp_earned = 100  # learned
        new_status = UnlockStatus.learned
        if score == 1.0:
            xp_earned += 50  # mastery bonus
            new_status = UnlockStatus.mastered

    # Update progress
    now = datetime.now(timezone.utc)
    if progress:
        if new_status.value > progress.status.value:
            progress.status = new_status
            if new_status == UnlockStatus.learned:
                progress.learned_at = now
            elif new_status == UnlockStatus.mastered:
                progress.mastered_at = now
            progress.xp_earned += xp_earned
            current_user.total_xp += xp_earned

    # Create attempt record
    attempt = QuizAttempt(
        user_id=current_user.id,
        motif_id=motif.id,
        score=score,
        answers_json={"answers": [a.model_dump() for a in payload.answers]},
        time_taken_seconds=payload.time_taken_seconds,
    )
    db.add(attempt)
    db.commit()

    return QuizSubmitResponse(
        attempt_id=attempt.id,
        score=score,
        passed=passed,
        xp_earned=xp_earned,
        new_status=new_status.value,
        total_xp=current_user.total_xp,
        results=results,
        badges_earned=[],  # TODO: badge check
    )


@app.post("/api/v1/motifs/{motif_id}/complete-lesson")
def complete_lesson(
    motif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark lesson as viewed, unlock quiz."""
    progress = db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .where(UserProgress.motif_id == motif_id)
    ).scalar_one_or_none()

    if not progress:
        raise HTTPException(404, "Progress not found")

    xp_earned = 0
    if not progress.lesson_viewed_at:
        progress.lesson_viewed_at = datetime.now(timezone.utc)
        xp_earned = 10
        progress.xp_earned += xp_earned
        current_user.total_xp += xp_earned
        db.commit()

    return {
        "quiz_unlocked": True,
        "xp_earned": xp_earned,
    }
```

#### 1.2.2 Badge Endpoints

```python
# ============================================
# BADGE ROUTES
# ============================================

@app.get("/api/v1/badges", response_model=list[BadgeOut])
def list_badges(db: Session = Depends(get_db)):
    """List all badges (hide details for secret ones)."""
    badges = db.execute(select(Badge).order_by(Badge.category)).scalars().all()
    return [BadgeOut.model_validate(b) for b in badges]


@app.get("/api/v1/users/me/badges", response_model=UserBadgesResponse)
def get_my_badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's earned badges and progress toward unearned ones."""
    # Earned badges
    earned_rows = db.execute(
        select(UserBadge, Badge)
        .join(Badge)
        .where(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.earned_at.desc())
    ).all()

    earned = [
        EarnedBadgeOut(
            badge=BadgeOut.model_validate(row.Badge),
            earned_at=row.UserBadge.earned_at,
        )
        for row in earned_rows
    ]

    # In-progress badges (sample logic)
    earned_slugs = {e.badge.slug for e in earned}
    all_badges = db.execute(select(Badge)).scalars().all()

    in_progress = []
    for badge in all_badges:
        if badge.slug in earned_slugs:
            continue
        # Calculate progress based on badge criteria
        current, target = _calculate_badge_progress(db, current_user, badge)
        if target > 0:
            in_progress.append(BadgeProgressOut(
                badge=BadgeOut.model_validate(badge),
                current=current,
                target=target,
                progress_percent=min(100.0, current / target * 100),
            ))

    total_xp = sum(e.badge.xp_bonus for e in earned)

    return UserBadgesResponse(
        earned=earned,
        in_progress=in_progress[:10],  # Top 10 closest
        total_badge_xp=total_xp,
    )


def _calculate_badge_progress(db: Session, user: User, badge: Badge) -> tuple[int, int]:
    """Calculate current/target for badge progress."""
    # Example for discovery badges
    if badge.slug == "first_discovery":
        count = db.execute(
            select(func.count())
            .select_from(UserProgress)
            .where(UserProgress.user_id == user.id)
            .where(UserProgress.status != UnlockStatus.hidden)
        ).scalar()
        return (count, 1)

    if badge.slug.startswith("explorer_"):
        target = int(badge.slug.split("_")[1])
        count = db.execute(
            select(func.count())
            .select_from(UserProgress)
            .where(UserProgress.user_id == user.id)
            .where(UserProgress.status != UnlockStatus.hidden)
        ).scalar()
        return (count, target)

    # Urn completion badges
    if badge.slug.endswith("_complete"):
        urn_slug = badge.slug.replace("_complete", "").replace("_", "-")
        urn = db.execute(select(Urn).where(Urn.slug == urn_slug)).scalar_one_or_none()
        if urn:
            total = db.execute(
                select(func.count()).select_from(Motif).where(Motif.urn_id == urn.id)
            ).scalar()
            discovered = db.execute(
                select(func.count())
                .select_from(UserProgress)
                .join(Motif)
                .where(UserProgress.user_id == user.id)
                .where(Motif.urn_id == urn.id)
                .where(UserProgress.status != UnlockStatus.hidden)
            ).scalar()
            return (discovered, total)

    return (0, 0)


def check_and_award_badges(db: Session, user: User) -> list[Badge]:
    """Check all unearned badges and award if criteria met."""
    earned_ids = db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user.id)
    ).scalars().all()

    all_badges = db.execute(
        select(Badge).where(Badge.id.notin_(earned_ids))
    ).scalars().all()

    newly_earned = []
    for badge in all_badges:
        current, target = _calculate_badge_progress(db, user, badge)
        if target > 0 and current >= target:
            user_badge = UserBadge(
                user_id=user.id,
                badge_id=badge.id,
            )
            db.add(user_badge)
            user.total_xp += badge.xp_bonus
            newly_earned.append(badge)

    if newly_earned:
        db.commit()

    return newly_earned
```

#### 1.2.3 Leaderboard Endpoints

```python
# ============================================
# LEADERBOARD ROUTES
# ============================================

@app.get("/api/v1/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    period: str = "all_time",  # all_time, weekly, monthly
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get leaderboard rankings."""
    # For all_time, simply order by total_xp
    if period == "all_time":
        query = (
            select(User)
            .where(User.role != UserRole.banned)
            .order_by(User.total_xp.desc(), User.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        users = db.execute(query).scalars().all()
        total_users = db.execute(
            select(func.count()).select_from(User).where(User.role != UserRole.banned)
        ).scalar()
    else:
        # Weekly/monthly: aggregate from quiz attempts
        if period == "weekly":
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
        else:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)

        # Complex query for period XP - simplified for spec
        users = db.execute(
            select(User)
            .order_by(User.total_xp.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
        total_users = len(users)

    entries = []
    for i, user in enumerate(users):
        rank_info, _, _ = _compute_rank(user.total_xp)
        entries.append(LeaderboardEntry(
            rank=offset + i + 1,
            user_id=user.id,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            total_xp=user.total_xp,
            level=rank_info["level"],
            level_name=rank_info["name"],
        ))

    # Current user's rank
    current_user_entry = None
    if current_user:
        user_rank = db.execute(
            select(func.count())
            .select_from(User)
            .where(User.total_xp > current_user.total_xp)
        ).scalar() + 1

        rank_info, _, _ = _compute_rank(current_user.total_xp)
        current_user_entry = LeaderboardEntry(
            rank=user_rank,
            user_id=current_user.id,
            display_name=current_user.display_name,
            avatar_url=current_user.avatar_url,
            total_xp=current_user.total_xp,
            level=rank_info["level"],
            level_name=rank_info["name"],
        )

    return LeaderboardResponse(
        entries=entries,
        current_user=current_user_entry,
        total_users=total_users,
        period=period,
    )


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional auth - returns None if not authenticated."""
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None
```

#### 1.2.4 Streak Endpoints

```python
# ============================================
# STREAK ROUTES
# ============================================

@app.get("/api/v1/users/me/streak", response_model=StreakResponse)
def get_my_streak(
    current_user: User = Depends(get_current_user),
):
    """Get current user's streak information."""
    today = date.today()
    last_active = current_user.last_active_at.date() if current_user.last_active_at else None

    streak_at_risk = False
    if last_active and last_active < today and current_user.current_streak > 0:
        streak_at_risk = True

    # Days until streak badge
    days_until = None
    for threshold in [7, 30, 100]:
        if current_user.current_streak < threshold:
            days_until = threshold - current_user.current_streak
            break

    return StreakResponse(
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        last_active_date=last_active,
        streak_freezes_available=2,  # TODO: track in user model
        streak_at_risk=streak_at_risk,
        days_until_next_badge=days_until,
    )


def update_streak(db: Session, user: User):
    """Update user's streak on activity. Call from other endpoints."""
    today = date.today()
    last_active = user.last_active_at.date() if user.last_active_at else None

    if last_active == today:
        return  # Already active today

    if last_active == today - timedelta(days=1):
        user.current_streak += 1
    elif last_active is None or last_active < today - timedelta(days=1):
        user.current_streak = 1

    if user.current_streak > user.longest_streak:
        user.longest_streak = user.current_streak

    user.last_active_at = datetime.now(timezone.utc)
```

#### 1.2.5 Urn & Motif Endpoints

```python
# ============================================
# URN ROUTES
# ============================================

@app.get("/api/v1/urns", response_model=UrnsListResponse)
def list_urns(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """List all 9 urns with motif counts and user progress."""
    urns = db.execute(
        select(Urn).order_by(Urn.display_order)
    ).scalars().all()

    result = []
    for urn in urns:
        motif_count = db.execute(
            select(func.count())
            .select_from(Motif)
            .where(Motif.urn_id == urn.id)
            .where(Motif.is_active.is_(True))
        ).scalar()

        user_progress = None
        if current_user:
            discovered = db.execute(
                select(func.count())
                .select_from(UserProgress)
                .join(Motif)
                .where(Motif.urn_id == urn.id)
                .where(UserProgress.user_id == current_user.id)
                .where(UserProgress.status != UnlockStatus.hidden)
            ).scalar()
            learned = db.execute(
                select(func.count())
                .select_from(UserProgress)
                .join(Motif)
                .where(Motif.urn_id == urn.id)
                .where(UserProgress.user_id == current_user.id)
                .where(UserProgress.status.in_([UnlockStatus.learned, UnlockStatus.mastered]))
            ).scalar()
            mastered = db.execute(
                select(func.count())
                .select_from(UserProgress)
                .join(Motif)
                .where(Motif.urn_id == urn.id)
                .where(UserProgress.user_id == current_user.id)
                .where(UserProgress.status == UnlockStatus.mastered)
            ).scalar()

            user_progress = UrnProgressOut(
                discovered=discovered,
                learned=learned,
                mastered=mastered,
                total=motif_count,
                completion_percent=discovered / motif_count * 100 if motif_count else 0,
            )

        result.append(UrnDetailOut(
            id=urn.id,
            slug=urn.slug,
            name=urn.name,
            name_han=urn.name_han,
            represents=urn.represents,
            description=urn.description,
            model_url=urn.model_url,
            thumbnail_url=urn.thumbnail_url,
            display_order=urn.display_order,
            motif_count=motif_count,
            user_progress=user_progress,
        ))

    return UrnsListResponse(urns=result)


@app.get("/api/v1/urns/{slug}")
def get_urn_detail(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get single urn with motifs."""
    urn = db.execute(select(Urn).where(Urn.slug == slug)).scalar_one_or_none()
    if not urn:
        raise HTTPException(404, "Urn not found")

    # Return urn detail + motifs (reuse existing get_motifs_by_urn logic)
    # ... implementation similar to list_urns + motifs list


@app.get("/api/v1/motifs/{motif_id}", response_model=MotifDetailOut)
def get_motif_detail(
    motif_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get detailed motif info with lesson content."""
    motif = db.execute(
        select(Motif)
        .options(selectinload(Motif.lesson), selectinload(Motif.urn))
        .where(Motif.id == motif_id)
    ).scalar_one_or_none()

    if not motif:
        raise HTTPException(404, "Motif not found")

    # Get quiz question count
    quiz_count = db.execute(
        select(func.count())
        .select_from(QuizQuestion)
        .where(QuizQuestion.motif_id == motif_id)
        .where(QuizQuestion.is_active.is_(True))
    ).scalar()

    # Get user progress
    user_progress = None
    if current_user:
        progress = db.execute(
            select(UserProgress)
            .where(UserProgress.user_id == current_user.id)
            .where(UserProgress.motif_id == motif_id)
        ).scalar_one_or_none()

        if progress:
            user_progress = MotifProgressOut(
                status=progress.status.value,
                discovered_at=progress.discovered_at,
                learned_at=progress.learned_at,
                mastered_at=progress.mastered_at,
                xp_earned=progress.xp_earned,
            )

    # Hide full lesson if not discovered
    lesson = None
    if motif.lesson:
        if not user_progress or user_progress.status == "hidden":
            lesson = LessonContentOut(description="Discover this motif to unlock!")
        else:
            lesson = LessonContentOut(
                intro_text=motif.lesson.intro_text,
                description=motif.lesson.description,
                historical_context=motif.lesson.historical_context,
                symbolism=motif.lesson.symbolism,
                fun_fact=motif.lesson.fun_fact,
                audio_narration_url=motif.lesson.audio_narration_url,
                video_url=motif.lesson.video_url,
            )

    return MotifDetailOut(
        id=motif.id,
        urn_id=motif.urn_id,
        urn_slug=motif.urn.slug,
        mesh_name=motif.mesh_name,
        name=motif.name,
        name_en=motif.name_en,
        category=motif.category.value,
        rarity=motif.rarity.value,
        pos_x=motif.pos_x,
        pos_y=motif.pos_y,
        pos_z=motif.pos_z,
        bounding_radius=motif.bounding_radius,
        cam_pos_x=motif.cam_pos_x,
        cam_pos_y=motif.cam_pos_y,
        cam_pos_z=motif.cam_pos_z,
        cam_look_at_x=motif.cam_look_at_x,
        cam_look_at_y=motif.cam_look_at_y,
        cam_look_at_z=motif.cam_look_at_z,
        thumbnail_url=motif.thumbnail_url,
        silhouette_url=motif.silhouette_url if not user_progress else None,
        lesson=lesson,
        quiz_question_count=quiz_count,
        user_progress=user_progress,
    )
```

#### 1.2.6 Collection Endpoints

```python
# ============================================
# COLLECTION ROUTES (Enhanced)
# ============================================

@app.get("/api/v1/users/me/collection/stats", response_model=CollectionFullStatsResponse)
def get_collection_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed collection statistics."""
    # Overall stats
    total = db.execute(
        select(func.count()).select_from(Motif).where(Motif.is_active.is_(True))
    ).scalar()

    discovered = db.execute(
        select(func.count())
        .select_from(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .where(UserProgress.status != UnlockStatus.hidden)
    ).scalar()

    learned = db.execute(
        select(func.count())
        .select_from(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .where(UserProgress.status.in_([UnlockStatus.learned, UnlockStatus.mastered]))
    ).scalar()

    mastered = db.execute(
        select(func.count())
        .select_from(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .where(UserProgress.status == UnlockStatus.mastered)
    ).scalar()

    # By urn
    urns = db.execute(select(Urn).order_by(Urn.display_order)).scalars().all()
    by_urn = []
    for urn in urns:
        urn_total = db.execute(
            select(func.count()).select_from(Motif)
            .where(Motif.urn_id == urn.id).where(Motif.is_active.is_(True))
        ).scalar()
        urn_discovered = db.execute(
            select(func.count()).select_from(UserProgress).join(Motif)
            .where(Motif.urn_id == urn.id)
            .where(UserProgress.user_id == current_user.id)
            .where(UserProgress.status != UnlockStatus.hidden)
        ).scalar()
        # ... similar for learned, mastered
        by_urn.append(CollectionByUrnOut(
            urn_slug=urn.slug,
            urn_name=urn.name,
            stats=CollectionStatsDetailOut(
                total=urn_total,
                discovered=urn_discovered,
                learned=0,  # calculate
                mastered=0,  # calculate
            ),
        ))

    # By category (similar logic)
    by_category = []
    for cat in MotifCategory:
        # ... count per category
        pass

    return CollectionFullStatsResponse(
        overall=CollectionStatsDetailOut(
            total=total,
            discovered=discovered,
            learned=learned,
            mastered=mastered,
        ),
        by_urn=by_urn,
        by_category=by_category,
        completion_percentage=discovered / total * 100 if total else 0,
    )
```

#### 1.2.7 Admin Endpoints

```python
# ============================================
# ADMIN ROUTES
# ============================================

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role."""
    if current_user.role not in (UserRole.admin, UserRole.super_admin):
        raise HTTPException(403, "Admin access required")
    return current_user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require super_admin role."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(403, "Super admin access required")
    return current_user


# --- Motif Management ---

@app.get("/api/v1/admin/motifs")
def admin_list_motifs(
    urn_id: Optional[UUID] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all motifs for admin (including inactive)."""
    query = select(Motif)
    if urn_id:
        query = query.where(Motif.urn_id == urn_id)
    if category:
        query = query.where(Motif.category == MotifCategory(category))
    if is_active is not None:
        query = query.where(Motif.is_active == is_active)

    motifs = db.execute(
        query.order_by(Motif.display_order.nulls_last())
        .limit(limit).offset(offset)
    ).scalars().all()

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar()

    return {"items": motifs, "total": total}


@app.post("/api/v1/admin/motifs")
def admin_create_motif(
    payload: AdminMotifCreateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create new motif."""
    # Validate urn exists
    urn = db.get(Urn, payload.urn_id)
    if not urn:
        raise HTTPException(404, "Urn not found")

    # Check mesh_name unique
    existing = db.execute(
        select(Motif).where(Motif.mesh_name == payload.mesh_name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "mesh_name already exists")

    motif = Motif(
        urn_id=payload.urn_id,
        mesh_name=payload.mesh_name,
        name=payload.name,
        name_en=payload.name_en,
        category=MotifCategory(payload.category),
        rarity=MotifRarity(payload.rarity),
        pos_x=payload.pos_x,
        pos_y=payload.pos_y,
        pos_z=payload.pos_z,
        bounding_radius=payload.bounding_radius,
        thumbnail_url=payload.thumbnail_url,
        is_demo=payload.is_demo,
    )
    db.add(motif)
    db.commit()
    db.refresh(motif)

    return motif


@app.put("/api/v1/admin/motifs/{motif_id}")
def admin_update_motif(
    motif_id: UUID,
    payload: AdminMotifUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update existing motif."""
    motif = db.get(Motif, motif_id)
    if not motif:
        raise HTTPException(404, "Motif not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "category" and value:
            value = MotifCategory(value)
        if key == "rarity" and value:
            value = MotifRarity(value)
        setattr(motif, key, value)

    db.commit()
    return motif


@app.delete("/api/v1/admin/motifs/{motif_id}")
def admin_delete_motif(
    motif_id: UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Soft delete motif."""
    motif = db.get(Motif, motif_id)
    if not motif:
        raise HTTPException(404, "Motif not found")

    motif.is_active = False
    db.commit()
    return {"deleted": True}


# --- Quiz Question Management ---

@app.post("/api/v1/admin/quiz-questions")
def admin_create_question(
    payload: AdminQuizQuestionCreateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create quiz question."""
    motif = db.get(Motif, payload.motif_id)
    if not motif:
        raise HTTPException(404, "Motif not found")

    # Validate options for multiple_choice
    if payload.question_type == "multiple_choice":
        if not payload.options or len(payload.options) < 2:
            raise HTTPException(400, "multiple_choice requires at least 2 options")
        if payload.correct_answer not in payload.options:
            raise HTTPException(400, "correct_answer must be in options")

    question = QuizQuestion(
        motif_id=payload.motif_id,
        question_type=QuestionType(payload.question_type),
        question_text=payload.question_text,
        options=payload.options,
        correct_answer=payload.correct_answer,
        target_mesh_name=payload.target_mesh_name,
        difficulty=payload.difficulty,
        explanation=payload.explanation,
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    return question


# --- User Management (Super Admin) ---

@app.get("/api/v1/admin/users")
def admin_list_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """List all users."""
    query = select(User)
    if role:
        query = query.where(User.role == UserRole(role))
    if search:
        query = query.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.display_name.ilike(f"%{search}%"),
            )
        )

    users = db.execute(
        query.order_by(User.created_at.desc())
        .limit(limit).offset(offset)
    ).scalars().all()

    return {"items": users, "total": len(users)}


@app.patch("/api/v1/admin/users/{user_id}/role")
def admin_change_role(
    user_id: UUID,
    new_role: str,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Change user role."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if user.id == admin.id:
        raise HTTPException(400, "Cannot change own role")

    user.role = UserRole(new_role)
    db.commit()
    return {"updated": True, "new_role": new_role}


# --- Analytics ---

@app.get("/api/v1/admin/analytics", response_model=AdminAnalyticsResponse)
def admin_analytics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Dashboard analytics."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # User stats
    total_users = db.execute(select(func.count()).select_from(User)).scalar()
    active_today = db.execute(
        select(func.count()).select_from(User)
        .where(func.date(User.last_active_at) == today)
    ).scalar()
    active_week = db.execute(
        select(func.count()).select_from(User)
        .where(User.last_active_at >= week_ago)
    ).scalar()
    new_month = db.execute(
        select(func.count()).select_from(User)
        .where(User.created_at >= month_ago)
    ).scalar()

    # Content stats
    motifs_total = db.execute(
        select(func.count()).select_from(Motif).where(Motif.is_active.is_(True))
    ).scalar()
    questions_total = db.execute(
        select(func.count()).select_from(QuizQuestion).where(QuizQuestion.is_active.is_(True))
    ).scalar()

    return AdminAnalyticsResponse(
        user_stats={
            "total": total_users,
            "active_today": active_today,
            "active_week": active_week,
            "new_this_month": new_month,
        },
        learning_stats={
            "discoveries_today": 0,  # TODO
            "quizzes_today": 0,  # TODO
            "avg_score": 0.0,  # TODO
        },
        content_stats={
            "motifs_total": motifs_total,
            "motifs_with_lesson": 0,  # TODO
            "questions_total": questions_total,
        },
        engagement={
            "avg_session_time": 0,
            "retention_7d": 0.0,
        },
    )
```

---

## 2. FRONTEND SPECIFICATIONS

### 2.1 New API Functions (lib/api.js additions)

```javascript
// ============================================
// QUIZ API
// ============================================

export function getMotifQuiz(motifId, { token }) {
  return apiRequest(`/api/v1/motifs/${motifId}/quiz`, { token });
}

export function submitQuiz({ motifId, answers, timeTakenSeconds }, { token }) {
  return apiRequest(`/api/v1/quiz/submit`, {
    method: "POST",
    token,
    body: {
      motif_id: motifId,
      answers,
      time_taken_seconds: timeTakenSeconds,
    },
  });
}

export function completeLesson(motifId, { token }) {
  return apiRequest(`/api/v1/motifs/${motifId}/complete-lesson`, {
    method: "POST",
    token,
  });
}

// ============================================
// BADGE API
// ============================================

export function getAllBadges() {
  return apiRequest(`/api/v1/badges`);
}

export function getMyBadges({ token }) {
  return apiRequest(`/api/v1/users/me/badges`, { token });
}

// ============================================
// LEADERBOARD API
// ============================================

export function getLeaderboard({ period = "all_time", limit = 50, offset = 0 }, { token } = {}) {
  const params = new URLSearchParams({ period, limit, offset });
  return apiRequest(`/api/v1/leaderboard?${params}`, { token });
}

// ============================================
// STREAK API
// ============================================

export function getMyStreak({ token }) {
  return apiRequest(`/api/v1/users/me/streak`, { token });
}

// ============================================
// URN API
// ============================================

export function getAllUrns({ token } = {}) {
  return apiRequest(`/api/v1/urns`, { token });
}

export function getUrnDetail(slug, { token } = {}) {
  return apiRequest(`/api/v1/urns/${slug}`, { token });
}

// ============================================
// MOTIF API
// ============================================

export function getMotifDetail(motifId, { token } = {}) {
  return apiRequest(`/api/v1/motifs/${motifId}`, { token });
}

// ============================================
// COLLECTION API (Enhanced)
// ============================================

export function getCollectionStats({ token }) {
  return apiRequest(`/api/v1/users/me/collection/stats`, { token });
}

// ============================================
// PROFILE API
// ============================================

export function getMyProfile({ token }) {
  return apiRequest(`/api/v1/users/me/profile`, { token });
}

export function updateMyProfile(data, { token }) {
  return apiRequest(`/api/v1/users/me/profile`, {
    method: "PATCH",
    token,
    body: data,
  });
}
```

### 2.2 New Zustand Stores

#### 2.2.1 Quiz Store (stores/quizStore.js)

```javascript
"use client";
import { create } from "zustand";
import { getMotifQuiz, submitQuiz } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export const useQuizStore = create((set, get) => ({
  // State
  motifId: null,
  questions: [],
  currentIndex: 0,
  answers: {},  // { [questionId]: answer }
  isLoading: false,
  isSubmitting: false,
  result: null,
  error: null,
  startTime: null,

  // Actions
  loadQuiz: async (motifId) => {
    const token = useAuthStore.getState().accessToken;
    set({ isLoading: true, error: null, result: null });

    try {
      const data = await getMotifQuiz(motifId, { token });
      set({
        motifId,
        questions: data.questions,
        currentIndex: 0,
        answers: {},
        isLoading: false,
        startTime: Date.now(),
      });
    } catch (err) {
      set({ isLoading: false, error: err.message });
    }
  },

  setAnswer: (questionId, answer) => {
    set((state) => ({
      answers: { ...state.answers, [questionId]: answer },
    }));
  },

  nextQuestion: () => {
    set((state) => ({
      currentIndex: Math.min(state.currentIndex + 1, state.questions.length - 1),
    }));
  },

  prevQuestion: () => {
    set((state) => ({
      currentIndex: Math.max(state.currentIndex - 1, 0),
    }));
  },

  submitQuiz: async () => {
    const { motifId, questions, answers, startTime } = get();
    const token = useAuthStore.getState().accessToken;

    const answerList = questions.map((q) => ({
      question_id: q.id,
      answer: answers[q.id] || "",
    }));

    const timeTaken = Math.floor((Date.now() - startTime) / 1000);

    set({ isSubmitting: true, error: null });

    try {
      const result = await submitQuiz(
        { motifId, answers: answerList, timeTakenSeconds: timeTaken },
        { token }
      );
      set({ result, isSubmitting: false });
      return result;
    } catch (err) {
      set({ isSubmitting: false, error: err.message });
      throw err;
    }
  },

  reset: () => {
    set({
      motifId: null,
      questions: [],
      currentIndex: 0,
      answers: {},
      result: null,
      error: null,
      startTime: null,
    });
  },
}));
```

#### 2.2.2 Badge Store (stores/badgeStore.js)

```javascript
"use client";
import { create } from "zustand";
import { getAllBadges, getMyBadges } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export const useBadgeStore = create((set, get) => ({
  allBadges: [],
  earnedBadges: [],
  inProgressBadges: [],
  totalBadgeXP: 0,
  isLoading: false,
  newlyEarned: [],  // For notification popup

  fetchAllBadges: async () => {
    try {
      const badges = await getAllBadges();
      set({ allBadges: badges });
    } catch (err) {
      console.error("Failed to fetch badges:", err);
    }
  },

  fetchMyBadges: async () => {
    const token = useAuthStore.getState().accessToken;
    if (!token) return;

    set({ isLoading: true });
    try {
      const data = await getMyBadges({ token });
      set({
        earnedBadges: data.earned,
        inProgressBadges: data.in_progress,
        totalBadgeXP: data.total_badge_xp,
        isLoading: false,
      });
    } catch (err) {
      set({ isLoading: false });
    }
  },

  showNewBadge: (badge) => {
    set((state) => ({
      newlyEarned: [...state.newlyEarned, badge],
    }));
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      set((state) => ({
        newlyEarned: state.newlyEarned.filter((b) => b.id !== badge.id),
      }));
    }, 5000);
  },

  dismissBadge: (badgeId) => {
    set((state) => ({
      newlyEarned: state.newlyEarned.filter((b) => b.id !== badgeId),
    }));
  },
}));
```

#### 2.2.3 Leaderboard Store (stores/leaderboardStore.js)

```javascript
"use client";
import { create } from "zustand";
import { getLeaderboard } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export const useLeaderboardStore = create((set) => ({
  entries: [],
  currentUser: null,
  totalUsers: 0,
  period: "all_time",
  isLoading: false,

  fetchLeaderboard: async (period = "all_time") => {
    const token = useAuthStore.getState().accessToken;
    set({ isLoading: true, period });

    try {
      const data = await getLeaderboard({ period }, { token });
      set({
        entries: data.entries,
        currentUser: data.current_user,
        totalUsers: data.total_users,
        isLoading: false,
      });
    } catch (err) {
      set({ isLoading: false });
    }
  },

  setPeriod: (period) => {
    set({ period });
  },
}));
```

### 2.3 New Page Components

#### 2.3.1 Explore Page (app/explore/page.jsx)

```jsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getAllUrns } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function ExplorePage() {
  const token = useAuthStore((s) => s.accessToken);
  const [urns, setUrns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAllUrns({ token })
      .then((data) => setUrns(data.urns))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <h1 className="mb-8 text-3xl font-bold text-white">Khám Phá Cửu Đỉnh</h1>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {urns.map((urn) => (
          <Link key={urn.id} href={`/urns/${urn.slug}`}>
            <div className="group relative overflow-hidden rounded-xl bg-gray-800 p-6 transition hover:bg-gray-700">
              {/* Thumbnail */}
              <div className="mb-4 aspect-square overflow-hidden rounded-lg bg-gray-700">
                {urn.thumbnail_url ? (
                  <img src={urn.thumbnail_url} alt={urn.name} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-4xl">🏺</div>
                )}
              </div>

              {/* Info */}
              <h2 className="text-xl font-bold text-white">{urn.name}</h2>
              <p className="text-sm text-gray-400">{urn.name_han}</p>
              <p className="mt-2 text-sm text-gray-300">{urn.represents}</p>

              {/* Progress */}
              {urn.user_progress && (
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-gray-400">
                    <span>{urn.user_progress.discovered}/{urn.motif_count} discovered</span>
                    <span>{Math.round(urn.user_progress.completion_percent)}%</span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-600">
                    <div
                      className="h-full bg-amber-500 transition-all"
                      style={{ width: `${urn.user_progress.completion_percent}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

#### 2.3.2 Collection Page (app/collection/page.jsx)

```jsx
"use client";
import { useEffect, useState } from "react";
import { getMyCollection, getCollectionStats } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function CollectionPage() {
  const token = useAuthStore((s) => s.accessToken);
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState({ category: null, status: null });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    Promise.all([
      getMyCollection({ token }),
      getCollectionStats({ token }),
    ])
      .then(([collection, statsData]) => {
        setItems(collection.items);
        setStats(statsData);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const filteredItems = items.filter((item) => {
    if (filter.category && item.category !== filter.category) return false;
    if (filter.status && item.status !== filter.status) return false;
    return true;
  });

  if (loading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <h1 className="mb-4 text-3xl font-bold text-white">Bộ Sưu Tập</h1>

      {/* Stats */}
      {stats && (
        <div className="mb-6 grid grid-cols-4 gap-4">
          <StatCard label="Total" value={stats.overall.total} />
          <StatCard label="Discovered" value={stats.overall.discovered} color="text-blue-400" />
          <StatCard label="Learned" value={stats.overall.learned} color="text-green-400" />
          <StatCard label="Mastered" value={stats.overall.mastered} color="text-amber-400" />
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <select
          className="rounded bg-gray-800 px-4 py-2 text-white"
          value={filter.status || ""}
          onChange={(e) => setFilter({ ...filter, status: e.target.value || null })}
        >
          <option value="">All Status</option>
          <option value="hidden">Hidden</option>
          <option value="discovered">Discovered</option>
          <option value="learned">Learned</option>
          <option value="mastered">Mastered</option>
        </select>

        <select
          className="rounded bg-gray-800 px-4 py-2 text-white"
          value={filter.category || ""}
          onChange={(e) => setFilter({ ...filter, category: e.target.value || null })}
        >
          <option value="">All Categories</option>
          <option value="linh_thu">Linh Thú</option>
          <option value="dong_vat">Động Vật</option>
          <option value="thao_moc">Thảo Mộc</option>
          <option value="dia_ly">Địa Lý</option>
          <option value="nong_nghiep">Nông Nghiệp</option>
          <option value="vo_bi">Võ Bị</option>
          <option value="giao_thuong">Giao Thương</option>
          <option value="thien_van">Thiên Văn</option>
          <option value="kien_truc">Kiến Trúc</option>
        </select>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {filteredItems.map((item) => (
          <MotifCard key={item.motif_id} item={item} />
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, color = "text-white" }) {
  return (
    <div className="rounded-lg bg-gray-800 p-4 text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}

function MotifCard({ item }) {
  const isHidden = item.status === "hidden";

  return (
    <div className={`relative aspect-square overflow-hidden rounded-lg ${isHidden ? "grayscale" : ""}`}>
      <img
        src={isHidden ? item.silhouette_url : item.thumbnail_url}
        alt={isHidden ? "???" : item.name}
        className="h-full w-full object-cover"
      />
      {!isHidden && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 p-2">
          <p className="truncate text-sm font-medium text-white">{item.name}</p>
          <p className="text-xs text-gray-300">{item.status}</p>
        </div>
      )}
      {/* Mastery indicator */}
      {item.status === "mastered" && (
        <div className="absolute right-2 top-2 text-2xl">⭐</div>
      )}
    </div>
  );
}
```

#### 2.3.3 Quiz Page (app/motif/[motifId]/quiz/page.jsx)

```jsx
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuizStore } from "@/stores/quizStore";
import { useAuthStore } from "@/stores/authStore";

export default function QuizPage({ params }) {
  const router = useRouter();
  const { motifId } = params;
  const token = useAuthStore((s) => s.accessToken);

  const {
    questions,
    currentIndex,
    answers,
    isLoading,
    isSubmitting,
    result,
    error,
    loadQuiz,
    setAnswer,
    nextQuestion,
    prevQuestion,
    submitQuiz,
    reset,
  } = useQuizStore();

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    loadQuiz(motifId);
    return () => reset();
  }, [motifId, token]);

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Loading quiz...</div>;
  }

  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center">
        <p className="text-red-500">{error}</p>
        <button onClick={() => router.back()} className="mt-4 text-blue-400">Go back</button>
      </div>
    );
  }

  // Show results
  if (result) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-900 p-8 text-white">
        <h1 className="mb-4 text-3xl font-bold">
          {result.passed ? "🎉 Congratulations!" : "Keep Learning!"}
        </h1>
        <p className="text-xl">Score: {Math.round(result.score * 100)}%</p>
        <p className="text-lg text-amber-400">+{result.xp_earned} XP</p>
        <p className="text-sm text-gray-400">New status: {result.new_status}</p>

        <div className="mt-8 space-y-4">
          {result.results.map((r, i) => (
            <div key={r.question_id} className={`rounded p-4 ${r.correct ? "bg-green-900/50" : "bg-red-900/50"}`}>
              <p className="font-medium">Q{i + 1}: {r.correct ? "✓" : "✗"}</p>
              <p className="text-sm">Your answer: {r.user_answer}</p>
              {!r.correct && <p className="text-sm text-green-400">Correct: {r.correct_answer}</p>}
              {r.explanation && <p className="mt-2 text-xs text-gray-400">{r.explanation}</p>}
            </div>
          ))}
        </div>

        <button
          onClick={() => router.push(`/motif/${motifId}`)}
          className="mt-8 rounded-lg bg-amber-600 px-6 py-3 font-bold"
        >
          Continue
        </button>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;
  const allAnswered = questions.every((q) => answers[q.id]);

  return (
    <div className="flex min-h-screen flex-col bg-gray-900 p-8 text-white">
      {/* Progress */}
      <div className="mb-8">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Question {currentIndex + 1} of {totalQuestions}</span>
          <span>{Object.keys(answers).length}/{totalQuestions} answered</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-700">
          <div
            className="h-full bg-amber-500 transition-all"
            style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <div className="flex-1">
        <h2 className="mb-6 text-xl font-bold">{currentQuestion.question_text}</h2>

        <div className="space-y-3">
          {currentQuestion.options?.map((option, i) => (
            <button
              key={i}
              onClick={() => setAnswer(currentQuestion.id, option)}
              className={`w-full rounded-lg p-4 text-left transition ${
                answers[currentQuestion.id] === option
                  ? "bg-amber-600"
                  : "bg-gray-800 hover:bg-gray-700"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="mt-8 flex justify-between">
        <button
          onClick={prevQuestion}
          disabled={currentIndex === 0}
          className="rounded bg-gray-700 px-4 py-2 disabled:opacity-50"
        >
          Previous
        </button>

        {currentIndex < totalQuestions - 1 ? (
          <button
            onClick={nextQuestion}
            className="rounded bg-gray-700 px-4 py-2"
          >
            Next
          </button>
        ) : (
          <button
            onClick={submitQuiz}
            disabled={!allAnswered || isSubmitting}
            className="rounded bg-amber-600 px-6 py-2 font-bold disabled:opacity-50"
          >
            {isSubmitting ? "Submitting..." : "Submit Quiz"}
          </button>
        )}
      </div>
    </div>
  );
}
```

#### 2.3.4 Leaderboard Page (app/leaderboard/page.jsx)

```jsx
"use client";
import { useEffect } from "react";
import { useLeaderboardStore } from "@/stores/leaderboardStore";
import { useAuthStore } from "@/stores/authStore";

export default function LeaderboardPage() {
  const { entries, currentUser, totalUsers, period, isLoading, fetchLeaderboard, setPeriod } =
    useLeaderboardStore();
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    fetchLeaderboard(period);
  }, [period]);

  const periods = [
    { value: "all_time", label: "All Time" },
    { value: "weekly", label: "This Week" },
    { value: "monthly", label: "This Month" },
  ];

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <h1 className="mb-6 text-3xl font-bold text-white">Bảng Xếp Hạng</h1>

      {/* Period Selector */}
      <div className="mb-6 flex gap-2">
        {periods.map((p) => (
          <button
            key={p.value}
            onClick={() => setPeriod(p.value)}
            className={`rounded-lg px-4 py-2 ${
              period === p.value ? "bg-amber-600 text-white" : "bg-gray-800 text-gray-300"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Current User Rank */}
      {currentUser && (
        <div className="mb-6 rounded-lg bg-amber-900/30 p-4">
          <p className="text-sm text-gray-400">Your Rank</p>
          <p className="text-2xl font-bold text-amber-400">#{currentUser.rank}</p>
          <p className="text-sm text-gray-300">{currentUser.total_xp} XP • {currentUser.level_name}</p>
        </div>
      )}

      {/* Leaderboard Table */}
      {isLoading ? (
        <p className="text-center text-gray-400">Loading...</p>
      ) : (
        <div className="overflow-hidden rounded-lg bg-gray-800">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm text-gray-300">Rank</th>
                <th className="px-4 py-3 text-left text-sm text-gray-300">Player</th>
                <th className="px-4 py-3 text-right text-sm text-gray-300">Level</th>
                <th className="px-4 py-3 text-right text-sm text-gray-300">XP</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.user_id}
                  className={`border-t border-gray-700 ${
                    entry.user_id === user?.id ? "bg-amber-900/20" : ""
                  }`}
                >
                  <td className="px-4 py-3">
                    {entry.rank <= 3 ? (
                      <span className="text-xl">{["🥇", "🥈", "🥉"][entry.rank - 1]}</span>
                    ) : (
                      <span className="text-gray-400">#{entry.rank}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 overflow-hidden rounded-full bg-gray-600">
                        {entry.avatar_url ? (
                          <img src={entry.avatar_url} alt="" className="h-full w-full object-cover" />
                        ) : (
                          <span className="flex h-full items-center justify-center text-sm">
                            {entry.display_name[0]}
                          </span>
                        )}
                      </div>
                      <span className="font-medium text-white">{entry.display_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-300">{entry.level_name}</td>
                  <td className="px-4 py-3 text-right font-mono text-amber-400">
                    {entry.total_xp.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-4 text-center text-sm text-gray-500">{totalUsers} total players</p>
    </div>
  );
}
```

#### 2.3.5 Profile Page (app/profile/page.jsx)

```jsx
"use client";
import { useEffect, useState } from "react";
import { getMyProfile, getMyStreak, getMyBadges } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function ProfilePage() {
  const token = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const stats = useAuthStore((s) => s.stats);
  const [streak, setStreak] = useState(null);
  const [badges, setBadges] = useState({ earned: [], in_progress: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    Promise.all([
      getMyStreak({ token }),
      getMyBadges({ token }),
    ])
      .then(([streakData, badgesData]) => {
        setStreak(streakData);
        setBadges(badgesData);
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      {/* Header */}
      <div className="mb-8 flex items-center gap-6">
        <div className="h-24 w-24 overflow-hidden rounded-full bg-gray-700">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-3xl text-white">
              {user?.display_name?.[0] || "?"}
            </div>
          )}
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">{user?.display_name}</h1>
          <p className="text-gray-400">{user?.email}</p>
          <p className="mt-1 text-amber-400">{stats?.rank?.name} • Level {stats?.rank?.level}</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard icon="⚡" label="Total XP" value={stats?.total_xp || 0} />
        <StatCard icon="🔥" label="Streak" value={`${streak?.current_streak || 0} days`} />
        <StatCard icon="🏅" label="Badges" value={badges.earned.length} />
        <StatCard icon="📚" label="Mastered" value={0} />
      </div>

      {/* Streak Warning */}
      {streak?.streak_at_risk && (
        <div className="mb-6 rounded-lg bg-red-900/30 p-4">
          <p className="font-bold text-red-400">⚠️ Streak at risk!</p>
          <p className="text-sm text-gray-300">Complete any lesson today to keep your streak.</p>
        </div>
      )}

      {/* XP Progress */}
      <div className="mb-8">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Progress to {stats?.next_rank?.name || "Max Rank"}</span>
          <span className="text-amber-400">{stats?.xp_to_next_rank || 0} XP to go</span>
        </div>
        <div className="mt-2 h-4 overflow-hidden rounded-full bg-gray-700">
          <div
            className="h-full bg-gradient-to-r from-amber-500 to-amber-400"
            style={{
              width: stats?.next_rank
                ? `${((stats.total_xp - stats.rank.xp) / (stats.next_rank.xp - stats.rank.xp)) * 100}%`
                : "100%",
            }}
          />
        </div>
      </div>

      {/* Badges */}
      <div className="mb-8">
        <h2 className="mb-4 text-xl font-bold text-white">Earned Badges</h2>
        <div className="grid grid-cols-4 gap-4 md:grid-cols-6">
          {badges.earned.map((item) => (
            <div key={item.badge.id} className="text-center">
              <img src={item.badge.icon_url} alt={item.badge.name} className="mx-auto h-16 w-16" />
              <p className="mt-1 text-xs text-gray-300">{item.badge.name}</p>
            </div>
          ))}
        </div>
      </div>

      {/* In Progress */}
      <div>
        <h2 className="mb-4 text-xl font-bold text-white">In Progress</h2>
        <div className="space-y-3">
          {badges.in_progress.slice(0, 5).map((item) => (
            <div key={item.badge.id} className="rounded-lg bg-gray-800 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <img src={item.badge.icon_url} alt="" className="h-10 w-10 opacity-50" />
                  <div>
                    <p className="font-medium text-white">{item.badge.name}</p>
                    <p className="text-xs text-gray-400">{item.badge.description}</p>
                  </div>
                </div>
                <span className="text-sm text-amber-400">
                  {item.current}/{item.target}
                </span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-700">
                <div
                  className="h-full bg-amber-600"
                  style={{ width: `${item.progress_percent}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="rounded-lg bg-gray-800 p-4 text-center">
      <div className="text-2xl">{icon}</div>
      <div className="mt-1 text-xl font-bold text-white">{value}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  );
}
```

---

## 3. INFRASTRUCTURE SPECIFICATIONS

### 3.1 Alembic Migration Setup

```python
# alembic.ini (root of project)
[alembic]
script_location = migrations
sqlalchemy.url = postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki

[loggers]
keys = root,sqlalchemy,alembic

[logger_root]
level = WARN
handlers =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Import all models to ensure they're registered
from models import Base

config = context.config

# Override sqlalchemy.url from environment
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3.2 Testing Setup

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base
from main import app, get_db

# In-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Test client with overridden database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from models import User
    from security import hash_password

    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        display_name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get auth headers for test user."""
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

```python
# tests/test_auth.py
import pytest


def test_register_success(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "display_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@example.com"


def test_register_duplicate_email(client, test_user):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "display_name": "Duplicate",
    })
    assert response.status_code == 409


def test_login_success(client, test_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client, test_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_me_authenticated(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "test@example.com"


def test_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
```

```python
# tests/test_quiz.py
import pytest
from uuid import uuid4


@pytest.fixture
def test_motif(db_session, test_urn):
    from models import Motif, MotifCategory, MotifRarity

    motif = Motif(
        urn_id=test_urn.id,
        mesh_name="test_motif_01",
        name="Test Motif",
        category=MotifCategory.linh_thu,
        rarity=MotifRarity.common,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=0.1,
    )
    db_session.add(motif)
    db_session.commit()
    db_session.refresh(motif)
    return motif


@pytest.fixture
def test_urn(db_session):
    from models import Urn

    urn = Urn(
        slug="test-urn",
        name="Test Urn",
        model_url="/models/test.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.commit()
    db_session.refresh(urn)
    return urn


def test_get_quiz_not_discovered(client, auth_headers, test_motif):
    response = client.get(f"/api/v1/motifs/{test_motif.id}/quiz", headers=auth_headers)
    assert response.status_code == 403


def test_submit_quiz(client, auth_headers, test_motif, db_session):
    # First discover the motif
    from models import UserProgress, UnlockStatus

    # ... setup discovered progress
    # ... submit quiz
    # ... assert score, XP, status change
    pass
```

### 3.3 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ruff black mypy
          pip install -r requirements.txt

      - name: Run ruff
        run: ruff check .

      - name: Run black
        run: black --check .

      - name: Run mypy
        run: mypy main.py models.py --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: luuniensuki_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test
        run: pytest --cov=. --cov-report=xml --cov-fail-under=60

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

  build-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Build
        run: npm run build
```

---

## 4. SEQUENCE DIAGRAMS

### 4.1 Quiz Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend
    participant DB as Database

    U->>FE: Click "Start Quiz"
    FE->>BE: GET /api/v1/motifs/{id}/quiz
    BE->>DB: Check UserProgress.status >= discovered
    alt Not discovered
        BE-->>FE: 403 Forbidden
        FE-->>U: "Discover motif first"
    else Discovered
        BE->>DB: SELECT quiz_questions
        BE-->>FE: questions (shuffled options)
        FE-->>U: Show question 1

        loop Each Question
            U->>FE: Select answer
            FE->>FE: Store in state
            U->>FE: Click Next
        end

        U->>FE: Click Submit
        FE->>BE: POST /api/v1/quiz/submit
        BE->>DB: Validate answers
        BE->>DB: Calculate score
        BE->>DB: Update UserProgress (status, xp)
        BE->>DB: Create QuizAttempt
        BE->>DB: Check badge criteria
        BE-->>FE: { score, xp_earned, new_status, badges }
        FE-->>U: Show results + celebration
    end
```

### 4.2 Badge Award Flow

```mermaid
sequenceDiagram
    participant BE as Backend
    participant DB as Database

    Note over BE: After any XP action
    BE->>DB: SELECT badges NOT IN user_badges

    loop Each Unearned Badge
        BE->>DB: Calculate progress (current, target)
        alt current >= target
            BE->>DB: INSERT user_badges
            BE->>DB: UPDATE user.total_xp += badge.xp_bonus
            BE->>BE: Add to newly_earned list
        end
    end

    BE-->>BE: Return newly_earned badges
```

---

**END OF PHASE 2 DOCUMENT**
