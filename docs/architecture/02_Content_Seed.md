# 02_Content_Seed.md

## Overview
**Role:** Content Director & Cultural Researcher
**Context:** Seed data for the "Luuniensuki" LMS Gamification Layer.
**Focus:** Thematic Quest "The Royal Gardens" (Cây cỏ) based on the Nine Urns (Cửu Đỉnh) of the Nguyen Dynasty.

---

## 1. Quest Definition: The Royal Gardens
**Quest Name:** Ngự Uyển Ký Sự (Chronicles of the Royal Gardens)
**Theme:** Flowers, Trees, and Plants carved on the Nine Urns.
**Objective:** Discover and catalog the flora represented on the dynastic urns to understand their symbolic meaning regarding prosperity, longevity, and the geography of Vietnam.

---

## 2. Seed Data (JSON)
The following JSON array contains sample motifs for the "Royal Gardens" quest.

```json
[
  {
    "id": "motif_flowers_001",
    "name_vi": "Hoa Sen",
    "name_en": "Lotus",
    "urn_location": "Cao Đỉnh",
    "description_short": "The supreme flower symbolizing purity and spiritual elevation, rising unblemished from the mud.",
    "description_educational": "In Hue culture and Vietnamese philosophy, the Lotus (Hoa Sen) is not just a flower but a mirror of the human spirit. Carved on the Cao Đỉnh (the highest of the urns), it represents the nobility of the soul, Buddhist enlightenment, and the capacity to remain pure amidst worldly impurities. It is the emblem of summer and spiritual awakening.",
    "quiz_question": {
      "question": "In the context of the Nguyen Dynasty's symbolism, what does the Lotus primarily represent?",
      "options": [
        "A. Military Strength",
        "B. Purity and Enlightenment",
        "C. Commercial Prosperity",
        "D. Autumn Harvest"
      ],
      "correct_answer": "B. Purity and Enlightenment"
    },
    "3d_mesh_id": "mesh_urn_cao_lotus_v1"
  },
  {
    "id": "motif_trees_002",
    "name_vi": "Cây Tùng",
    "name_en": "Pine Tree (Cypress)",
    "urn_location": "Nhân Đỉnh",
    "description_short": "A symbol of the resilient gentleman who stands tall and green even in the harshest winter.",
    "description_educational": "The Tùng tree is a classic symbol in the 'Four Gentlemen' (Tùng, Cúc, Trúc, Mai) motif. Placing it on the Nhân Đỉnh (Urn of Benevolence) emphasizes the Confucian ideal of a virtuous leader: one who possesses endurance, longevity, and moral integrity that does not wither under pressure, much like the pine remains green in winter.",
    "quiz_question": {
      "question": "Which season is the Tùng tree traditionally associated with in the 'Four Seasons' quartet?",
      "options": [
        "A. Spring",
        "B. Summer",
        "C. Autumn",
        "D. Winter"
      ],
      "correct_answer": "D. Winter"
    },
    "3d_mesh_id": "mesh_urn_nhan_pine_v1"
  },
  {
    "id": "motif_trees_003",
    "name_vi": "Cây Thông",
    "name_en": "Pine Tree (Pinus)",
    "urn_location": "Tuyên Đỉnh",
    "description_short": "The whistling pine representing vitality and the enduring nature of the dynasty.",
    "description_educational": "While similar to the Tùng, the Thông (Pinus) specifically carved on the Tuyên Đỉnh represents the rugged, natural vitality of Vietnam's forests. It symbolizes righteousness and the wish for the dynasty to last ten thousand generations, rooted deeply in the land like the ancient pines of the imperial capital.",
    "quiz_question": {
      "question": "On which Urn can you find the specific carving of the 'Cây Thông'?",
      "options": [
        "A. Cao Đỉnh",
        "B. Tuyên Đỉnh",
        "C. Dụ Đỉnh",
        "D. Huyền Đỉnh"
      ],
      "correct_answer": "B. Tuyên Đỉnh"
    },
    "3d_mesh_id": "mesh_urn_tuyen_pinus_v1"
  }
]
```

---

## 3. Gamification Assets: Ranks
As users discover more motifs within "The Royal Gardens" quest, they unlock specific titles reflecting their knowledge level.

| Rank Level | Title (Vietnamese) | Title (English) | Requirement |
| :--- | :--- | :--- | :--- |
| **Novice** | **Người Làm Vườn** | **Apprentice Gardener** | Scan 1 plant motif. |
| **Intermediate** | **Giám Sát Ngự Uyển** | **Royal Garden Supervisor** | Scan 5 plant motifs & pass 3 quizzes. |
| **Master** | **Thượng Lâm Lệnh** | **Grand Commissioner of Parks** | Complete the entire "Royal Gardens" collection (All floral motifs). |
