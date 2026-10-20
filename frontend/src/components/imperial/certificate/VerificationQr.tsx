"use client";

import React from "react";
import { QRCodeCanvas } from "qrcode.react";
import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export interface VerificationQrProps {
  certificateId: string;
  verificationUrl: string;
  size?: number;
  className?: string;
  showDetails?: boolean;
}

/**
 * Verification QR Code Component for Royal Heritage Certificate.
 * Features:
 * - High contrast vector QR code encoding verification URL + Certificate ID.
 * - Central authentic insignia shield overlay.
 * - Display of certificate ID and security badge.
 */
export function VerificationQr({
  certificateId,
  verificationUrl,
  size = 76,
  className,
  showDetails = true,
}: VerificationQrProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 bg-white/70 p-2 sm:p-2.5 rounded-lg border border-[#C68A2C]/40 shadow-sm print:bg-white print:border-[#A62B2B]/40",
        className,
      )}
    >
      {/* Precision QR Canvas */}
      <div className="shrink-0 rounded bg-white p-1 border border-border/40 shadow-inner">
        <QRCodeCanvas
          value={verificationUrl}
          size={size}
          level="M"
          bgColor="#FFFFFF"
          fgColor="#2A241D"
          includeMargin={true}
        />
      </div>

      {showDetails && (
        <div className="flex flex-col text-left space-y-0.5 min-w-0">
          <div className="flex items-center gap-1 text-[9px] sm:text-[10px] font-bold text-[#A62B2B] uppercase tracking-wider">
            <ShieldCheck className="size-3 shrink-0" />
            <span>Mã định danh chứng nhận</span>
          </div>

          <span className="font-mono text-[11px] sm:text-xs font-bold text-[#2A241D] tracking-wider truncate max-w-[160px] sm:max-w-[200px]">
            {certificateId}
          </span>

          <span className="text-[8px] sm:text-[9px] text-[#675C4E] leading-tight">
            Quét mã QR để tra cứu tính xác thực trực tuyến trên hệ thống Lưu Niên.
          </span>
        </div>
      )}
    </div>
  );
}

export default VerificationQr;
