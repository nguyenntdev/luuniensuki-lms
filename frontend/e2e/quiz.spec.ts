import { APIRequestContext, expect, test } from "@playwright/test";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function registerUser(request: APIRequestContext) {
  const email = `quiz-${Date.now()}@example.com`;
  const password = "password123";
  const displayName = "Quiz User";

  const response = await request.post(`${apiBaseUrl}/api/v1/auth/register`, {
    data: {
      email,
      password,
      display_name: displayName,
    },
  });

  expect(response.ok()).toBeTruthy();
  return { email, password, displayName };
}

test("should complete a quiz flow", async ({ page }) => {
  await registerUser(page.request);

  const urnsResponse = await page.request.get(`${apiBaseUrl}/api/v1/urns`);
  expect(urnsResponse.ok()).toBeTruthy();
  const urns = await urnsResponse.json();
  if (!Array.isArray(urns) || urns.length === 0) {
    test.skip(true, "No urns available for quiz test");
    return;
  }

  let selectedMotif = null;

  for (const urn of urns) {
    if (!urn?.slug) continue;
    const motifsResponse = await page.request.get(
      `${apiBaseUrl}/motifs/${encodeURIComponent(urn.slug)}`,
    );
    if (!motifsResponse.ok()) continue;
    const motifsPayload = await motifsResponse.json();
    const motifs = motifsPayload?.motifs || [];
    for (const motif of motifs) {
      const detailResponse = await page.request.get(
        `${apiBaseUrl}/api/v1/motifs/${motif.id}`,
      );
      if (!detailResponse.ok()) continue;
      const detail = await detailResponse.json();
      if ((detail?.quiz_question_count || 0) > 0) {
        selectedMotif = motif;
        break;
      }
    }
    if (selectedMotif) break;
  }

  if (!selectedMotif) {
    test.skip(true, "No motifs with quiz questions found");
    return;
  }

  await page.request.post(`${apiBaseUrl}/progress/unlock`, {
    data: {
      motif_id: selectedMotif.id,
      mesh_name: selectedMotif.mesh_name,
    },
  });

  await page.request.post(
    `${apiBaseUrl}/api/v1/motifs/${selectedMotif.id}/complete-lesson`,
  );

  const quizResponse = await page.request.get(
    `${apiBaseUrl}/api/v1/motifs/${selectedMotif.id}/quiz`,
  );
  expect(quizResponse.ok()).toBeTruthy();
  const quizPayload = await quizResponse.json();
  const questions = quizPayload?.questions || [];
  if (!questions.length) {
    test.skip(true, "Quiz questions not available after setup");
    return;
  }

  await page.goto(`/motif/${selectedMotif.id}/quiz`);
  await expect(page.getByRole("heading", { level: 2 })).toBeVisible({
    timeout: 15000,
  });

  for (let index = 0; index < questions.length; index += 1) {
    const question = questions[index];
    const card = page.locator("div.rounded-2xl.border.bg-card").first();

    if (question.question_type === "image_select") {
      await card.getByRole("button").first().click();
    } else if (question.question_type === "mesh_location") {
      const select = card.locator("select");
      if (await select.count()) {
        await select.selectOption({ index: 1 });
      } else {
        await card.locator('input[type="text"]').fill(selectedMotif.mesh_name);
      }
    } else if (
      question.question_type === "multiple_choice" ||
      question.question_type === "true_false"
    ) {
      await card.locator("label").first().click();
    } else {
      await card.locator('input[type="text"]').fill("test");
    }

    if (index < questions.length - 1) {
      await page.getByRole("button", { name: /Câu tiếp/ }).click();
    }
  }

  await page.getByRole("button", { name: "Nộp bài" }).click();
  await expect(page.getByText("Xem lại câu trả lời")).toBeVisible();
  await expect(page.getByText("Điểm:")).toBeVisible();
});
