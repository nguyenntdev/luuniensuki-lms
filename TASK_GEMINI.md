# 🎨 GEMINI TASKS - Frontend & Content Creation

## 📋 Assigned Tasks

### ~~Phase 2: Frontend UI/UX~~ ✅ DONE

| # | Task | Status |
|---|------|--------|
| ~~2.3~~ | ~~Badge gallery page `/badges`~~ | ✅ |
| ~~2.4~~ | ~~Quiz UI improvements~~ | ✅ |
| ~~2.5~~ | ~~Collection page filters~~ | ✅ |
| ~~2.6~~ | ~~Loading states & skeleton UI~~ | ✅ |
| ~~2.7~~ | ~~Mobile responsive~~ | ✅ |
| ~~2.8~~ | ~~Toast notifications~~ | ✅ |

### ~~Phase 3: 3D Viewer~~ ✅ DONE

| # | Task | Status |
|---|------|--------|
| ~~3.7~~ | ~~Motif info popup~~ | ✅ |

---

## 🆕 Phase 4: Content Creation (NEW) - HIGH PRIORITY 🔥

> **LƯU Ý:** Dùng Google Search để research thông tin lịch sử về Cửu Đỉnh triều Nguyễn!

| # | Task | Priority | Status |
|---|------|----------|--------|
| 4.0.1 | Define enriched JSON schema | HIGH | [ ] |
| 4.0.2 | Enrich Cao Đỉnh data (18 motifs) | HIGH | [ ] |
| 4.0.3 | Enrich remaining 8 urns data | HIGH | [ ] |
| 4.0.4 | Review content quality | MEDIUM | [ ] |

### 4.0.1 Define enriched JSON schema

**Output file:** `docs/content/ENRICHED_JSON_SCHEMA.md`

**New JSON structure cho mỗi motif:**
```json
{
  "id": "urn_cao_dinh_02",
  "name_vi": "Long",
  "name_en": "Dragon",
  "urn_location": "Cao Đỉnh",
  "category": "linh_thu",
  "rarity": "legendary",

  "description_short": "Con rồng - biểu tượng quyền lực hoàng đế (1-2 câu)",
  "description_educational": "Mô tả chi tiết 200+ từ về họa tiết...",
  "historical_context": "Bối cảnh lịch sử: vua nào đúc, năm nào, ý nghĩa...",
  "symbolism": "Ý nghĩa biểu tượng trong văn hóa Việt Nam...",
  "fun_fact": "Điều thú vị ít người biết về họa tiết này...",

  "is_ai_generated": true,

  "quiz_questions": [
    {
      "type": "multiple_choice",
      "question": "Câu hỏi 1?",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "B. ...",
      "difficulty": 1,
      "explanation": "Giải thích tại sao đáp án đúng..."
    },
    {
      "type": "true_false",
      "question": "Câu hỏi đúng/sai?",
      "correct_answer": "True",
      "difficulty": 2,
      "explanation": "..."
    },
    {
      "type": "multiple_choice",
      "question": "Câu hỏi khó hơn?",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "D. ...",
      "difficulty": 3,
      "explanation": "..."
    }
  ]
}
```

**Categories available:**
- `linh_thu` - Linh thú (rồng, phượng, kỳ lân...)
- `dong_vat` - Động vật (hổ, voi, cá...)
- `thao_moc` - Thảo mộc (hoa, cây, quả...)
- `dia_ly` - Địa lý (sông, núi, biển...)
- `nong_nghiep` - Nông nghiệp (lúa, cày, thuyền...)
- `vo_bi` - Vũ khí (gươm, giáo, cung...)
- `giao_thuong` - Giao thương (thuyền buôn, tiền...)
- `thien_van` - Thiên văn (mặt trời, mặt trăng, sao...)
- `kien_truc` - Kiến trúc (cung điện, đền...)

**Rarity levels:**
- `common` - Phổ biến
- `uncommon` - Ít gặp
- `rare` - Hiếm
- `epic` - Sử thi
- `legendary` - Huyền thoại

---

### 4.0.2 Enrich Cao Đỉnh data (18 motifs)

**File:** `data/05_Data_CaoDinh.json`

**Research keywords để Google:**
- "Cao Đỉnh Cửu Đỉnh triều Nguyễn"
- "Họa tiết [tên] trên Cửu Đỉnh"
- "Ý nghĩa biểu tượng [tên] văn hóa Việt"
- "Vua Gia Long Minh Mạng Cửu Đỉnh"

**Cao Đỉnh motifs cần enrich:**
1. Cao Đỉnh (thụy hiệu vua Gia Long)
2. Long (Rồng)
3. Ba La Mật (Mít)
4. Canh (Lúa tẻ)
5. ... (còn 14 motifs khác)

**Yêu cầu:**
- `description_educational`: 200+ từ, có dẫn chứng lịch sử
- `historical_context`: Liên quan đến triều Nguyễn, năm đúc 1835-1837
- `symbolism`: Ý nghĩa trong triết học phương Đông
- `fun_fact`: Điều thú vị, có thể là so sánh với văn hóa khác
- `quiz_questions`: 3-5 câu mỗi motif, đa dạng difficulty

---

### 4.0.3 Enrich remaining 8 urns data

**Files:**
- `data/06_Data_NhanDinh.json` - Nhân Đỉnh (vua Minh Mạng)
- `data/07_Data_ChuongDinh.json` - Chương Đỉnh (vua Thiệu Trị)
- `data/08_Data_AnhDinh.json` - Anh Đỉnh
- `data/09_Data_NghiDinh.json` - Nghị Đỉnh
- `data/10_Data_ThuanDinh.json` - Thuần Đỉnh
- `data/11_Data_TuyenDinh.json` - Tuyên Đỉnh
- `data/12_Data_DuDinh.json` - Dụ Đỉnh
- `data/13_Data_HuyenDinh.json` - Huyền Đỉnh

**Tổng:** ~144 motifs còn lại

---

### 4.0.4 Review content quality

**Checklist:**
- [ ] Mỗi motif có đủ: name_en, category, rarity
- [ ] description_educational >= 200 từ
- [ ] historical_context có dẫn chứng cụ thể
- [ ] quiz_questions >= 3 câu, difficulty 1-3
- [ ] correct_answer không phải luôn là option A
- [ ] Không có lỗi chính tả tiếng Việt

---

## 🆕 Phase 5: Content Enrichment Frontend (NEW)

| # | Task | Priority | Status |
|---|------|----------|--------|
| 5.1 | Historical context section | HIGH | [ ] |
| 5.2 | Symbolism section | HIGH | [ ] |
| 5.3 | Fun fact highlight card | MEDIUM | [ ] |
| 5.4 | Quiz explanation display | HIGH | [ ] |
| 5.5 | Improved lesson page layout | MEDIUM | [ ] |

---

## 📝 NEW TASK DETAILS

### 5.1 Historical context section

**Location:** `frontend/src/app/motif/[motifId]/page.jsx`

**Add expandable section for historical_context:**
```jsx
{motif.lesson?.historical_context && (
  <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
    <button
      onClick={() => setShowHistory(!showHistory)}
      className="flex w-full items-center justify-between text-left"
    >
      <h3 className="flex items-center gap-2 font-semibold text-amber-900">
        <span>📜</span> Bối cảnh lịch sử
      </h3>
      <span className="text-amber-600">{showHistory ? '▲' : '▼'}</span>
    </button>
    {showHistory && (
      <p className="mt-3 text-sm leading-relaxed text-amber-800">
        {motif.lesson.historical_context}
      </p>
    )}
  </div>
)}
```

---

### 5.2 Symbolism section

**Location:** `frontend/src/app/motif/[motifId]/page.jsx`

**Add section for cultural symbolism:**
```jsx
{motif.lesson?.symbolism && (
  <div className="mt-6 rounded-xl border border-purple-200 bg-purple-50 p-4">
    <h3 className="flex items-center gap-2 font-semibold text-purple-900">
      <span>🔮</span> Ý nghĩa biểu tượng
    </h3>
    <p className="mt-3 text-sm leading-relaxed text-purple-800">
      {motif.lesson.symbolism}
    </p>
  </div>
)}
```

---

### 5.3 Fun fact highlight card

**Location:** `frontend/src/app/motif/[motifId]/page.jsx`

**Add visually distinct fun fact card:**
```jsx
{motif.lesson?.fun_fact && (
  <div className="mt-6 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 p-4 text-white shadow-lg">
    <h3 className="flex items-center gap-2 font-semibold">
      <span>💡</span> Bạn có biết?
    </h3>
    <p className="mt-2 text-sm leading-relaxed opacity-95">
      {motif.lesson.fun_fact}
    </p>
  </div>
)}
```

---

### 5.4 Quiz explanation display

**Location:** `frontend/src/app/motif/[motifId]/quiz/page.jsx`

**After quiz submission, show explanation for each question:**
```jsx
// In the results review section
{result.results?.map((r, idx) => (
  <div key={r.question_id} className="border-b pb-4 last:border-0">
    <div className="flex items-start gap-2">
      <span className={r.correct ? 'text-green-500' : 'text-red-500'}>
        {r.correct ? '✓' : '✗'}
      </span>
      <div className="flex-1">
        <p className="font-medium">{questions[idx]?.question_text}</p>
        <p className="mt-1 text-sm text-gray-600">
          Đáp án của bạn: <span className={r.correct ? 'text-green-600' : 'text-red-600'}>{r.user_answer || 'Bỏ qua'}</span>
        </p>
        {!r.correct && (
          <p className="mt-1 text-sm text-green-600">
            Đáp án đúng: {r.correct_answer}
          </p>
        )}
        {r.explanation && (
          <div className="mt-2 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
            <span className="font-medium">💡 Giải thích:</span> {r.explanation}
          </div>
        )}
      </div>
    </div>
  </div>
))}
```

---

### 5.5 Improved lesson page layout

**Location:** `frontend/src/app/motif/[motifId]/page.jsx`

**Restructure layout for rich content:**
```jsx
<main className="mx-auto max-w-4xl px-6 py-10">
  {/* Header with motif info */}
  <header className="mb-8">
    <div className="flex items-start gap-6">
      {/* Thumbnail */}
      <div className="h-32 w-32 flex-shrink-0 overflow-hidden rounded-xl bg-gray-100">
        {motif.thumbnail_url && (
          <img src={motif.thumbnail_url} alt={motif.name} className="h-full w-full object-cover" />
        )}
      </div>
      {/* Info */}
      <div>
        <p className="text-sm font-medium text-indigo-600">{motif.urn?.name}</p>
        <h1 className="mt-1 text-3xl font-bold text-gray-900">{motif.name}</h1>
        {motif.name_en && <p className="mt-1 text-lg text-gray-500">{motif.name_en}</p>}
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium">{motif.category}</span>
          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium">{motif.rarity}</span>
        </div>
      </div>
    </div>
  </header>

  {/* Main content sections */}
  <div className="space-y-6">
    {/* Intro */}
    {motif.lesson?.intro_text && (
      <p className="text-lg font-medium text-gray-700">{motif.lesson.intro_text}</p>
    )}

    {/* Main description */}
    <div className="prose prose-gray max-w-none">
      <p>{motif.lesson?.description}</p>
    </div>

    {/* Historical context - expandable */}
    {/* ... Task 4.1 ... */}

    {/* Symbolism */}
    {/* ... Task 4.2 ... */}

    {/* Fun fact */}
    {/* ... Task 4.3 ... */}
  </div>

  {/* Action buttons */}
  <div className="mt-8 flex gap-4">
    <button className="btn-primary">Đánh dấu đã học</button>
    <Link href={`/motif/${motif.id}/quiz`} className="btn-secondary">Làm bài kiểm tra</Link>
  </div>
</main>
```

---

## 🔧 FILES TO MODIFY

| File | Changes |
|------|---------|
| `frontend/src/app/motif/[motifId]/page.jsx` | Add content sections, improve layout |
| `frontend/src/app/motif/[motifId]/quiz/page.jsx` | Add explanation display |

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Historical context shows in expandable section
- [ ] Symbolism section displays with proper styling
- [ ] Fun fact shows as highlighted card
- [ ] Quiz results show explanation for each question
- [ ] Lesson page has improved visual hierarchy
- [ ] All sections handle missing data gracefully (don't show if null)

---

## 🚀 RUN COMMAND

```bash
cd /root/luuniensuki-lms
docker compose up -d --build web
# Visit https://lms.histolab.icu/motif/[id] to test
```

