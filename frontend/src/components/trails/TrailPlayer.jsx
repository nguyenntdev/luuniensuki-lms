"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  completeTrailStep,
  getTrailDetail,
  setTrailPace,
  startTrail,
  submitTrailCheckpoint,
} from "@/lib/api";

const PACE_OPTIONS = [
  { value: "daily", label: "Hàng ngày" },
  { value: "2x_week", label: "2 lần/tuần" },
  { value: "weekly", label: "Hàng tuần" },
];

export default function TrailPlayer({ slug }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // active step UI state
  const [currentMotif, setCurrentMotif] = useState(null);
  const [pendingCheckpoint, setPendingCheckpoint] = useState(null);
  const [completion, setCompletion] = useState(null);
  const [busy, setBusy] = useState(false);
  const [pace, setPace] = useState("daily");

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTrailDetail(slug);
      setDetail(data);
      if (data?.progress?.pace) setPace(data.progress.pace);
      if (data?.progress?.completed_at) {
        setCompletion({
          outro: data.trail.narrator_outro,
          certificate_hash: null,
          certificate_url: null,
        });
      }
    } catch (err) {
      setError(err?.message || "Không tải được lộ trình");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    reload();
  }, [reload]);

  async function handleStart() {
    setBusy(true);
    try {
      const res = await startTrail(slug);
      if (res?.first_motif) {
        setCurrentMotif(res.first_motif);
      } else {
        // Server returned no motif — likely the trail has zero published
        // steps despite being marked published. Surface a clear error.
        setError(
          "Lộ trình này chưa có bước nào — vui lòng liên hệ admin.",
        );
      }
      if (res?.progress?.pace) setPace(res.progress.pace);
      // refresh detail to update step counts
      const data = await getTrailDetail(slug);
      setDetail(data);
    } catch (err) {
      setError(err?.message || "Không thể bắt đầu lộ trình");
    } finally {
      setBusy(false);
    }
  }

  async function handleComplete(position) {
    setBusy(true);
    try {
      const res = await completeTrailStep(slug, position);
      handleStepResponse(res);
    } catch (err) {
      setError(err?.message || "Không thể hoàn thành bước này");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmitCheckpoint(text) {
    if (!pendingCheckpoint) return;
    setBusy(true);
    try {
      const res = await submitTrailCheckpoint(
        slug,
        pendingCheckpoint.after_position,
        text,
      );
      setPendingCheckpoint(null);
      if (res?.next) handleStepResponse(res.next);
    } catch (err) {
      setError(err?.message || "Không gửi được phản hồi");
    } finally {
      setBusy(false);
    }
  }

  function handleStepResponse(res) {
    if (!res || !res.type) return;
    if (res.type === "next_motif") {
      setCurrentMotif(res.motif);
      setPendingCheckpoint(null);
    } else if (res.type === "checkpoint") {
      setPendingCheckpoint(res);
    } else if (res.type === "completed") {
      setCompletion(res);
      setCurrentMotif(null);
      setPendingCheckpoint(null);
      reload();
    }
  }

  async function handlePaceChange(value) {
    if (!detail?.trail?.id) return;
    setPace(value);
    try {
      await setTrailPace(detail.trail.id, value);
    } catch {
      // best-effort: revert UI on next reload
    }
  }

  if (loading) {
    return (
      <div className="px-6 py-12 text-sm text-muted-foreground" role="status">
        Đang tải lộ trình…
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="px-6 py-12 text-sm text-destructive"
        role="alert"
        aria-live="assertive"
      >
        {error}
      </div>
    );
  }

  if (!detail) return null;

  const { trail, progress } = detail;
  const started = !!progress?.started_at;
  const completed = !!progress?.completed_at;

  return (
    <div className="px-6 py-8">
      <Link
        href="/trails"
        className="text-sm text-muted-foreground hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        ← Tất cả lộ trình
      </Link>

      <header className="mt-3">
        <h1 id="trail-heading" className="text-3xl font-bold tracking-tight">
          {trail.title_vi}
        </h1>
        <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
          {trail.difficulty} · {trail.estimated_minutes} phút ·{" "}
          {trail.step_count} bước · {trail.checkpoint_count} điểm suy ngẫm
        </p>
        {trail.description_vi ? (
          <p className="mt-3 max-w-2xl text-sm text-muted-foreground">
            {trail.description_vi}
          </p>
        ) : null}
      </header>

      {trail.narrator_intro && !started ? (
        <section className="mt-6 rounded-lg border border-border bg-card p-5 italic">
          <p>{trail.narrator_intro}</p>
        </section>
      ) : null}

      {!started ? (
        <button
          type="button"
          disabled={busy}
          onClick={handleStart}
          className="mt-6 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          {busy ? "Đang xử lý…" : "Bắt đầu lộ trình"}
        </button>
      ) : null}

      {started && !completed ? (
        <PaceSelector value={pace} onChange={handlePaceChange} />
      ) : null}

      {pendingCheckpoint ? (
        <CheckpointDialog
          checkpoint={pendingCheckpoint}
          busy={busy}
          onSubmit={handleSubmitCheckpoint}
        />
      ) : null}

      {currentMotif ? (
        <section
          className="mt-6 rounded-lg border border-border bg-card p-5"
          aria-labelledby="step-heading"
        >
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Bước {currentMotif.position} / {trail.step_count}
          </p>
          <h2 id="step-heading" className="mt-1 text-xl font-bold">
            {currentMotif.motif_name || "Hoạ tiết"}
          </h2>
          {currentMotif.description ? (
            <p className="mt-3 text-sm text-muted-foreground">
              {currentMotif.description}
            </p>
          ) : null}
          <button
            type="button"
            disabled={busy}
            onClick={() => handleComplete(currentMotif.position)}
            className="mt-5 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Hoàn thành bước này
          </button>
        </section>
      ) : null}

      {!currentMotif && started && !completion && progress?.current_position ? (
        <section className="mt-6 rounded-lg border border-border bg-card p-5">
          <p className="text-sm text-muted-foreground">
            Bạn đang ở bước {progress.current_position}.
          </p>
          <button
            type="button"
            disabled={busy}
            onClick={() => handleComplete(progress.current_position)}
            className="mt-3 rounded-md border border-border px-4 py-2 text-sm hover:bg-muted disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Tiếp tục
          </button>
        </section>
      ) : null}

      {completion ? <CompletionPanel completion={completion} trail={trail} /> : null}
    </div>
  );
}

function PaceSelector({ value, onChange }) {
  return (
    <fieldset className="mt-6 rounded-lg border border-border bg-card p-4">
      <legend className="px-1 text-sm font-semibold">Nhịp học</legend>
      <div className="flex flex-wrap gap-3">
        {PACE_OPTIONS.map((opt) => (
          <label
            key={opt.value}
            className={`cursor-pointer rounded-md border px-3 py-1.5 text-sm transition ${
              value === opt.value
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border hover:bg-muted"
            }`}
          >
            <input
              type="radio"
              name="pace"
              value={opt.value}
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
              className="sr-only"
            />
            {opt.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function CheckpointDialog({ checkpoint, busy, onSubmit }) {
  const [text, setText] = useState("");
  const ref = useRef(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  return (
    <section
      className="mt-6 rounded-lg border-2 border-primary bg-card p-5"
      role="dialog"
      aria-labelledby="checkpoint-heading"
      aria-modal="false"
    >
      <h2
        id="checkpoint-heading"
        className="text-lg font-semibold tracking-tight"
      >
        Điểm suy ngẫm
      </h2>
      <p className="mt-2 text-sm">{checkpoint.prompt_vi}</p>
      <textarea
        ref={ref}
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
        className="mt-3 w-full rounded-md border border-border bg-background p-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        placeholder="Ghi lại suy nghĩ của bạn…"
      />
      <button
        type="button"
        disabled={busy || !text.trim()}
        onClick={() => onSubmit(text.trim())}
        className="mt-3 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-60"
      >
        Tiếp tục
      </button>
    </section>
  );
}

function CompletionPanel({ completion, trail }) {
  return (
    <section
      className="mt-6 rounded-lg border-2 border-primary bg-card p-6"
      role="status"
      aria-live="polite"
    >
      <h2 className="text-2xl font-bold tracking-tight">Đã hoàn thành!</h2>
      {completion.outro ? (
        <p className="mt-2 italic">{completion.outro}</p>
      ) : trail.narrator_outro ? (
        <p className="mt-2 italic">{trail.narrator_outro}</p>
      ) : null}
      {completion.certificate_url ? (
        <a
          href={completion.certificate_url}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-block rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90"
        >
          Tải chứng chỉ
        </a>
      ) : null}
      {completion.certificate_hash ? (
        <p className="mt-3 text-xs text-muted-foreground">
          Mã xác thực: {completion.certificate_hash}
        </p>
      ) : null}
    </section>
  );
}
