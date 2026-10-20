"use client";

import React, { useEffect, useState } from "react";
import { Loader2, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { ArtDetailCard } from "./ArtDetailCard";
import { fetchArtDetail } from "@/lib/imperial/v51-api";
import type { ImperialArtDetail } from "@/lib/imperial/v51-types";

interface ArtDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  artDetail?: ImperialArtDetail | null;
  detailSlug?: string | null;
  variant?: "dialog" | "sheet";
}

export function ArtDetailModal({
  isOpen,
  onClose,
  artDetail: initialDetail,
  detailSlug,
  variant = "dialog",
}: ArtDetailModalProps) {
  const [detail, setDetail] = useState<ImperialArtDetail | null>(initialDetail || null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialDetail) {
      setDetail(initialDetail);
      return;
    }

    if (isOpen && detailSlug) {
      let isMounted = true;
      setLoading(true);
      fetchArtDetail(detailSlug)
        .then((res) => {
          if (isMounted) setDetail(res);
        })
        .finally(() => {
          if (isMounted) setLoading(false);
        });

      return () => {
        isMounted = false;
      };
    }
  }, [isOpen, detailSlug, initialDetail]);

  const content = (
    <div className="relative">
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm">Đang tải hồ sơ mỹ thuật di sản...</p>
        </div>
      ) : detail ? (
        <ArtDetailCard detail={detail} />
      ) : (
        <div className="py-16 text-center text-sm text-muted-foreground">
          Không tìm thấy thông tin chi tiết mỹ thuật này.
        </div>
      )}
    </div>
  );

  if (variant === "sheet") {
    return (
      <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <SheetContent
          side="right"
          className="w-full sm:max-w-2xl overflow-y-auto p-6 bg-background/95 backdrop-blur-md"
        >
          <SheetHeader className="sr-only">
            <SheetTitle>{detail?.title || "Chi tiết mỹ thuật di sản"}</SheetTitle>
            <SheetDescription>
              Hồ sơ khảo cứu mỹ thuật và điển tích lịch sử Đại Nội Huế
            </SheetDescription>
          </SheetHeader>
          {content}
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto p-6 sm:p-8 bg-background/95 backdrop-blur-md border-border/80">
        <DialogHeader className="sr-only">
          <DialogTitle>{detail?.title || "Chi tiết mỹ thuật di sản"}</DialogTitle>
          <DialogDescription>
            Hồ sơ khảo cứu mỹ thuật và điển tích lịch sử Đại Nội Huế
          </DialogDescription>
        </DialogHeader>
        {content}
      </DialogContent>
    </Dialog>
  );
}
