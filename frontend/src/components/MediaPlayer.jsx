"use client";

import { useRef, useState, useEffect } from "react";
import { Play, Pause, Volume2, VolumeX, Maximize, RotateCcw } from "lucide-react";

/**
 * MediaPlayer - Audio and Video playback component for lesson content
 *
 * Features:
 * - Play/Pause controls
 * - Progress bar with seek
 * - Volume control
 * - Fullscreen for video
 * - Time display
 * - Responsive design
 */

function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// Audio Player Component
export function AudioPlayer({ src, title = "Audio", onPlay, onEnded, className = "" }) {
    const audioRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;

        const handleLoadedMetadata = () => {
            setDuration(audio.duration);
            setIsLoading(false);
        };

        const handleTimeUpdate = () => {
            setCurrentTime(audio.currentTime);
        };

        const handleEnded = () => {
            setIsPlaying(false);
            setCurrentTime(0);
            onEnded?.();
        };

        const handleError = () => {
            setError("Không thể tải audio");
            setIsLoading(false);
        };

        const handleCanPlay = () => {
            setIsLoading(false);
        };

        audio.addEventListener("loadedmetadata", handleLoadedMetadata);
        audio.addEventListener("timeupdate", handleTimeUpdate);
        audio.addEventListener("ended", handleEnded);
        audio.addEventListener("error", handleError);
        audio.addEventListener("canplay", handleCanPlay);

        return () => {
            audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
            audio.removeEventListener("timeupdate", handleTimeUpdate);
            audio.removeEventListener("ended", handleEnded);
            audio.removeEventListener("error", handleError);
            audio.removeEventListener("canplay", handleCanPlay);
        };
    }, [onEnded]);

    const togglePlay = () => {
        const audio = audioRef.current;
        if (!audio) return;

        if (isPlaying) {
            audio.pause();
        } else {
            audio.play();
            onPlay?.();
        }
        setIsPlaying(!isPlaying);
    };

    const handleSeek = (e) => {
        const audio = audioRef.current;
        if (!audio || !duration) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percent = x / rect.width;
        audio.currentTime = percent * duration;
    };

    const toggleMute = () => {
        const audio = audioRef.current;
        if (!audio) return;

        audio.muted = !isMuted;
        setIsMuted(!isMuted);
    };

    const handleVolumeChange = (e) => {
        const audio = audioRef.current;
        if (!audio) return;

        const newVolume = parseFloat(e.target.value);
        audio.volume = newVolume;
        setVolume(newVolume);
        setIsMuted(newVolume === 0);
    };

    const restart = () => {
        const audio = audioRef.current;
        if (!audio) return;
        audio.currentTime = 0;
        setCurrentTime(0);
    };

    if (!src) return null;

    if (error) {
        return (
            <div className={`rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive ${className}`}>
                {error}
            </div>
        );
    }

    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

    return (
        <div className={`rounded-xl border border-border bg-card p-4 ${className}`}>
            <audio ref={audioRef} src={src} preload="metadata" />

            {/* Title */}
            <div className="mb-3 flex items-center gap-2">
                <span className="text-lg">🎧</span>
                <span className="text-sm font-medium text-foreground">{title}</span>
                {isLoading && (
                    <span className="text-xs text-muted-foreground">Đang tải...</span>
                )}
            </div>

            {/* Progress Bar */}
            <div
                className="mb-3 h-2 cursor-pointer rounded-full bg-muted"
                onClick={handleSeek}
            >
                <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${progress}%` }}
                />
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {/* Play/Pause */}
                    <button
                        onClick={togglePlay}
                        disabled={isLoading}
                        className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground transition hover:bg-primary/90 disabled:opacity-50"
                    >
                        {isPlaying ? (
                            <Pause className="h-5 w-5" />
                        ) : (
                            <Play className="h-5 w-5 ml-0.5" />
                        )}
                    </button>

                    {/* Restart */}
                    <button
                        onClick={restart}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition hover:bg-muted hover:text-foreground"
                    >
                        <RotateCcw className="h-4 w-4" />
                    </button>

                    {/* Time */}
                    <span className="text-xs tabular-nums text-muted-foreground">
                        {formatTime(currentTime)} / {formatTime(duration)}
                    </span>
                </div>

                {/* Volume */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={toggleMute}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition hover:bg-muted hover:text-foreground"
                    >
                        {isMuted || volume === 0 ? (
                            <VolumeX className="h-4 w-4" />
                        ) : (
                            <Volume2 className="h-4 w-4" />
                        )}
                    </button>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={isMuted ? 0 : volume}
                        onChange={handleVolumeChange}
                        className="h-1 w-16 cursor-pointer accent-primary"
                    />
                </div>
            </div>
        </div>
    );
}

// Video Player Component
export function VideoPlayer({ src, poster, title = "Video", onPlay, onEnded, className = "" }) {
    const videoRef = useRef(null);
    const containerRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showControls, setShowControls] = useState(true);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        const handleLoadedMetadata = () => {
            setDuration(video.duration);
            setIsLoading(false);
        };

        const handleTimeUpdate = () => {
            setCurrentTime(video.currentTime);
        };

        const handleEnded = () => {
            setIsPlaying(false);
            setCurrentTime(0);
            onEnded?.();
        };

        const handleError = () => {
            setError("Không thể tải video");
            setIsLoading(false);
        };

        const handleCanPlay = () => {
            setIsLoading(false);
        };

        video.addEventListener("loadedmetadata", handleLoadedMetadata);
        video.addEventListener("timeupdate", handleTimeUpdate);
        video.addEventListener("ended", handleEnded);
        video.addEventListener("error", handleError);
        video.addEventListener("canplay", handleCanPlay);

        return () => {
            video.removeEventListener("loadedmetadata", handleLoadedMetadata);
            video.removeEventListener("timeupdate", handleTimeUpdate);
            video.removeEventListener("ended", handleEnded);
            video.removeEventListener("error", handleError);
            video.removeEventListener("canplay", handleCanPlay);
        };
    }, [onEnded]);

    // Hide controls after inactivity
    useEffect(() => {
        if (!isPlaying) {
            setShowControls(true);
            return;
        }

        const timer = setTimeout(() => {
            setShowControls(false);
        }, 3000);

        return () => clearTimeout(timer);
    }, [isPlaying, showControls]);

    const togglePlay = () => {
        const video = videoRef.current;
        if (!video) return;

        if (isPlaying) {
            video.pause();
        } else {
            video.play();
            onPlay?.();
        }
        setIsPlaying(!isPlaying);
    };

    const handleSeek = (e) => {
        const video = videoRef.current;
        if (!video || !duration) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percent = x / rect.width;
        video.currentTime = percent * duration;
    };

    const toggleFullscreen = () => {
        const container = containerRef.current;
        if (!container) return;

        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            container.requestFullscreen();
        }
    };

    if (!src) return null;

    if (error) {
        return (
            <div className={`rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive ${className}`}>
                {error}
            </div>
        );
    }

    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

    return (
        <div
            ref={containerRef}
            className={`relative overflow-hidden rounded-xl border border-border bg-black ${className}`}
            onMouseMove={() => setShowControls(true)}
            onMouseLeave={() => isPlaying && setShowControls(false)}
        >
            {/* Video Element */}
            <video
                ref={videoRef}
                src={src}
                poster={poster}
                preload="metadata"
                className="w-full aspect-video object-contain"
                onClick={togglePlay}
            />

            {/* Loading Overlay */}
            {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                    <div className="text-white text-sm">Đang tải...</div>
                </div>
            )}

            {/* Play Button Overlay (when paused) */}
            {!isPlaying && !isLoading && (
                <div
                    className="absolute inset-0 flex cursor-pointer items-center justify-center bg-black/30 transition hover:bg-black/40"
                    onClick={togglePlay}
                >
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/90 text-primary-foreground">
                        <Play className="h-8 w-8 ml-1" />
                    </div>
                </div>
            )}

            {/* Controls Bar */}
            <div
                className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity ${
                    showControls ? "opacity-100" : "opacity-0"
                }`}
            >
                {/* Progress Bar */}
                <div
                    className="mb-3 h-1 cursor-pointer rounded-full bg-white/30"
                    onClick={handleSeek}
                >
                    <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                {/* Controls */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        {/* Play/Pause */}
                        <button
                            onClick={togglePlay}
                            className="text-white transition hover:text-primary"
                        >
                            {isPlaying ? (
                                <Pause className="h-6 w-6" />
                            ) : (
                                <Play className="h-6 w-6" />
                            )}
                        </button>

                        {/* Time */}
                        <span className="text-xs tabular-nums text-white/80">
                            {formatTime(currentTime)} / {formatTime(duration)}
                        </span>
                    </div>

                    {/* Fullscreen */}
                    <button
                        onClick={toggleFullscreen}
                        className="text-white transition hover:text-primary"
                    >
                        <Maximize className="h-5 w-5" />
                    </button>
                </div>
            </div>

            {/* Title */}
            {title && (
                <div
                    className={`absolute left-0 right-0 top-0 bg-gradient-to-b from-black/80 to-transparent p-4 transition-opacity ${
                        showControls ? "opacity-100" : "opacity-0"
                    }`}
                >
                    <span className="text-sm font-medium text-white">{title}</span>
                </div>
            )}
        </div>
    );
}

// Image Gallery Component
export function ImageGallery({ images = [], title = "Hình ảnh bổ sung", className = "" }) {
    const [selectedIndex, setSelectedIndex] = useState(null);
    const imageCount = images?.length || 0;

    const openLightbox = (index) => {
        setSelectedIndex(index);
    };

    const closeLightbox = () => {
        setSelectedIndex(null);
    };

    const goToPrev = (e) => {
        e.stopPropagation();
        setSelectedIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    };

    const goToNext = (e) => {
        e.stopPropagation();
        setSelectedIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    };

    // Handle keyboard navigation
    useEffect(() => {
        if (selectedIndex === null || imageCount === 0) return;

        const handleKeyDown = (e) => {
            if (e.key === "Escape") closeLightbox();
            if (e.key === "ArrowLeft") setSelectedIndex((prev) => (prev === 0 ? imageCount - 1 : prev - 1));
            if (e.key === "ArrowRight") setSelectedIndex((prev) => (prev === imageCount - 1 ? 0 : prev + 1));
        };

        document.addEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "hidden";

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            document.body.style.overflow = "";
        };
    }, [selectedIndex, imageCount]);

    if (!images || imageCount === 0) return null;

    return (
        <div className={className}>
            {/* Title */}
            <div className="mb-3 flex items-center gap-2">
                <span className="text-lg">🖼️</span>
                <span className="text-sm font-medium text-foreground">{title}</span>
                <span className="text-xs text-muted-foreground">({images.length} ảnh)</span>
            </div>

            {/* Thumbnail Grid */}
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                {images.map((src, index) => (
                    <button
                        key={index}
                        onClick={() => openLightbox(index)}
                        className="group relative aspect-square overflow-hidden rounded-lg border border-border bg-muted transition hover:border-primary"
                    >
                        <img
                            src={src}
                            alt={`Hình ${index + 1}`}
                            loading="lazy"
                            decoding="async"
                            className="h-full w-full object-cover transition duration-200 group-hover:scale-[1.025]"
                        />
                        <div className="absolute inset-0 bg-black/0 transition group-hover:bg-black/20" />
                    </button>
                ))}
            </div>

            {/* Lightbox Modal */}
            {selectedIndex !== null && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90"
                    onClick={closeLightbox}
                >
                    {/* Close Button */}
                    <button
                        onClick={closeLightbox}
                        className="absolute right-4 top-4 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20"
                    >
                        ✕
                    </button>

                    {/* Navigation Buttons */}
                    {images.length > 1 && (
                        <>
                            <button
                                onClick={goToPrev}
                                className="absolute left-4 top-1/2 z-10 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-2xl text-white transition hover:bg-white/20"
                            >
                                ‹
                            </button>
                            <button
                                onClick={goToNext}
                                className="absolute right-4 top-1/2 z-10 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-2xl text-white transition hover:bg-white/20"
                            >
                                ›
                            </button>
                        </>
                    )}

                    {/* Image */}
                    <img
                        src={images[selectedIndex]}
                        alt={`Hình ${selectedIndex + 1}`}
                        className="max-h-[90vh] max-w-[90vw] object-contain"
                        onClick={(e) => e.stopPropagation()}
                    />

                    {/* Counter */}
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-black/50 px-4 py-2 text-sm text-white">
                        {selectedIndex + 1} / {images.length}
                    </div>
                </div>
            )}
        </div>
    );
}

// Combined Media Section Component
export default function MediaPlayer({
    audioUrl,
    videoUrl,
    additionalImages = [],
    audioTitle = "Bài đọc",
    videoTitle = "Video",
    onAudioPlay,
    onVideoPlay,
    className = ""
}) {
    const hasMedia = audioUrl || videoUrl || additionalImages?.length > 0;

    if (!hasMedia) return null;

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Video Player */}
            {videoUrl && (
                <VideoPlayer
                    src={videoUrl}
                    title={videoTitle}
                    onPlay={onVideoPlay}
                />
            )}

            {/* Audio Player */}
            {audioUrl && (
                <AudioPlayer
                    src={audioUrl}
                    title={audioTitle}
                    onPlay={onAudioPlay}
                />
            )}

            {/* Image Gallery */}
            {additionalImages?.length > 0 && (
                <ImageGallery images={additionalImages} />
            )}
        </div>
    );
}
