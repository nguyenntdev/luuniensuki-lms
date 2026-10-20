"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface CertificateFrameProps {
  children?: React.ReactNode;
  className?: string;
  id?: string;
}

/**
 * Imperial Cloud & Dragon Vector Ornaments for Vietnamese Royal Decrees (Sắc phong triều Nguyễn).
 * Rendered using precision SVG vectors for razor-sharp 300+ DPI print output.
 */
function ImperialCornerBracket({
  position,
}: {
  position: "top-left" | "top-right" | "bottom-left" | "bottom-right";
}) {
  const transform = {
    "top-left": "",
    "top-right": "scale(-1, 1)",
    "bottom-left": "scale(1, -1)",
    "bottom-right": "scale(-1, -1)",
  }[position];

  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute z-10 size-20 sm:size-28 md:size-32 transition-transform",
        position === "top-left" && "top-0 left-0",
        position === "top-right" && "top-0 right-0",
        position === "bottom-left" && "bottom-0 left-0",
        position === "bottom-right" && "bottom-0 right-0",
      )}
    >
      <svg
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-full w-full"
        style={{ transform }}
      >
        <g stroke="#A62B2B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {/* Outer Corner Meander (Hồi văn triện góc) */}
          <path d="M6 114 V6 H114" stroke="#C68A2C" strokeWidth="2.5" />
          <path d="M14 104 V14 H104" stroke="#A62B2B" strokeWidth="1.5" />
          <path d="M22 94 V22 H94" stroke="#C68A2C" strokeWidth="1" strokeDasharray="3 3" />

          {/* Traditional Geometric Meander Key */}
          <path
            d="M6 34 H34 V6"
            stroke="#A62B2B"
            strokeWidth="2"
            fill="none"
          />
          <path
            d="M14 26 H26 V14"
            stroke="#C68A2C"
            strokeWidth="1.5"
            fill="#A62B2B"
            fillOpacity="0.15"
          />

          {/* Imperial Stylized Dragon & Auspicious Cloud (Long vân cách điệu) */}
          <path
            d="M26 42 C 26 26, 42 26, 42 34 C 42 42, 54 40, 56 32 C 58 24, 70 24, 72 32 C 74 42, 60 52, 48 52 C 34 52, 26 44, 26 42 Z"
            fill="#A62B2B"
            fillOpacity="0.12"
            stroke="#C68A2C"
            strokeWidth="1.5"
          />
          <path
            d="M32 60 C 26 66, 24 76, 32 82 C 40 88, 52 84, 52 74 C 52 64, 40 60, 32 60 Z"
            fill="#C68A2C"
            fillOpacity="0.15"
            stroke="#A62B2B"
            strokeWidth="1.2"
          />
          <path
            d="M60 32 C 66 26, 76 24, 82 32 C 88 40, 84 52, 74 52 C 64 52, 60 40, 60 32 Z"
            fill="#C68A2C"
            fillOpacity="0.15"
            stroke="#A62B2B"
            strokeWidth="1.2"
          />

          {/* Auspicious Flaming Pearl Flamelets */}
          <path
            d="M36 36 Q 44 24, 48 36 Q 52 48, 36 36 Z"
            fill="#A62B2B"
            stroke="#C68A2C"
            strokeWidth="1"
          />
        </g>
        {/* Vermilion Accent Stud */}
        <circle cx="14" cy="14" r="3.5" fill="#A62B2B" stroke="#C68A2C" strokeWidth="1.5" />
      </svg>
    </div>
  );
}

/**
 * Top Central Royal Crest (Mặt trời thái dương, mây ngũ sắc & rồng chầu phong cách cung đình Huế)
 */
function ImperialTopCrest() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute -top-3 sm:-top-4 left-1/2 -translate-x-1/2 z-20 w-48 sm:w-64 md:w-80"
    >
      <svg
        viewBox="0 0 320 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto drop-shadow-sm"
      >
        {/* Central Sun / Auspicious Disc */}
        <circle cx="160" cy="22" r="13" fill="#A62B2B" stroke="#C68A2C" strokeWidth="2" />
        <circle cx="160" cy="22" r="8" fill="#F4E6C8" stroke="#A62B2B" strokeWidth="1" />
        <circle cx="160" cy="22" r="3" fill="#A62B2B" />

        {/* Radiating solar flames */}
        <path
          d="M160 5 V0 M160 39 V44 M143 22 H138 M177 22 H182 M148 10 L144 6 M172 34 L176 38 M148 34 L144 38 M172 10 L176 6"
          stroke="#C68A2C"
          strokeWidth="1.5"
          strokeLinecap="round"
        />

        {/* Left Auspicious Clouds */}
        <path
          d="M136 22 C 130 14, 116 12, 110 20 C 104 14, 90 14, 84 22 C 78 18, 66 18, 58 25 C 44 25, 36 30, 24 33 C 12 36, 0 32, 0 32"
          stroke="#A62B2B"
          strokeWidth="1.7"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M136 24 C 128 20, 118 22, 112 28 C 102 24, 88 28, 80 34 C 70 34, 52 35, 42 39"
          stroke="#C68A2C"
          strokeWidth="1.2"
          fill="none"
          strokeLinecap="round"
        />

        {/* Right Auspicious Clouds (Mirrored) */}
        <path
          d="M184 22 C 190 14, 204 12, 210 20 C 216 14, 230 14, 236 22 C 242 18, 254 18, 262 25 C 276 25, 284 30, 296 33 C 308 36, 320 32, 320 32"
          stroke="#A62B2B"
          strokeWidth="1.7"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M184 24 C 192 20, 202 22, 208 28 C 218 24, 232 28, 240 34 C 250 34, 268 35, 278 39"
          stroke="#C68A2C"
          strokeWidth="1.2"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

/**
 * Bottom Royal Wave & Mountain Border Motif (Thủy ba tam sơn - Biểu trưng trường tồn của hoàng triều)
 */
function ImperialBottomWave() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute -bottom-1 left-1/2 -translate-x-1/2 z-20 w-56 sm:w-72 md:w-96"
    >
      <svg
        viewBox="0 0 380 28"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto drop-shadow-sm"
      >
        {/* Central Sacred Mountain (Tam sơn đỉnh) */}
        <path
          d="M190 4 L196 16 L204 16 L210 24 H170 L176 16 L184 16 Z"
          fill="#C68A2C"
          fillOpacity="0.25"
          stroke="#A62B2B"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path
          d="M190 4 V24 M184 16 V24 M196 16 V24"
          stroke="#C68A2C"
          strokeWidth="1"
        />

        {/* Waves Left (Thủy ba triều dâng) */}
        <path
          d="M170 24 C 160 14, 148 14, 138 24 C 128 14, 116 14, 106 24 C 96 14, 84 14, 74 24 C 64 14, 52 14, 42 24 C 32 16, 18 18, 0 24"
          stroke="#A62B2B"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M165 24 C 158 18, 150 18, 143 24 C 136 18, 128 18, 121 24 C 114 18, 106 18, 99 24 C 92 18, 84 18, 77 24 C 70 18, 60 18, 50 24"
          stroke="#C68A2C"
          strokeWidth="1.2"
          fill="none"
          strokeLinecap="round"
        />

        {/* Waves Right (Thủy ba triều dâng) */}
        <path
          d="M210 24 C 220 14, 232 14, 242 24 C 252 14, 264 14, 274 24 C 284 14, 296 14, 306 24 C 316 14, 328 14, 338 24 C 348 16, 362 18, 380 24"
          stroke="#A62B2B"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M215 24 C 222 18, 230 18, 237 24 C 244 18, 252 18, 259 24 C 266 18, 274 18, 281 24 C 288 18, 296 18, 303 24 C 310 18, 320 18, 330 24"
          stroke="#C68A2C"
          strokeWidth="1.2"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

/**
 * CertificateFrame Component
 * Landscape royal decree decorative framing for imperial certificates.
 * Features:
 * - A4 Landscape proportion (297mm x 210mm ≈ 1.414 aspect ratio).
 * - Multi-layer royal decree borders with gold and vermilion inks.
 * - Corner ornaments (hồi văn triện góc và long vân).
 * - Authentic Nguyen Dynasty Imperial sun and water emblems.
 * - Traditional paper background simulation with warm ivory/parchment hue.
 */
export function CertificateFrame({
  children,
  className,
  id,
}: CertificateFrameProps) {
  return (
    <div
      id={id}
      className={cn(
        // Landscape A4 frame container with natural royal ivory/parchment background
        "relative mx-auto w-full max-w-[1020px] aspect-[297/210] min-h-[580px] sm:min-h-[640px] md:min-h-[700px]",
        "bg-[#FCF9F2] text-[#2A241D] select-none",
        "shadow-2xl rounded-sm overflow-hidden",
        "print:w-[297mm] print:h-[210mm] print:max-w-none print:shadow-none print:aspect-auto print:rounded-none print:m-0 print:border-none",
        className,
      )}
      style={{
        // Imperial parchment subtle texture
        backgroundImage: `
          radial-gradient(#C68A2C 0.65px, transparent 0.65px),
          radial-gradient(#A62B2B 0.45px, transparent 0.45px),
          linear-gradient(135deg, rgba(254, 251, 243, 0.95) 0%, rgba(247, 239, 224, 0.9) 100%)
        `,
        backgroundSize: "24px 24px, 48px 48px, 100% 100%",
        backgroundPosition: "0 0, 12px 12px, 0 0",
      }}
    >
      {/* Outer Imperial Border Rails (Khung viền son thếp vàng kép) */}
      <div className="absolute inset-2 sm:inset-3 md:inset-4 border-[3px] border-[#A62B2B] pointer-events-none z-10 print:inset-2">
        {/* Secondary Inner Fine Gold Border */}
        <div className="absolute inset-1 sm:inset-1.5 border border-[#C68A2C] pointer-events-none" />
        {/* Third Inner Dotted Filigree Line */}
        <div className="absolute inset-2 sm:inset-3 border border-[#A62B2B]/40 border-dashed pointer-events-none" />
      </div>

      {/* Decorative Corner Ornaments */}
      <ImperialCornerBracket position="top-left" />
      <ImperialCornerBracket position="top-right" />
      <ImperialCornerBracket position="bottom-left" />
      <ImperialCornerBracket position="bottom-right" />

      {/* Top Auspicious Crest */}
      <ImperialTopCrest />

      {/* Bottom Wave & Mountain Motif */}
      <ImperialBottomWave />

      {/* Subtle Guilloche / Watermark imperial dragon emblem in certificate center */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.038] z-0"
      >
        <svg
          viewBox="0 0 600 600"
          className="w-[70%] max-w-[440px] h-auto drop-shadow-sm"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Circular Imperial Dragon Emblem (Đồ án Rồng cuộn triều Nguyễn) */}
          <circle cx="300" cy="300" r="260" stroke="#A62B2B" strokeWidth="6" />
          <circle cx="300" cy="300" r="248" stroke="#C68A2C" strokeWidth="2" strokeDasharray="10 6" />
          <circle cx="300" cy="300" r="236" stroke="#A62B2B" strokeWidth="4" />
          <circle cx="300" cy="300" r="160" stroke="#C68A2C" strokeWidth="2" />
          <path
            d="M300 80 Q 420 120, 480 240 Q 520 380, 400 480 Q 280 540, 160 480 Q 60 400, 100 260 Q 140 140, 300 80 Z"
            stroke="#A62B2B"
            strokeWidth="12"
            fill="none"
          />
          <path
            d="M300 140 Q 380 180, 400 260 Q 420 340, 360 400 Q 280 440, 220 400 Q 160 340, 180 260 Q 200 180, 300 140 Z"
            stroke="#C68A2C"
            strokeWidth="8"
            fill="none"
          />
          <circle cx="300" cy="300" r="48" fill="#A62B2B" stroke="#C68A2C" strokeWidth="4" />
        </svg>
      </div>

      {/* Certificate Content Interior */}
      <div className="relative z-10 h-full w-full flex flex-col p-6 sm:p-9 md:p-12 print:p-8">
        {children}
      </div>
    </div>
  );
}

export default CertificateFrame;
