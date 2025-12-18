# 🤖 CODEX TASKS - Backend Improvements

## 📋 Assigned Tasks

### ~~Phase 1: Backend APIs~~ ✅ DONE

| # | Task | Status |
|---|------|--------|
| ~~1.4~~ | ~~`POST /api/v1/streak/freeze`~~ | ✅ |
| ~~1.5~~ | ~~Thêm 7 badges mới~~ | ✅ |
| ~~1.6~~ | ~~Badge awarding logic mở rộng~~ | ✅ |
| ~~1.7~~ | ~~Error handling improvements~~ | ✅ |

---

## 🆕 Phase 2: Content Enrichment Backend (NEW)

| # | Task | Priority | Status |
|---|------|----------|--------|
| 2.1 | Update `seed.py` upsert_lesson() | HIGH | [ ] |
| 2.2 | Multiple quiz questions support | HIGH | [ ] |
| 2.3 | Category/rarity mapping from JSON | MEDIUM | [ ] |
| 2.4 | Quiz explanation in API response | MEDIUM | [ ] |

---

## 📝 NEW TASK DETAILS

### 2.1 Update seed.py upsert_lesson()

**Location:** `backend/seed.py`

**Current function:**
```python
def upsert_lesson(session: Session, *, motif: Motif, intro_text: str | None, description: str) -> LessonContent:
```

**Update to handle new fields:**
```python
def upsert_lesson(
    session: Session,
    *,
    motif: Motif,
    intro_text: str | None,
    description: str,
    historical_context: str | None = None,  # NEW
    symbolism: str | None = None,            # NEW
    fun_fact: str | None = None,             # NEW
    is_ai_generated: bool = False,           # NEW
) -> LessonContent:
    lesson = session.execute(select(LessonContent).where(LessonContent.motif_id == motif.id)).scalar_one_or_none()
    if lesson is None:
        lesson = LessonContent(
            motif_id=motif.id,
            intro_text=intro_text,
            description=description,
            historical_context=historical_context,
            symbolism=symbolism,
            fun_fact=fun_fact,
            is_ai_generated=is_ai_generated,
        )
        session.add(lesson)
        session.flush()
        return lesson

    lesson.intro_text = intro_text
    lesson.description = description
    lesson.historical_context = historical_context
    lesson.symbolism = symbolism
    lesson.fun_fact = fun_fact
    lesson.is_ai_generated = is_ai_generated
    session.flush()
    return lesson
```

**Update main seeding loop (~line 598):**
```python
upsert_lesson(
    session,
    motif=motif,
    intro_text=description_short,
    description=str(description_educational),
    historical_context=item.get("historical_context"),  # NEW
    symbolism=item.get("symbolism"),                    # NEW
    fun_fact=item.get("fun_fact"),                      # NEW
    is_ai_generated=item.get("is_ai_generated", False), # NEW
)
```

---

### 2.2 Multiple quiz questions support

**Location:** `backend/seed.py`

**Current:** Handles single `quiz_question` object
**New:** Handle `quiz_questions` array

**Update seeding logic:**
```python
# Support both old format (quiz_question) and new format (quiz_questions)
quiz_questions = item.get("quiz_questions", [])
if not quiz_questions:
    # Fallback to old single question format
    quiz = item.get("quiz_question")
    if isinstance(quiz, dict):
        quiz_questions = [quiz]

for quiz in quiz_questions:
    if not isinstance(quiz, dict):
        continue
    question_text = quiz.get("question")
    correct_answer = quiz.get("correct_answer")
    if not question_text or not correct_answer:
        continue

    # Map question type string to enum
    q_type_str = quiz.get("type", "multiple_choice")
    q_type = QuestionType[q_type_str] if q_type_str in QuestionType.__members__ else QuestionType.multiple_choice

    upsert_quiz_question(
        session,
        motif=motif,
        question_type=q_type,                    # NEW: support different types
        question_text=str(question_text),
        options=quiz.get("options"),
        correct_answer=str(correct_answer),
        difficulty=quiz.get("difficulty", 1),    # NEW: difficulty level
        explanation=quiz.get("explanation"),     # NEW: explanation
    )
```

**Update `upsert_quiz_question()` function:**
```python
def upsert_quiz_question(
    session: Session,
    *,
    motif: Motif,
    question_type: QuestionType = QuestionType.multiple_choice,  # NEW
    question_text: str,
    options: list | None,
    correct_answer: str,
    difficulty: int = 1,      # NEW
    explanation: str | None = None,  # NEW
) -> QuizQuestion:
    # Check if question already exists (by motif + question_text)
    existing = session.execute(
        select(QuizQuestion).where(
            QuizQuestion.motif_id == motif.id,
            QuizQuestion.question_text == question_text
        )
    ).scalar_one_or_none()

    if existing:
        existing.question_type = question_type
        existing.options = options
        existing.correct_answer = correct_answer
        existing.difficulty = difficulty
        existing.explanation = explanation
        session.flush()
        return existing

    question = QuizQuestion(
        motif_id=motif.id,
        question_type=question_type,
        question_text=question_text,
        options=options,
        correct_answer=correct_answer,
        difficulty=difficulty,
        explanation=explanation,
    )
    session.add(question)
    session.flush()
    return question
```

---

### 2.3 Category/rarity mapping from JSON

**Location:** `backend/seed.py`

**Current:** Hardcoded `category=MotifCategory.thao_moc, rarity=MotifRarity.common`

**Update `upsert_motif()` call:**
```python
# Map category string to enum
category_str = item.get("category", "thao_moc")
category = MotifCategory[category_str] if category_str in MotifCategory.__members__ else MotifCategory.thao_moc

# Map rarity string to enum
rarity_str = item.get("rarity", "common")
rarity = MotifRarity[rarity_str] if rarity_str in MotifRarity.__members__ else MotifRarity.common

motif = upsert_motif(
    session,
    urn=urn,
    mesh_name=mesh_name,
    name_vi=name_vi,
    name_en=item.get("name_en"),
    category=category,   # FROM JSON
    rarity=rarity,       # FROM JSON
    display_order=display_order,
    thumbnail_url=thumbnail_url,
)
```

---

### 2.4 Quiz explanation in API response

**Location:** `backend/main.py`

**Update `QuizQuestionOut` schema:**
```python
class QuizQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_type: str
    question_text: str
    options: Optional[list] = None
    difficulty: int = 1
    # NOTE: Don't include correct_answer or explanation here (shown after submit)
```

**Update quiz submit response to include explanations:**
```python
class QuizResultOut(BaseModel):
    score: int
    max_score: int
    percentage: int
    passed: bool
    xp_earned: int
    results: list[dict]  # Include explanation for each question
```

**In `submit_quiz()` endpoint, add explanation to results:**
```python
results = []
for q in questions:
    user_answer = answers_dict.get(str(q.id))
    is_correct = user_answer == q.correct_answer
    results.append({
        "question_id": str(q.id),
        "correct": is_correct,
        "correct_answer": q.correct_answer,
        "user_answer": user_answer,
        "explanation": q.explanation,  # NEW: include explanation
    })
```

---

## 🔧 FILES TO MODIFY

| File | Changes |
|------|---------|
| `backend/seed.py` | upsert_lesson(), upsert_quiz_question(), main seeding loop |
| `backend/main.py` | QuizResultOut schema, submit_quiz() response |

---

## ✅ ACCEPTANCE CRITERIA

- [ ] `upsert_lesson()` handles historical_context, symbolism, fun_fact
- [ ] Multiple quiz questions per motif supported
- [ ] Quiz questions have difficulty levels (1-3)
- [ ] Category/rarity read from JSON, not hardcoded
- [ ] Quiz submit returns explanation for each question
- [ ] Backward compatible with old JSON format

---

## 🚀 RUN COMMAND

```bash
cd /root/luuniensuki-lms
docker compose up -d --build api
docker compose exec api python seed.py
docker compose exec api pytest tests/ -v
```

