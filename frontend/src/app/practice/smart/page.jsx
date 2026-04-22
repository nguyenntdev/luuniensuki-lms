"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { usePracticeStore } from "@/stores/practiceStore";
import { useAuthStore } from "@/stores/authStore";

export default function SmartPracticePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const {
    dueCards,
    currentCard,
    sessionResults,
    loadDueCards,
    startSession,
    submitReview,
    endSession,
    getSessionProgress,
    loading,
    error,
  } = usePracticeStore();

  const [sessionStarted, setSessionStarted] = useState(false);
  const [showAnswer, setShowAnswer] = useState(false);
  const [selectedQuality, setSelectedQuality] = useState(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    if (!sessionStarted) {
      loadDueCards(20);
    }
  }, [isAuthenticated, sessionStarted, router, loadDueCards]);

  const handleStartSession = () => {
    if (dueCards.length === 0) {
      alert("Không có thẻ nào cần ôn!");
      return;
    }
    startSession(dueCards);
    setSessionStarted(true);
  };

  const handleShowAnswer = () => {
    setShowAnswer(true);
  };

  const handleSubmitQuality = async (quality) => {
    setSelectedQuality(quality);
    
    try {
      await submitReview(quality);
      
      // Reset for next card
      setShowAnswer(false);
      setSelectedQuality(null);
      
      // Check if session is complete
      const progress = getSessionProgress();
      if (progress.remaining === 0) {
        // Session complete
        setTimeout(() => {
          router.push("/practice/results");
        }, 1000);
      }
    } catch (err) {
      console.error("Failed to submit review:", err);
      alert("Không thể gửi đánh giá. Vui lòng thử lại!");
    }
  };

  const handleEndSession = () => {
    if (confirm("Bạn có chắc muốn kết thúc phiên ôn tập?")) {
      endSession();
      router.push("/practice");
    }
  };

  if (!sessionStarted) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <div className="bg-card rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold mb-4">Ôn tập thông minh</h1>
          <p className="text-muted-foreground mb-6">
            Hệ thống sẽ tự động chọn những họa tiết cần ôn tập dựa trên lịch sử học của bạn.
          </p>

          <div className="bg-secondary border border-border rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-2">Sẵn sàng ôn tập</h2>
            <p className="text-3xl font-bold text-primary mb-2">
              {dueCards.length} thẻ
            </p>
            <p className="text-sm text-muted-foreground">
              Ước tính: {Math.ceil(dueCards.length * 0.5)} phút
            </p>
          </div>

          {error && (
            <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="flex gap-4">
            <button
              onClick={handleStartSession}
              disabled={loading || dueCards.length === 0}
              className="flex-1 bg-primary hover:bg-primary/90 disabled:bg-muted text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {loading ? "Đang tải..." : "Bắt đầu ôn tập"}
            </button>
            <button
              onClick={() => router.push("/practice")}
              className="px-6 py-3 border border-border rounded-lg hover:bg-secondary transition-colors"
            >
              Quay lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!currentCard) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold mb-2">Hoàn thành!</h2>
          <p className="text-muted-foreground">Đang chuyển đến kết quả...</p>
        </div>
      </div>
    );
  }

  const progress = getSessionProgress();
  const progressPercent = (progress.completed / progress.total) * 100;

  return (
    <div className="min-h-screen bg-background">
      {/* Progress bar */}
      <div className="bg-card shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">
              {progress.completed} / {progress.total}
            </span>
            <button
              onClick={handleEndSession}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Kết thúc
            </button>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Review Card */}
      <div className="container mx-auto px-6 py-8 max-w-3xl">
        <div className="bg-card rounded-lg shadow-lg p-8">
          {/* Motif Information */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">
              {currentCard.motif?.title || "Họa tiết"}
            </h2>

            {currentCard.motif?.image_url && (
              <div className="mb-6">
                <img
                  src={currentCard.motif.image_url}
                  alt={currentCard.motif.title}
                  className="w-full max-h-96 object-contain rounded-lg"
                />
              </div>
            )}

            <div className="text-sm text-muted-foreground mb-4">
              <p>Danh mục: {currentCard.motif?.category || "Không rõ"}</p>
              <p>Lần ôn: {currentCard.repetitions + 1}</p>
            </div>
          </div>

          {/* Review Actions */}
          {!showAnswer ? (
            <div>
              <p className="text-lg mb-6">
                Bạn có nhớ ý nghĩa và đặc điểm của họa tiết này không?
              </p>
              <button
                onClick={handleShowAnswer}
                className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-4 px-6 rounded-lg text-lg"
              >
                Hiển thị đáp án
              </button>
            </div>
          ) : (
            <div>
              {currentCard.motif?.description && (
                <div className="mb-6 p-4 bg-secondary rounded-lg">
                  <h3 className="font-semibold mb-2">Mô tả:</h3>
                  <p className="text-foreground">
                    {currentCard.motif.description}
                  </p>
                </div>
              )}

              <p className="text-lg font-semibold mb-4">Bạn nhớ như thế nào?</p>

              <div className="space-y-3">
                <QualityButton
                  quality={5}
                  label="Hoàn hảo"
                  description="Nhớ rất rõ, trả lời ngay lập tức"
                  color="bg-success hover:bg-success/90"
                  onClick={handleSubmitQuality}
                  disabled={loading}
                  selected={selectedQuality === 5}
                />
                <QualityButton
                  quality={4}
                  label="Tốt"
                  description="Nhớ rõ sau khi nghĩ một chút"
                  color="bg-info hover:bg-info/90"
                  onClick={handleSubmitQuality}
                  disabled={loading}
                  selected={selectedQuality === 4}
                />
                <QualityButton
                  quality={3}
                  label="Được"
                  description="Nhớ được nhưng khó khăn"
                  color="bg-primary hover:bg-primary/90"
                  onClick={handleSubmitQuality}
                  disabled={loading}
                  selected={selectedQuality === 3}
                />
                <QualityButton
                  quality={2}
                  label="Khó"
                  description="Sai nhưng khi xem lại thì dễ nhớ"
                  color="bg-bronze hover:bg-bronze/90"
                  onClick={handleSubmitQuality}
                  disabled={loading}
                  selected={selectedQuality === 2}
                />
                <QualityButton
                  quality={1}
                  label="Rất khó"
                  description="Sai và khó nhớ lại"
                  color="bg-destructive hover:bg-destructive/90"
                  onClick={handleSubmitQuality}
                  disabled={loading}
                  selected={selectedQuality === 1}
                />
                <QualityButton
                  quality={0}
                  label="Không nhớ"
                  description="Hoàn toàn quên"
                  color="bg-muted-foreground hover:bg-muted-foreground/90"
                  onClick={handleSubmitQuality}
                  disabled={loading}
                  selected={selectedQuality === 0}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QualityButton({ quality, label, description, color, onClick, disabled, selected }) {
  return (
    <button
      onClick={() => onClick(quality)}
      disabled={disabled}
      className={`w-full ${color} ${selected ? "ring-4 ring-background" : ""} text-white p-4 rounded-lg text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold">{label}</p>
          <p className="text-sm opacity-90">{description}</p>
        </div>
        {selected && (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        )}
      </div>
    </button>
  );
}


