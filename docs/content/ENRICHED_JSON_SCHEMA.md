# Enriched Motif JSON Schema

> **Status:** Current / verified against `data/05..13_Data_*Dinh.json` on 2026-05-20.

This document defines the schema for the enriched motif data files (e.g., `05_Data_CaoDinh.json`, `07_Data_ChuongDinh.json`, etc.) used in the Luuniensuki LMS project.

## Root Object

The file contains an array of motif objects. Each object represents a specific motif carved on one of the Nine Urns (Cửu Đỉnh).

## Motif Object Structure

| Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `id` | String | Unique identifier for the motif. Format: `urn_<urn_name>_<index>` | `urn_chuong_dinh_01` |
| `name_vi` | String | The name of the motif in Vietnamese. | `Chương Đỉnh` |
| `name_en` | String | The name of the motif in English. | `The Urn of Radiance` |
| `urn_location` | String | The specific urn where this motif is located. | `Chương Đỉnh` |
| `category` | String | The category of the motif. | `kien_truc` |
| `rarity` | String | The rarity level of the motif (gameplay/collection context). Values: `common`, `uncommon`, `rare`, `epic`, `legendary`. | `legendary` |
| `description_short` | String | A concise description of the motif (1-2 sentences). | `Chương Đỉnh - chiếc đỉnh tượng trưng cho vẻ đẹp rực rỡ và sự văn minh của triều đại.` |
| `description_educational` | String | A detailed educational description (200+ words target) covering the nature, characteristics, and significance of the motif. | `Chương Đỉnh là chiếc đỉnh thứ ba trong Cửu Đỉnh...` |
| `historical_context` | String | Information regarding the historical relevance of the motif to the Nguyen Dynasty or Vietnamese history. | `Đúc năm 1835, Chương Đỉnh tôn vinh vua Thiệu Trị...` |
| `symbolism` | String | The symbolic meaning of the motif in culture and art. | `Tên 'Chương' gợi lên hình ảnh của ánh sáng lan tỏa...` |
| `fun_fact` | String | An interesting, lesser-known fact about the motif. | `Vua Thiệu Trị là tác giả của tập thơ 'Thần Kinh Nhị Thập Cảnh'...` |
| `is_ai_generated` | Boolean | Flag indicating if the content was generated/enriched by AI. | `true` |
| `quiz_questions` | Array | A list of quiz questions related to the motif. See [Quiz Object](#quiz-object-structure). | `[...]` |
| `3d_mesh_id` | String | Identifier for the associated 3D model asset. | `mesh_urn_chuong_dinh_01_v1` |
| `thumbnail_url` | String | Path to the thumbnail image of the motif. | `/assets/ban-duc-noi/CHƯƠNG%20DỈNH/CHƯƠNG ĐỈNH.jpg` |

### Categories

*   `kien_truc`: Architecture (Urns, Gates, Canons)
*   `thao_moc`: Plants, Flowers, Trees
*   `dong_vat`: Animals, Birds, Fish, Insects
*   `dia_ly`: Rivers, Mountains, Seas, Places
*   `vo_bi`: Weaponry, Boats, Vehicles
*   `thien_van`: Astronomy, Weather phenomena
*   `linh_thu`: Mythical Creatures

## Quiz Object Structure

| Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `type` | String | The type of question. Values: `multiple_choice`, `true_false`. | `multiple_choice` |
| `question` | String | The text of the question. | `Chương Đỉnh được dành để tôn vinh vị vua nào?` |
| `options` | Array | An array of string options for the answer. | `["A. Vua Minh Mạng", "B. Vua Thiệu Trị", ...]` |
| `correct_answer` | String | The correct option string (must match one of the options exactly). | `B. Vua Thiệu Trị` |
| `difficulty` | Integer | Difficulty level of the question (1: Easy, 2: Medium, 3: Hard). | `1` |
| `explanation` | String | Detailed explanation of why the answer is correct. | `Chương Đỉnh là đỉnh thứ ba...` |

## Example JSON

```json
{
  "id": "urn_chuong_dinh_01",
  "name_vi": "Chương Đỉnh",
  "name_en": "The Urn of Radiance",
  "urn_location": "Chương Đỉnh",
  "category": "kien_truc",
  "rarity": "legendary",
  "description_short": "Chương Đỉnh - chiếc đỉnh tượng trưng cho vẻ đẹp rực rỡ và sự văn minh của triều đại.",
  "description_educational": "Chương Đỉnh là chiếc đỉnh thứ ba trong Cửu Đỉnh...",
  "historical_context": "Đúc năm 1835, Chương Đỉnh tôn vinh vua Thiệu Trị...",
  "symbolism": "Tên 'Chương' gợi lên hình ảnh của ánh sáng lan tỏa...",
  "fun_fact": "Vua Thiệu Trị là tác giả của tập thơ 'Thần Kinh Nhị Thập Cảnh'...",
  "is_ai_generated": true,
  "quiz_questions": [
    {
      "type": "multiple_choice",
      "question": "Chương Đỉnh được dành để tôn vinh vị vua nào?",
      "options": [
        "A. Vua Minh Mạng",
        "B. Vua Thiệu Trị",
        "C. Vua Tự Đức",
        "D. Vua Khải Định"
      ],
      "correct_answer": "B. Vua Thiệu Trị",
      "difficulty": 1,
      "explanation": "Chương Đỉnh là đỉnh thứ ba..."
    }
  ],
  "3d_mesh_id": "mesh_urn_chuong_dinh_01_v1",
  "thumbnail_url": "/assets/ban-duc-noi/CHƯƠNG%20DỈNH/CHƯƠNG ĐỈNH.jpg"
}
```