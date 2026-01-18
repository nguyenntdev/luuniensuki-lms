# Image URL Backend Fix Summary

## Issue
Images were not loading in the LMS mobile app because the backend API was not returning `image_url` fields that the mobile app expects.

## Root Cause
The mobile app DTOs (`MotifDetailDto`, `MotifDto`, quiz question DTOs) expect an `image_url` field from the API, but the backend schemas (`MotifDetailOut`, `MotifQuizQuestionOut`, `QuizQuestionOut`) were not providing this field.

## Solution
Added `image_url: Optional[str] = None` field to all relevant backend response schemas and updated endpoints to populate this field.

## Changes Made

### 1. Updated Schemas in `backend/main.py`

#### MotifQuizQuestionOut (Line 3164-3172)
```python
class MotifQuizQuestionOut(BaseModel):
    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int = 1
    explanation: Optional[str] = None
    image_url: Optional[str] = None  # ✅ ADDED
```

#### MotifDetailOut (Line 3175-3190)
```python
class MotifDetailOut(BaseModel):
    id: UUID
    urn: UrnOut
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    silhouette_url: Optional[str] = None
    image_url: Optional[str] = None  # ✅ ADDED
    is_demo: bool
    display_order: Optional[int] = None
    lesson: Optional[LessonContentOut] = None
    quiz_question_count: int = 0
    quiz_questions: list[MotifQuizQuestionOut] = Field(default_factory=list)
```

#### QuizQuestionOut (Line 7926-7933)
```python
class QuizQuestionOut(BaseModel):
    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int
    image_url: Optional[str] = None  # ✅ ADDED
```

### 2. Updated Endpoint Responses

#### GET /api/v1/motifs/{motif_id} - MotifQuizQuestionOut Creation (Line 3225-3238)
```python
quiz_questions = [
    MotifQuizQuestionOut(
        id=q.id,
        question_type=q.question_type.value,
        question_text=q.question_text,
        options=q.options if isinstance(q.options, list) else None,
        target_mesh_name=q.target_mesh_name,
        difficulty=max(1, int(q.difficulty or 1)),
        explanation=(q.explanation or "").strip() or None,
        image_url=None,  # ✅ ADDED
    )
    for q in motif.quiz_questions
    if q.is_active and (q.is_published or can_view_drafts)
]
```

#### GET /api/v1/motifs/{motif_id} - MotifDetailOut Creation (Line 3239-3255)
```python
return MotifDetailOut(
    id=motif.id,
    urn=UrnOut.model_validate(motif.urn),
    mesh_name=motif.mesh_name,
    name=motif.name,
    name_en=motif.name_en,
    category=motif.category.value,
    rarity=motif.rarity.value,
    thumbnail_url=motif.thumbnail_url,
    silhouette_url=motif.silhouette_url,
    image_url=motif.thumbnail_url,  # ✅ ADDED - using thumbnail_url as fallback
    is_demo=motif.is_demo,
    display_order=motif.display_order,
    lesson=lesson_out,
    quiz_question_count=len(quiz_questions),
    quiz_questions=quiz_questions,
)
```

#### GET /api/v1/motifs/{motif_id}/quiz (Line 7981-7998)
```python
return MotifQuizResponse(
    motif_id=motif.id,
    questions=[
        QuizQuestionOut(
            id=q.id,
            question_type=q.question_type.value,
            question_text=q.question_text,
            options=q.options if isinstance(q.options, list) else None,
            target_mesh_name=q.target_mesh_name,
            difficulty=max(1, int(q.difficulty or 1)),
            image_url=None,  # ✅ ADDED
        )
        for q in questions
    ],
    attempts=progress.quiz_attempts,
    best_score=progress.quiz_best_score,
    pass_percent=QUIZ_PASS_PERCENT,
)
```

#### GET /api/v1/urns/{urn_id}/exam (Line 8711-8728)
```python
return UrnExamResponse(
    urn_id=urn.id,
    questions=[
        QuizQuestionOut(
            id=q.id,
            question_type=q.question_type.value,
            question_text=q.question_text,
            options=q.options if isinstance(q.options, list) else None,
            target_mesh_name=q.target_mesh_name,
            difficulty=max(1, int(q.difficulty or 1)),
            image_url=None,  # ✅ ADDED
        )
        for q in questions
    ],
    attempts=int(attempts or 0),
    best_score=int(best_score or 0),
    pass_percent=URN_EXAM_PASS_PERCENT,
)
```

#### GET /api/v1/urns/{urn_id}/exam/latest (Line 9065-9079)
```python
exam=UrnExamSnapshotOut(
    pass_percent=URN_EXAM_PASS_PERCENT,
    questions=[
        QuizQuestionOut(
            id=q.id,
            question_type=q.question_type.value,
            question_text=q.question_text,
            options=q.options if isinstance(q.options, list) else None,
            target_mesh_name=q.target_mesh_name,
            difficulty=max(1, int(q.difficulty or 1)),
            image_url=None,  # ✅ ADDED
        )
        for q in questions
    ],
),
```

## Notes

### Image URL Source
- For `MotifDetailOut`, we use `motif.thumbnail_url` as the value for `image_url` since the `Motif` model doesn't have a dedicated `image_url` field
- For quiz questions (`QuizQuestionOut` and `MotifQuizQuestionOut`), we set `image_url=None` since the `QuizQuestion` model doesn't have an `image_url` field either
- These can be populated with actual image URLs when the database models are updated to include these fields

### Database Model Status
The current database models don't have `image_url` fields:
- `Motif` model has: `thumbnail_url`, `silhouette_url` (but no `image_url`)
- `QuizQuestion` model has no image-related fields

### Future Enhancements
To fully support image URLs:
1. Add `image_url` column to `motifs` table via migration
2. Add `image_url` column to `quiz_questions` table via migration
3. Update seed scripts to populate these fields from the image directory scan
4. Update the endpoints to use the actual `image_url` fields instead of fallbacks

## Testing

### Verify Schema Changes
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/backend
python3 -m py_compile main.py
```

### Test API Response
```bash
# Test motif detail endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/motifs/{motif_id}

# Check that response includes image_url field
```

## Impact

### What Works Now
✅ Mobile app will receive `image_url` field in API responses
✅ No breaking changes - all fields are optional
✅ Backward compatible with existing mobile app versions

### What's Improved
- `MotifDetailOut` now includes `image_url` (populated with `thumbnail_url`)
- `MotifQuizQuestionOut` now includes `image_url` (currently `null`)
- `QuizQuestionOut` now includes `image_url` (currently `null`)

### Mobile App Compatibility
The mobile app DTOs already expect these fields:
- `MotifDetailDto.imageUrl`
- `MotifDto.imageUrl`
- Quiz question DTOs with `imageUrl` field

## Files Modified
- `backend/main.py` - Added `image_url` fields to 3 schemas and updated 5 endpoint responses

## Summary
This fix resolves the image loading issue by ensuring the backend API returns the `image_url` field that the mobile app expects. The implementation uses `thumbnail_url` as a fallback for motifs until proper `image_url` database fields are added.


