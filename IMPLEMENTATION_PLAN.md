# Implementation Plan: New Features for Luuniensuki LMS

## Overview

This document contains detailed implementation prompts for Codex CLI and Gemini CLI to implement:
1. **User Profile Editing** with avatar upload
2. **Public User Page** with QR codes
3. **Urn Exams System** with generated questions
4. **Certification System** with QR verification

---

## Phase 1: User Profile Editing with Avatar Upload

### Task 1.1 - Backend: Add User Model Fields (CODEX)

```bash
codex -a auto-edit "Add new fields to User model in backend/models.py:

1. Add 'bio' field: Optional[str], Text, nullable=True
2. Add 'is_profile_public' field: bool, default=True (new users have public profiles by default)

Location: backend/models.py, User class (around line 80-108)

Add after 'avatar_url' field:
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_profile_public: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))

Import Boolean from sqlalchemy if not already imported."
```

### Task 1.2 - Backend: Create PATCH /users/me Endpoint (CODEX)

```bash
codex -a auto-edit "Create PATCH /api/v1/users/me endpoint in backend/main.py:

1. Create Pydantic model 'UpdateProfileRequest':
   - display_name: Optional[str] = Field(None, min_length=2, max_length=100)
   - bio: Optional[str] = Field(None, max_length=500)
   - is_profile_public: Optional[bool] = None

2. Create Pydantic model 'UpdateProfileResponse':
   - user: UserOut (reuse existing)
   - message: str

3. Create endpoint:
   @app.patch('/api/v1/users/me', response_model=UpdateProfileResponse)
   def update_profile(
       request: UpdateProfileRequest,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       - Update only non-None fields
       - Validate display_name doesn't contain special chars (alphanumeric, spaces, Vietnamese chars only)
       - db.commit()
       - Return updated user

Add after the existing /api/v1/auth/me endpoint (around line 387)."
```

### Task 1.3 - Backend: Create Avatar Upload Endpoint (CODEX)

```bash
codex -a auto-edit "Create POST /api/v1/users/me/avatar endpoint in backend/main.py:

1. Add imports at top:
   from fastapi import File, UploadFile
   import os
   import uuid as uuid_module
   from pathlib import Path

2. Add constant:
   AVATAR_UPLOAD_DIR = Path('/app/uploads/avatars')
   ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
   MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB

3. Create endpoint:
   @app.post('/api/v1/users/me/avatar')
   async def upload_avatar(
       file: UploadFile = File(...),
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       - Validate file.content_type in ALLOWED_IMAGE_TYPES
       - Validate file size <= MAX_AVATAR_SIZE
       - Generate unique filename: {user_id}_{uuid4()}.{extension}
       - Create AVATAR_UPLOAD_DIR if not exists
       - Save file to AVATAR_UPLOAD_DIR / filename
       - Update current_user.avatar_url = f'/assets/avatars/{filename}'
       - db.commit()
       - Return {'avatar_url': current_user.avatar_url}

Add after the update_profile endpoint."
```

### Task 1.4 - Backend: Create Change Password Endpoint (CODEX)

```bash
codex -a auto-edit "Create POST /api/v1/users/me/change-password endpoint in backend/main.py:

1. Create Pydantic model 'ChangePasswordRequest':
   - current_password: str
   - new_password: str = Field(..., min_length=8)

2. Create endpoint:
   @app.post('/api/v1/users/me/change-password')
   def change_password(
       request: ChangePasswordRequest,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       - Verify current_password using verify_password(request.current_password, current_user.password_hash)
       - If invalid, raise HTTPException(400, 'Current password is incorrect')
       - Hash new password: current_user.password_hash = hash_password(request.new_password)
       - db.commit()
       - Return {'message': 'Password changed successfully'}

Add after the avatar upload endpoint."
```

### Task 1.5 - Frontend: Create ProfileEditForm Component (CODEX)

```bash
codex -a auto-edit "Create frontend/src/components/ProfileEditForm.jsx:

A React component for editing user profile with:
1. Props: user (current user data), onSave (callback), onCancel (callback)
2. State: formData (display_name, bio, is_profile_public), loading, error
3. Form fields:
   - Display Name: text input, required, 2-100 chars
   - Bio: textarea, optional, max 500 chars
   - Public Profile: checkbox toggle
4. Validation before submit
5. Call PATCH /api/v1/users/me via api.js
6. Show loading spinner during save
7. Show error toast on failure
8. Call onSave with updated user on success

Style with TailwindCSS matching existing components.
Add updateProfile function to frontend/src/lib/api.js:
export function updateProfile({ token, displayName, bio, isProfilePublic }) {
  return apiRequest('/api/v1/users/me', {
    method: 'PATCH',
    token,
    body: { display_name: displayName, bio, is_profile_public: isProfilePublic }
  });
}"
```

### Task 1.6 - Frontend: Add Avatar Upload Component (CODEX)

```bash
codex -a auto-edit "Create frontend/src/components/AvatarUpload.jsx:

A React component for avatar upload with preview:
1. Props: currentAvatarUrl, onUpload (callback with new URL)
2. Features:
   - Display current avatar or placeholder
   - Click to open file picker
   - Preview selected image before upload
   - Upload button to confirm
   - Cancel button to reset
   - Loading state during upload
   - Error handling for invalid files
3. Validation:
   - Accept only image/jpeg, image/png, image/webp
   - Max 5MB file size
4. Call POST /api/v1/users/me/avatar with FormData

Add uploadAvatar function to frontend/src/lib/api.js:
export async function uploadAvatar({ token, file }) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/v1/users/me/avatar', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + token },
    body: formData
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

Style with TailwindCSS, circular avatar preview, hover overlay for change."
```

### Task 1.7 - Frontend: Integrate Edit Form into UserProfile (CODEX)

```bash
codex -a auto-edit "Modify frontend/src/components/UserProfile.js to add edit mode:

1. Add state: isEditing (boolean, default false)
2. Add 'Edit Profile' button in header section (pencil icon)
3. When isEditing=true:
   - Show ProfileEditForm instead of display-only info
   - Show AvatarUpload instead of static avatar
4. When isEditing=false:
   - Show current display (existing code)
5. On save success:
   - Set isEditing=false
   - Refresh user data via fetchMe()
6. On cancel:
   - Set isEditing=false
   - Reset any local changes

Add imports for ProfileEditForm and AvatarUpload.
Add edit button with icon (use existing icon pattern or add Pencil icon)."
```

---

## Phase 2: Public User Page with QR Codes

### Task 2.1 - Backend: Create Public Profile Endpoint (CODEX)

```bash
codex -a auto-edit "Create GET /api/v1/users/{user_id}/public endpoint in backend/main.py:

1. Create Pydantic models:
   class PublicBadgeOut(BaseModel):
       slug: str
       name: str
       icon_url: str
       earned_at: datetime

   class PublicCertificateOut(BaseModel):
       urn_name: str
       certificate_number: str
       earned_at: datetime

   class PublicProfileResponse(BaseModel):
       user_id: UUID
       display_name: str
       avatar_url: Optional[str]
       bio: Optional[str]
       total_xp: int
       rank: RankOut
       badges: list[PublicBadgeOut]
       certificates: list[PublicCertificateOut]
       stats: dict  # discovered, learned, mastered counts
       member_since: datetime

2. Create endpoint (no auth required):
   @app.get('/api/v1/users/{user_id}/public', response_model=PublicProfileResponse)
   def get_public_profile(user_id: UUID, db: Session = Depends(get_db)):
       - Fetch user by ID
       - If not found, raise 404
       - If is_profile_public=False, raise 403 'Profile is private'
       - Fetch user's badges with earned_at
       - Fetch user's certificates (after Phase 4)
       - Calculate stats from user_progress
       - Return PublicProfileResponse

Add after /api/v1/users/me/badges endpoint."
```

### Task 2.2 - Frontend: Create Public Profile Page (CODEX)

```bash
codex -a auto-edit "Create frontend/src/app/u/[userId]/page.jsx:

A public profile page showing:
1. User avatar, display name, bio
2. XP and rank with progress bar
3. Member since date
4. Stats: motifs discovered/learned/mastered
5. Badges grid (earned badges with dates)
6. Certificates section (after Phase 4)
7. Share button with QR code modal

Features:
- Fetch from GET /api/v1/users/{userId}/public
- Handle 404 (user not found) and 403 (private profile)
- Loading skeleton
- Responsive design

Add getPublicProfile to frontend/src/lib/api.js:
export function getPublicProfile(userId) {
  return apiRequest('/api/v1/users/' + userId + '/public');
}

Style matching existing profile page but read-only."
```

### Task 2.3 - Frontend: Add QR Code Generation (CODEX)

```bash
codex -a auto-edit "Add QR code component for profile sharing:

1. Install qrcode.react: Add to frontend/package.json dependencies
   'qrcode.react': '^3.1.0'

2. Create frontend/src/components/ShareQRModal.jsx:
   - Props: url (string), title (string), isOpen, onClose
   - Display QR code for the URL
   - Show URL text below QR
   - Copy URL button
   - Download QR as PNG button
   - Close button

3. Use in public profile page and UserProfile:
   - Share button opens modal
   - URL: https://lms.histolab.icu/u/{userId}

Import QRCodeSVG from 'qrcode.react'.
Style as modal overlay with TailwindCSS."
```

### Task 2.4 - Frontend: Add Share Button and Privacy Toggle (CODEX)

```bash
codex -a auto-edit "Add share functionality to UserProfile.js:

1. Add Share button next to Edit button in header
2. On click, open ShareQRModal with profile URL
3. In ProfileEditForm, add privacy toggle:
   - Label: 'Hồ sơ công khai' (Public Profile)
   - Checkbox with description: 'Cho phép người khác xem hồ sơ của bạn'
   - When unchecked, show warning: 'Hồ sơ của bạn sẽ không hiển thị với người khác'

Add Share icon (use existing icon pattern or add Share2 icon)."
```

---

## Phase 3: Urn Exams System

### Task 3.1 - Backend: Add Urn Exam Models (CODEX)

```bash
codex -a auto-edit "Modify backend/models.py to add urn exam support:

1. Add urn_id to QuizQuestion model (after motif_id):
   urn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
       PG_UUID(as_uuid=True),
       ForeignKey('urns.id', ondelete='CASCADE'),
       nullable=True,
   )
   # Add relationship
   urn: Mapped[Optional[Urn]] = relationship(back_populates='exam_questions')

2. Add to Urn model:
   exam_questions: Mapped[list[QuizQuestion]] = relationship(
       back_populates='urn',
       foreign_keys='QuizQuestion.urn_id',
   )

3. Create UrnExamAttempt model (after QuizAttempt):
   class UrnExamAttempt(Base):
       __tablename__ = 'urn_exam_attempts'
       __table_args__ = (
           Index('idx_urn_exam_user', 'user_id'),
           Index('idx_urn_exam_urn', 'urn_id'),
       )

       id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
       urn_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('urns.id', ondelete='CASCADE'), nullable=False)
       score: Mapped[int] = mapped_column(Integer, nullable=False)
       max_score: Mapped[int] = mapped_column(Integer, nullable=False)
       percentage: Mapped[int] = mapped_column(Integer, nullable=False)
       passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
       answers: Mapped[Any] = mapped_column(JSONB, nullable=False)
       time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer)
       completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

       user: Mapped[User] = relationship()
       urn: Mapped[Urn] = relationship()"
```

### Task 3.2 - Backend: Create Urn Exam API Endpoints (CODEX)

```bash
codex -a auto-edit "Create urn exam endpoints in backend/main.py:

1. Constants:
   URN_EXAM_PASS_PERCENT = 80
   URN_EXAM_QUESTION_COUNT = 15

2. GET /api/v1/urns/{urn_slug}/exam - Get exam questions:
   - Require auth
   - Check user has learned >= 50% of urn's motifs (prerequisite)
   - Fetch questions: mix of urn-specific (urn_id=urn.id) and motif questions from that urn
   - Randomly select URN_EXAM_QUESTION_COUNT questions
   - Return questions without correct_answer field

3. POST /api/v1/urns/{urn_slug}/exam/submit - Submit exam:
   - Require auth
   - Validate answers format
   - Calculate score
   - Create UrnExamAttempt record
   - If passed (>=80%), check for certificate eligibility
   - Return score, percentage, passed, correct_answers

4. GET /api/v1/urns/{urn_slug}/exam/history - Get user's exam attempts:
   - Require auth
   - Return list of UrnExamAttempt for this user/urn
   - Order by completed_at desc

Pydantic models:
- UrnExamQuestionOut (id, question_text, options, question_type)
- UrnExamSubmitRequest (answers: dict[str, str], time_taken_seconds: int)
- UrnExamResultResponse (score, max_score, percentage, passed, correct_answers, xp_awarded)
- UrnExamAttemptOut (id, score, percentage, passed, completed_at)"
```

### Task 3.3 - Gemini: Generate Urn Exam Questions (GEMINI)

```bash
# Run for each urn (example for Cao Đỉnh)
gemini -m gemini-3-pro-preview "Generate 15 Vietnamese exam questions for Cao Đỉnh (高鼎) urn in Cửu Đỉnh.

Context: Cao Đỉnh is dedicated to Emperor Gia Long, founder of Nguyen Dynasty. It contains motifs including:
- Long (Dragon) - symbol of imperial power
- Phượng (Phoenix) - symbol of empress
- Mặt Trời (Sun) - symbol of enlightenment
- Various flora and fauna representing Vietnamese nature

Requirements:
1. Questions should test SYNTHESIS knowledge across multiple motifs
2. Mix of question types: multiple_choice (10), true_false (3), image_select (2)
3. Difficulty levels: easy (5), medium (7), hard (3)
4. Questions should connect themes: symbolism, history, cultural significance
5. All text in Vietnamese

Output JSON format:
{
  'urn_slug': 'cao-dinh',
  'questions': [
    {
      'question_type': 'multiple_choice',
      'question_text': '...',
      'options': ['A. ...', 'B. ...', 'C. ...', 'D. ...'],
      'correct_answer': 'A. ...',
      'difficulty': 1-3,
      'explanation': '...'
    }
  ]
}

Generate questions that require understanding relationships between motifs, not just memorization."
```

Repeat for all 9 urns:
- cao-dinh (Cao Đỉnh - Gia Long)
- nhan-dinh (Nhân Đỉnh - Minh Mạng)
- chuong-dinh (Chương Đỉnh - Thiệu Trị)
- anh-dinh (Anh Đỉnh - Tự Đức)
- nghi-dinh (Nghị Đỉnh - Kiến Phúc)
- thuan-dinh (Thuần Đỉnh - Đồng Khánh)
- tuyen-dinh (Tuyên Đỉnh - Thành Thái)
- du-dinh (Dụ Đỉnh - Duy Tân)
- huyen-dinh (Huyền Đỉnh - Khải Định)

### Task 3.4 - Frontend: Create Urn Exam UI (CODEX)

```bash
codex -a auto-edit "Create urn exam pages in frontend:

1. Create frontend/src/app/urns/[urnSlug]/exam/page.jsx:
   - Check prerequisites (learned motifs count)
   - Show exam info: 15 questions, 80% to pass, time limit optional
   - Start Exam button
   - Previous attempts history

2. Create frontend/src/components/UrnExamFlow.jsx:
   - Question-by-question flow (similar to motif quiz)
   - Progress indicator (1/15, 2/15, etc.)
   - Timer (optional)
   - Previous/Next navigation
   - Submit button on last question

3. Create frontend/src/app/urns/[urnSlug]/exam/result/page.jsx:
   - Show score, percentage, pass/fail
   - Correct answers review
   - If passed: Show certificate claim button
   - Retry button if failed

Add API functions to frontend/src/lib/api.js:
- getUrnExam({ token, urnSlug })
- submitUrnExam({ token, urnSlug, answers, timeTakenSeconds })
- getUrnExamHistory({ token, urnSlug })"
```

---

## Phase 4: Certification System

### Task 4.1 - Backend: Create Certificate Models (CODEX)

```bash
codex -a auto-edit "Create Certificate models in backend/models.py:

1. Create Certificate model:
   class Certificate(Base):
       __tablename__ = 'certificates'

       id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
       urn_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('urns.id', ondelete='CASCADE'), nullable=False)
       name: Mapped[str] = mapped_column(String(255), nullable=False)
       name_en: Mapped[Optional[str]] = mapped_column(String(255))
       description: Mapped[Optional[str]] = mapped_column(Text)
       image_url: Mapped[Optional[str]] = mapped_column(Text)
       xp_bonus: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

       urn: Mapped[Urn] = relationship()
       user_certificates: Mapped[list[UserCertificate]] = relationship(back_populates='certificate')

2. Create UserCertificate model:
   class UserCertificate(Base):
       __tablename__ = 'user_certificates'
       __table_args__ = (
           UniqueConstraint('user_id', 'certificate_id', name='uq_user_certificate'),
           Index('idx_user_cert_user', 'user_id'),
           Index('idx_user_cert_number', 'certificate_number'),
       )

       id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
       certificate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('certificates.id', ondelete='CASCADE'), nullable=False)
       certificate_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
       exam_score: Mapped[int] = mapped_column(Integer, nullable=False)
       earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

       user: Mapped[User] = relationship()
       certificate: Mapped[Certificate] = relationship(back_populates='user_certificates')

Add relationships to User model:
   user_certificates: Mapped[list[UserCertificate]] = relationship(back_populates='user', cascade='all, delete-orphan')"
```

### Task 4.2 - Backend: Create Certification API Endpoints (CODEX)

```bash
codex -a auto-edit "Create certification endpoints in backend/main.py:

1. GET /api/v1/urns/{urn_slug}/certificate-status:
   - Require auth
   - Return: eligible (bool), requirements_met (dict), best_exam_score, certificate (if earned)
   - Requirements: passed urn exam (>=80%)

2. POST /api/v1/urns/{urn_slug}/claim-certificate:
   - Require auth
   - Check eligibility (must have passed exam)
   - Generate unique certificate_number: 'LNS-{URN_CODE}-{YEAR}-{SEQUENCE}'
   - Create UserCertificate record
   - Award XP bonus
   - Return certificate details

3. GET /api/v1/users/me/certificates:
   - Require auth
   - Return list of user's certificates with urn info

Pydantic models:
- CertificateStatusResponse (eligible, requirements_met, best_exam_score, certificate)
- CertificateOut (certificate_number, urn_name, urn_slug, name, earned_at, exam_score)
- ClaimCertificateResponse (certificate: CertificateOut, xp_awarded)

Helper function to generate certificate number:
def _generate_certificate_number(urn_slug: str, db: Session) -> str:
    year = datetime.now().year
    urn_code = urn_slug[:3].upper()
    count = db.execute(select(func.count(UserCertificate.id)).where(...)).scalar_one()
    return f'LNS-{urn_code}-{year}-{count+1:04d}'"
```

### Task 4.3 - Backend: Create Certificate Verification Endpoint (CODEX)

```bash
codex -a auto-edit "Create certificate verification endpoint in backend/main.py:

GET /api/v1/certificates/{certificate_number}/verify (no auth required):
   - Fetch UserCertificate by certificate_number
   - If not found, raise 404
   - Return verification info:
     - valid: true
     - certificate_number
     - holder_name (display_name)
     - urn_name
     - certificate_name
     - earned_at
     - exam_score

Pydantic model:
class CertificateVerifyResponse(BaseModel):
    valid: bool
    certificate_number: str
    holder_name: str
    urn_name: str
    certificate_name: str
    earned_at: datetime
    exam_score: int"
```

### Task 4.4 - Frontend: Create Certificate Display Pages (CODEX)

```bash
codex -a auto-edit "Create certificate pages in frontend:

1. Create frontend/src/components/CertificateCard.jsx:
   - Display certificate with urn name, date, score
   - QR code linking to verification URL
   - Download/Print button
   - Share button

2. Create frontend/src/app/verify/[certNumber]/page.jsx:
   - Public verification page
   - Fetch from GET /api/v1/certificates/{certNumber}/verify
   - Show verification status (valid/invalid)
   - Display certificate details if valid
   - Show holder name, urn, date, score

3. Add certificates section to UserProfile.js:
   - Fetch user's certificates
   - Display CertificateCard grid
   - Empty state if no certificates

Add API functions to frontend/src/lib/api.js:
- getMyCertificates({ token })
- getCertificateStatus({ token, urnSlug })
- claimCertificate({ token, urnSlug })
- verifyCertificate(certNumber)"
```

### Task 4.5 - Frontend: Add QR Code to Certificates (CODEX)

```bash
codex -a auto-edit "Add QR code to CertificateCard component:

1. Import QRCodeSVG from 'qrcode.react'
2. Generate verification URL: https://lms.histolab.icu/verify/{certificate_number}
3. Display QR code on certificate card
4. Add download QR as PNG functionality
5. Style QR code to fit certificate design

The QR code should be:
- Size: 100x100px on card, larger on full view
- Include LMS logo in center (optional)
- High error correction level for reliability"
```

---

## Phase 5: Database Migration and Deployment

### Task 5.1 - Create Alembic Migration (CODEX)

```bash
codex -a auto-edit "Create migrations/versions/0002_new_features.py:

Alembic migration adding:
1. Users table changes:
   - Add 'bio' column (Text, nullable)
   - Add 'is_profile_public' column (Boolean, default true)

2. quiz_questions table changes:
   - Add 'urn_id' column (UUID, FK to urns.id, nullable)

3. New table 'urn_exam_attempts':
   - id (UUID PK)
   - user_id (UUID FK)
   - urn_id (UUID FK)
   - score (Integer)
   - max_score (Integer)
   - percentage (Integer)
   - passed (Boolean)
   - answers (JSONB)
   - time_taken_seconds (Integer, nullable)
   - completed_at (Timestamp)

4. New table 'certificates':
   - id (UUID PK)
   - slug (String unique)
   - urn_id (UUID FK)
   - name (String)
   - name_en (String, nullable)
   - description (Text, nullable)
   - image_url (Text, nullable)
   - xp_bonus (Integer, default 100)
   - created_at (Timestamp)

5. New table 'user_certificates':
   - id (UUID PK)
   - user_id (UUID FK)
   - certificate_id (UUID FK)
   - certificate_number (String unique)
   - exam_score (Integer)
   - earned_at (Timestamp)
   - Unique constraint on (user_id, certificate_id)

Use op.add_column, op.create_table, op.create_index, op.create_foreign_key."
```

### Task 5.2 - Seed Certificate Data (CODEX)

```bash
codex -a auto-edit "Add certificate seeding to backend/seed.py:

1. Add CERTIFICATES data:
   CERTIFICATES = [
       {'slug': 'cao-dinh-master', 'urn_slug': 'cao-dinh', 'name': 'Chứng chỉ Cao Đỉnh', 'name_en': 'Cao Dinh Certificate', 'xp_bonus': 100},
       {'slug': 'nhan-dinh-master', 'urn_slug': 'nhan-dinh', 'name': 'Chứng chỉ Nhân Đỉnh', 'name_en': 'Nhan Dinh Certificate', 'xp_bonus': 100},
       # ... all 9 urns
   ]

2. Add upsert_certificate function:
   def upsert_certificate(session, *, slug, urn_slug, name, name_en, xp_bonus):
       urn = session.execute(select(Urn).where(Urn.slug == urn_slug)).scalar_one()
       cert = session.execute(select(Certificate).where(Certificate.slug == slug)).scalar_one_or_none()
       if cert is None:
           cert = Certificate(slug=slug, urn_id=urn.id, name=name, name_en=name_en, xp_bonus=xp_bonus)
           session.add(cert)
       else:
           cert.name = name
           cert.name_en = name_en
           cert.xp_bonus = xp_bonus
       session.flush()
       return cert

3. Call in main seed function after urns are seeded."
```

### Task 5.3 - Update nginx.conf (CODEX)

```bash
codex -a auto-edit "Update nginx.conf for avatar uploads:

1. Add volume mount for avatars in docker-compose.yml:
   - ./uploads/avatars:/var/www/assets/avatars:ro

2. Update nginx.conf:
   - /assets/avatars/ location already covered by /assets/ block
   - Ensure client_max_body_size is at least 10m (already set)

3. Allow POST method for /api/ routes (already allowed)

4. Create uploads/avatars directory in project root."
```

### Task 5.4 - Deploy Commands

```bash
# Run in order:

# 1. Create uploads directory
mkdir -p uploads/avatars

# 2. Run migration
docker compose exec api alembic upgrade head

# 3. Seed certificates
docker compose exec api python -m backend.seed --seed-path data --image-path ban-duc-noi

# 4. Rebuild and restart
docker compose down
docker compose up -d --build

# 5. Verify
curl https://lms.histolab.icu/api/v1/urns
curl https://lms.histolab.icu/health
```

---

## Execution Order

1. **Phase 1** (Profile Edit): Tasks 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7
2. **Phase 2** (Public Profile): Tasks 2.1 → 2.2 → 2.3 → 2.4
3. **Phase 3** (Urn Exams): Tasks 3.1 → 3.2 → 3.3 (Gemini) → 3.4
4. **Phase 4** (Certification): Tasks 4.1 → 4.2 → 4.3 → 4.4 → 4.5
5. **Phase 5** (Deploy): Tasks 5.1 → 5.2 → 5.3 → 5.4

## Tool Assignment Summary

| Task | Tool | Description |
|------|------|-------------|
| 1.1-1.7 | Codex | User profile editing backend + frontend |
| 2.1-2.4 | Codex | Public profile backend + frontend |
| 3.1-3.2 | Codex | Urn exam backend |
| 3.3 | Gemini | Generate exam questions for 9 urns |
| 3.4 | Codex | Urn exam frontend |
| 4.1-4.5 | Codex | Certification system |
| 5.1-5.3 | Codex | Migration and config |
| 5.4 | Manual | Deploy commands |

