/**
 * STTTNNĐ Spec STTT-SPEC-AUDIO-PASSPORT-002
 * Audio Types & Interfaces for Heritage Audio Guide & Transcript Sync
 */

export interface TimedTranscriptCue {
  id: string;
  startTime: number; // in seconds
  endTime: number; // in seconds
  textVi: string;
  textEn?: string;
  speaker?: string; // e.g. "Thuyết minh viên", "Sử quan"
  sectionTitle?: string;
}

export interface AudioGuideTrack {
  id: string;
  siteSlug: string;
  siteNameVi: string;
  siteNameHanNom?: string;
  titleVi: string;
  titleEn?: string;
  narrator: string;
  duration: number; // in seconds
  audioUrl: string;
  transcript: TimedTranscriptCue[];
  historicalPeriod?: string;
  summary?: string;
  tags?: string[];
  coverImage?: string;
  soundscapeDesc?: string;
}

export type PlaybackRate = 0.75 | 1.0 | 1.25 | 1.5;

export interface AudioPlayerState {
  currentTrack: AudioGuideTrack | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  playbackRate: PlaybackRate;
  volume: number; // 0 to 1
  isMuted: boolean;
  isLoading: boolean;
  isMinimized: boolean;
  isDrawerOpen: boolean;
  activeCueId: string | null;
}

export interface AudioPlayerActions {
  playTrack: (track: AudioGuideTrack, autoPlay?: boolean) => void;
  playSite: (siteSlug: string, autoPlay?: boolean) => Promise<boolean>;
  togglePlayPause: () => void;
  pause: () => void;
  resume: () => void;
  seekTo: (seconds: number) => void;
  skipTime: (deltaSeconds: number) => void;
  setPlaybackRate: (rate: PlaybackRate) => void;
  cyclePlaybackRate: () => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  setMinimized: (minimized: boolean) => void;
  toggleMinimized: () => void;
  setDrawerOpen: (open: boolean) => void;
  toggleDrawer: () => void;
  closePlayer: () => void;
  updateTime: (currentTime: number, duration?: number) => void;
  setIsLoading: (loading: boolean) => void;
  setIsPlaying: (isPlaying: boolean) => void;
}

export type AudioPlayerStore = AudioPlayerState & AudioPlayerActions;
