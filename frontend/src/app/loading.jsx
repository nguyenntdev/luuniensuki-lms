export default function Loading() {
  return (
    <div className="grid min-h-[60vh] place-items-center" role="status" aria-live="polite">
      <div className="flex flex-col items-center gap-3">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary border-r-transparent" />
        <span className="text-sm text-muted-foreground">Đang tải…</span>
      </div>
    </div>
  );
}
