# Adaptive Quiz System (P1-ADAP-02)

> **Intelligent difficulty adjustment for personalized learning**

## Overview

The Adaptive Quiz System automatically adjusts quiz difficulty based on each user's skill level. Using an ELO-like rating algorithm, the system tracks user proficiency across different skill types and selects questions that are neither too easy nor too hard, optimizing the learning experience.

## Key Features

🎯 **Personalized Difficulty** - Questions matched to user skill level
📊 **Multi-Skill Tracking** - Separate proficiency tracking for different skill types
🔄 **Automatic Updates** - Skills update in real-time as users practice
📈 **Historical Analysis** - Recalculate skills from quiz history
🎓 **Intelligent Learning** - ELO-like algorithm ensures fair skill progression

## Quick Start

### For Developers

1. **Run Migration:**
   ```bash
   alembic upgrade head
   ```

2. **Test Endpoints:**
   ```bash
   API_TOKEN="your-token" ./test_adaptive_quiz.sh
   ```

3. **Read Documentation:**
   - [API Reference](P1-ADAP-02_API_REFERENCE.md)
   - [Quick Reference](P1-ADAP-02_QUICK_REFERENCE.md)

### For Content Creators

Assign skill types to questions:
- `motif_recognition` - Visual pattern identification
- `history_knowledge` - Historical facts and context
- `cultural_understanding` - Cultural significance

## API Endpoints

### Get Adaptive Quiz
```bash
GET /api/v1/quiz/adaptive?skill_type=motif_recognition&limit=10
```

### Get User Skills
```bash
GET /api/v1/skills
```

### Recalculate Skills
```bash
POST /api/v1/skills/recalculate
```

## Example Usage

### Frontend Integration

```javascript
// Get user's current skills
const response = await fetch('/api/v1/skills', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { skills, overall_level } = await response.json();

// Display skill levels
skills.forEach(skill => {
  console.log(`${skill.skill_type}: ${skill.skill_level}`);
  console.log(`Accuracy: ${skill.accuracy}%`);
});

// Get adaptive practice questions
const quiz = await fetch('/api/v1/quiz/adaptive?skill_type=motif_recognition&limit=5', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { questions, recommended_difficulty } = await quiz.json();

// Present questions to user
```

### Backend Integration

```python
from backend.services.adaptive_quiz import (
    get_user_skill_level,
    update_skill_level,
    get_adaptive_questions
)

# Get user's skill level
skill = get_user_skill_level(db, user_id, "motif_recognition")
print(f"Skill Level: {skill.skill_level}")

# Update skill after answering a question
updated_skill = update_skill_level(
    db,
    user_id=user_id,
    skill_type="motif_recognition",
    question_difficulty=3,  # 1-5 scale
    is_correct=True
)

# Get adaptive questions
questions = get_adaptive_questions(
    db,
    user_id=user_id,
    skill_type="motif_recognition",
    limit=10
)
```

## How It Works

### 1. Skill Initialization
- New users start at skill_level = 0.5 (intermediate)
- Each skill type tracked independently

### 2. Question Selection
- Questions selected within ±0.15 of user's skill level
- Ensures optimal challenge (flow state)
- Randomized within difficulty range

### 3. Skill Updates
- After each quiz question:
  - Calculate expected performance
  - Compare to actual performance
  - Adjust skill level using ELO formula
- Updates happen automatically during quiz submission

### 4. Progression
```
Beginner (0.0-0.3) → Novice (0.3-0.5) → Intermediate (0.5-0.7) 
→ Advanced (0.7-0.9) → Expert (0.9-1.0)
```

## Skill Types

| Type | Description | Example Questions |
|------|-------------|-------------------|
| `motif_recognition` | Visual pattern identification | "Identify the motif in this image" |
| `history_knowledge` | Historical facts and context | "Which dynasty created this style?" |
| `cultural_understanding` | Cultural significance | "What does this symbol represent?" |

## Algorithm

### ELO-like Rating System

```
Expected = 1.0 - |skill_level - question_difficulty|
Actual = 1.0 (if correct) or 0.0 (if wrong)
Delta = 0.1 × (Actual - Expected)
New_Skill = Clamp(Old_Skill + Delta, 0.0, 1.0)
```

**Key Properties:**
- Getting hard questions right → Larger skill increase
- Getting easy questions wrong → Larger skill decrease
- Performance at appropriate level → Small adjustments
- Converges to true skill level over time

## Documentation

- **[Index](P1-ADAP-02_INDEX.md)** - Documentation navigation
- **[Summary](P1-ADAP-02_SUMMARY.md)** - Implementation overview
- **[API Reference](P1-ADAP-02_API_REFERENCE.md)** - Complete API docs
- **[Quick Reference](P1-ADAP-02_QUICK_REFERENCE.md)** - Quick lookup
- **[Implementation](P1-ADAP-02_IMPLEMENTATION.md)** - Technical details
- **[Deployment](P1-ADAP-02_DEPLOYMENT_CHECKLIST.md)** - Deployment guide

## Testing

Run the automated test suite:

```bash
chmod +x test_adaptive_quiz.sh
export API_TOKEN="your-jwt-token"
./test_adaptive_quiz.sh
```

Tests cover:
- ✅ Skill retrieval
- ✅ Adaptive question selection
- ✅ Skill type filtering
- ✅ Error handling
- ✅ Skill recalculation

## Database Schema

### user_skill_levels
```sql
CREATE TABLE user_skill_levels (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    skill_type VARCHAR(50) NOT NULL,
    skill_level FLOAT DEFAULT 0.5,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    last_updated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, skill_type)
);
```

### quiz_questions (modified)
```sql
ALTER TABLE quiz_questions 
ADD COLUMN skill_type VARCHAR(50);
```

## Performance

- **Question Selection:** Single query with randomization
- **Skill Updates:** Single UPDATE per question
- **Caching:** 5-10 minute TTL recommended
- **Indexes:** Optimized for user_id and skill_type lookups

## Future Enhancements

- 🔮 Automatic question categorization using NLP
- 📊 Learning analytics dashboard
- 🎯 Adaptive learning paths
- 🌳 Hierarchical skill trees
- 📉 Skill decay over time
- 🤝 Peer comparison analytics

## Support

For issues or questions:
1. Check [Troubleshooting](P1-ADAP-02_SUMMARY.md#support--troubleshooting)
2. Review [API Reference](P1-ADAP-02_API_REFERENCE.md)
3. Contact backend team

## License

Part of the Luuniensuki LMS platform.

---

**Status:** ✅ Complete and Ready for Deployment
**Version:** 1.0
**Last Updated:** January 20, 2025

