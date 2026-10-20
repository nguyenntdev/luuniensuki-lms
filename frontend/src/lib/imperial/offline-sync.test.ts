import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import {
  enqueueOfflineSubmission,
  getPendingSubmissions,
  clearPendingSubmission,
  clearAllPendingSubmissions,
  subscribeOfflineSync,
  syncOfflineQueue,
  initOfflineSyncListener,
} from "./offline-sync";

describe("Offline Sync & IndexedDB Engine (offline-sync.ts)", () => {
  let mockStorage: Record<string, string> = {};

  beforeEach(async () => {
    mockStorage = {};
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => mockStorage[key] ?? null,
      setItem: (key: string, value: string) => {
        mockStorage[key] = value;
      },
      removeItem: (key: string) => {
        delete mockStorage[key];
      },
      clear: () => {
        mockStorage = {};
      },
    });
  });

  afterEach(async () => {
    vi.restoreAllMocks();
  });

  it("enqueues a student submission into the offline queue", async () => {
    const testSubmission = {
      monument_slug: "ngo-mon",
      monument_name_vi: "Ngọ Môn",
      student_id: "stu-test-1",
      student_name: "Lê Minh Trí",
      student_class: "11 Sử",
      claim: "Ngọ Môn là biểu tượng uy quyền tối cao của vương triều Nguyễn.",
      evidence: "Trích Khâm Định Đại Nam Hội Điển Sự Lệ.",
      evidence_citations: ["Hội Điển Sự Lệ"],
      explanation: "Kiến trúc năm cửa thể hiện tôn ti trật tự phong kiến nghiêm ngặt.",
    };

    const queued = await enqueueOfflineSubmission(testSubmission);
    expect(queued).toBeDefined();
    expect(queued.id).toMatch(/^queue-/);
    expect(queued.submission.monument_slug).toBe("ngo-mon");
    expect(queued.retry_count).toBe(0);
    expect(queued.enqueued_at).toBeDefined();

    const pending = await getPendingSubmissions();
    expect(pending.length).toBeGreaterThanOrEqual(1);
    const found = pending.find((p) => p.id === queued.id);
    expect(found).toBeDefined();
    expect(found?.submission.claim).toBe(testSubmission.claim);
  });

  it("clears a pending submission by id", async () => {
    const item = await enqueueOfflineSubmission({
      monument_slug: "dien-thai-hoa",
      student_id: "stu-test-2",
      student_name: "Hoàng Oanh",
      student_class: "10 Văn",
      claim: "Mệnh đề thử nghiệm",
      evidence: "Bằng chứng",
      evidence_citations: [],
      explanation: "Diễn giải",
    });

    const beforeClear = await getPendingSubmissions();
    expect(beforeClear.some((p) => p.id === item.id)).toBe(true);

    await clearPendingSubmission(item.id);

    const afterClear = await getPendingSubmissions();
    expect(afterClear.some((p) => p.id === item.id)).toBe(false);
  });

  it("subscribes to offline sync status events", async () => {
    const events: any[] = [];
    const unsubscribe = subscribeOfflineSync((ev) => {
      events.push(ev);
    });

    expect(typeof unsubscribe).toBe("function");

    await enqueueOfflineSubmission({
      monument_slug: "the-to-mieu",
      student_id: "stu-test-3",
      student_name: "Quốc Dũng",
      student_class: "12 Sử",
      claim: "Thế Tổ Miếu tuân thủ Tả Chiêu Hữu Mục",
      evidence: "Bài vị các vị hoàng đế",
      evidence_citations: [],
      explanation: "Trật tự thờ tự",
    });

    expect(events.length).toBeGreaterThanOrEqual(1);
    const lastEvent = events[events.length - 1];
    expect(lastEvent.type).toBe("sync_start");
    expect(lastEvent.pendingCount).toBeGreaterThan(0);

    unsubscribe();
  });

  it("syncOfflineQueue sends pending items and removes successful ones", async () => {
    await clearAllPendingSubmissions();

    const item = await enqueueOfflineSubmission({
      monument_slug: "cung-dien-tho",
      student_id: "stu-test-4",
      student_name: "Thanh Nga",
      student_class: "11 Văn",
      claim: "Cung Diên Thọ có vi khí hậu mát mẻ",
      evidence: "Hồ sen và cây cổ thụ",
      evidence_citations: [],
      explanation: "Kiến trúc sinh thái",
    });

    // Mock global fetch
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ success: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const syncResult = await syncOfflineQueue("/api/v1/imperial/submissions");
    expect(syncResult.syncedCount).toBe(1);
    expect(syncResult.errorsCount).toBe(0);

    const pending = await getPendingSubmissions();
    expect(pending.some((p) => p.id === item.id)).toBe(false);
  });

  it("handles offline sync server errors gracefully by keeping item in queue", async () => {
    await clearAllPendingSubmissions();

    const item = await enqueueOfflineSubmission({
      monument_slug: "dien-kien-trung",
      student_id: "stu-test-5",
      student_name: "Bảo Long",
      student_class: "12 A1",
      claim: "Kiến trúc Đông Dương tân cổ điển",
      evidence: "Sành sứ đắp nổi",
      evidence_citations: [],
      explanation: "Tiếp biến văn hóa",
    });

    // Mock fetch error
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network connection lost")));

    const syncResult = await syncOfflineQueue("/api/v1/imperial/submissions");
    expect(syncResult.syncedCount).toBe(0);
    expect(syncResult.errorsCount).toBe(1);

    const pending = await getPendingSubmissions();
    const stillPending = pending.find((p) => p.id === item.id);
    expect(stillPending).toBeDefined();
    expect(stillPending?.retry_count).toBeGreaterThan(0);
  });
});
