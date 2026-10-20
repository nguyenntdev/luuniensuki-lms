"use client";

/**
 * RoyalSealStamp.tsx — Authentic Imperial Royal Seal SVG Vector Art & Stamping Engine.
 * SPEC ID: STTT-SPEC-AUDIO-PASSPORT-002 (§3.1)
 *
 * Renders Nguyen Dynasty imperial seal craft (Ấn triện son Hoàng triều) for all 16 Đại Nội monuments:
 * - Double-bordered square, circular, octagonal, or arched frames with imperial cloud/fire/wave motifs.
 * - Authentic Sino-Vietnamese Han-Nom seal script characters and Quốc ngữ seal inscription.
 * - High-fidelity historical monument iconography.
 * - Three visual states:
 *     - 'locked': Faint slate outline (opacity-30, grayscale, watermark on dó paper).
 *     - 'unlocked': Rich cinnabar vermilion ink (#A62B2B) with gold patina texture and realistic tilt.
 *     - 'stamping': Dynamic stamp-down impact animation, ink splatter burst, and synthetic sound effect.
 */

import React, { useEffect, useId, useState } from "react";
import {
  type MonumentSeal,
  type SealBorderPattern,
  type SealShape,
  type SealStatus,
  type SealMotifType,
  getMonumentSeal,
  getZoneRoyalSeal,
  getGrandRoyalSeal,
} from "@/lib/imperial/passport-types";
import {
  playRoyalSealSound,
  playRoyalGongChime,
  playZoneCompletionSound,
} from "@/lib/imperial/seal-audio";

export interface RoyalSealStampProps {
  /** Monument slug (e.g., "ngo-mon", "dien-thai-hoa") or full seal definition */
  monumentSlug?: string;
  /** Spatial zone slug for completed zone royal seal (e.g. "central-ceremonial-axis") */
  zoneSlug?: string;
  /** Whether this renders the Grand Imperial Seal of completion (Đại Kim Bảo) */
  isGrandSeal?: boolean;
  seal?: MonumentSeal;
  /** Current state of the seal */
  status?: SealStatus;
  /** Dimension size in pixels or standard presets */
  size?: "sm" | "md" | "lg" | "xl" | number;
  /** Custom slight rotation in degrees (-3.0 to +3.0) */
  rotationAngle?: number;
  /** Whether the seal can be clicked to trigger a stamping animation or preview */
  interactive?: boolean;
  /** Whether to play synthetic audio thump when stamping (default: true) */
  playSoundEffect?: boolean;
  /** Display Quốc ngữ seal text label beneath or beside the stamp */
  showLabel?: boolean;
  /** Display date or era caption */
  showDate?: boolean;
  /** Callback when stamping animation completes */
  onStampingComplete?: (seal: MonumentSeal) => void;
  /** Generic click handler */
  onClick?: (seal: MonumentSeal) => void;
  /** Additional CSS class names */
  className?: string;
}

const SIZE_MAP: Record<string, number> = {
  sm: 76,
  md: 124,
  lg: 176,
  xl: 232,
};

export const RoyalSealStamp: React.FC<RoyalSealStampProps> = ({
  monumentSlug,
  zoneSlug,
  isGrandSeal = false,
  seal: propSeal,
  status: propStatus,
  size = "md",
  rotationAngle,
  interactive = false,
  playSoundEffect = true,
  showLabel = false,
  showDate = false,
  onStampingComplete,
  onClick,
  className = "",
}) => {
  // Resolve seal definition (supports monument, zone royal seal, or grand imperial seal)
  const resolvedSeal =
    propSeal ||
    (isGrandSeal ? getGrandRoyalSeal() : undefined) ||
    (zoneSlug ? getZoneRoyalSeal(zoneSlug) : undefined) ||
    (monumentSlug ? getMonumentSeal(monumentSlug) : undefined);

  // State management for dynamic stamping
  const currentStatus: SealStatus = propStatus || resolvedSeal?.status || "locked";
  const [internalStatus, setInternalStatus] = useState<SealStatus>(currentStatus);
  const [isAnimatingSplatter, setIsAnimatingSplatter] = useState(false);
  const filterId = useId().replace(/[:]/g, "_");

  // Sync internal state with props
  useEffect(() => {
    setInternalStatus(currentStatus);
  }, [currentStatus]);

  // Handle stamping animation lifecycle and audio trigger
  useEffect(() => {
    if (internalStatus === "stamping") {
      setIsAnimatingSplatter(true);
      if (playSoundEffect) {
        const isZoneOrGrand =
          resolvedSeal?.sealCategory === "zone_royal" ||
          resolvedSeal?.sealCategory === "grand_royal";
        const material =
          resolvedSeal?.material ||
          (resolvedSeal?.motif === "kim_bao"
            ? "gold"
            : resolvedSeal?.motif === "ngu_ty"
              ? "jade"
              : resolvedSeal?.shape === "square"
                ? "stone"
                : "wood");

        if (isZoneOrGrand) {
          playZoneCompletionSound(resolvedSeal?.motif === "ngu_ty" ? "ngu_ty" : "kim_bao").catch(
            () => {},
          );
        } else {
          playRoyalSealSound({
            volume: 0.9,
            material,
          }).catch(() => {});
        }
      }

      const timer = setTimeout(() => {
        setInternalStatus("unlocked");
        setIsAnimatingSplatter(false);
        if (resolvedSeal && onStampingComplete) {
          onStampingComplete(resolvedSeal);
        }
      }, 700);

      return () => clearTimeout(timer);
    }
  }, [internalStatus, playSoundEffect, resolvedSeal, onStampingComplete]);

  if (!resolvedSeal) {
    return (
      <div className={`flex items-center justify-center p-3 text-xs text-stone-400 ${className}`}>
        [Thiếu ấn triện]
      </div>
    );
  }

  // Size calculations
  const dimension = typeof size === "number" ? size : SIZE_MAP[size] || 124;
  const tilt =
    rotationAngle !== undefined
      ? rotationAngle
      : internalStatus === "locked"
        ? 0
        : resolvedSeal.defaultTiltAngle;

  const isLocked = internalStatus === "locked";
  const isStamping = internalStatus === "stamping";
  const isUnlocked = internalStatus === "unlocked";

  const handleInteraction = () => {
    if (!interactive) return;
    if (onClick) {
      onClick(resolvedSeal);
    }
    if (internalStatus === "locked") {
      setInternalStatus("stamping");
    }
  };

  return (
    <div
      className={`royal-seal-container inline-flex flex-col items-center justify-center select-none ${className}`}
      style={{ width: dimension }}
    >
      <div
        className={`relative flex items-center justify-center transition-transform duration-300 ${
          interactive ? "cursor-pointer hover:scale-105 active:scale-95" : ""
        } ${isStamping ? "animate-seal-slam" : ""}`}
        style={{
          width: dimension,
          height: dimension,
          transform: `rotate(${tilt}deg)`,
        }}
        onClick={handleInteraction}
        role={interactive ? "button" : "img"}
        tabIndex={interactive ? 0 : undefined}
        onKeyDown={(e) => {
          if (interactive && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            handleInteraction();
          }
        }}
        aria-label={`Ấn triện son: ${resolvedSeal.sealTextQuocNgu} - Di tích ${
          resolvedSeal.monumentNameVi
        } (${isUnlocked ? "Đã đóng dấu" : isStamping ? "Đang đóng dấu" : "Chưa mở khóa"})`}
      >
        {/* Ink Splatter Ring on Stamp Impact */}
        {isAnimatingSplatter && (
          <div
            className="absolute inset-0 pointer-events-none z-10 flex items-center justify-center animate-splatter-burst"
            aria-hidden="true"
          >
            <svg
              viewBox="0 0 200 200"
              className="w-[140%] h-[140%] max-w-none text-[#A62B2B]"
              fill="currentColor"
            >
              {/* Radial ink splatter droplets */}
              <circle cx="25" cy="40" r="3" opacity="0.8" />
              <circle cx="15" cy="55" r="1.5" opacity="0.6" />
              <circle cx="180" cy="35" r="2.8" opacity="0.85" />
              <circle cx="192" cy="50" r="1.8" opacity="0.7" />
              <circle cx="175" cy="165" r="3.2" opacity="0.8" />
              <circle cx="188" cy="150" r="2" opacity="0.6" />
              <circle cx="28" cy="160" r="2.5" opacity="0.75" />
              <circle cx="15" cy="140" r="1.8" opacity="0.5" />
              <circle cx="100" cy="12" r="3.5" opacity="0.85" />
              <circle cx="100" cy="190" r="3" opacity="0.8" />
              <circle cx="12" cy="100" r="2.4" opacity="0.7" />
              <circle cx="190" cy="102" r="2.6" opacity="0.75" />
              {/* Ink shockwave ring */}
              <circle
                cx="100"
                cy="100"
                r="88"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeDasharray="4 8"
                opacity="0.5"
              />
            </svg>
          </div>
        )}

        {/* Master SVG Vector Stamp */}
        <svg
          viewBox="0 0 240 240"
          className="w-full h-full overflow-visible drop-shadow-sm transition-all duration-300"
          style={{
            filter: isLocked
              ? "grayscale(100%) opacity(0.32)"
              : isStamping
                ? "url(#stamp-filter-" + filterId + ") brightness(1.15)"
                : "url(#stamp-filter-" + filterId + ")",
          }}
        >
          <defs>
            {/* Ink bleed and paper roughness texture filter */}
            <filter id={`stamp-filter-${filterId}`} x="-10%" y="-10%" width="120%" height="120%">
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.04"
                numOctaves="3"
                result="paperNoise"
              />
              <feDisplacementMap
                in="SourceGraphic"
                in2="paperNoise"
                scale={isLocked ? "0" : "1.8"}
                xChannelSelector="R"
                yChannelSelector="G"
                result="displaced"
              />
              {/* Subtle gold patina sheen for authentic vermilion imperial seal */}
              {resolvedSeal.goldPatina && !isLocked && (
                <feColorMatrix
                  type="matrix"
                  values="
                    1.02 0.00 0.00 0 0.02
                    0.00 0.98 0.00 0 0.01
                    0.00 0.00 0.95 0 0.00
                    0.00 0.00 0.00 1 0.00
                  "
                />
              )}
            </filter>

            {/* Circular Path for curved Quốc ngữ seal text */}
            <path
              id={`circle-text-path-top-${filterId}`}
              d="M 38,120 A 82,82 0 1,1 202,120"
              fill="none"
            />
            <path
              id={`circle-text-path-bottom-${filterId}`}
              d="M 202,120 A 82,82 0 0,1 38,120"
              fill="none"
            />
          </defs>

          {/* BACKGROUND FAINT WASH (Only when unlocked, simulating damp vermilion cinnabar pigment) */}
          {!isLocked && (
            <rect
              x="12"
              y="12"
              width="216"
              height="216"
              rx={resolvedSeal.shape === "circle" ? "108" : resolvedSeal.shape === "arch" ? "40" : "16"}
              fill="#A62B2B"
              fillOpacity="0.06"
            />
          )}

          {/* MAIN GEOMETRIC FRAME & CORNER MOTIFS */}
          <SealFrame
            shape={resolvedSeal.shape}
            borderPattern={resolvedSeal.borderPattern}
            isLocked={isLocked}
            inkColor={isLocked ? "#475569" : resolvedSeal.inkColor}
          />

          {/* MONUMENT ICONIC EMBLEM & MOTIF */}
          <MonumentEmblem
            slug={resolvedSeal.monumentSlug}
            isLocked={isLocked}
            inkColor={isLocked ? "#475569" : resolvedSeal.inkColor}
          />

          {/* HAN-NOM SEAL CHARACTERS (TRIỆN THƯ / CHÂN THƯ) */}
          <SealHanNomCharacters
            characters={resolvedSeal.sealScriptCharacters}
            isLocked={isLocked}
            inkColor={isLocked ? "#475569" : resolvedSeal.inkColor}
            shape={resolvedSeal.shape}
          />

          {/* QUỐC NGỮ SEAL INSCRIPTION BANNER */}
          <SealQuocNguText
            text={resolvedSeal.sealTextQuocNgu}
            shape={resolvedSeal.shape}
            filterId={filterId}
            isLocked={isLocked}
            inkColor={isLocked ? "#475569" : resolvedSeal.inkColor}
          />
        </svg>
      </div>

      {/* Optional Descriptive Label */}
      {showLabel && (
        <div className="mt-2 text-center">
          <p
            className={`text-xs font-serif tracking-wide font-medium ${
              isLocked ? "text-stone-400" : "text-amber-950 dark:text-amber-200"
            }`}
          >
            {resolvedSeal.monumentNameVi}
          </p>
          <p
            className={`text-[10px] tracking-tight ${
              isLocked ? "text-stone-400/80" : "text-[#A62B2B] font-semibold"
            }`}
          >
            {resolvedSeal.sealTextQuocNgu}
          </p>
        </div>
      )}

      {/* Optional Date / Era Caption */}
      {showDate && (
        <span className="text-[9px] text-stone-400 font-mono mt-0.5">
          {isUnlocked && resolvedSeal.unlockedAt
            ? new Date(resolvedSeal.unlockedAt).toLocaleDateString("vi-VN")
            : resolvedSeal.historicalEra}
        </span>
      )}

      {/* Inline styles for stamp slam and splatter keyframes */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
        @keyframes sealSlam {
          0% {
            transform: scale(1.48) translateY(-14px);
            opacity: 0.1;
          }
          65% {
            transform: scale(0.96) translateY(0);
            opacity: 1;
          }
          85% {
            transform: scale(1.03);
          }
          100% {
            transform: scale(1);
          }
        }
        @keyframes splatterBurst {
          0% {
            transform: scale(0.6);
            opacity: 0.95;
          }
          100% {
            transform: scale(1.36);
            opacity: 0;
          }
        }
        .animate-seal-slam {
          animation: sealSlam 0.5s cubic-bezier(0.25, 1, 0.5, 1) forwards;
        }
        .animate-splatter-burst {
          animation: splatterBurst 0.65s ease-out forwards;
        }
      `,
        }}
      />
    </div>
  );
};

// ===========================================================================
// SUB-COMPONENT: SEAL FRAME (Double borders & imperial corner ornaments)
// ===========================================================================

interface SealFrameProps {
  shape: SealShape;
  borderPattern: SealBorderPattern;
  isLocked: boolean;
  inkColor: string;
}

const SealFrame: React.FC<SealFrameProps> = ({ shape, isLocked, inkColor }) => {
  const strokeColor = inkColor;
  const outerStrokeWidth = isLocked ? "2" : "3.6";
  const innerStrokeWidth = isLocked ? "1" : "1.8";
  const dashArray = isLocked ? "4 3" : undefined;

  switch (shape) {
    case "circle":
      return (
        <g className="seal-frame-circle" stroke={strokeColor} fill="none">
          {/* Outer circle */}
          <circle
            cx="120"
            cy="120"
            r="104"
            strokeWidth={outerStrokeWidth}
            strokeDasharray={dashArray}
          />
          {/* Beaded imperial pearl ring */}
          <circle cx="120" cy="120" r="97" strokeWidth="1" strokeDasharray="2 6" opacity="0.6" />
          {/* Inner circle */}
          <circle cx="120" cy="120" r="90" strokeWidth={innerStrokeWidth} />
          {/* Quad cardinal cloud dots */}
          <circle cx="120" cy="22" r="3" fill={strokeColor} />
          <circle cx="120" cy="218" r="3" fill={strokeColor} />
          <circle cx="22" cy="120" r="3" fill={strokeColor} />
          <circle cx="218" cy="120" r="3" fill={strokeColor} />
        </g>
      );

    case "octagon":
      return (
        <g className="seal-frame-octagon" stroke={strokeColor} fill="none">
          {/* Outer octagon */}
          <polygon
            points="70,16 170,16 224,70 224,170 170,224 70,224 16,170 16,70"
            strokeWidth={outerStrokeWidth}
            strokeDasharray={dashArray}
            strokeLinejoin="round"
          />
          {/* Inner octagon */}
          <polygon
            points="74,26 166,26 214,74 214,166 166,214 74,214 26,166 26,74"
            strokeWidth={innerStrokeWidth}
            strokeLinejoin="round"
          />
          {/* Corner diagonal decorative brackets */}
          <line x1="68" y1="20" x2="20" y2="68" strokeWidth="1" opacity="0.5" />
          <line x1="172" y1="20" x2="220" y2="68" strokeWidth="1" opacity="0.5" />
          <line x1="220" y1="172" x2="172" y2="220" strokeWidth="1" opacity="0.5" />
          <line x1="20" y1="172" x2="68" y2="220" strokeWidth="1" opacity="0.5" />
        </g>
      );

    case "arch":
      return (
        <g className="seal-frame-arch" stroke={strokeColor} fill="none">
          {/* Outer bell / arch shape */}
          <path
            d="M 32,216 L 32,96 C 32,48 70,18 120,18 C 170,18 208,48 208,96 L 208,216 Z"
            strokeWidth={outerStrokeWidth}
            strokeDasharray={dashArray}
            strokeLinejoin="round"
          />
          {/* Inner arch */}
          <path
            d="M 42,206 L 42,98 C 42,56 76,28 120,28 C 164,28 198,56 198,98 L 198,206 Z"
            strokeWidth={innerStrokeWidth}
            strokeLinejoin="round"
          />
          {/* Arch crown finial lotus flame */}
          <path
            d="M 120,14 C 117,10 114,8 120,4 C 126,8 123,10 120,14 Z"
            fill={strokeColor}
            stroke="none"
          />
        </g>
      );

    case "square":
    default:
      return (
        <g className="seal-frame-square" stroke={strokeColor} fill="none">
          {/* Outer square with slight rounded corners */}
          <rect
            x="18"
            y="18"
            width="204"
            height="204"
            rx="8"
            strokeWidth={outerStrokeWidth}
            strokeDasharray={dashArray}
          />
          {/* Inner border square */}
          <rect x="28" y="28" width="184" height="184" rx="4" strokeWidth={innerStrokeWidth} />

          {/* 4 Corner Cloud Motifs (Hồi Vân Mây Lửa / Vân Đao) */}
          {/* Top-Left Corner Cloud */}
          <path
            d="M 32,44 C 40,44 44,38 44,32 M 32,54 C 46,54 54,44 54,32"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
          {/* Top-Right Corner Cloud */}
          <path
            d="M 208,44 C 200,44 196,38 196,32 M 208,54 C 194,54 186,44 186,32"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
          {/* Bottom-Left Corner Cloud */}
          <path
            d="M 32,196 C 40,196 44,202 44,208 M 32,186 C 46,186 54,196 54,208"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
          {/* Bottom-Right Corner Cloud */}
          <path
            d="M 208,196 C 200,196 196,202 196,208 M 208,186 C 194,186 186,196 186,208"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
        </g>
      );
  }
};

// ===========================================================================
// SUB-COMPONENT: MONUMENT EMBLEM (Architectural vector heart for 16 sites)
// ===========================================================================

interface MonumentEmblemProps {
  slug: string;
  isLocked: boolean;
  inkColor: string;
}

const MonumentEmblem: React.FC<MonumentEmblemProps> = ({ slug, inkColor }) => {
  const stroke = inkColor;
  const fill = inkColor;

  switch (slug) {
    case "ngo-mon":
      // Ngọ Môn: Lầu Ngũ Phụng roofline over U-shaped masonry with 5 gate arches
      return (
        <g className="emblem-ngo-mon" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Upper roof ridge of Ngũ Phụng */}
          <path d="M 85,90 Q 120,80 155,90 L 150,96 L 90,96 Z" fill={fill} fillOpacity="0.35" />
          {/* Mid roof deck */}
          <path d="M 76,104 Q 120,95 164,104" strokeWidth="1.6" />
          {/* Gate base terrace */}
          <rect x="70" y="112" width="100" height="24" fill={fill} fillOpacity="0.15" />
          {/* 5 Portals: Central royal gate & 4 flanking side gates */}
          <path d="M 112,136 L 112,122 C 112,118 128,118 128,122 L 128,136 Z" fill={fill} />
          <path d="M 94,136 L 94,125 C 94,122 104,122 104,125 L 104,136 Z" fill={fill} />
          <path d="M 136,136 L 136,125 C 136,122 146,122 146,125 L 146,136 Z" fill={fill} />
          <path d="M 78,136 L 78,128 C 78,126 86,126 86,128 L 86,136 Z" fill={fill} />
          <path d="M 154,136 L 154,128 C 154,126 161,126 161,128 L 161,136 Z" fill={fill} />
        </g>
      );

    case "cau-trung-dao":
      // Cầu Trung Đạo: Arched bridge spanning lotus waves
      return (
        <g className="emblem-cau-trung-dao" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Bridge balustrade arch */}
          <path d="M 68,118 Q 120,98 172,118" strokeWidth="2.2" />
          <path d="M 72,124 Q 120,106 168,124" strokeWidth="1.5" />
          {/* Balusters */}
          <line x1="90" y1="113" x2="90" y2="122" />
          <line x1="120" y1="108" x2="120" y2="117" />
          <line x1="150" y1="113" x2="150" y2="122" />
          {/* Water waves of Hồ Thái Dịch */}
          <path d="M 64,136 Q 78,130 92,136 T 120,136 T 148,136 T 176,136" />
          <path d="M 72,142 Q 86,138 100,142 T 128,142 T 156,142" opacity="0.6" />
          {/* Lotus flower bud center */}
          <path d="M 120,94 C 116,98 116,104 120,106 C 124,104 124,98 120,94 Z" fill={fill} />
        </g>
      );

    case "san-dai-trieu-nghi":
      // Sân Đại Triều Nghi: Stepped terrace courts and stone rank steles (Phẩm tán)
      return (
        <g className="emblem-san-dai-trieu-nghi" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Upper terrace and lower terrace */}
          <rect x="74" y="92" width="92" height="14" fill={fill} fillOpacity="0.2" />
          <rect x="66" y="108" width="108" height="24" fill={fill} fillOpacity="0.1" />
          <line x1="66" y1="120" x2="174" y2="120" strokeDasharray="3 3" />
          {/* Central imperial path (Đường Dũng Đạo) */}
          <line x1="120" y1="92" x2="120" y2="132" strokeWidth="2" />
          {/* Left rank steles (Quan Văn) */}
          <rect x="80" y="112" width="5" height="12" fill={fill} />
          <rect x="92" y="114" width="5" height="10" fill={fill} />
          <rect x="104" y="116" width="5" height="8" fill={fill} />
          {/* Right rank steles (Quan Võ) */}
          <rect x="131" y="116" width="5" height="8" fill={fill} />
          <rect x="143" y="114" width="5" height="10" fill={fill} />
          <rect x="155" y="112" width="5" height="12" fill={fill} />
        </g>
      );

    case "dien-thai-hoa":
      // Điện Thái Hòa: Trùng thiềm điệp ốc rooflines with dragon cloud crest & sun
      return (
        <g className="emblem-dien-thai-hoa" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Sun disc above palace */}
          <circle cx="120" cy="80" r="7" fill={fill} fillOpacity="0.8" />
          <path d="M 120,70 L 120,73 M 120,87 L 120,90 M 110,80 L 113,80 M 127,80 L 130,80" />
          {/* Upper palace roof (Tiền điện) */}
          <path d="M 80,95 Q 120,88 160,95 L 154,103 L 86,103 Z" fill={fill} fillOpacity="0.25" />
          {/* Lower palace roof (Chính điện - Trùng thiềm điệp ốc) */}
          <path d="M 72,109 Q 120,101 168,109 L 161,118 L 78,118 Z" fill={fill} fillOpacity="0.4" />
          {/* Columns & imperial throne platform */}
          <rect x="82" y="118" width="76" height="18" />
          <line x1="94" y1="118" x2="94" y2="136" />
          <line x1="120" y1="118" x2="120" y2="136" strokeWidth="2" />
          <line x1="146" y1="118" x2="146" y2="136" />
        </g>
      );

    case "the-to-mieu":
      // Thế Tổ Miếu: Sacred ancestral temple sanctuary with sacred incense flame
      return (
        <g className="emblem-the-to-mieu" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Urn cauldron belly */}
          <path
            d="M 96,108 C 96,128 144,128 144,108 Z"
            fill={fill}
            fillOpacity="0.3"
            strokeWidth="1.8"
          />
          {/* Urn rim and two ears/handles */}
          <line x1="90" y1="108" x2="150" y2="108" strokeWidth="2.5" />
          <path d="M 92,108 L 92,98 L 98,98 L 98,108" strokeWidth="1.8" />
          <path d="M 148,108 L 148,98 L 142,98 L 142,108" strokeWidth="1.8" />
          {/* Three solid tripod legs */}
          <line x1="102" y1="126" x2="98" y2="138" strokeWidth="2.5" />
          <line x1="120" y1="128" x2="120" y2="140" strokeWidth="2.5" />
          <line x1="138" y1="126" x2="142" y2="138" strokeWidth="2.5" />
          {/* Sacred incense flame cloud above */}
          <path
            d="M 120,84 C 114,92 126,96 120,104"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </g>
      );

    case "hien-lam-cac":
      // Hiển Lâm Các: 3-tier wooden pavilion towering 17m high
      return (
        <g className="emblem-hien-lam-cac" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Tier 3 roof (Top) */}
          <path d="M 98,82 Q 120,77 142,82 L 138,88 L 102,88 Z" fill={fill} fillOpacity="0.4" />
          <rect x="106" y="88" width="28" height="10" />
          {/* Tier 2 roof (Middle) */}
          <path d="M 88,100 Q 120,94 152,100 L 146,106 L 94,106 Z" fill={fill} fillOpacity="0.3" />
          <rect x="98" y="106" width="44" height="12" />
          {/* Tier 1 roof (Ground base) */}
          <path d="M 76,120 Q 120,113 164,120 L 158,127 L 82,127 Z" fill={fill} fillOpacity="0.2" />
          <rect x="88" y="127" width="64" height="12" />
          {/* Columns */}
          <line x1="102" y1="127" x2="102" y2="139" />
          <line x1="120" y1="127" x2="120" y2="139" strokeWidth="1.8" />
          <line x1="138" y1="127" x2="138" y2="139" />
        </g>
      );

    case "hung-to-mieu":
      // Hưng Tổ Miếu: Auspicious filial temple & Wan (Chữ Vạn) fretwork
      return (
        <g className="emblem-hung-to-mieu" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Shrine roof */}
          <path d="M 84,94 Q 120,86 156,94 L 150,102 L 90,102 Z" fill={fill} fillOpacity="0.3" />
          {/* Temple hall */}
          <rect x="92" y="102" width="56" height="34" />
          {/* Wan character (Chữ Vạn) in the center of the shrine */}
          <path
            d="M 112,112 L 120,112 L 120,126 M 120,119 L 128,119 L 128,126 M 120,119 L 112,119 L 112,112 M 128,119 L 128,112 L 120,112"
            strokeWidth="1.5"
            strokeLinecap="square"
          />
        </g>
      );

    case "trieu-to-mieu":
      // Triệu Tổ Miếu: Archaic ancestral shrine with founder sunrays
      return (
        <g className="emblem-trieu-to-mieu" stroke={stroke} strokeWidth="1.4" fill="none">
          <circle cx="120" cy="88" r="8" fill={fill} fillOpacity="0.25" />
          {/* Traditional temple roof */}
          <path d="M 82,102 Q 120,94 158,102 L 152,110 L 88,110 Z" fill={fill} fillOpacity="0.35" />
          <rect x="92" y="110" width="56" height="26" />
          {/* Royal foundation stone pedestal */}
          <line x1="84" y1="136" x2="156" y2="136" strokeWidth="2.5" />
        </g>
      );

    case "dai-cung-mon":
      // Đại Cung Môn: Triple palace portal of the Forbidden City
      return (
        <g className="emblem-dai-cung-mon" stroke={stroke} strokeWidth="1.4" fill="none">
          <path d="M 76,96 Q 120,88 164,96 L 158,104 L 82,104 Z" fill={fill} fillOpacity="0.3" />
          <rect x="80" y="104" width="80" height="32" fill={fill} fillOpacity="0.1" />
          {/* 3 doors of Great Palace Gate */}
          <rect x="88" y="114" width="14" height="22" fill={fill} />
          <rect x="110" y="110" width="20" height="26" fill={fill} />
          <rect x="138" y="114" width="14" height="22" fill={fill} />
        </g>
      );

    case "dien-can-chanh":
      // Điện Cần Chánh: Royal governance scroll and vermilion brush
      return (
        <g className="emblem-dien-can-chanh" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Audience hall roof */}
          <path d="M 82,94 Q 120,87 158,94 L 152,101 L 88,101 Z" fill={fill} fillOpacity="0.3" />
          {/* Royal edict scroll unrolled */}
          <rect x="94" y="107" width="52" height="24" rx="2" fill={fill} fillOpacity="0.15" />
          {/* Scroll lines representing state decrees */}
          <line x1="100" y1="113" x2="140" y2="113" strokeDasharray="2 2" />
          <line x1="100" y1="119" x2="135" y2="119" strokeDasharray="2 2" />
          <line x1="100" y1="125" x2="128" y2="125" strokeDasharray="2 2" />
          {/* Royal brush pointing down */}
          <path d="M 136,101 L 144,124 L 142,126 L 134,103 Z" fill={fill} />
        </g>
      );

    case "dien-kien-trung":
      // Điện Kiến Trung: Neo-classical Indochinese facade with ceramic mosaic arches
      return (
        <g className="emblem-dien-kien-trung" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* French-Italian Mansard style roofline */}
          <path d="M 80,92 L 96,82 L 144,82 L 160,92 L 156,98 L 84,98 Z" fill={fill} fillOpacity="0.3" />
          <rect x="84" y="98" width="72" height="38" />
          {/* Three Italianate arched french windows */}
          <path d="M 92,120 L 92,108 C 92,104 100,104 100,108 L 100,120 Z" fill={fill} />
          <path d="M 112,120 L 112,106 C 112,102 128,102 128,106 L 128,120 Z" fill={fill} />
          <path d="M 140,120 L 140,108 C 140,104 148,104 148,108 L 148,120 Z" fill={fill} />
          {/* Balustrade balcony */}
          <line x1="84" y1="126" x2="156" y2="126" strokeWidth="1.8" />
        </g>
      );

    case "duyet-thi-duong":
      // Duyệt Thị Đường: Royal opera theatre stage, bronze gong, star canopy
      return (
        <g className="emblem-duyet-thi-duong" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Theatre ceiling canopy with stars */}
          <path d="M 80,88 Q 120,80 160,88" strokeWidth="1.8" />
          <circle cx="100" cy="84" r="1.5" fill={fill} />
          <circle cx="120" cy="82" r="2.2" fill={fill} />
          <circle cx="140" cy="84" r="1.5" fill={fill} />
          {/* Royal performance square stage */}
          <rect x="88" y="104" width="64" height="26" fill={fill} fillOpacity="0.2" />
          {/* Bronze court music gong hanging from ornate dragon frame */}
          <circle cx="120" cy="116" r="8" fill={fill} fillOpacity="0.4" strokeWidth="1.8" />
          <circle cx="120" cy="116" r="2.5" fill={fill} />
        </g>
      );

    case "thai-binh-lau":
      // Thái Bình Lâu: Royal book pavilion flanked by scroll and lotus pond
      return (
        <g className="emblem-thai-binh-lau" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* 2-tier library roof */}
          <path d="M 92,86 Q 120,80 148,86 L 144,92 L 96,92 Z" fill={fill} fillOpacity="0.35" />
          <rect x="100" y="92" width="40" height="10" />
          <path d="M 82,104 Q 120,97 158,104 L 152,111 L 88,111 Z" fill={fill} fillOpacity="0.25" />
          <rect x="92" y="111" width="56" height="24" />
          {/* Book icon in pavilion center */}
          <path d="M 112,120 L 120,123 L 128,120 L 128,128 L 120,131 L 112,128 Z" fill={fill} />
        </g>
      );

    case "cung-dien-tho":
      // Cung Diên Thọ: Longevity medallion (Chữ Thọ tròn) flanked by auspicious bats
      return (
        <g className="emblem-cung-dien-tho" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Medallion ring */}
          <circle cx="120" cy="112" r="22" strokeWidth="1.8" fill={fill} fillOpacity="0.1" />
          {/* Shou / Thọ longevity glyph lines */}
          <line x1="107" y1="104" x2="133" y2="104" strokeWidth="1.8" />
          <line x1="120" y1="96" x2="120" y2="128" strokeWidth="1.8" />
          <line x1="110" y1="112" x2="130" y2="112" strokeWidth="1.5" />
          <line x1="110" y1="120" x2="130" y2="120" strokeWidth="1.5" />
          {/* Auspicious bat wings on flanks */}
          <path d="M 90,112 Q 95,106 97,112 Q 95,118 90,112" fill={fill} />
          <path d="M 150,112 Q 145,106 143,112 Q 145,118 150,112" fill={fill} />
        </g>
      );

    case "cung-truong-sanh":
      // Cung Trường Sanh: Peach of immortality & serene garden water canal
      return (
        <g className="emblem-cung-truong-sanh" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Peach of Immortality (Đào tiên trường thọ) */}
          <path
            d="M 120,90 C 104,90 102,114 120,124 C 138,114 136,90 120,90 Z"
            fill={fill}
            fillOpacity="0.3"
            strokeWidth="1.8"
          />
          {/* Leaf sprig */}
          <path d="M 120,90 Q 128,84 132,88 Q 126,92 120,90" fill={fill} />
          {/* Meandering water moat ripples */}
          <path d="M 76,134 Q 98,128 120,134 T 164,134" strokeWidth="1.5" />
          <path d="M 86,140 Q 108,136 130,140 T 154,140" opacity="0.6" strokeWidth="1.2" />
        </g>
      );

    case "dien-phung-tien":
      // Điện Phụng Tiên: Sacred Tam Quan gate and veneration orchid
      return (
        <g className="emblem-dien-phung-tien" stroke={stroke} strokeWidth="1.4" fill="none">
          {/* Triple arch Tam Quan gate */}
          <path d="M 80,98 Q 120,91 160,98 L 154,105 L 86,105 Z" fill={fill} fillOpacity="0.3" />
          <rect x="84" y="105" width="72" height="28" fill={fill} fillOpacity="0.1" />
          {/* Left, Center, Right arches */}
          <path d="M 90,133 L 90,118 C 90,114 98,114 98,118 L 98,133 Z" fill={fill} />
          <path d="M 112,133 L 112,114 C 112,110 128,110 128,114 L 128,133 Z" fill={fill} />
          <path d="M 142,133 L 142,118 C 142,114 150,114 150,118 L 150,133 Z" fill={fill} />
        </g>
      );

    // =======================================================================
    // UNIQUE COMPLETED ZONE ROYAL SEALS (Kim Bảo & Ngự Tỷ Motifs)
    // =======================================================================
    case "zone-central-ceremonial-axis":
    case "hoang-de-chi-bao":
    case "kim-bao-central":
      // Kim Bảo: Hoàng Đế Chi Bảo — Golden Dragon (Kim Long Nữu) with flaming solar pearl
      return (
        <g className="emblem-kim-bao-central" stroke={stroke} strokeWidth="1.6" fill="none">
          {/* Imperial Solar Disc / Sacred Flaming Pearl */}
          <circle cx="120" cy="80" r="10" fill={fill} fillOpacity="0.5" strokeWidth="2" />
          <circle cx="120" cy="80" r="5" fill={fill} />
          {/* Solar fire flames */}
          <path d="M 120,66 L 120,62 M 120,94 L 120,98 M 106,80 L 102,80 M 134,80 L 138,80" strokeWidth="1.8" />
          <path d="M 110,70 L 106,66 M 130,90 L 134,94 M 110,90 L 106,94 M 130,70 L 134,66" strokeWidth="1.5" />
          {/* Golden Dragon Head & Crest (Kim Long Nữu) */}
          <path
            d="M 92,106 Q 120,92 148,106 Q 154,124 140,134 Q 120,138 100,134 Q 86,124 92,106 Z"
            fill={fill}
            fillOpacity="0.3"
            strokeWidth="2"
          />
          {/* Dragon Antlers & Whiskers */}
          <path d="M 104,96 Q 96,86 90,88 Q 94,96 102,100" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M 136,96 Q 144,86 150,88 Q 146,96 138,100" strokeWidth="1.8" strokeLinecap="round" />
          {/* Dragon eyes */}
          <circle cx="108" cy="112" r="2.5" fill={fill} />
          <circle cx="132" cy="112" r="2.5" fill={fill} />
          {/* Dragon nose bridge & mouth */}
          <path d="M 116,112 L 120,118 L 124,112" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M 110,126 Q 120,130 130,126" strokeWidth="2" strokeLinecap="round" />
        </g>
      );

    case "zone-ancestral-worship-space":
    case "ton-mieu-ngu-ty":
    case "ngu-ty-worship":
      // Ngự Tỷ: Tôn Miếu Ngự Tỷ — Sacred Jade Kylin and Ancestral Lotus Censer
      return (
        <g className="emblem-ngu-ty-worship" stroke={stroke} strokeWidth="1.5" fill="none">
          {/* Jade Seal Pedestal / Sacred Urn */}
          <path
            d="M 94,112 C 94,134 146,134 146,112 Z"
            fill={fill}
            fillOpacity="0.28"
            strokeWidth="2"
          />
          <line x1="88" y1="112" x2="152" y2="112" strokeWidth="3" />
          {/* Incense handles & tripod base */}
          <path d="M 90,112 L 90,102 L 96,102" strokeWidth="2" />
          <path d="M 150,112 L 150,102 L 144,102" strokeWidth="2" />
          <line x1="102" y1="130" x2="98" y2="142" strokeWidth="2.8" strokeLinecap="round" />
          <line x1="120" y1="132" x2="120" y2="144" strokeWidth="2.8" strokeLinecap="round" />
          <line x1="138" y1="130" x2="142" y2="142" strokeWidth="2.8" strokeLinecap="round" />
          {/* Sacred Kylin Horn & Auspicious Lotus Cloud */}
          <path
            d="M 120,78 C 108,86 114,96 120,104 C 126,96 132,86 120,78 Z"
            fill={fill}
            fillOpacity="0.45"
            strokeWidth="1.8"
          />
          <path d="M 114,88 Q 120,82 126,88" strokeWidth="1.5" />
        </g>
      );

    case "zone-purple-forbidden-city":
    case "ngu-tien-chi-bao":
    case "kim-bao-forbidden":
      // Kim Bảo: Ngự Tiền Chi Bảo — Inner Palace Golden Edict Scroll & Vermilion Brush
      return (
        <g className="emblem-kim-bao-forbidden" stroke={stroke} strokeWidth="1.5" fill="none">
          {/* Inner Palace Throne Shield */}
          <polygon
            points="120,74 154,92 154,126 120,140 86,126 86,92"
            fill={fill}
            fillOpacity="0.22"
            strokeWidth="2"
          />
          {/* Royal edict decree scroll */}
          <rect x="98" y="98" width="44" height="24" rx="2" strokeWidth="1.8" fill={fill} fillOpacity="0.2" />
          <line x1="104" y1="105" x2="136" y2="105" strokeDasharray="3 2" strokeWidth="1.5" />
          <line x1="104" y1="111" x2="132" y2="111" strokeDasharray="3 2" strokeWidth="1.5" />
          <line x1="104" y1="117" x2="126" y2="117" strokeDasharray="3 2" strokeWidth="1.5" />
          {/* Royal Vermilion Brush crossing from upper right */}
          <path d="M 144,82 L 150,88 L 132,128 L 126,126 Z" fill={fill} strokeWidth="1.5" />
          <path d="M 126,126 L 122,134 L 130,130 Z" fill={fill} />
        </g>
      );

    case "zone-royal-living-gardens":
    case "dien-tho-ngu-ty":
    case "ngu-ty-living":
      // Ngự Tỷ: Diên Thọ Ngự Tỷ — Auspicious Imperial Phoenix & Longevity Peach
      return (
        <g className="emblem-ngu-ty-living" stroke={stroke} strokeWidth="1.5" fill="none">
          {/* Auspicious Peach of Longevity (Đào tiên hoàng tộc) */}
          <path
            d="M 120,84 C 100,84 96,112 120,128 C 144,112 140,84 120,84 Z"
            fill={fill}
            fillOpacity="0.32"
            strokeWidth="2"
          />
          {/* Phoenix crown feathers */}
          <path d="M 120,84 Q 128,72 136,78 Q 126,84 120,84" fill={fill} />
          <path d="M 120,84 Q 112,72 104,78 Q 114,84 120,84" fill={fill} />
          {/* Longevity character lines inside peach */}
          <line x1="110" y1="102" x2="130" y2="102" strokeWidth="1.8" />
          <line x1="120" y1="94" x2="120" y2="118" strokeWidth="1.8" />
          <line x1="112" y1="110" x2="128" y2="110" strokeWidth="1.5" />
          {/* Water rippling garden ripples */}
          <path d="M 80,136 Q 100,130 120,136 T 160,136" strokeWidth="1.6" />
          <path d="M 90,142 Q 105,138 120,142 T 150,142" opacity="0.6" strokeWidth="1.2" />
        </g>
      );

    case "grand-master-all":
    case "dai-nam-hoang-de-chi-bao":
      // Đại Kim Bảo: Đại Nam Hoàng Đế Chi Bảo — Dual Imperial Dragons Flanking Solar Pearl
      return (
        <g className="emblem-grand-master-kim-bao" stroke={stroke} strokeWidth="1.6" fill="none">
          {/* Sacred Celestial Pearl */}
          <circle cx="120" cy="80" r="12" fill={fill} fillOpacity="0.6" strokeWidth="2.2" />
          <circle cx="120" cy="80" r="6" fill={fill} />
          {/* Pearl Flames */}
          <path d="M 120,64 L 120,58 M 120,96 L 120,102 M 104,80 L 98,80 M 136,80 L 142,80" strokeWidth="2" />
          {/* Left Dragon Body & Horn */}
          <path d="M 72,118 Q 86,96 106,96 Q 114,106 108,122" strokeWidth="2" strokeLinecap="round" />
          <path d="M 88,94 Q 78,86 74,90 Q 82,98 90,98" strokeWidth="1.6" fill={fill} />
          <circle cx="98" cy="106" r="2.5" fill={fill} />
          {/* Right Dragon Body & Horn */}
          <path d="M 168,118 Q 154,96 134,96 Q 126,106 132,122" strokeWidth="2" strokeLinecap="round" />
          <path d="M 152,94 Q 161.9,86 166,90 Q 158,98 150,98" strokeWidth="1.6" fill={fill} />
          <circle cx="142" cy="106" r="2.5" fill={fill} />
          {/* Sacred Mountain Base (Tam Sơn Đỉnh) */}
          <polygon
            points="120,116 134,136 106,136"
            fill={fill}
            fillOpacity="0.4"
            strokeWidth="2"
          />
          <line x1="84" y1="136" x2="156" y2="136" strokeWidth="2.5" />
        </g>
      );

    default:
      return (
        <g className="emblem-generic" stroke={stroke} strokeWidth="1.4" fill="none">
          <circle cx="120" cy="114" r="16" fill={fill} fillOpacity="0.2" />
        </g>
      );
  }
};

// ===========================================================================
// SUB-COMPONENT: HAN-NOM SEAL CHARACTERS (Traditional Triện thư / Chân thư)
// ===========================================================================

interface SealHanNomProps {
  characters: string[];
  isLocked: boolean;
  inkColor: string;
  shape: SealShape;
}

const SealHanNomCharacters: React.FC<SealHanNomProps> = ({
  characters,
  inkColor,
  shape,
}) => {
  const fill = inkColor;
  const isFour = characters.length === 4;

  // Render 4 characters in traditional 2-column seal order:
  // Col 1 (Right): Char 0 (top-right), Char 1 (bottom-right)
  // Col 2 (Left):  Char 2 (top-left),  Char 3 (bottom-left)
  if (isFour) {
    const c0 = characters[0]; // Top Right
    const c1 = characters[1]; // Bottom Right
    const c2 = characters[2]; // Top Left
    const c3 = characters[3]; // Bottom Left

    return (
      <g
        className="seal-han-nom-grid select-none"
        fill={fill}
        style={{
          fontFamily:
            "'Noto Serif SC', 'SimSun', 'Songti SC', 'STSong', 'KaiTi', 'Baskerville', serif",
          fontWeight: 900,
        }}
      >
        {/* Top-Right Character */}
        <text
          x={shape === "circle" ? "170" : "176"}
          y="74"
          fontSize="24"
          textAnchor="middle"
          dominantBaseline="central"
          opacity="0.9"
        >
          {c0}
        </text>

        {/* Bottom-Right Character */}
        <text
          x={shape === "circle" ? "170" : "176"}
          y="156"
          fontSize="24"
          textAnchor="middle"
          dominantBaseline="central"
          opacity="0.9"
        >
          {c1}
        </text>

        {/* Top-Left Character */}
        <text
          x={shape === "circle" ? "70" : "64"}
          y="74"
          fontSize="24"
          textAnchor="middle"
          dominantBaseline="central"
          opacity="0.9"
        >
          {c2}
        </text>

        {/* Bottom-Left Character */}
        <text
          x={shape === "circle" ? "70" : "64"}
          y="156"
          fontSize="24"
          textAnchor="middle"
          dominantBaseline="central"
          opacity="0.9"
        >
          {c3}
        </text>
      </g>
    );
  }

  // Fallback for 6 characters (e.g. Thái Hòa Điện Khảo Ký Ấn or Thế Miếu Phụng Tự Chi Triện)
  const rightCol = characters.slice(0, 3);
  const leftCol = characters.slice(3, 6);

  return (
    <g
      className="seal-han-nom-columns select-none"
      fill={fill}
      style={{
        fontFamily:
          "'Noto Serif SC', 'SimSun', 'Songti SC', 'STSong', 'KaiTi', 'Baskerville', serif",
        fontWeight: 900,
      }}
    >
      {rightCol.map((char, i) => (
        <text
          key={`r-${i}`}
          x="176"
          y={64 + i * 44}
          fontSize="20"
          textAnchor="middle"
          dominantBaseline="central"
          opacity="0.92"
        >
          {char}
        </text>
      ))}
      {leftCol.map((char, i) => (
        <text
          key={`l-${i}`}
          x="64"
          y={64 + i * 44}
          fontSize="20"
          textAnchor="middle"
          dominantBaseline="central"
          opacity="0.92"
        >
          {char}
        </text>
      ))}
    </g>
  );
};

// ===========================================================================
// SUB-COMPONENT: QUỐC NGỮ SEAL TEXT (Clear, elegant Vietnamese inscription)
// ===========================================================================

interface SealQuocNguTextProps {
  text: string;
  shape: SealShape;
  filterId: string;
  isLocked: boolean;
  inkColor: string;
}

const SealQuocNguText: React.FC<SealQuocNguTextProps> = ({
  text,
  shape,
  filterId,
  inkColor,
}) => {
  const fill = inkColor;

  if (shape === "circle") {
    return (
      <g className="seal-quoc-ngu-circle select-none">
        <text
          fill={fill}
          fontSize="11.5"
          fontWeight="bold"
          letterSpacing="0.22em"
          textAnchor="middle"
          className="font-serif uppercase"
          opacity="0.9"
        >
          <textPath
            href={`#circle-text-path-bottom-${filterId}`}
            startOffset="50%"
            textAnchor="middle"
          >
            {text}
          </textPath>
        </text>
      </g>
    );
  }

  // Rectangular / Arch / Octagonal banner at bottom or center rim
  return (
    <g className="seal-quoc-ngu-banner select-none">
      {/* Decorative double underline */}
      <line x1="56" y1="184" x2="184" y2="184" stroke={fill} strokeWidth="1" opacity="0.6" />
      <line x1="72" y1="187" x2="168" y2="187" stroke={fill} strokeWidth="0.8" opacity="0.4" />

      {/* Primary Quốc ngữ text */}
      <text
        x="120"
        y="178"
        fill={fill}
        fontSize="11.5"
        fontWeight="bold"
        fontFamily="Cinzel, 'Times New Roman', 'Noto Serif', Georgia, serif"
        letterSpacing="0.14em"
        textAnchor="middle"
        dominantBaseline="auto"
        opacity="0.95"
      >
        {text}
      </text>
    </g>
  );
};

export default RoyalSealStamp;
